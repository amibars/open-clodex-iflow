# Windowed Runtime Contract

Status: normative truth contract for `windowed` and `dedicated-windows` behavior.

This document prevents ambiguity between current-terminal visibility and true dedicated OS-window lane execution.

## Current Truth

Current v1 `windowed` means:

- `/orch` is operator-visible.
- Provider output is streamed through the current terminal/runtime log path.
- Artifacts are written to the trace output directory.
- Execution is sequential by default and can be parallel only through explicit `--execution parallel`.

Current v1 `dedicated-windows` means:

- `/orch` launches each lane through a separate Windows console window when `--mode dedicated-windows` is selected.
- The backend uses a JSON request file and `python -m open_clodex_iflow.adapters.window_command` instead of passing the review prompt through the shell command line.
- The helper owns the provider subprocess, captures `stdout.txt`, `stderr.txt`, and `dedicated_window_status.json`, and reports timeout status back to orchestration.
- Timeout handling kills the provider child process and preserves partial output as evidence.
- Non-zero exit, invalid output, timeout, or launch failure becomes a synthetic blocking provider review instead of crashing the entire `/orch` run.

Current v1 `dedicated-windows` does not mean:

- Windows Terminal pane orchestration,
- persistent interactive provider sessions,
- sending prompts into windows that the operator opened manually,
- user-controlled live TUI panes,
- guaranteed cleanup of arbitrary child processes spawned by a provider CLI,
- a native slash command embedded inside Codex.

Those are separate product expansions and must not be implied by docs, release notes, or examples.

## Runtime Modes

| Mode | Implemented meaning | Operator visibility | Scope |
| --- | --- | --- | --- |
| `headless` | Run providers without streaming as the default operator surface | artifacts/logs after execution | current v1 |
| `windowed` | Run providers with operator-visible progress/output in the current terminal flow | current terminal + artifacts/logs | current v1 default |
| `dedicated-windows` | Run each lane through a separate Windows console window with JSON request/status capture | separate OS windows + artifacts/logs | current v1 explicit mode |

`dedicated-windows` is Windows-only. On unsupported platforms or failed window-launch capability, the lane is normalized into a synthetic blocking review with attempt evidence.

## Dedicated Window Backend

The implemented backend is deliberately conservative:

1. The orchestrator writes `dedicated_window_request.json` next to the lane artifacts.
2. The orchestrator launches a new window with `cmd.exe /d /s /c start <title> /wait <python> -m open_clodex_iflow.adapters.window_command <request.json>`.
3. The helper reads the request JSON and starts the real provider command as an argument array.
4. The helper writes `stdout.txt`, `stderr.txt`, and `dedicated_window_status.json`.
5. The orchestrator reads those files and converts the result into normal `attempt.json` and `review.json` artifacts.

This design is chosen because opening a window alone is not enough. The runtime must also preserve output, status, timeout facts, and traceability.

## Backend Contract

The current backend provides:

- backend availability check for Windows `cmd.exe`,
- lane window title,
- command injection boundary through request JSON instead of shell prompt interpolation,
- stdout/stderr capture files,
- timeout/kill for the provider child process owned by the helper,
- status file with `exit_code` and `timed_out`,
- artifact path handoff back into `attempt.json`.

The current backend intentionally does not provide:

- durable window/pane ids,
- reusable interactive sessions,
- interactive `send_input`,
- Windows Terminal split-pane layout control,
- cleanup of provider-grandchild processes outside the helper-owned child.

## Security Boundaries

Dedicated windows increase risk because they can:

- expose prompts or paths to the screen,
- run through shell launch layers,
- leave orphan provider-grandchild processes,
- confuse operator authority between lanes,
- capture less output if a provider bypasses stdout/stderr.

Therefore dedicated-window mode must keep the provider prompt out of the `cmd start` command line and must preserve command shape/artifact evidence for audit.

## Documentation Rules

Docs may say:

- current `windowed` is visible current-terminal execution,
- `dedicated-windows` opens separate Windows console windows for one-shot non-interactive lane commands,
- `dedicated-windows` is explicit opt-in and Windows-only,
- current dedicated windows are not persistent TUI panes.

Docs must not say:

- current `/orch` is a Codex-native slash-command shell,
- current provider panes are persistent interactive sessions,
- current `/orch` can attach to windows the operator opened manually,
- current backend provides Windows Terminal pane management.

## Current Implementation Status

The current product is a working sequential-by-default v1 orchestrator with optional parallel lane execution and explicit Windows-only `dedicated-windows` mode.

Dedicated Windows Terminal panes, persistent worker sessions, and native Codex slash-mode remain product expansions, not completed v1 scope.
