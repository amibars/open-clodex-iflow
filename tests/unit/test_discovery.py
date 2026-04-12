from open_clodex_iflow.adapters.discovery import discover_cli_state, installed_provider_names


def test_discover_cli_state_reuses_existing_state_dirs(tmp_path):
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    (home / ".config" / "opencode").mkdir(parents=True)

    snapshot = discover_cli_state(
        home=home,
        which=lambda name: f"C:/Tools/{name}.exe" if name in {"codex", "opencode"} else None,
    )

    assert snapshot["codex"]["available"] is True
    assert snapshot["codex"]["state_dirs"] == [str(home / ".codex")]
    assert snapshot["claude"]["available"] is False
    assert snapshot["opencode"]["state_dirs"] == [str(home / ".config" / "opencode")]
    assert installed_provider_names(snapshot) == ["codex", "opencode"]
