from __future__ import annotations

import copy

from scripts import check_generated_pack


def test_generated_pack_manifest_matches_current_templates():
    actual = check_generated_pack.load_manifest()
    expected = check_generated_pack.build_expected_manifest()

    assert check_generated_pack.collect_manifest_violations(actual, expected) == []


def test_generated_pack_manifest_detects_changed_template_hash():
    expected = check_generated_pack.build_expected_manifest()
    actual = copy.deepcopy(expected)
    actual["files"][0]["sha256"] = "0" * 64

    violations = check_generated_pack.collect_manifest_violations(actual, expected)

    assert any("manifest hashes/metadata changed" in violation for violation in violations)


def test_generated_pack_manifest_detects_missing_template_path():
    expected = check_generated_pack.build_expected_manifest()
    actual = copy.deepcopy(expected)
    actual["files"] = actual["files"][1:]
    actual["file_count"] = len(actual["files"])

    violations = check_generated_pack.collect_manifest_violations(actual, expected)

    assert any("manifest missing generated paths" in violation for violation in violations)
