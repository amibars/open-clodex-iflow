from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Callable, Mapping


def resolve_discovery_home(home: Path | None = None) -> Path:
    base = home or Path.home()
    if base.name == ".codex-store-userhome":
        return base.parent
    return base


def readiness_level(binary_found: bool, existing_state_dirs: list[str]) -> str:
    if binary_found and existing_state_dirs:
        return "binary+state"
    if binary_found:
        return "binary-only"
    return "missing"


def default_provider_config_path(
    cwd: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> Path | None:
    env = environment or os.environ
    configured = env.get("OPEN_CLODEX_IFLOW_PROVIDER_CONFIG")
    if configured:
        return Path(configured)
    candidate = (cwd or Path.cwd()) / ".open-clodex-iflow" / "providers.json"
    return candidate if candidate.exists() else None


def load_provider_override_config(
    cwd: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, dict[str, object]]:
    config_path = default_provider_config_path(cwd, environment)
    if config_path is None or not config_path.exists():
        return {}

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    raw_providers = payload.get("providers", payload) if isinstance(payload, dict) else {}
    if not isinstance(raw_providers, dict):
        return {}

    normalized: dict[str, dict[str, object]] = {}
    for provider, config in raw_providers.items():
        if not isinstance(config, dict):
            continue
        env_map = config.get("env", {})
        normalized_env = {
            str(key): str(value)
            for key, value in env_map.items()
            if isinstance(env_map, dict)
        }
        normalized[str(provider)] = {
            "base_url": str(config["base_url"]) if isinstance(config.get("base_url"), str) else None,
            "env": normalized_env,
        }
    return normalized


def build_state_dir_map(home: Path | None = None) -> dict[str, list[Path]]:
    base = resolve_discovery_home(home)
    return {
        "codex": [base / ".codex"],
        "claude": [base / ".claude", base / ".config" / "claude"],
        "iflow": [base / ".iflow", base / ".config" / "iflow"],
        "opencode": [
            base / ".opencode",
            base / ".config" / "opencode",
            base / "AppData" / "Roaming" / "OpenCode",
        ],
    }


def discover_cli_state(
    home: Path | None = None,
    cwd: Path | None = None,
    environment: Mapping[str, str] | None = None,
    which: Callable[[str], str | None] | None = None,
) -> dict[str, dict[str, object]]:
    locate_binary = which or shutil.which
    overrides = load_provider_override_config(cwd, environment)
    snapshot: dict[str, dict[str, object]] = {}

    for cli_name, state_dirs in build_state_dir_map(home).items():
        binary = locate_binary(cli_name)
        binary_found = bool(binary)
        existing_state_dirs = [str(path) for path in state_dirs if path.exists()]
        override = overrides.get(cli_name, {})
        override_env = override.get("env", {})
        snapshot[cli_name] = {
            "available": binary_found,
            "binary": binary,
            "binary_found": binary_found,
            "reuse_state_detected": bool(existing_state_dirs),
            "readiness": readiness_level(binary_found, existing_state_dirs),
            "state_dirs": existing_state_dirs,
            "override_configured": bool(override),
            "override_base_url": override.get("base_url"),
            "override_env_keys": sorted(override_env.keys()) if isinstance(override_env, dict) else [],
        }

    return snapshot


def installed_provider_names(snapshot: dict[str, dict[str, object]]) -> list[str]:
    return sorted(name for name, metadata in snapshot.items() if metadata.get("available"))
