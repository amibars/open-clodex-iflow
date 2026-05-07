from open_clodex_iflow.contracts import AttemptRecord
from open_clodex_iflow.orchestration.preflight import build_artifact_packet, build_consolidated_review


def test_solo_packet_preserves_privacy_boundary():
    artifact = build_artifact_packet(
        mode="solo",
        task="private fix",
        provider_snapshot={"codex": {"available": True, "binary": "codex", "state_dirs": []}},
    )

    assert artifact.fan_out_requested is False
    assert artifact.privacy_boundary == "codex-only"
    assert artifact.planned_providers == []
    assert artifact.required_docs_gate_passed is True
    assert artifact.traceability_audit_path == "docs/GUIDE_TRACEABILITY_AUDIT.md"


def test_orch_review_blocks_when_no_provider_is_available():
    artifact = build_artifact_packet(mode="orch", task="orchestrate", provider_snapshot={})
    review = build_consolidated_review(artifact)

    assert review.verdict == "block"
    assert review.blocking_findings


def test_orch_review_requires_task_summary_before_proceeding():
    artifact = build_artifact_packet(
        mode="orch",
        task="",
        provider_snapshot={"iflow": {"available": True, "binary": "iflow", "state_dirs": []}},
        runtime_mode="windowed",
    )
    review = build_consolidated_review(artifact)

    assert artifact.runtime_mode == "windowed"
    assert review.verdict == "fix_plan"


def test_orch_review_proceeds_when_packet_and_provider_plan_exist():
    artifact = build_artifact_packet(
        mode="orch",
        task="review repo state",
        provider_snapshot={
            "claude": {"available": True, "binary": "claude", "state_dirs": ["C:/Users/karte/.claude"]}
        },
    )
    review = build_consolidated_review(artifact)

    assert artifact.planned_providers == ["claude"]
    assert review.verdict == "proceed"
    assert review.provider_reviews[0].provider == "claude"


def test_attempt_record_serializes_runtime_evidence_paths():
    record = AttemptRecord(
        attempt_id="attempt-test",
        trace_id="trace-test",
        lane_id="opencode-minimax-plan",
        provider="opencode",
        model="opencode/minimax-m2.5-free",
        mode="plan",
        runtime_mode="headless",
        state="completed",
        started_at="2026-05-07T00:00:00Z",
        ended_at="2026-05-07T00:00:01Z",
        timeout_seconds=180,
        process_terminated=False,
        exit_code=0,
        stdout_tail_file="providers/opencode/stdout.txt",
        stderr_tail_file="providers/opencode/stderr.txt",
        raw_output_file="providers/opencode/raw_output.txt",
        review_file="providers/opencode/review.json",
        retryable=False,
        operator_inspection_hint="Provider completed with a valid normalized review.",
        command_shape=["opencode", "run", "<review-prompt-redacted>"],
        cwd="C:/Projects/open-clodex-iflow",
    )

    payload = record.to_dict()

    assert payload["state"] == "completed"
    assert payload["review_file"].endswith("review.json")
    assert "<review-prompt-redacted>" in payload["command_shape"]
