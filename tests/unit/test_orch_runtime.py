from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from open_clodex_iflow.contracts import ArtifactPacket
from open_clodex_iflow.adapters import runtime as runtime_module
from open_clodex_iflow.lanes import list_lane_presets
from open_clodex_iflow.orchestration.runtime import run_orchestration


def write_fake_provider_script(path: Path, provider: str, *, verdict: str = "proceed", invalid: bool = False) -> None:
    script = f"""
from __future__ import annotations

import json
import sys
from pathlib import Path

provider = {provider!r}
invalid = {invalid!r}
verdict = {verdict!r}
args = sys.argv[1:]
output_file = None
for index, value in enumerate(args):
    if value in ("-o", "--output-file"):
        output_file = args[index + 1]
        break

payload = "not-json" if invalid else json.dumps({{
    "provider": provider,
    "verdict": verdict,
    "summary": f"{{provider}} completed review",
    "blocking_findings": [] if verdict != "block" else [f"{{provider}} blocking finding"],
    "non_blocking_notes": [f"{{provider}} note"],
    "tests_to_add": [f"{{provider}} regression test"],
    "plan_risks": [f"{{provider}} runtime risk"],
    "confidence": "medium",
}})

if output_file:
    Path(output_file).write_text(payload, encoding="utf-8")
else:
    print(payload)
"""
    path.write_text(script.strip() + "\n", encoding="utf-8")


def write_sleeping_provider_script(path: Path, provider: str, *, seconds: int) -> None:
    script = f"""
from __future__ import annotations

import time

time.sleep({seconds})
    """
    path.write_text(script.strip() + "\n", encoding="utf-8")


def write_partial_output_provider_script(path: Path, *, seconds: int) -> None:
    script = f"""
from __future__ import annotations

import sys
import time

sys.stdout.write("partial")
sys.stdout.flush()
time.sleep({seconds})
"""
    path.write_text(script.strip() + "\n", encoding="utf-8")


def write_valid_payload_then_sleep_provider_script(path: Path, provider: str, *, seconds: int) -> None:
    script = f"""
from __future__ import annotations

import json
import sys
import time

print(json.dumps({{
    "provider": "{provider}",
    "verdict": "proceed",
    "summary": "{provider} emitted a review before timing out",
    "blocking_findings": [],
    "non_blocking_notes": [],
    "tests_to_add": [],
    "plan_risks": [],
    "confidence": "high"
}}))
sys.stdout.flush()
time.sleep({seconds})
"""
    path.write_text(script.strip() + "\n", encoding="utf-8")


def write_parallel_sleep_provider_script(path: Path, provider: str, *, seconds: float) -> None:
    script = f"""
from __future__ import annotations

import json
import sys
import time

args = sys.argv[1:]
model = ""
for index, value in enumerate(args):
    if value in ("--model", "-m") and index + 1 < len(args):
        model = args[index + 1]
        break

time.sleep({seconds})

print(json.dumps({{
    "provider": {provider!r},
    "verdict": "proceed",
    "summary": model or "provider-default",
    "blocking_findings": [],
    "non_blocking_notes": [],
    "tests_to_add": [],
    "plan_risks": [],
    "confidence": "high"
}}))
"""
    path.write_text(script.strip() + "\n", encoding="utf-8")


def write_lock_sensitive_provider_script(path: Path, lock_path: Path, *, seconds: float) -> None:
    script = f"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

lock_path = Path({str(lock_path)!r})
args = sys.argv[1:]
model = ""
for index, value in enumerate(args):
    if value in ("--model", "-m") and index + 1 < len(args):
        model = args[index + 1]
        break

if lock_path.exists():
    print("provider concurrency lock collision", file=sys.stderr)
    raise SystemExit(17)

lock_path.write_text(model or "provider-default", encoding="utf-8")
try:
    time.sleep({seconds})
finally:
    lock_path.unlink(missing_ok=True)

print(json.dumps({{
    "provider": "opencode",
    "verdict": "proceed",
    "summary": model or "provider-default",
    "blocking_findings": [],
    "non_blocking_notes": [],
    "tests_to_add": [],
    "plan_risks": [],
    "confidence": "high"
}}))
"""
    path.write_text(script.strip() + "\n", encoding="utf-8")


def write_model_sensitive_timeout_provider_script(path: Path, *, timeout_model: str, seconds: int) -> None:
    script = f"""
from __future__ import annotations

import json
import sys
import time

args = sys.argv[1:]
model = ""
for index, value in enumerate(args):
    if value == "--model" and index + 1 < len(args):
        model = args[index + 1]
        break

if model == {timeout_model!r}:
    sys.stdout.write("partial timeout lane")
    sys.stdout.flush()
    time.sleep({seconds})
else:
    print(json.dumps({{
        "provider": "opencode",
        "verdict": "proceed",
        "summary": model or "provider-default",
        "blocking_findings": [],
        "non_blocking_notes": [],
        "tests_to_add": [],
        "plan_risks": [],
        "confidence": "high"
    }}))
"""
    path.write_text(script.strip() + "\n", encoding="utf-8")


def write_nested_payload_provider_script(path: Path, provider: str) -> None:
    script = f"""
from __future__ import annotations

import json

print(json.dumps({{"meta": {{"provider": "{provider}", "verdict": "proceed"}}}}))
"""
    path.write_text(script.strip() + "\n", encoding="utf-8")


def write_invalid_confidence_provider_script(path: Path, provider: str) -> None:
    script = f"""
from __future__ import annotations

import json

