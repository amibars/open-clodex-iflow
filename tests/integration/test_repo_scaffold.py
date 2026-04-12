import os
import subprocess
import sys
from pathlib import Path


REQUIRED_PATHS = [
    "docs/START_HERE.md",
    "docs/READ_FIRST.md",
    "docs/EXECUTION_PRINCIPLES.md",
    "docs/AI_PROJECT_CHECKLIST.md",
    "docs/PRD.md",
    "docs/AGENTS.md",
    "docs/SKILLS.md",
    "docs/ORCHESTRATED.md",
    "docs/ARCHITECTURE_BASELINE.md",
    "docs/QUALITY_GATES.md",
    "docs/ARCH_SPEC.md",
    "docs/JTBD.md",
    "TASKS.md",
    "TODO.md",
    "HABIT_TRACKER.md",
    "reviewer.md",
    "tasks/epics/epic-1-bootstrap-open-clodex-iflow.md",
    "tasks/stories/1.1-repo-bootstrap.story.md",
    "enforcement/deps_rules.py",
    "enforcement/secret_scan.py",
    "enforcement/tdd_guard.py",
    "enforcement/tdd_guard.json",
    "scripts/validate_story.py",
    "scripts/run_skeleton_tester.py",
    ".pre-commit-config.yaml",
    ".github/workflows/ci.yml",
    "skeleton-tester/README.md",
    "Makefile",
]


def test_required_scaffold_files_exist():
    root = Path(__file__).resolve().parents[2]
    missing = [path for path in REQUIRED_PATHS if not (root / path).exists()]
    assert not missing, f"Missing scaffold files: {missing}"


def test_package_entrypoint_doctor_runs_with_src_pythonpath():
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    result = subprocess.run(
        [sys.executable, "-m", "open_clodex_iflow", "doctor"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert '"codex"' in result.stdout
