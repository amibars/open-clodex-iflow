from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "## 1. Контекст",
    "## 2. Outcome",
    "## 3. Architecture integration",
    "## 4. Step-by-step план",
    "## 5. Test cases",
    "## 6. Edge cases",
    "## 7. Acceptance criteria",
    "## 8. Команды проверки",
    "## 9. Что не делать",
]


def validate_story(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [section for section in REQUIRED_SECTIONS if section not in text]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Validate all story files")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root containing tasks/stories",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    stories = sorted((root / "tasks" / "stories").glob("*.md"))
    if not args.all:
        print("No-op without --all")
        return 0

    missing_sections = False
    for story in stories:
        missing = validate_story(story)
        if missing:
            missing_sections = True
            print(f"{story}: missing sections {missing}", file=sys.stderr)

    if missing_sections:
        return 1

    print("story validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
