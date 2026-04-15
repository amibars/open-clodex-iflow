from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from open_clodex_iflow.contracts import ArtifactPacket, ProviderReview, write_json

RUNTIME_PROVIDERS = ("claude", "iflow", "opencode")
ALLOWED_VERDICTS = {"proceed", "fix_code", "fix_plan", "block"}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}
REQUIRED_REVIEW_KEYS = {
    "provider",
    "verdict",
    "summary",
    "blocking_findings",
    "non_blocking_notes",
    "tests_to_add",
    "plan_risks",
    "confidence",
}


def runnable_provider_names(
    snapshot: dict[str, dict[str, object]],
    requested_providers: list[str] | None = None,
) -> list[str]:
    candidates = requested_providers or list(RUNTIME_PROVIDERS)
    return [
        provider
        for provider in candidates
        if provider in RUNTIME_PROVIDERS
        and snapshot.get(provider, {}).get("available")
        and snapshot.get(provider, {}).get("binary")
    ]


def command_prefix(binary: str, python_executable: Path | None = None) -> list[str]:
    if binary.endswith(".py"):
        return [str(python_executable or Path(sys.executable)), binary]
    return [binary]


def build_review_prompt(provider: str, artifact: ArtifactPacket) -> str:
    artifact_payload = json.dumps(artifact.to_dict(), sort_keys=True)
    if provider == "claude":
        return (
            "Return exactly one minified JSON object and nothing else.\n"
            "Do not use markdown, code fences, explanations, or preambles.\n"
            "Do not ask follow-up questions.\n"
            "Do not inspect the workspace or infer extra context from cwd.\n"
            "Treat the artifact JSON below as the complete context.\n"
            f'Set "provider" to "{provider}".\n'
            "Required keys: provider, verdict, summary, blocking_findings, non_blocking_notes, "
            "tests_to_add, plan_risks, confidence.\n"
            "Allowed verdict values: proceed, fix_code, fix_plan, block.\n"
            f"ARTIFACT_JSON={artifact_payload}\n"
        )
    if provider == "iflow":
        compact_payload = json.dumps(artifact.to_dict(), separators=(",", ":"), sort_keys=True)
        return (
            "Review this artifact and reply with exactly one minified JSON object. "
            "Use keys provider, verdict, summary, blocking_findings, non_blocking_notes, "
            "tests_to_add, plan_risks, confidence. "
            "provider must be iflow. "
            "verdict must be one of proceed, fix_code, fix_plan, block. "
            "confidence must be one of low, medium, high. "
            f"Artifact: {compact_payload}"
        )

    artifact_payload = json.dumps(artifact.to_dict(), indent=2, sort_keys=True)
    return (
        f"You are the {provider} review lane for open-clodex-iflow.\n"
        "Review the structured artifact below and return ONLY one JSON object.\n"
        "Required keys: provider, verdict, summary, blocking_findings, non_blocking_notes, "
        "tests_to_add, plan_risks, confidence.\n"
        "Allowed verdict values: proceed, fix_code, fix_plan, block.\n"
        "Artifact:\n"
        f"{artifact_payload}\n"
    )


def build_provider_command(
    provider: str,
    *,
    binary: str,
    prompt: str,
    output_file: Path,
    workdir: Path,
    timeout_seconds: int,
    python_executable: Path | None = None,
) -> list[str]:
    prefix = command_prefix(binary, python_executable)
    if provider == "claude":
        return [*prefix, "-p", prompt]
    if provider == "iflow":
        return [
            *prefix,
            "-p",
            prompt,
            "--max-turns",
            "1",
            "--timeout",
            str(timeout_seconds),
            "--stream",
            "false",
        ]
    if provider == "opencode":
        return [*prefix, "run", "--format", "json", "--dir", str(workdir), prompt]
    raise ValueError(f"Unsupported provider for runtime execution: {provider}")


def execution_workdir(provider: str, output_dir: Path, project_root: Path) -> Path:
    if provider == "opencode":
        return project_root
    isolated_dir = output_dir / "workspace"
    isolated_dir.mkdir(parents=True, exist_ok=True)
    return isolated_dir


def provider_runtime_env(provider: str, metadata: dict[str, object]) -> dict[str, str]:
    if provider != "iflow":
        return {}

    state_dirs = metadata.get("state_dirs")
    if not isinstance(state_dirs, list):
        return {}

    for candidate in state_dirs:
        state_dir = Path(str(candidate))
        if state_dir.name.lower() != ".iflow":
            continue
        home_dir = state_dir.parent
        home_text = str(home_dir)
        home_drive = home_dir.drive
        home_path = home_text[len(home_drive) :] if home_drive else home_text
        return {
            "HOME": home_text,
            "USERPROFILE": home_text,
            "HOMEDRIVE": home_drive,
            "HOMEPATH": home_path,
        }

    return {}


