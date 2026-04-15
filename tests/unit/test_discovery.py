import json

from open_clodex_iflow.adapters.discovery import (
    discover_cli_state,
    installed_provider_names,
    resolve_discovery_home,
)


def test_discover_cli_state_reuses_existing_state_dirs(tmp_path):
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    (home / ".config" / "opencode").mkdir(parents=True)

    snapshot = discover_cli_state(
        home=home,
        which=lambda name: f"C:/Tools/{name}.exe" if name in {"codex", "opencode"} else None,
    )

    assert snapshot["codex"]["available"] is True
    assert snapshot["codex"]["binary_found"] is True
    assert snapshot["codex"]["reuse_state_detected"] is True
    assert snapshot["codex"]["readiness"] == "binary+state"
    assert snapshot["codex"]["state_dirs"] == [str(home / ".codex")]
    assert snapshot["claude"]["available"] is False
    assert snapshot["claude"]["binary_found"] is False
    assert snapshot["claude"]["reuse_state_detected"] is False
    assert snapshot["claude"]["readiness"] == "missing"
    assert snapshot["opencode"]["state_dirs"] == [str(home / ".config" / "opencode")]
    assert snapshot["opencode"]["binary_found"] is True
    assert snapshot["opencode"]["reuse_state_detected"] is True
    assert snapshot["opencode"]["readiness"] == "binary+state"
    assert installed_provider_names(snapshot) == ["codex", "opencode"]


def test_discover_cli_state_redacts_provider_override_config(tmp_path):
    home = tmp_path / "home"
    cwd = tmp_path / "workspace"
    (cwd / ".open-clodex-iflow").mkdir(parents=True)
    (cwd / ".open-clodex-iflow" / "providers.json").write_text(
        json.dumps(
            {
                "providers": {
                    "opencode": {
                        "base_url": "https://llm.local",
                        "env": {
                            "TEST_PROVIDER_BASE_URL": "https://llm.local",
                            "TEST_PROVIDER_API_KEY": "secret",
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    snapshot = discover_cli_state(
        home=home,
        cwd=cwd,
        which=lambda name: f"C:/Tools/{name}.exe" if name == "opencode" else None,
    )

    assert snapshot["opencode"]["override_configured"] is True
    assert snapshot["opencode"]["override_base_url"] == "https://llm.local"
    assert snapshot["opencode"]["override_env_keys"] == [
        "TEST_PROVIDER_API_KEY",
        "TEST_PROVIDER_BASE_URL",
    ]


def test_resolve_discovery_home_unwraps_codex_store_userhome(tmp_path):
    wrapped_home = tmp_path / ".codex-store-userhome"

    assert resolve_discovery_home(wrapped_home) == tmp_path