print(json.dumps({{
    "provider": "{provider}",
    "verdict": "proceed",
    "summary": "{provider} completed review",
    "blocking_findings": [],
    "non_blocking_notes": [],
    "tests_to_add": [],
    "plan_risks": [],
    "confidence": "whatever"
}}))
    """
    path.write_text(script.strip() + "\n", encoding="utf-8")


def write_incidental_json_provider_script(path: Path, provider: str) -> None:
    review_payload = {
        "provider": provider,
        "verdict": "proceed",
        "summary": "payload hidden inside logs",
        "blocking_findings": [],
        "non_blocking_notes": [],
        "tests_to_add": [],
        "plan_risks": [],
        "confidence": "high",
    }
    script = f"""
from __future__ import annotations

import json

print("runtime: boot")
print("runtime: " + json.dumps({review_payload!r}) + " :runtime")
print("runtime: done")
"""
    path.write_text(script.strip() + "\n", encoding="utf-8")


def write_wrapped_opencode_payload_provider_script(path: Path, provider: str) -> None:
    review_payload = {
        "provider": provider,
        "verdict": "fix_plan",
        "summary": "wrapped payload",
        "blocking_findings": ["missing changed_files"],
        "non_blocking_notes": ["binary available"],
        "tests_to_add": [],
        "plan_risks": ["empty packet"],
        "confidence": 0.95,
    }
    event_lines = [
        {
            "type": "step_start",
            "timestamp": 1,
            "part": {"type": "step-start"},
        },
        {
            "type": "text",
            "timestamp": 2,
            "part": {
                "type": "text",
                "text": json.dumps(review_payload, indent=2),
            },
        },
        {
            "type": "step_finish",
            "timestamp": 3,
            "part": {"type": "step-finish", "reason": "stop"},
        },
    ]
    script = f"""
from __future__ import annotations

import json

for line in {event_lines!r}:
    print(json.dumps(line))
"""
    path.write_text(script.strip() + "\n", encoding="utf-8")


def write_env_sensitive_provider_script(path: Path, provider: str, env_var: str) -> None:
    script = f"""
from __future__ import annotations

import json
import os

value = os.environ.get("{env_var}", "")
print(json.dumps({{
    "provider": "{provider}",
    "verdict": "proceed" if value == "https://llm.local" else "block",
    "summary": value or "missing-override",
    "blocking_findings": [] if value == "https://llm.local" else ["override missing"],
    "non_blocking_notes": [],
    "tests_to_add": [],
    "plan_risks": [],
    "confidence": "high"
}}))
"""
    path.write_text(script.strip() + "\n", encoding="utf-8")


def write_cwd_sensitive_provider_script(path: Path, provider: str, forbidden_cwd: str) -> None:
    script = f"""
from __future__ import annotations

import json
import sys
from pathlib import Path

provider = {provider!r}
forbidden_cwd = Path({forbidden_cwd!r})
args = sys.argv[1:]
output_file = None
for index, value in enumerate(args):
    if value in ("-o", "--output-file"):
        output_file = args[index + 1]
        break

current_cwd = Path.cwd()
payload = json.dumps({{
    "provider": provider,
    "verdict": "block" if current_cwd == forbidden_cwd else "proceed",
    "summary": str(current_cwd),
    "blocking_findings": ["provider executed from repo root"] if current_cwd == forbidden_cwd else [],
    "non_blocking_notes": [],
    "tests_to_add": [],
    "plan_risks": [],
    "confidence": "high",
}})

if output_file:
    Path(output_file).write_text(payload, encoding="utf-8")
else:
    print(payload)
"""
    path.write_text(script.strip() + "\n", encoding="utf-8")


def test_review_prompt_marks_unplanned_missing_providers_as_non_blocking():
    artifact = ArtifactPacket(
        trace_id="trace-test",
        generated_at="2026-04-30T00:00:00Z",
        mode="orch",
        task="review default lane",
        runtime_mode="headless",
        packet_stage="runtime-execution",
        privacy_boundary="structured-packet-only",
        fan_out_requested=True,
        planned_providers=["opencode"],
        planned_lanes=["opencode-minimax-plan"],
        provider_snapshot={
            "iflow": {"available": False, "binary": None, "readiness": "missing"},
            "opencode": {"available": True, "binary": "opencode", "readiness": "binary+state"},
        },
        next_step="Inspect runtime reviews.",
    )

    prompt = runtime_module.build_review_prompt("opencode", artifact)

    assert "Only evaluate planned_providers and planned_lanes" in prompt
    assert "not blocking when that provider is not planned" in prompt


def test_review_prompt_includes_lane_lens_without_narrowing_scope():
    artifact = ArtifactPacket(
        trace_id="trace-test",
        generated_at="2026-04-30T00:00:00Z",
        mode="orch",
        task="review adapter runtime",
        runtime_mode="headless",
        packet_stage="runtime-execution",
        privacy_boundary="structured-packet-only",
        fan_out_requested=True,
        planned_providers=["opencode"],
        planned_lanes=["nvidia-devstral2-plan"],
        provider_snapshot={
            "opencode": {"available": True, "binary": "opencode", "readiness": "binary+state"},
        },
        next_step="Inspect runtime reviews.",
    )
    lane = list_lane_presets()["nvidia-devstral2-plan"]

    prompt = runtime_module.build_review_prompt("opencode", artifact, lane=lane)

    assert "Review the full artifact." in prompt
    assert "Your primary lens is implementation/code/runtime/test reviewer" in prompt
    assert "Do not limit yourself to that lens." in prompt
    assert "Report any blocker you find." in prompt
    assert "Spend extra attention on your primary lens." in prompt


def write_iflow_stdout_provider_script(path: Path, provider: str) -> None:
    payload = {
        "provider": provider,
        "verdict": "proceed",
        "summary": "stdout payload",
        "blocking_findings": [],
        "non_blocking_notes": [],
        "tests_to_add": [],
        "plan_risks": [],
        "confidence": "medium",
    }
    script = f"""
