from pathlib import Path

from scripts.validate_overlays import (
    OVERLAY_DIR,
    REQUIRED_OVERLAYS,
    REQUIRED_SECTIONS,
    collect_overlay_violations,
)


def test_required_audit_overlays_exist_and_have_contract_sections():
    assert set(REQUIRED_OVERLAYS) == {
        "repo-forensics-review.md",
        "test-forensics-audit.md",
        "release-risk-gate.md",
        "reviewer-packet.md",
    }

    violations = collect_overlay_violations()

    assert violations == []


def test_reviewer_packet_overlay_mentions_runtime_packet_contracts():
    text = (OVERLAY_DIR / "reviewer-packet.md").read_text(encoding="utf-8")

    assert "artifact.json" in text
    assert "review.json" in text
    assert "consolidated_review.json" in text


def test_overlay_validator_reports_missing_sections(tmp_path):
    overlay_dir = tmp_path / "overlays"
    overlay_dir.mkdir()
    for name in REQUIRED_OVERLAYS:
        (overlay_dir / name).write_text("# incomplete\n\n## Trigger\n", encoding="utf-8")

    violations = collect_overlay_violations(root=Path(tmp_path))

    for section in REQUIRED_SECTIONS - {"## Trigger"}:
        assert any(section in violation for violation in violations)
