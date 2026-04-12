import pytest

from open_clodex_iflow.scaffold.bootstrap import scaffold_workspace


def test_scaffold_workspace_creates_required_files(tmp_path):
    destination = tmp_path / "fresh-workspace"

    created = scaffold_workspace(destination)

    assert created
    assert (destination / "README.md").exists()
    assert (destination / "TASKS.md").exists()
    assert (destination / "docs" / "START_HERE.md").exists()
    assert (destination / "docs" / "READ_FIRST.md").exists()
    assert (destination / "docs" / "EXECUTION_PRINCIPLES.md").exists()
    assert (destination / "docs" / "AI_PROJECT_CHECKLIST.md").exists()
    assert (destination / "docs" / "JTBD.md").exists()
    assert (destination / "tasks" / "epics").exists()


def test_scaffold_workspace_refuses_non_empty_destination_without_force(tmp_path):
    destination = tmp_path / "existing-workspace"
    destination.mkdir()
    (destination / "README.md").write_text("existing\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        scaffold_workspace(destination)