def stringify_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def is_review_payload(value: Any) -> bool:
    return isinstance(value, dict) and REQUIRED_REVIEW_KEYS.issubset(value.keys())


def parse_json_candidate(value: str) -> Any | None:
    stripped = value.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        fenced_lines = stripped.splitlines()
        if len(fenced_lines) >= 3:
            stripped = "\n".join(fenced_lines[1:-1]).strip()
    if not stripped or stripped[0] not in "{[":
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def strip_execution_info(text: str) -> str:
    marker = "<Execution Info>"
    if marker not in text:
        return text
    return text.split(marker, 1)[0].rstrip()


def find_review_payload(value: Any) -> dict[str, Any] | None:
    if is_review_payload(value):
        return value

    if isinstance(value, list):
        for item in value:
            match = find_review_payload(item)
            if match is not None:
                return match
        return None

    if isinstance(value, dict):
        part = value.get("part")
        if isinstance(part, dict):
            text_value = part.get("text")
            if isinstance(text_value, str):
                parsed = parse_json_candidate(text_value)
                if parsed is not None:
                    return find_review_payload(parsed)
        return None

    if isinstance(value, str):
        parsed = parse_json_candidate(value)
        if parsed is not None:
            return find_review_payload(parsed)
    return None


def parse_review_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("provider output is empty")

    candidates: list[Any] = []
    whole_text_candidate = parse_json_candidate(stripped)
    if whole_text_candidate is not None:
        candidates.append(whole_text_candidate)

    try:
        candidates.append(json.loads(stripped))
    except json.JSONDecodeError:
        pass

    for line in stripped.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            candidates.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    for candidate in candidates:
        payload = find_review_payload(candidate)
        if payload is not None:
            return payload

    raise ValueError("provider output did not contain a review payload")


def normalize_confidence(value: Any) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ALLOWED_CONFIDENCE:
            return normalized
        try:
            value = float(normalized)
        except ValueError as exc:
            raise ValueError(f"unsupported confidence: {value}") from exc

    if isinstance(value, (int, float)):
        numeric = float(value)
        if 0.0 <= numeric <= 1.0:
            if numeric < 0.34:
                return "low"
            if numeric < 0.67:
                return "medium"
            return "high"
        if 0.0 <= numeric <= 100.0:
            if numeric < 34.0:
                return "low"
            if numeric < 67.0:
                return "medium"
            return "high"

    raise ValueError(f"unsupported confidence: {value}")


def normalize_review(
    provider: str,
    payload: dict[str, Any],
    *,
    runtime_mode: str,
    raw_output_file: Path,
    log_file: Path,
) -> ProviderReview:
    provider_name = str(payload.get("provider", ""))
    if provider_name != provider:
        raise ValueError(f"provider field mismatch: expected {provider}, got {provider_name or 'empty'}")

    verdict = str(payload.get("verdict", "block"))
    if verdict not in ALLOWED_VERDICTS:
        raise ValueError(f"unsupported verdict: {verdict}")
    confidence = normalize_confidence(payload.get("confidence", "medium"))
    return ProviderReview(
        provider=provider,
        review_stage="runtime",
        verdict=verdict,
        summary=str(payload.get("summary", f"{provider} completed review")),
        blocking_findings=stringify_list(payload.get("blocking_findings")),
        non_blocking_notes=stringify_list(payload.get("non_blocking_notes")),
        tests_to_add=stringify_list(payload.get("tests_to_add")),
        plan_risks=stringify_list(payload.get("plan_risks")),
        confidence=confidence,
        runtime_mode=runtime_mode,
        raw_output_file=str(raw_output_file),
        log_file=str(log_file),
    )


def synthetic_failure_review(
    provider: str,
    reason: str,
    *,
    runtime_mode: str,
    raw_output_file: Path,
    log_file: Path,
) -> ProviderReview:
    return ProviderReview(
        provider=provider,
        review_stage="synthetic-failure",
        verdict="block",
        summary=f"{provider} runtime failed before producing a valid review",
        blocking_findings=[reason],
        non_blocking_notes=[],
        tests_to_add=[],
        plan_risks=[f"{provider} runtime is not stable enough for trustworthy review"],
        confidence="high",
        runtime_mode=runtime_mode,
        raw_output_file=str(raw_output_file),
        log_file=str(log_file),
    )


