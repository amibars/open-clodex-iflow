from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_enforcement_modules():
    from enforcement import deps_rules, secret_scan, tdd_guard

    return deps_rules, secret_scan, tdd_guard


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_base_workspace(root: Path) -> None:
    required_docs = {
        "docs/START_HERE.md": "# START_HERE\n",
        "docs/READ_FIRST.md": "# READ_FIRST\n",
        "docs/EXECUTION_PRINCIPLES.md": "# EXECUTION_PRINCIPLES\n",
        "docs/AI_PROJECT_CHECKLIST.md": "# AI_PROJECT_CHECKLIST\n",
        "docs/PRD.md": "# PRD\n",
        "docs/ARCH_SPEC.md": "# ARCH_SPEC\n",
        "docs/ARCHITECTURE_BASELINE.md": "# ARCHITECTURE_BASELINE\n",
        "docs/QUALITY_GATES.md": "# QUALITY_GATES\n",
        "docs/AGENTS.md": "# AGENTS\n",
        "docs/ORCHESTRATED.md": "# ORCHESTRATED\n",
        "docs/SKILLS.md": "# SKILLS\n",
        "docs/JTBD.md": "# JTBD\n",
        "TASKS.md": "# TASKS\n",
        "TODO.md": "# TODO\n",
        "HABIT_TRACKER.md": "# HABIT_TRACKER\n",
        "reviewer.md": "# reviewer\n",
        ".pre-commit-config.yaml": "repos: []\n",
        ".github/workflows/ci.yml": "name: ci\n",
        "skeleton-tester/README.md": "# skeleton tester\n",
        "enforcement/tdd_guard.json": (
            "{\n"
            '  "required": [\n'
            '    {"source": "src/open_clodex_iflow/orchestration/good.py", "tests": ["tests/unit/test_good.py"]},\n'
            '    {"source": "enforcement/tdd_guard.py", "tests": ["tests/unit/test_tdd_guard.py"]}\n'
            "  ]\n"
            "}\n"
        ),
        "enforcement/tdd_guard.py": "# placeholder, only path existence matters here\n",
    }
    for relative_path, content in required_docs.items():
        write(root / relative_path, content)

    write(root / "src/open_clodex_iflow/orchestration/good.py", "VALUE = 1\n")
    write(root / "tests/unit/test_good.py", "def test_good():\n    assert True\n")
    write(root / "tests/unit/test_tdd_guard.py", "def test_tdd_guard():\n    assert True\n")


def scenario_forbidden_import(root: Path) -> bool:
    deps_rules, _, _ = load_enforcement_modules()
    create_base_workspace(root)
    write(root / "src/open_clodex_iflow/orchestration/bad_import.py", "import requests\n")
    violations = deps_rules.collect_violations(root)
    return any("forbidden import 'requests'" in violation for violation in violations)


def scenario_layer_violation(root: Path) -> bool:
    deps_rules, _, _ = load_enforcement_modules()
    create_base_workspace(root)
    write(
        root / "src/open_clodex_iflow/adapters/domain_leak.py",
        "from open_clodex_iflow.orchestration.preflight import build_artifact_packet\n",
    )
    violations = deps_rules.collect_violations(root)
    return any("layer violation" in violation for violation in violations)


def scenario_secret_detection(root: Path) -> bool:
    _, secret_scan, _ = load_enforcement_modules()
    create_base_workspace(root)
    token = "sk-" + "1234567890abcdef"
    write(root / "README.md", f"token = '{token}'\n")
    violations = secret_scan.scan_repository(root)
    return any("Potential secret found" in violation for violation in violations)


def scenario_tdd_guard(root: Path) -> bool:
    _, _, tdd_guard = load_enforcement_modules()
    create_base_workspace(root)
    write(root / "src/open_clodex_iflow/scaffold/new_module.py", "VALUE = 2\n")
    violations = tdd_guard.collect_violations(root)
    return any("unmapped source file" in violation for violation in violations)


def run_scenarios() -> list[tuple[str, bool]]:
    temp_root = Path(tempfile.mkdtemp(prefix="open-clodex-iflow-skeleton-"))
    results: list[tuple[str, bool]] = []
    scenarios = {
        "forbidden-import": scenario_forbidden_import,
        "layer-violation": scenario_layer_violation,
        "secret-detection": scenario_secret_detection,
        "tdd-guard": scenario_tdd_guard,
    }

    try:
        for name, scenario in scenarios.items():
            scenario_root = temp_root / name
            results.append((name, scenario(scenario_root)))
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    return results


def main() -> int:
    results = run_scenarios()
    failed = [name for name, passed in results if not passed]

    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {name}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
