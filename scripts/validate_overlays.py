from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OVERLAY_DIR = ROOT / "overlays"

REQUIRED_OVERLAYS = (
    "repo-forensics-review.md",
    "test-forensics-audit.md",
    "release-risk-gate.md",
    "reviewer-packet.md",
)

REQUIRED_SECTIONS = {
    "## Trigger",
    "## Permission Boundary",
    "## Required Evidence",
    "## Output Format",
    "## Non-Goals",
}


def collect_overlay_violations(root: Path = ROOT) -> list[str]:
    overlay_dir = root / "overlays"
    violations: list[str] = []

    if not overlay_dir.exists():
        return [f"missing overlay directory: {overlay_dir}"]

    for name in REQUIRED_OVERLAYS:
        path = overlay_dir / name
        if not path.exists():
            violations.append(f"missing overlay: overlays/{name}")
            continue
        text = path.read_text(encoding="utf-8")
        for section in sorted(REQUIRED_SECTIONS):
            if section not in text:
                violations.append(f"overlays/{name} missing required section {section}")
        if "read-only" not in text.lower() and name != "reviewer-packet.md":
            violations.append(f"overlays/{name} must state its read-only boundary")

    return violations


def main() -> int:
    violations = collect_overlay_violations()
    if violations:
        for violation in violations:
            print(f"VIOLATION: {violation}", file=sys.stderr)
        return 1
    print("overlay validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
