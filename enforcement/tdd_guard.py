from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SKIP_NAMES = {"__init__.py", "__main__.py"}


def load_config(root: Path) -> dict[str, object]:
    config_path = root / "enforcement" / "tdd_guard.json"
    return json.loads(config_path.read_text(encoding="utf-8"))


def governed_source_files(root: Path) -> set[Path]:
    source_roots = [
        root / "src" / "open_clodex_iflow",
        root / "enforcement",
        root / "scripts",
    ]
    governed: set[Path] = set()
    for source_root in source_roots:
        if not source_root.exists():
            continue
        for path in source_root.rglob("*.py"):
            if path.name in SKIP_NAMES:
                continue
            governed.add(path.resolve())
    return governed


def collect_violations(root: Path) -> list[str]:
    config = load_config(root)
    rules = config.get("required", [])
    if not isinstance(rules, list):
        return ["tdd_guard.json: 'required' must be a list"]

    violations: list[str] = []
    mapped_sources: set[Path] = set()

    for index, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            violations.append(f"tdd_guard.json: rule #{index} must be an object")
            continue

        source_pattern = rule.get("source")
        test_patterns = rule.get("tests")
        if not isinstance(source_pattern, str) or not isinstance(test_patterns, list):
            violations.append(
                f"tdd_guard.json: rule #{index} must define 'source' and list 'tests'"
            )
            continue

        matched_sources = [path for path in root.glob(source_pattern) if path.is_file()]
        if not matched_sources:
            violations.append(f"tdd_guard.json: source pattern matched no files: {source_pattern}")
            continue

        mapped_sources.update(path.resolve() for path in matched_sources)

        matched_tests = [
            path
            for pattern in test_patterns
            for path in root.glob(pattern)
            if path.is_file()
        ]
        if not matched_tests:
            violations.append(
                f"tdd_guard.json: source pattern '{source_pattern}' has no matching tests"
            )

    unmapped_sources = sorted(governed_source_files(root) - mapped_sources)
    for path in unmapped_sources:
        violations.append(f"unmapped source file in tdd_guard: {path.relative_to(root)}")

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root to validate",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    violations = collect_violations(root)

    if violations:
        for violation in violations:
            print(f"TDD VIOLATION: {violation}", file=sys.stderr)
        return 1

    print("tdd guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