def execute_headless(
    provider: str,
    *,
    command: list[str],
    workdir: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: int,
    extra_env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    process_env = os.environ.copy()
    process_env.update(extra_env or {})
    completed = subprocess.run(
        command,
        cwd=workdir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout_seconds,
        check=False,
        env=process_env,
    )
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    return completed.returncode, completed.stdout, completed.stderr


def _visible_stdout_reader(
    process: subprocess.Popen[str],
    provider: str,
    collected: list[str],
) -> None:
    assert process.stdout is not None
    for line in iter(process.stdout.readline, ""):
        collected.append(line)
        print(f"[{provider}] {line}", end="")
    process.stdout.close()


def execute_visible(
    provider: str,
    *,
    command: list[str],
    workdir: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: int,
    extra_env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    process_env = os.environ.copy()
    process_env.update(extra_env or {})
    process = subprocess.Popen(
        command,
        cwd=workdir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
        env=process_env,
    )
    collected: list[str] = []
    reader = threading.Thread(
        target=_visible_stdout_reader,
        args=(process, provider, collected),
        daemon=True,
    )
    reader.start()
    deadline = time.monotonic() + timeout_seconds
    try:
        while True:
            return_code = process.poll()
            if return_code is not None:
                break
            if time.monotonic() >= deadline:
                process.kill()
                process.wait()
                reader.join(timeout=1)
                raise subprocess.TimeoutExpired(
                    command,
                    timeout_seconds,
                    output="".join(collected),
                )
            reader.join(timeout=0.1)
    except subprocess.TimeoutExpired as exc:
        raise exc
    finally:
        reader.join(timeout=1)

    stdout_text = "".join(collected)
    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text("", encoding="utf-8")
    return return_code, stdout_text, ""


def select_runner(runtime_mode: str):
    runners = {
        "headless": execute_headless,
        "windowed": execute_visible,
    }
    try:
        return runners[runtime_mode]
    except KeyError as exc:
        raise ValueError(f"unsupported runtime mode: {runtime_mode}") from exc


def run_provider_review(
    provider: str,
    *,
    artifact: ArtifactPacket,
    metadata: dict[str, object],
    output_dir: Path,
    runtime_mode: str,
    timeout_seconds: int = 180,
    python_executable: Path | None = None,
    provider_override: dict[str, object] | None = None,
) -> ProviderReview:
    output_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = output_dir / "stdout.txt"
    stderr_path = output_dir / "stderr.txt"
    raw_output_path = output_dir / "raw_output.txt"
    review_path = output_dir / "review.json"
    project_root = Path.cwd()
    provider_workdir = execution_workdir(provider, output_dir, project_root)

    binary = str(metadata["binary"])
    prompt = build_review_prompt(provider, artifact)
    command = build_provider_command(
        provider,
        binary=binary,
        prompt=prompt,
        output_file=raw_output_path,
        workdir=project_root,
        timeout_seconds=timeout_seconds,
        python_executable=python_executable,
    )
    runner = select_runner(runtime_mode)
    extra_env = provider_runtime_env(provider, metadata)
    if provider_override:
        env_map = provider_override.get("env", {})
        if isinstance(env_map, dict):
            extra_env.update({str(key): str(value) for key, value in env_map.items()})

    try:
        return_code, stdout_text, stderr_text = runner(
            provider,
            command=command,
            workdir=provider_workdir,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            timeout_seconds=timeout_seconds,
            extra_env=extra_env,
        )
    except subprocess.TimeoutExpired as exc:
        timeout_note = f"{provider} timed out after {timeout_seconds}s"
        partial_stdout = ""
        if exc.output:
            partial_stdout = (
                exc.output.decode("utf-8", errors="replace")
                if isinstance(exc.output, bytes)
                else str(exc.output)
            )
        if partial_stdout and not partial_stdout.endswith("\n"):
            partial_stdout += "\n"
        stdout_path.write_text(
            partial_stdout + f"{timeout_note} before stdout could be collected.\n",
            encoding="utf-8",
        )
        stderr_path.write_text("", encoding="utf-8")
        raw_output_path.write_text(partial_stdout, encoding="utf-8")
        review = synthetic_failure_review(
            provider,
            timeout_note,
            runtime_mode=runtime_mode,
            raw_output_file=raw_output_path,
            log_file=stdout_path,
        )
        write_json(review_path, review)
        return review

    source_text = stdout_text
    if provider == "iflow":
        source_text = strip_execution_info(stdout_text)
        raw_output_path.write_text(source_text, encoding="utf-8")
    else:
        raw_output_path.write_text(source_text, encoding="utf-8")

    if return_code != 0:
        review = synthetic_failure_review(
            provider,
            f"{provider} exited with code {return_code}: {(stderr_text or stdout_text).strip()}",
            runtime_mode=runtime_mode,
            raw_output_file=raw_output_path,
            log_file=stdout_path,
        )
        write_json(review_path, review)
        return review

    try:
        if provider == "iflow":
            payload = parse_review_text(source_text)
        else:
            payload = parse_review_text(source_text)
        review = normalize_review(
            provider,
            payload,
            runtime_mode=runtime_mode,
            raw_output_file=raw_output_path,
            log_file=stdout_path,
        )
    except ValueError as exc:
        review = synthetic_failure_review(
            provider,
            f"{provider} returned invalid review payload: {exc}",
            runtime_mode=runtime_mode,
            raw_output_file=raw_output_path,
            log_file=stdout_path,
        )

    write_json(review_path, review)
    return review
