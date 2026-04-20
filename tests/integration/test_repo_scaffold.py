import os
import subprocess
import sys
import venv
from pathlib import Path


REQUIRED_PATHS = [
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
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
    "docs/OPERATOR_RUNBOOK.md",
    "docs/releases/v0.1.0.md",
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


def test_installed_console_script_doctor_runs_from_isolated_venv(tmp_path):
    root = Path(__file__).resolve().parents[2]
    venv_dir = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True).create(venv_dir)

    scripts_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    python_bin = scripts_dir / ("python.exe" if os.name == "nt" else "python")
    cli_bin = scripts_dir / ("open-clodex-iflow.exe" if os.name == "nt" else "open-clodex-iflow")

    install = subprocess.run(
        [str(python_bin), "-m", "pip", "install", "-e", str(root)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert install.returncode == 0, install.stderr
    assert cli_bin.exists(), f"Installed console script not found: {cli_bin}"

    result = subprocess.run(
        [str(cli_bin), "doctor"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert '"codex"' in result.stdout
