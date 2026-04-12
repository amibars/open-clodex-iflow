from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


FORBIDDEN_IMPORTS = {
    "requests": "Use stdlib or a reviewed HTTP client abstraction instead.",
    "subprocess32": "Use Python stdlib subprocess.",
}

LAYER_RULES = {
    "src/open_clodex_iflow/adapters": [
        "open_clodex_iflow.orchestration",
        "open_clodex_iflow.scaffold",
    ],
    "src/open_clodex_iflow/orchestration": [
        "open_clodex_iflow.scaffold",
    ],
    "src/open_clodex_iflow/scaffold": [
        "open_clodex_iflow.adapters",
        "open_clodex_iflow.orchestration",
    ],
}

SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "dist", "build"}
REQUIRED_PATHS = [
    "docs/START_HERE.md",
    "docs/READ_FIRST.md",
    "docs/EXECUTION_PRINCIPLES.md",
    "docs/AI_PROJECT_CHECKLIST.md",
    "docs/PRD.md",
    "docs/ARCH_SPEC.md",
    "docs/ARCHITECTURE_BASELINE.md",
    "docs/QUALITY_GATES.md",
    "docs/AGENTS.md",
    "docs/ORCHESTRATED.md",
    "docs/SKILLS.md",
    "docs/JTBD.md",
    "TASKS.md",
    "TODO.md",
    "HABIT_TRACKER.md",
    "reviewer.md",
    ".pre-commit-config.yaml",
    ".github/workflows/ci.yml",
    "enforcement/tdd_guard.py",
    "enforcement/tdd_guard.json",
    "skeleton-tester/README.md",
]


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def collect_py_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*.py") if not should_skip(path)]


def check_forbidden_imports(file_path: Path) -> list[str]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"{file_path}: syntax error during enforcement parse: {exc}"]

    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".")[0]]
        else:
            continue

        for name in names:
            if name in FORBIDDEN_IMPORTS:
                violations.append(
                    f"{file_path}: forbidden import '{name}'. {FORBIDDEN_IMPORTS[name]}"
                )
    return violations


def imported_modules(file_path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imports: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.lineno, node.module))

    return imports


def check_layer_isolation(file_path: Path, root: Path) -> list[str]:
    normalized_path = file_path.relative_to(root).as_posix()
    violations: list[str] = []

    current_layer = next(
        (layer for layer in LAYER_RULES if normalized_path.startswith(layer)),
        None,
    )
    if current_layer is None:
        return violations

    try:
        imports = imported_modules(file_path)
    except SyntaxError as exc:
        return [f"{file_path}: syntax error during layer parse: {exc}"]

    for lineno, module_name in imports:
        for forbidden_prefix in LAYER_RULES[current_layer]:
            if module_name == forbidden_prefix or module_name.startswith(f"{forbidden_prefix}."):
                violations.append(
                    f"{file_path}:{lineno}: layer violation - {current_layer} "
                    f"cannot import {forbidden_prefix}"
                )

    return violations


def check_required_paths(root: Path) -> list[str]:
    return [f"missing required path: {path}" for path in REQUIRED_PATHS if not (root / path).exists()]


def collect_violations(root: Path) -> list[str]:
    violations: list[str] = []

    for path in collect_py_files(root / "src"):
        violations.extend(check_forbidden_imports(path))
        violations.extend(check_layer_isolation(path, root))

    violations.extend(check_required_paths(root))
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
            print(f"VIOLATION: {violation}", file=sys.stderr)
        return 1

    print("enforcement passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
