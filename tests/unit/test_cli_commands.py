import json
import sys

import open_clodex_iflow.cli as cli
from open_clodex_iflow.contracts import ArtifactPacket, ConsolidatedReview


def test_main_uses_real_sys_argv(monkeypatch, tmp_path):
    monkeypatch.setattr(
        sys,
        "argv",
        ["open-clodex-iflow", "solo", "from-sys-argv", "--output-dir", str(tmp_path)],
    )

    exit_code = cli.main()

    artifact = json.loads((tmp_path / "artifact.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert artifact["task"] == "from-sys-argv"
    assert artifact["mode"] == "solo"


def test_orch_uses_runtime_orchestrator(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        cli,
        "discover_cli_state",
        lambda: {
            "codex": {"available": True, "binary": "codex", "state_dirs": ["C:/Users/karte/.codex"]},
            "iflow": {"available": True, "binary": "iflow", "state_dirs": ["C:/Users/karte/.iflow"]},
        },
    )
    artifact = ArtifactPacket(
        trace_id="trace-test",
        generated_at="2026-04-12T00:00:00Z",
        mode="orch",
        task="audit bootstrap",
        runtime_mode="headless",
        packet_stage="runtime-execution",
        privacy_boundary="structured-packet-only",
        fan_out_requested=True,
        planned_providers=["iflow"],
        provider_snapshot={"iflow": {"available": True, "binary": "iflow", "state_dirs": []}},
        next_step="Inspect runtime reviews.",
    )
    review = ConsolidatedReview(
        trace_id="trace-test",
        generated_at="2026-04-12T00:00:01Z",
        review_stage="runtime",
        verdict="proceed",
        provider_reviews=[],
        next_action="Proceed",
    )
    monkeypatch.setattr(
        cli,
        "run_orchestration",
        lambda **kwargs: captured.update(kwargs) or (artifact, review),
    )

    exit_code = cli.main(
        [
            "orch",
            "audit bootstrap",
            "--mode",
            "headless",
            "--providers",
            "iflow",
            "--timeout-seconds",
            "15",
            "--output-dir",
            str(tmp_path),
        ]
    )

    artifact = json.loads((tmp_path / "artifact.json").read_text(encoding="utf-8"))
    review = json.loads((tmp_path / "consolidated_review.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert artifact["runtime_mode"] == "headless"
    assert artifact["packet_stage"] == "runtime-execution"
    assert review["verdict"] == "proceed"
    assert captured["requested_providers"] == ["iflow"]
    assert captured["timeout_seconds"] == 15


def test_scaffold_command_creates_workspace(tmp_path):
    destination = tmp_path / "demo-workspace"

    exit_code = cli.main(["scaffold", str(destination)])

    assert exit_code == 0
    assert (destination / "docs" / "PRD.md").exists()
    assert (destination / "tasks" / "stories" / "1.1-repo-bootstrap.story.md").exists()
