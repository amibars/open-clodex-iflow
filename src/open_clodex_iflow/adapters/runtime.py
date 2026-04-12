from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from open_clodex_iflow.contracts import ArtifactPacket, ProviderReview, write_json

RUNTIME_PROVIDERS = ("claude", "iflow", "opencode")


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
    python_executable: Path | None = None,
) -> list[str]:
    prefix = command_prefix(binary, python_executable)
    if provider == "claude":
        return [*prefix, "-p", prompt]
    if provider == "iflow":
        return [*prefix, "-p", prompt, "--plan", "-o", str(output_file)]
    if provider == "opencode":
        return [*prefix, "run", "--format", "json", "--dir", str(workdir), prompt]
    raise ValueError(f"Unsupported provider for runtime execution: {provider}")


def stringify_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def find_review_payload(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if "verdict" in value:
            return value
        for nested in value.values():
            match = find_review_payload(nested)
            if match is not None:
                return match
        return None

    if isinstance(value, list):
        for item in value:
            match = find_review_payload(item)
            if match is not None:
                return match
        return None

    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                return None
            return find_review_payload(parsed)
    return None


def parse_review_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("provider output is empty")

    candidates: list[Any] = []
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

    if not candidates and "{" in stripped and "}" in stripped:
        start = stripped.find("{")
        end = stripped.rfind("}") + 1
        try:
            candidates.append(json.loads(stripped[start:end]))
        except json.JSONDecodeError as exc:
            raise ValueError("provider output did not contain valid JSON") from exc

    for candidate in candidates:
        payload = find_review_payload(candidate)
        if payload is not None:
            return payload

    raise ValueError("provider output did not contain a review payload")


def normalize_review(
    provider: str,
    payload: dict[str, Any],
    *,
    runtime_mode: str,
    raw_output_file: Path,
    log_file: Path,
) -> ProviderReview:
    verdict = str(payload.get("verdict", "block"))
    if verdict not in {"proceed", "fix_code", "fix_plan", "block"}:
        raise ValueError(f"unsupported verdict: {verdict}")
    return ProviderReview(
        provider=provider,
        review_stage="runtime",
        verdict=verdict,
        summary=str(payload.get("summary", f"{provider} completed review")),
        blocking_findings=stringify_list(payload.get("blocking_findings")),
        non_blocking_notes=stringify_list(payload.get("non_blocking_notes")),
        tests_to_add=stringify_list(payload.get("tests_to_add")),
        plan_risks=stringify_list(payload.get("plan_risks")),
        confidence=str(payload.get("confidence", "medium")),
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
) -> tuple[int, str, str]:
    completed = subprocess.run(
        command,
        cwd=workdir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout_seconds,
        check=False,
    )
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    return completed.returncode, completed.stdout, completed.stderr


def execute_visible(
    provider: str,
    *,
    command: list[str],
    workdir: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: int,
) -> tuple[int, str, str]:
    process = subprocess.Popen(
        command,
        cwd=workdir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    collected: list[str] = []
    try:
        assert process.stdout is not None
        for line in process.stdout:
            collected.append(line)
            print(f"[{provider}] {line}", end="")
        return_code = process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        raise exc

    stdout_text = "".join(collected)
    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text("", encoding="utf-8")
    return return_code, stdout_text, ""


def run_provider_review(
    provider: str,
    *,
    artifact: ArtifactPacket,
    metadata: dict[str, object],
    output_dir: Path,
    runtime_mode: str,
    timeout_seconds: int = 180,
    python_executable: Path | None = None,
) -> ProviderReview:
    output_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = output_dir / "stdout.txt"
    stderr_path = output_dir / "stderr.txt"
    raw_output_path = output_dir / "raw_output.txt"
    review_path = output_dir / "review.json"

    binary = str(metadata["binary"])
    prompt = build_review_prompt(provider, artifact)
    command = build_provider_command(
        provider,
        binary=binary,
        prompt=prompt,
        output_file=raw_output_path,
        workdir=Path.cwd(),
        python_executable=python_executable,
    )

    try:
        if runtime_mode == "windowed":
            return_code, stdout_text, stderr_text = execute_visible(
                provider,
                command=command,
                workdir=Path.cwd(),
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                timeout_seconds=timeout_seconds,
            )
        else:
            return_code, stdout_text, stderr_text = execute_headless(
                provider,
                command=command,
                workdir=Path.cwd(),
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                timeout_seconds=timeout_seconds,
            )
    except subprocess.TimeoutExpired:
        stdout_path.write_text(
            f"{provider} timed out after {timeout_seconds}s before stdout could be collected.\n",
            encoding="utf-8",
        )
        stderr_path.write_text("", encoding="utf-8")
        raw_output_path.write_text("", encoding="utf-8")
        review = synthetic_failure_review(
            provider,
            f"{provider} timed out after {timeout_seconds}s",
            runtime_mode=runtime_mode,
            raw_output_file=raw_output_path,
            log_file=stdout_path,
        )
        write_json(review_path, review)
        return review

    source_text = stdout_text
    if provider == "iflow" and raw_output_path.exists():
        source_text = raw_output_path.read_text(encoding="utf-8")
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