from __future__ import annotations

import json
import sys
from pathlib import Path

args = sys.argv[1:]
output_file = None
for index, value in enumerate(args):
    if value in ("-o", "--output-file"):
        output_file = args[index + 1]
        break

print(json.dumps({payload!r}))
print()
print("<Execution Info>")
print(json.dumps({{"session-id": "sess-123", "assistantRounds": 1}}, indent=2))
print("</Execution Info>")

if output_file:
    Path(output_file).write_text(
        json.dumps({{"session-id": "sess-123", "assistantRounds": 1}}, indent=2),
        encoding="utf-8",
    )
"""
    path.write_text(script.strip() + "\n", encoding="utf-8")


def write_iflow_noisy_stdout_file_payload_provider_script(path: Path, provider: str) -> None:
    payload = {
        "provider": provider,
        "verdict": "proceed",
        "summary": "file payload",
        "blocking_findings": [],
        "non_blocking_notes": [],
        "tests_to_add": [],
        "plan_risks": [],
        "confidence": "medium",
    }
    script = f"""
from __future__ import annotations

import json
import sys
from pathlib import Path

args = sys.argv[1:]
output_file = None
for index, value in enumerate(args):
    if value in ("-o", "--output-file"):
        output_file = args[index + 1]
        break

print("booting iflow runtime")
if output_file:
    Path(output_file).write_text(json.dumps({payload!r}), encoding="utf-8")
