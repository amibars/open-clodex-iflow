from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable


def build_state_dir_map(home: Path | None = None) -> dict[str, list[Path]]:
    base = home or Path.home()
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
    which: Callable[[str], str | None] | None = None,
) -> dict[str, dict[str, object]]:
    locate_binary = which or shutil.which
    snapshot: dict[str, dict[str, object]] = {}

    for cli_name, state_dirs in build_state_dir_map(home).items():
        binary = locate_binary(cli_name)
        existing_state_dirs = [str(path) for path in state_dirs if path.exists()]
        snapshot[cli_name] = {
            "available": bool(binary),
            "binary": binary,
            "state_dirs": existing_state_dirs,
        }

    return snapshot


def installed_provider_names(snapshot: dict[str, dict[str, object]]) -> list[str]:
    return sorted(name for name, metadata in snapshot.items() if metadata.get("available"))
