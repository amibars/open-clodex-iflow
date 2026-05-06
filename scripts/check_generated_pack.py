from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
MANIFEST_PATH = ROOT / "docs" / "GENERATED_PACK_MANIFEST.json"
CANONICAL_PROJECT_NAME = "Manifest Project"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from open_clodex_iflow.scaffold.bootstrap import render_templates  # noqa: E402


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_expected_manifest(project_name: str = CANONICAL_PROJECT_NAME) -> dict[str, Any]:
    templates = render_templates(project_name)
    files = [
        {
            "path": relative_path,
            "sha256": _sha256_text(content),
            "bytes": len(content.encode("utf-8")),
        }
        for relative_path, content in sorted(templates.items())
    ]

    return {
        "schema_version": 1,
        "generator": "open_clodex_iflow.scaffold.bootstrap.render_templates",
        "canonical_project_name": project_name,
        "file_count": len(files),
        "files": files,
    }


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_manifest_violations(
    actual: dict[str, Any],
    expected: dict[str, Any] | None = None,
) -> list[str]:
    expected_manifest = expected or build_expected_manifest()
    violations: list[str] = []

    actual_copy = copy.deepcopy(actual)
    expected_copy = copy.deepcopy(expected_manifest)

    actual_files = {entry.get("path"): entry for entry in actual_copy.get("files", [])}
    expected_files = {entry.get("path"): entry for entry in expected_copy.get("files", [])}

    missing = sorted(set(expected_files) - set(actual_files))
    extra = sorted(set(actual_files) - set(expected_files))
    changed = sorted(
        path
        for path in set(actual_files) & set(expected_files)
        if actual_files[path] != expected_files[path]
    )

    if missing:
        violations.append(f"manifest missing generated paths: {', '.join(missing)}")
    if extra:
        violations.append(f"manifest has stale generated paths: {', '.join(extra)}")
    if changed:
        violations.append(f"manifest hashes/metadata changed for: {', '.join(changed)}")

    actual_copy["files"] = sorted(actual_copy.get("files", []), key=lambda entry: entry.get("path", ""))
    expected_copy["files"] = sorted(
        expected_copy.get("files", []),
        key=lambda entry: entry.get("path", ""),
    )

    for key in ("schema_version", "generator", "canonical_project_name", "file_count"):
        if actual_copy.get(key) != expected_copy.get(key):
            violations.append(
                f"manifest field '{key}' is {actual_copy.get(key)!r}, "
                f"expected {expected_copy.get(key)!r}"
            )

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST_PATH,
        help="Path to the generated pack manifest.",
    )
    parser.add_argument(
        "--print-expected",
        action="store_true",
        help="Print the expected manifest JSON to stdout.",
    )
    args = parser.parse_args(argv)

    expected = build_expected_manifest()
    if args.print_expected:
        print(canonical_json(expected), end="")
        return 0

    if not args.manifest.exists():
        print(f"VIOLATION: missing generated pack manifest: {args.manifest}", file=sys.stderr)
        return 1

    violations = collect_manifest_violations(load_manifest(args.manifest), expected)
    if violations:
        for violation in violations:
            print(f"VIOLATION: {violation}", file=sys.stderr)
        print(
            "Run `python scripts/check_generated_pack.py --print-expected` "
            "and update docs/GENERATED_PACK_MANIFEST.json intentionally.",
            file=sys.stderr,
        )
        return 1

    print("generated pack manifest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
