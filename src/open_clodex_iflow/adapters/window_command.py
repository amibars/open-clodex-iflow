from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any


TIMEOUT_EXIT_CODE = 124
LAUNCH_FAILURE_EXIT_CODE = 127


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _write_status(path: Path, *, exit_code: int | None, timed_out: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "exit_code": exit_code,
                "timed_out": timed_out,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list of strings")
    return value


def _tee_reader(
    stream,
    collected: list[str],
    visible_stream,
) -> None:
    for chunk in iter(stream.readline, ""):
        collected.append(chunk)
        visible_stream.write(chunk)
        visible_stream.flush()
    stream.close()


def _hold_window(hold_seconds: int) -> None:
    if hold_seconds <= 0:
        return
    print(f"\n[open-clodex-iflow] holding window for {hold_seconds}s before closing...")
    time.sleep(hold_seconds)


def run_window_request(request_path: Path) -> int:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    command = _string_list(request.get("command"), "command")
    cwd = Path(str(request["cwd"]))
    stdout_path = Path(str(request["stdout_path"]))
    stderr_path = Path(str(request["stderr_path"]))
    status_path = Path(str(request["status_path"]))
    timeout_seconds = int(request["timeout_seconds"])
    hold_seconds = max(0, int(request.get("hold_seconds", 0)))
    env = request.get("env", {})
    if not isinstance(env, dict):
        raise ValueError("env must be an object")

    process_env = os.environ.copy()
    process_env.update({str(key): str(value) for key, value in env.items()})

    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=process_env,
        )
    except OSError as exc:
        _write_text(stdout_path, "")
        _write_text(stderr_path, str(exc))
        _write_status(status_path, exit_code=LAUNCH_FAILURE_EXIT_CODE, timed_out=False)
        _hold_window(hold_seconds)
        return LAUNCH_FAILURE_EXIT_CODE

    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    assert process.stdout is not None
    assert process.stderr is not None
    stdout_thread = threading.Thread(
        target=_tee_reader,
        args=(process.stdout, stdout_chunks, sys.stdout),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_tee_reader,
        args=(process.stderr, stderr_chunks, sys.stderr),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()

    timed_out = False
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        process.wait()
    finally:
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)

    stdout_text = "".join(stdout_chunks)
    stderr_text = "".join(stderr_chunks)
    if timed_out:
        _write_text(stdout_path, stdout_text)
        _write_text(stderr_path, stderr_text)
        _write_status(status_path, exit_code=None, timed_out=True)
        _hold_window(hold_seconds)
        return TIMEOUT_EXIT_CODE

    _write_text(stdout_path, stdout_text)
    _write_text(stderr_path, stderr_text)
    _write_status(status_path, exit_code=process.returncode, timed_out=False)
    _hold_window(hold_seconds)
    return int(process.returncode)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m open_clodex_iflow.adapters.window_command <request.json>", file=sys.stderr)
        return 2
    return run_window_request(Path(args[0]))


if __name__ == "__main__":
    raise SystemExit(main())