"""
    path.write_text(script.strip() + "\n", encoding="utf-8")


def runtime_snapshot(tmp_path: Path, providers: dict[str, dict[str, str]]) -> dict[str, dict[str, object]]:
    snapshot: dict[str, dict[str, object]] = {}
    for name, config in providers.items():
        script_path = tmp_path / f"{name}.py"
        write_fake_provider_script(
            script_path,
            name,
            verdict=config.get("verdict", "proceed"),
            invalid=config.get("invalid", False),
        )
        snapshot[name] = {
            "available": True,
            "binary": str(script_path),
            "state_dirs": [f"C:/fake/{name}"],
        }
    snapshot["codex"] = {
        "available": True,
        "binary": "codex",
        "state_dirs": ["C:/fake/codex"],
    }
    return snapshot


def test_run_orchestration_emits_provider_reviews_and_aggregates_verdict(tmp_path):
    snapshot = runtime_snapshot(
        tmp_path,
        {
            "claude": {"verdict": "proceed"},
            "iflow": {"verdict": "fix_code"},
            "opencode": {"verdict": "proceed"},
        },
    )

    artifact, review = run_orchestration(
        task="audit repository runtime",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["claude", "iflow", "opencode"],
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert artifact.packet_stage == "runtime-execution"
    assert artifact.planned_providers == ["claude", "iflow", "opencode"]
    assert review.review_stage == "runtime"
    assert review.verdict == "fix_code"
    assert len(review.provider_reviews) == 3
    assert (tmp_path / "session" / "providers" / "claude" / "review.json").exists()
    assert (tmp_path / "session" / "providers" / "iflow" / "review.json").exists()
    assert (tmp_path / "session" / "session.log").exists()


def test_run_orchestration_defaults_to_lane_aware_planner_pack(tmp_path):
    snapshot = runtime_snapshot(
        tmp_path,
        {
            "iflow": {"verdict": "proceed"},
            "opencode": {"verdict": "proceed"},
        },
    )

    artifact, review = run_orchestration(
        task="default planner lanes",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert artifact.planned_providers == ["opencode"]
    assert artifact.planned_lanes == [
        "opencode-minimax-plan",
    ]
    assert len(review.provider_reviews) == 1
    assert (tmp_path / "session" / "providers" / "opencode-minimax-plan" / "review.json").exists()


def test_run_orchestration_parallel_execution_runs_different_providers_concurrently(tmp_path):
    opencode_script_path = tmp_path / "opencode.py"
    iflow_script_path = tmp_path / "iflow.py"
    write_parallel_sleep_provider_script(
        opencode_script_path,
        "opencode",
        seconds=0.8,
    )
    write_parallel_sleep_provider_script(
        iflow_script_path,
        "iflow",
        seconds=0.8,
    )
    snapshot = {
        "opencode": {
            "available": True,
            "binary": str(opencode_script_path),
            "state_dirs": ["C:/fake/opencode"],
        },
        "iflow": {
            "available": True,
            "binary": str(iflow_script_path),
            "state_dirs": ["C:/fake/iflow"],
        }
    }

    started = time.monotonic()
    _, review = run_orchestration(
        task="parallel smoke",
        runtime_mode="headless",
        execution_mode="parallel",
        provider_snapshot=snapshot,
        requested_lanes=["opencode-minimax-plan", "iflow-qwen3coder-plan"],
        timeout_seconds=5,
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )
    elapsed = time.monotonic() - started

    assert elapsed < 1.5
    assert review.verdict == "proceed"
    assert [item.lane_id for item in review.provider_reviews] == [
        "opencode-minimax-plan",
        "iflow-qwen3coder-plan",
    ]
    assert (tmp_path / "session" / "providers" / "opencode-minimax-plan" / "attempt.json").exists()
    assert (tmp_path / "session" / "providers" / "iflow-qwen3coder-plan" / "attempt.json").exists()
    session_log = (tmp_path / "session" / "session.log").read_text(encoding="utf-8")
    assert "execution_mode=parallel" in session_log


def test_run_orchestration_parallel_serializes_same_provider_lanes(tmp_path):
    script_path = tmp_path / "opencode.py"
    write_lock_sensitive_provider_script(
        script_path,
        tmp_path / "opencode.lock",
        seconds=0.2,
    )
    snapshot = {
        "opencode": {
            "available": True,
            "binary": str(script_path),
            "state_dirs": ["C:/fake/opencode"],
        }
    }

    _, review = run_orchestration(
        task="provider lock smoke",
        runtime_mode="headless",
        execution_mode="parallel",
        provider_snapshot=snapshot,
        requested_lanes=["opencode-minimax-plan", "nvidia-glm51-plan"],
        timeout_seconds=5,
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert review.verdict == "proceed"
    assert [item.review_stage for item in review.provider_reviews] == ["runtime", "runtime"]
    session_log = (tmp_path / "session" / "session.log").read_text(encoding="utf-8")
    assert "provider_concurrency=opencode:serialized:2" in session_log


def test_run_orchestration_parallel_timeout_does_not_cancel_sibling_lane(tmp_path):
    script_path = tmp_path / "opencode.py"
    write_model_sensitive_timeout_provider_script(
        script_path,
        timeout_model="nvidia/z-ai/glm-5.1",
        seconds=2,
    )
    snapshot = {
        "opencode": {
            "available": True,
            "binary": str(script_path),
            "state_dirs": ["C:/fake/opencode"],
        }
    }

    _, review = run_orchestration(
        task="parallel timeout isolation",
        runtime_mode="headless",
        execution_mode="parallel",
        provider_snapshot=snapshot,
        requested_lanes=["opencode-minimax-plan", "nvidia-glm51-plan"],
        timeout_seconds=1,
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    by_lane = {item.lane_id: item for item in review.provider_reviews}
    assert by_lane["opencode-minimax-plan"].review_stage == "runtime"
    assert by_lane["nvidia-glm51-plan"].review_stage == "synthetic-failure"
    timeout_attempt = json.loads(
        (tmp_path / "session" / "providers" / "nvidia-glm51-plan" / "attempt.json").read_text(
            encoding="utf-8"
        )
    )
    success_attempt = json.loads(
        (tmp_path / "session" / "providers" / "opencode-minimax-plan" / "attempt.json").read_text(
            encoding="utf-8"
        )
    )
    assert timeout_attempt["state"] == "timeout_incomplete"
    assert success_attempt["state"] == "completed"


def test_select_runner_returns_expected_execution_function():
    assert runtime_module.select_runner("headless") is runtime_module.execute_headless
    assert runtime_module.select_runner("windowed") is runtime_module.execute_visible
    assert runtime_module.select_runner("dedicated-windows") is runtime_module.execute_dedicated_windows


def test_dedicated_window_launch_command_uses_json_request_not_prompt_shell():
    command = runtime_module.build_dedicated_window_launch_command(
        title="trace-test opencode-minimax-plan",
        request_path=Path("C:/tmp/request.json"),
        python_executable=Path("C:/Python/python.exe"),
    )

    assert command[:5] == ["cmd.exe", "/d", "/s", "/c", "start"]
    assert "/wait" in command
    assert "-m" in command
    assert "open_clodex_iflow.adapters.window_command" in command
    assert "review prompt" not in " ".join(command).lower()


def test_execute_dedicated_windows_round_trips_request_and_status(monkeypatch, tmp_path):
    captured: dict[str, object] = {}
    stdout_path = tmp_path / "stdout.txt"
    stderr_path = tmp_path / "stderr.txt"

    monkeypatch.setattr(runtime_module, "dedicated_windows_available", lambda: True)

    def fake_run(command, **kwargs):
        request = json.loads(Path(command[-1]).read_text(encoding="utf-8"))
        captured["launch_command"] = command
        captured["request"] = request
        Path(request["stdout_path"]).write_text("captured stdout", encoding="utf-8")
        Path(request["stderr_path"]).write_text("captured stderr", encoding="utf-8")
        Path(request["status_path"]).write_text(
            json.dumps({"exit_code": 0, "timed_out": False}),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(runtime_module.subprocess, "run", fake_run)

    exit_code, stdout_text, stderr_text = runtime_module.execute_dedicated_windows(
        "opencode",
        command=[sys.executable, "-c", "print('hidden prompt never reaches shell')"],
        workdir=tmp_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_seconds=3,
        extra_env={"OCIFLOW_TEST": "1"},
    )

    request = captured["request"]
    assert exit_code == 0
    assert stdout_text == "captured stdout"
    assert stderr_text == "captured stderr"
    assert request["env"] == {"OCIFLOW_TEST": "1"}
    assert request["command"][0] == sys.executable
    assert captured["launch_command"][:5] == ["cmd.exe", "/d", "/s", "/c", "start"]


def test_execute_dedicated_windows_raises_timeout_from_status(monkeypatch, tmp_path):
    stdout_path = tmp_path / "stdout.txt"
    stderr_path = tmp_path / "stderr.txt"

    monkeypatch.setattr(runtime_module, "dedicated_windows_available", lambda: True)

    def fake_run(command, **kwargs):
        request = json.loads(Path(command[-1]).read_text(encoding="utf-8"))
        Path(request["stdout_path"]).write_text("partial stdout", encoding="utf-8")
        Path(request["stderr_path"]).write_text("partial stderr", encoding="utf-8")
        Path(request["status_path"]).write_text(
            json.dumps({"exit_code": None, "timed_out": True}),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 124, "", "")

    monkeypatch.setattr(runtime_module.subprocess, "run", fake_run)

    with pytest.raises(subprocess.TimeoutExpired) as excinfo:
        runtime_module.execute_dedicated_windows(
            "opencode",
            command=[sys.executable, "-c", "print('partial stdout')"],
            workdir=tmp_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            timeout_seconds=1,
        )

    assert excinfo.value.output == "partial stdout"
    assert excinfo.value.stderr == "partial stderr"


def test_parse_review_text_extracts_review_from_wrapped_opencode_events():
    review_payload = {
        "provider": "opencode",
        "verdict": "fix_plan",
        "summary": "wrapped payload",
        "blocking_findings": ["missing changed_files"],
        "non_blocking_notes": ["binary available"],
        "tests_to_add": [],
        "plan_risks": ["empty packet"],
        "confidence": 0.95,
    }
    wrapped = "\n".join(
        [
            json.dumps({"type": "step_start", "part": {"type": "step-start"}}),
            json.dumps({"type": "text", "part": {"type": "text", "text": json.dumps(review_payload)}}),
            json.dumps({"type": "step_finish", "part": {"type": "step-finish", "reason": "stop"}}),
        ]
    )

    payload = runtime_module.parse_review_text(wrapped)

    assert payload["provider"] == "opencode"
    assert payload["verdict"] == "fix_plan"


def test_normalize_review_accepts_numeric_confidence():
    review = runtime_module.normalize_review(
        "opencode",
        {
            "provider": "opencode",
            "verdict": "proceed",
            "summary": "numeric confidence payload",
            "blocking_findings": [],
            "non_blocking_notes": [],
            "tests_to_add": [],
            "plan_risks": [],
            "confidence": 0.95,
        },
        runtime_mode="headless",
        raw_output_file=Path("raw.json"),
        log_file=Path("stdout.txt"),
    )

    assert review.confidence == "high"


def test_run_orchestration_creates_synthetic_block_on_invalid_provider_output(tmp_path):
    snapshot = runtime_snapshot(
        tmp_path,
        {
            "claude": {"verdict": "proceed"},
            "iflow": {"invalid": True},
        },
    )

    artifact, review = run_orchestration(
        task="audit repository runtime",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["claude", "iflow"],
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert artifact.planned_providers == ["claude", "iflow"]
    assert review.verdict == "block"
    iflow_review = next(item for item in review.provider_reviews if item.provider == "iflow")
    assert iflow_review.review_stage == "synthetic-failure"
    assert iflow_review.blocking_findings


def test_run_orchestration_blocks_when_no_runnable_provider_exists(tmp_path):
    artifact, review = run_orchestration(
        task="audit repository runtime",
        runtime_mode="headless",
        provider_snapshot={
            "codex": {"available": True, "binary": "codex", "state_dirs": ["C:/fake/codex"]},
        },
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert artifact.planned_providers == []
    assert review.verdict == "block"
    assert review.blocking_findings
    assert not (tmp_path / "session" / "providers").exists()


def test_run_orchestration_respects_requested_providers(tmp_path):
    snapshot = runtime_snapshot(
        tmp_path,
        {
            "claude": {"verdict": "proceed"},
            "iflow": {"verdict": "proceed"},
        },
    )

    artifact, review = run_orchestration(
        task="review only claude",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["claude"],
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert artifact.planned_providers == ["claude"]
    assert review.verdict == "proceed"
    assert len(review.provider_reviews) == 1
    assert review.provider_reviews[0].provider == "claude"


def test_run_orchestration_timeout_writes_placeholder_log_files(tmp_path):
    script_path = tmp_path / "claude.py"
    write_sleeping_provider_script(script_path, "claude", seconds=2)
    snapshot = {
        "claude": {
            "available": True,
            "binary": str(script_path),
            "state_dirs": ["C:/fake/claude"],
        }
    }

    artifact, review = run_orchestration(
        task="slow provider smoke",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["claude"],
        timeout_seconds=1,
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert artifact.planned_providers == ["claude"]
    assert review.verdict == "block"
    assert (tmp_path / "session" / "providers" / "claude" / "stdout.txt").exists()
    assert (tmp_path / "session" / "providers" / "claude" / "raw_output.txt").exists()
    attempt = json.loads(
        (tmp_path / "session" / "providers" / "claude" / "attempt.json").read_text(
            encoding="utf-8"
        )
    )
    assert attempt["state"] == "timeout_incomplete"
    assert attempt["provider"] == "claude"
    assert attempt["lane_id"] == "claude"
    assert attempt["timeout_seconds"] == 1
    assert attempt["process_terminated"] is True
    assert attempt["exit_code"] is None
    assert attempt["retryable"] is False
    assert attempt["raw_output_file"].endswith("raw_output.txt")
    assert attempt["stdout_tail_file"].endswith("stdout.txt")
    assert attempt["stderr_tail_file"].endswith("stderr.txt")
    assert attempt["review_file"].endswith("review.json")
    assert "<review-prompt-redacted>" in attempt["command_shape"]


def test_run_orchestration_logs_dropped_requested_providers(tmp_path):
    snapshot = runtime_snapshot(
        tmp_path,
        {
            "opencode": {"verdict": "proceed"},
        },
    )

    artifact, review = run_orchestration(
        task="review selected providers",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["opencode", "missing", "codex"],
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    session_log = (tmp_path / "session" / "session.log").read_text(encoding="utf-8")
    assert artifact.planned_providers == ["opencode"]
    assert any("missing" in note for note in artifact.notes)
    assert any("codex" in note for note in artifact.notes)
    assert any("missing" in note for note in review.non_blocking_notes)
    assert any("codex" in note for note in review.non_blocking_notes)
    assert "dropped_requested_providers=missing,codex" in session_log


def test_run_orchestration_executes_claude_and_iflow_outside_repo_root(tmp_path):
    repo_root = str(Path.cwd())

    for provider in ("claude", "iflow"):
        script_path = tmp_path / f"{provider}.py"
        write_cwd_sensitive_provider_script(script_path, provider, repo_root)
        snapshot = {
            provider: {
                "available": True,
                "binary": str(script_path),
                "state_dirs": [f"C:/fake/{provider}"],
            }
        }

        _, review = run_orchestration(
            task=f"cwd isolation check for {provider}",
            runtime_mode="headless",
            provider_snapshot=snapshot,
            requested_providers=[provider],
            output_dir=tmp_path / f"{provider}-session",
            python_executable=Path(sys.executable),
        )

        provider_review = review.provider_reviews[0]
        assert review.verdict == "proceed"
        assert provider_review.review_stage == "runtime"
        assert provider_review.summary != repo_root


def test_parse_review_text_accepts_fenced_json_block():
    payload = """
