from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{10,}"),
    re.compile(r"ghp_[A-Za-z0-9]{10,}"),
    re.compile(r"api[_-]?key\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE),
]

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "dist", "build"}
CHECK_EXTENSIONS = {".py", ".md", ".toml", ".yml", ".yaml", ".json"}


def should_scan(path: Path) -> bool:
    return path.suffix in CHECK_EXTENSIONS and not any(part in SKIP_DIRS for part in path.parts)


def scan_repository(root: Path) -> list[str]:
    violations: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file() or not should_scan(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in PATTERNS:
            if pattern.search(text):
                violations.append(f"Potential secret found in {path}")
                break

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root to scan",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    violations = scan_repository(root)

    if violations:
        for violation in violations:
            print(violation, file=sys.stderr)
        return 1

    print("secret scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
