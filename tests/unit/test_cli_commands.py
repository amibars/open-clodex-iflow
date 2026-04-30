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


def test_orch_defaults_to_lane_pack_when_no_explicit_provider_selection(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        cli,
        "discover_cli_state",
        lambda: {
            "iflow": {"available": True, "binary": "iflow", "state_dirs": ["C:/Users/karte/.iflow"]},
            "opencode": {"available": True, "binary": "opencode", "state_dirs": ["C:/Users/karte/.opencode"]},
        },
    )
    artifact = ArtifactPacket(
        trace_id="trace-test",
        generated_at="2026-04-15T00:00:00Z",
        mode="orch",
        task="default lanes",
        runtime_mode="headless",
        packet_stage="runtime-execution",
        privacy_boundary="structured-packet-only",
        fan_out_requested=True,
        planned_providers=["iflow", "opencode"],
        planned_lanes=[
            "opencode-minimax-plan",
        ],
        provider_snapshot={},
        next_step="Inspect runtime reviews.",
    )
    review = ConsolidatedReview(
        trace_id="trace-test",
        generated_at="2026-04-15T00:00:01Z",
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

    exit_code = cli.main(["orch", "default lanes", "--mode", "headless", "--output-dir", str(tmp_path)])

    assert exit_code == 0
    assert captured["requested_lanes"] is None
    assert captured["lane_set"] == "default-planners"
    assert captured["requested_providers"] is None


def test_lanes_command_prints_default_and_optional_profiles(capsys):
    exit_code = cli.main(["lanes"])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "default-planners" in captured
    assert "opencode-minimax-plan" in captured
    assert "opencode-gpt5nano-plan-thinking" in captured
    assert "iflow-glm5-plan-thinking" in captured
    assert "legacy/API-key" in captured
    assert "opencode-minimax-build-thinking" in captured


def test_scaffold_command_creates_workspace(tmp_path):
    destination = tmp_path / "demo-workspace"

    exit_code = cli.main(["scaffold", str(destination)])

    assert exit_code == 0
    assert (destination / "docs" / "PRD.md").exists()
    assert (destination / "tasks" / "stories" / "1.1-repo-bootstrap.story.md").exists()


def test_orch_default_output_dir_is_trace_safe(monkeypatch, tmp_path):
    captured: dict[str, object] = {}
    output_dirs: list[object] = []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "new_trace_id", lambda: "trace-collision")
    monkeypatch.setattr(
        cli,
        "discover_cli_state",
        lambda: {
            "codex": {"available": True, "binary": "codex", "state_dirs": ["C:/Users/karte/.codex"]},
        },
    )

    def fake_run_orchestration(**kwargs):
        output_dirs.append(kwargs["output_dir"])
        task = kwargs["task"]
        artifact = ArtifactPacket(
            trace_id="trace-test",
            generated_at="2026-04-12T00:00:00Z",
            mode="orch",
            task=task,
            runtime_mode="headless",
            packet_stage="runtime-execution",
            privacy_boundary="structured-packet-only",
            fan_out_requested=True,
            planned_providers=[],
            provider_snapshot={},
            next_step="Inspect runtime reviews.",
        )
        review = ConsolidatedReview(
            trace_id="trace-test",
            generated_at="2026-04-12T00:00:01Z",
            review_stage="runtime",
            verdict="block",
            provider_reviews=[],
            next_action="Provide providers",
        )
        captured.update(kwargs)
        return artifact, review

    monkeypatch.setattr(
        cli,
        "run_orchestration",
        fake_run_orchestration,
    )

    first_exit_code = cli.main(["orch", "audit bootstrap first"])
    second_exit_code = cli.main(["orch", "audit bootstrap second"])

    first_output_dir, second_output_dir = output_dirs
    first_artifact = json.loads((first_output_dir / "artifact.json").read_text(encoding="utf-8"))
    second_artifact = json.loads((second_output_dir / "artifact.json").read_text(encoding="utf-8"))

    assert first_exit_code == 0
    assert second_exit_code == 0
    assert first_output_dir != second_output_dir
    assert first_output_dir.name == "trace-collision"
    assert second_output_dir.name.startswith("trace-collision-")
    assert first_artifact["task"] == "audit bootstrap first"
    assert second_artifact["task"] == "audit bootstrap second"
