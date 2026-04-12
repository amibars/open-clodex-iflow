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
