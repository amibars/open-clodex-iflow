from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from open_clodex_iflow.contracts import ArtifactPacket
from open_clodex_iflow.adapters import runtime as runtime_module
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


def test_select_runner_returns_expected_execution_function():
    assert runtime_module.select_runner("headless") is runtime_module.execute_headless
    assert runtime_module.select_runner("windowed") is runtime_module.execute_visible


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
    assert "Do not ask follow-up questions" in prompt
    assert "Treat the artifact JSON below as the complete context" in prompt
    assert "Return exactly one minified JSON object" in prompt
    assert 'Set "provider" to "claude"' in prompt
    assert "review lane" not in prompt
    assert "ARTIFACT_JSON=" in prompt


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
    command = runtime_module.build_provider_command(
        "iflow",
        binary="iflow",
        prompt="compatibility",
        output_file=tmp_path / "raw.txt",
        workdir=tmp_path,
        timeout_seconds=45,
    )

    assert "--max-turns" in command
    assert command[command.index("--max-turns") + 1] == "1"
    assert "--timeout" in command
    assert command[command.index("--timeout") + 1] == "45"
    assert "--stream" in command
    assert command[command.index("--stream") + 1] == "false"
    assert "--plan" not in command
    assert "-o" not in command
    assert "--output-file" not in command


def test_provider_runtime_env_for_iflow_uses_state_dir_parent():
    env = runtime_module.provider_runtime_env(
        "iflow",
        {"state_dirs": ["C:/Users/karte/.iflow"]},
    )

    assert env["HOME"] == "C:\\Users\\karte"
    assert env["USERPROFILE"] == "C:\\Users\\karte"
    assert env["HOMEDRIVE"] == "C:"
    assert env["HOMEPATH"] == "\\Users\\karte"


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
