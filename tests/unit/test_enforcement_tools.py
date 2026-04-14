import json
import os
import subprocess
from pathlib import Path

import pytest

from enforcement import deps_rules, secret_scan, tdd_guard
from scripts.validate_story import validate_story


def test_deps_rules_detect_forbidden_import(tmp_path):
    file_path = tmp_path / "bad.py"
    file_path.write_text("import requests\n", encoding="utf-8")

    violations = deps_rules.check_forbidden_imports(file_path)

    assert violations
    assert "forbidden import 'requests'" in violations[0]


def test_deps_rules_detect_layer_violation(tmp_path):
    root = tmp_path
    file_path = root / "src" / "open_clodex_iflow" / "adapters" / "bad.py"
    file_path.parent.mkdir(parents=True)
    file_path.write_text(
        "from open_clodex_iflow.orchestration.preflight import build_artifact_packet\n",
        encoding="utf-8",
    )

    violations = deps_rules.check_layer_isolation(file_path, root)

    assert violations
    assert "layer violation" in violations[0]


def test_deps_rules_detect_missing_required_paths(tmp_path):
    violations = deps_rules.check_required_paths(tmp_path)
    assert any("docs/PRD.md" in violation for violation in violations)
    assert any(".pre-commit-config.yaml" in violation for violation in violations)


def test_secret_scan_detects_token_pattern(tmp_path):
    file_path = tmp_path / "README.md"
    secret = "sk-" + "1234567890abc"
    file_path.write_text(f"token = '{secret}'\n", encoding="utf-8")

    violations = secret_scan.scan_repository(tmp_path)

    assert violations == [f"Potential secret found in {file_path}"]


def test_story_validator_flags_missing_sections(tmp_path):
    story_path = tmp_path / "story.md"
    story_path.write_text("# Story\n\n## 1. Контекст\n\nOnly one section.\n", encoding="utf-8")

    missing_sections = validate_story(story_path)

    assert "## 2. Outcome" in missing_sections


def test_tdd_guard_flags_unmapped_source_files(tmp_path):
    root = tmp_path
    (root / "src" / "open_clodex_iflow").mkdir(parents=True)
    (root / "enforcement").mkdir()
    (root / "scripts").mkdir()
    (root / "src" / "open_clodex_iflow" / "new_module.py").write_text("x = 1\n", encoding="utf-8")
    (root / "enforcement" / "tdd_guard.json").write_text(json.dumps({"required": []}), encoding="utf-8")

    violations = tdd_guard.collect_violations(root)

    assert any("unmapped source file" in violation for violation in violations)


def test_tdd_guard_flags_missing_matching_tests_for_declared_rule(tmp_path):
    root = tmp_path
    (root / "src" / "open_clodex_iflow").mkdir(parents=True)
    (root / "enforcement").mkdir()
    (root / "scripts").mkdir()
    (root / "src" / "open_clodex_iflow" / "covered_module.py").write_text("x = 1\n", encoding="utf-8")
    (root / "enforcement" / "tdd_guard.json").write_text(
        json.dumps(
            {
                "required": [
                    {
                        "source": "src/open_clodex_iflow/covered_module.py",
                        "tests": ["tests/unit/test_missing.py"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    violations = tdd_guard.collect_violations(root)

    assert any("has no matching tests" in violation for violation in violations)


def _create_directory_alias(target: Path, alias: Path) -> None:
    if os.name != "nt":
        alias.symlink_to(target, target_is_directory=True)
        return

    try:
        alias.symlink_to(target, target_is_directory=True)
        return
    except OSError:
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(alias), str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("directory alias creation is unavailable on this platform")


def test_tdd_guard_handles_root_alias_paths(tmp_path):
    real_root = tmp_path / "real-root"
    alias_root = tmp_path / "alias-root"
    (real_root / "src" / "open_clodex_iflow").mkdir(parents=True)
    (real_root / "enforcement").mkdir()
    (real_root / "scripts").mkdir()
    (real_root / "src" / "open_clodex_iflow" / "new_module.py").write_text(
        "x = 1\n",
        encoding="utf-8",
    )
    (real_root / "enforcement" / "tdd_guard.json").write_text(
        json.dumps({"required": []}),
        encoding="utf-8",
    )

    _create_directory_alias(real_root, alias_root)

    violations = tdd_guard.collect_violations(alias_root)

    assert any(
        violation.replace("\\", "/").endswith("src/open_clodex_iflow/new_module.py")
        for violation in violations
    )
