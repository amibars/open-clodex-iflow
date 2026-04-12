from __future__ import annotations

import sys
from pathlib import Path

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
