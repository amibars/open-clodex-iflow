import json
import sys

from open_clodex_iflow.adapters.window_command import run_window_request


def test_run_window_request_writes_stdout_stderr_status_and_tees_visible_output(tmp_path, capsys):
    request_path = tmp_path / "request.json"
    stdout_path = tmp_path / "stdout.txt"
    stderr_path = tmp_path / "stderr.txt"
    status_path = tmp_path / "status.json"
    script = "import sys; print('visible stdout'); print('visible stderr', file=sys.stderr)"
    request_path.write_text(
        json.dumps(
            {
                "command": [sys.executable, "-c", script],
                "cwd": str(tmp_path),
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "status_path": str(status_path),
                "timeout_seconds": 5,
                "env": {},
            }
        ),
        encoding="utf-8",
    )

    exit_code = run_window_request(request_path)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert stdout_path.read_text(encoding="utf-8").strip() == "visible stdout"
    assert stderr_path.read_text(encoding="utf-8").strip() == "visible stderr"
    assert "visible stdout" in captured.out
    assert "visible stderr" in captured.err
    assert json.loads(status_path.read_text(encoding="utf-8")) == {
        "exit_code": 0,
        "timed_out": False,
    }


def test_run_window_request_marks_timeout(tmp_path):
    request_path = tmp_path / "request.json"
    stdout_path = tmp_path / "stdout.txt"
    stderr_path = tmp_path / "stderr.txt"
    status_path = tmp_path / "status.json"
    script = "import time; print('partial', flush=True); time.sleep(2)"
    request_path.write_text(
        json.dumps(
            {
                "command": [sys.executable, "-c", script],
                "cwd": str(tmp_path),
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "status_path": str(status_path),
                "timeout_seconds": 1,
                "env": {},
            }
        ),
        encoding="utf-8",
    )

    exit_code = run_window_request(request_path)

    assert exit_code == 124
    assert "partial" in stdout_path.read_text(encoding="utf-8")
    assert json.loads(status_path.read_text(encoding="utf-8")) == {
        "exit_code": None,
        "timed_out": True,
    }