```json
{
  "provider": "claude",
  "verdict": "proceed",
  "summary": "ok",
  "blocking_findings": [],
  "non_blocking_notes": [],
  "tests_to_add": [],
  "plan_risks": [],
  "confidence": "high"
}
```
"""

    parsed = runtime_module.parse_review_text(payload)

    assert parsed["provider"] == "claude"
    assert parsed["verdict"] == "proceed"


def test_parse_review_text_accepts_warning_prefix_before_fenced_json_block():
    payload = """
Model Qwen3-Coder-Plus does not support thinking mode
```json
{
  "provider": "iflow",
  "verdict": "proceed",
  "summary": "ok",
  "blocking_findings": [],
  "non_blocking_notes": [],
  "tests_to_add": [],
  "plan_risks": [],
  "confidence": "high"
}
```
"""

    parsed = runtime_module.parse_review_text(payload)

    assert parsed["provider"] == "iflow"
    assert parsed["verdict"] == "proceed"


def test_run_orchestration_iflow_uses_stdout_payload_instead_of_output_file_metadata(tmp_path):
    script_path = tmp_path / "iflow.py"
    write_iflow_stdout_provider_script(script_path, "iflow")
    snapshot = {
        "iflow": {
            "available": True,
            "binary": str(script_path),
            "state_dirs": ["C:/fake/iflow"],
        }
    }

    _, review = run_orchestration(
        task="iflow stdout payload contract",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["iflow"],
        output_dir=tmp_path / "iflow-stdout-session",
        python_executable=Path(sys.executable),
    )

    provider_review = review.provider_reviews[0]
    assert review.verdict == "proceed"
    assert provider_review.review_stage == "runtime"
    assert provider_review.summary == "stdout payload"
    raw_output = Path(provider_review.raw_output_file).read_text(encoding="utf-8")
    assert "stdout payload" in raw_output


def test_run_orchestration_iflow_blocks_when_stdout_is_noise_without_output_file_fallback(tmp_path):
    script_path = tmp_path / "iflow.py"
    write_iflow_noisy_stdout_file_payload_provider_script(script_path, "iflow")
    snapshot = {
        "iflow": {
            "available": True,
            "binary": str(script_path),
            "state_dirs": ["C:/fake/iflow"],
        }
    }

    _, review = run_orchestration(
        task="iflow noisy stdout fallback",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["iflow"],
        output_dir=tmp_path / "iflow-noisy-session",
        python_executable=Path(sys.executable),
    )

    provider_review = review.provider_reviews[0]
    assert review.verdict == "block"
    assert provider_review.review_stage == "synthetic-failure"
    assert "review payload" in provider_review.blocking_findings[0]


def test_build_review_prompt_for_claude_is_explicitly_non_interactive():
    artifact = ArtifactPacket(
        trace_id="trace-test",
        generated_at="2026-04-14T20:00:00Z",
        mode="orch",
        task="compatibility smoke",
        runtime_mode="headless",
        packet_stage="runtime-execution",
        privacy_boundary="structured-packet-only",
        fan_out_requested=True,
        planned_providers=["claude", "iflow"],
        provider_snapshot={},
        next_step="Inspect provider reviews.",
    )

    prompt = runtime_module.build_review_prompt("claude", artifact)
    assert prompt.startswith("Return exactly one minified JSON object with keys provider, verdict, summary, blocking_findings, non_blocking_notes, tests_to_add, plan_risks, confidence.")
    assert "provider must be claude" in prompt
    assert "verdict must be one of proceed, fix_code, fix_plan, block" in prompt
    assert "confidence must be one of low, medium, high" in prompt
    assert "Do not ask follow-up questions" not in prompt
    assert "ARTIFACT_JSON=" not in prompt
    assert "\n" not in prompt
    assert '"planned_providers":["claude","iflow"]' in prompt


def test_build_review_prompt_for_iflow_uses_compact_artifact_summary():
    artifact = ArtifactPacket(
        trace_id="trace-test",
        generated_at="2026-04-14T20:00:00Z",
        mode="orch",
        task="compatibility smoke",
        runtime_mode="headless",
        packet_stage="runtime-execution",
        privacy_boundary="structured-packet-only",
        fan_out_requested=True,
        planned_providers=["claude", "iflow"],
        provider_snapshot={
            "iflow": {
                "available": True,
                "binary": "iflow",
                "state_dirs": ["C:/fake/iflow"],
            }
        },
        notes=["System CLI discovery was captured before execution."],
        next_step="Inspect provider reviews.",
    )

    prompt = runtime_module.build_review_prompt("iflow", artifact)

    assert prompt.startswith("Review this artifact and reply with exactly one minified JSON object.")
    assert "provider must be iflow" in prompt
    assert "verdict must be one of proceed, fix_code, fix_plan, block" in prompt
    assert "confidence must be one of low, medium, high" in prompt
    assert "ARTIFACT_JSON=" not in prompt
    assert "Do not ask follow-up questions" not in prompt
    assert "\n" not in prompt
    assert '"provider_snapshot":{"iflow":{"available":true' in prompt
    assert '"traceability_audit_path":"docs/GUIDE_TRACEABILITY_AUDIT.md"' in prompt
    assert '"task":"compatibility smoke"' in prompt
    assert '"planned_providers":["claude","iflow"]' in prompt


def test_build_provider_command_for_iflow_limits_turns_and_timeout(tmp_path):
    lane = list_lane_presets()["iflow-glm5-plan-thinking"]
    command = runtime_module.build_provider_command(
        "iflow",
        binary="iflow",
        prompt="compatibility",
        output_file=tmp_path / "raw.txt",
        workdir=tmp_path,
        timeout_seconds=45,
        lane=lane,
    )

    assert "-m" in command
    assert command[command.index("-m") + 1] == "GLM-5"
    assert "--max-turns" in command
    assert command[command.index("--max-turns") + 1] == "1"
    assert "--timeout" in command
    assert command[command.index("--timeout") + 1] == "45"
    assert "--stream" in command
    assert command[command.index("--stream") + 1] == "false"
    assert "--plan" in command
    assert "--thinking" in command
    assert "-o" not in command
    assert "--output-file" not in command


def test_build_provider_command_for_claude_disables_session_persistence(tmp_path):
    command = runtime_module.build_provider_command(
        "claude",
        binary="claude",
        prompt="compatibility",
        output_file=tmp_path / "raw.txt",
        workdir=tmp_path,
        timeout_seconds=45,
    )

    assert command == ["claude", "-p", "compatibility", "--no-session-persistence"]


def test_build_provider_command_for_opencode_plan_lane_uses_agent_model_and_thinking(tmp_path):
    lane = list_lane_presets()["opencode-minimax-plan-thinking"]

    command = runtime_module.build_provider_command(
        "opencode",
        binary="opencode",
        prompt="compatibility",
        output_file=tmp_path / "raw.txt",
        workdir=tmp_path,
        timeout_seconds=45,
        lane=lane,
    )

    assert "--agent" in command
    assert command[command.index("--agent") + 1] == "plan"
    assert "--model" in command
    assert command[command.index("--model") + 1] == "opencode/minimax-m2.5-free"
    assert "--thinking" in command


def test_build_provider_command_for_opencode_plan_lane_can_disable_thinking(tmp_path):
    lane = list_lane_presets()["opencode-minimax-plan"]

    command = runtime_module.build_provider_command(
        "opencode",
        binary="opencode",
        prompt="compatibility",
        output_file=tmp_path / "raw.txt",
        workdir=tmp_path,
        timeout_seconds=45,
        lane=lane,
    )

    assert "--agent" in command
    assert command[command.index("--agent") + 1] == "plan"
    assert "--model" in command
    assert command[command.index("--model") + 1] == "opencode/minimax-m2.5-free"
    assert "--thinking" not in command


def test_build_provider_command_for_nvidia_lane_runs_through_opencode(tmp_path):
    lane = list_lane_presets()["nvidia-glm51-plan"]

    command = runtime_module.build_provider_command(
        "opencode",
        binary="opencode",
        prompt="compatibility",
        output_file=tmp_path / "raw.txt",
        workdir=tmp_path,
        timeout_seconds=45,
        lane=lane,
    )

    assert command[:3] == ["opencode", "run", "--format"]
    assert "--agent" in command
    assert command[command.index("--agent") + 1] == "plan"
    assert "--model" in command
    assert command[command.index("--model") + 1] == "nvidia/z-ai/glm-5.1"
    assert "--thinking" not in command


def test_provider_runtime_env_for_iflow_uses_state_dir_parent():
    env = runtime_module.provider_runtime_env(
        "iflow",
        {"state_dirs": ["C:/Users/karte/.iflow"]},
    )

    assert env["HOME"] == "C:\\Users\\karte"
    assert env["USERPROFILE"] == "C:\\Users\\karte"
    assert env["HOMEDRIVE"] == "C:"
    assert env["HOMEPATH"] == "\\Users\\karte"


def test_provider_runtime_env_for_iflow_preserves_posix_state_dir_parent():
    env = runtime_module.provider_runtime_env(
        "iflow",
        {"state_dirs": ["/home/karte/.iflow"]},
    )

    assert env["HOME"] == "/home/karte"
    assert env["USERPROFILE"] == "/home/karte"
    assert env["HOMEDRIVE"] == ""
    assert env["HOMEPATH"] == "/home/karte"


def test_run_orchestration_rejects_nested_incidental_verdict_payload(tmp_path):
    script_path = tmp_path / "opencode.py"
    write_nested_payload_provider_script(script_path, "opencode")
    snapshot = {
        "opencode": {
            "available": True,
            "binary": str(script_path),
            "state_dirs": ["C:/fake/opencode"],
        }
    }

    _, review = run_orchestration(
        task="review nested payload",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["opencode"],
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert review.verdict == "block"
    provider_review = review.provider_reviews[0]
    assert provider_review.review_stage == "synthetic-failure"
    assert provider_review.blocking_findings


def test_run_orchestration_rejects_incidental_json_embedded_in_log_text(tmp_path):
    script_path = tmp_path / "opencode.py"
    write_incidental_json_provider_script(script_path, "opencode")
    snapshot = {
        "opencode": {
            "available": True,
            "binary": str(script_path),
            "state_dirs": ["C:/fake/opencode"],
        }
    }

    _, review = run_orchestration(
        task="review incidental log payload",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["opencode"],
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert review.verdict == "block"
    provider_review = review.provider_reviews[0]
    assert provider_review.review_stage == "synthetic-failure"
    assert provider_review.blocking_findings


def test_run_orchestration_rejects_invalid_confidence_value(tmp_path):
    script_path = tmp_path / "opencode.py"
    write_invalid_confidence_provider_script(script_path, "opencode")
    snapshot = {
        "opencode": {
            "available": True,
            "binary": str(script_path),
            "state_dirs": ["C:/fake/opencode"],
        }
    }

    _, review = run_orchestration(
        task="review invalid confidence",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["opencode"],
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert review.verdict == "block"
    provider_review = review.provider_reviews[0]
    assert provider_review.review_stage == "synthetic-failure"
    assert provider_review.blocking_findings


def test_run_orchestration_accepts_wrapped_opencode_event_output(tmp_path):
    script_path = tmp_path / "opencode.py"
    write_wrapped_opencode_payload_provider_script(script_path, "opencode")
    snapshot = {
        "opencode": {
            "available": True,
            "binary": str(script_path),
            "state_dirs": ["C:/fake/opencode"],
        }
    }

    _, review = run_orchestration(
        task="review wrapped output",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["opencode"],
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert review.verdict == "fix_plan"
    provider_review = review.provider_reviews[0]
    assert provider_review.review_stage == "runtime"
    assert provider_review.confidence == "high"


def test_windowed_timeout_respects_timeout_with_partial_output(tmp_path):
    script_path = tmp_path / "claude.py"
    write_partial_output_provider_script(script_path, seconds=2)
    snapshot = {
        "claude": {
            "available": True,
            "binary": str(script_path),
            "state_dirs": ["C:/fake/claude"],
        }
    }

    started = time.monotonic()
    _, review = run_orchestration(
        task="windowed timeout",
        runtime_mode="windowed",
        provider_snapshot=snapshot,
        requested_providers=["claude"],
        timeout_seconds=1,
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )
    elapsed = time.monotonic() - started

    assert review.verdict == "block"
    assert elapsed < 1.8
    timeout_log = (tmp_path / "session" / "providers" / "claude" / "stdout.txt").read_text(
        encoding="utf-8"
    )
    assert "partial" in timeout_log
    assert "timed out after 1s" in timeout_log


def test_headless_timeout_preserves_valid_payload_if_review_was_already_emitted(tmp_path):
    script_path = tmp_path / "iflow.py"
    write_valid_payload_then_sleep_provider_script(script_path, "iflow", seconds=2)
    snapshot = {
        "iflow": {
            "available": True,
            "binary": str(script_path),
            "state_dirs": ["C:/fake/iflow"],
        }
    }

    _, review = run_orchestration(
        task="headless timeout payload salvage",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["iflow"],
        timeout_seconds=1,
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    provider_review = review.provider_reviews[0]
    assert review.verdict == "proceed"
    assert provider_review.review_stage == "runtime"
    assert provider_review.summary == "iflow emitted a review before timing out"
    assert any("timed out after 1s" in note for note in provider_review.non_blocking_notes)
    attempt = json.loads(
        (tmp_path / "session" / "providers" / "iflow" / "attempt.json").read_text(
            encoding="utf-8"
        )
    )
    assert attempt["state"] == "timeout_incomplete"
    assert attempt["provider"] == "iflow"
    assert attempt["review_file"].endswith("review.json")
    assert attempt["operator_inspection_hint"].startswith("Provider timed out")


def test_run_orchestration_attempt_record_marks_completed_review(tmp_path):
    snapshot = runtime_snapshot(
        tmp_path,
        {
            "opencode": {"verdict": "proceed"},
        },
    )

    _, review = run_orchestration(
        task="attempt record success",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["opencode"],
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert review.verdict == "proceed"
    attempt = json.loads(
        (tmp_path / "session" / "providers" / "opencode" / "attempt.json").read_text(
            encoding="utf-8"
        )
    )
    assert attempt["state"] == "completed"
    assert attempt["exit_code"] == 0
    assert attempt["process_terminated"] is False
    assert attempt["retryable"] is False


def test_run_orchestration_attempt_record_marks_invalid_output(tmp_path):
    script_path = tmp_path / "opencode.py"
    write_invalid_confidence_provider_script(script_path, "opencode")
    snapshot = {
        "opencode": {
            "available": True,
            "binary": str(script_path),
            "state_dirs": ["C:/fake/opencode"],
        }
    }

    _, review = run_orchestration(
        task="attempt invalid output",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["opencode"],
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert review.verdict == "block"
    attempt = json.loads(
        (tmp_path / "session" / "providers" / "opencode" / "attempt.json").read_text(
            encoding="utf-8"
        )
    )
    assert attempt["state"] == "invalid_output"
    assert attempt["exit_code"] == 0


def test_run_orchestration_applies_provider_override_env_from_config(tmp_path, monkeypatch):
    script_path = tmp_path / "opencode.py"
    write_env_sensitive_provider_script(script_path, "opencode", "TEST_PROVIDER_BASE_URL")
    config_path = tmp_path / "providers.json"
    config_path.write_text(
        """
{
  "providers": {
    "opencode": {
      "base_url": "https://llm.local",
      "env": {
        "TEST_PROVIDER_BASE_URL": "https://llm.local"
      }
    }
  }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPEN_CLODEX_IFLOW_PROVIDER_CONFIG", str(config_path))
    snapshot = {
        "opencode": {
            "available": True,
            "binary": str(script_path),
            "state_dirs": ["C:/fake/opencode"],
        }
    }

    artifact, review = run_orchestration(
        task="review with override config",
        runtime_mode="headless",
        provider_snapshot=snapshot,
        requested_providers=["opencode"],
        output_dir=tmp_path / "session",
        python_executable=Path(sys.executable),
    )

    assert review.verdict == "proceed"
    assert review.provider_reviews[0].summary == "https://llm.local"
    assert any("override config" in note for note in artifact.notes)
