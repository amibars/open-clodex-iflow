# Windowed Runtime Contract

Status: normative truth contract for `windowed` behavior.

This document prevents ambiguity between the current implemented `windowed` mode and the future desired dedicated OS-window worker lanes.

## Current Truth

Current v1 `windowed` means:

- `/orch` is operator-visible.
- Provider execution is sequential.
- Provider output is surfaced through the current terminal/runtime log path.
- Artifacts are written to the trace output directory.

Current v1 `windowed` does not mean:

- one OS window per lane,
- one Windows Terminal pane per lane,
- persistent interactive provider sessions,
- user-controlled live TUI panes,
- a native slash command embedded inside Codex.

Those are future capabilities and must not be implied by docs, release notes, or examples.

## Runtime Modes

| Mode | Implemented meaning | Operator visibility | Scope |
| --- | --- | --- | --- |
| `headless` | Run providers without streaming as the default operator surface | artifacts/logs after execution | current v1 |
| `windowed` | Run providers with operator-visible sequential progress/output in the current terminal flow | current terminal + artifacts/logs | current v1 |
| `dedicated-windows` | Spawn and manage separate OS windows/panes per lane | separate process windows/panes + artifacts/logs | future |

`dedicated-windows` is intentionally not a public CLI mode until its backend contract and tests exist.

## Dedicated Window Requirements

Before claiming dedicated OS-window spawning, the project must define and test:

- backend selection on Windows,
- capability detection,
- process lifecycle ownership,
- pane/window naming,
- command injection boundaries,
- stdout/stderr capture semantics,
- timeout/kill behavior,
- cleanup behavior,
- crash recovery,
- artifact path handoff,
- how the operator maps a visible window back to a lane id and trace id.

## Candidate Backends

| Backend | Pros | Risks |
| --- | --- | --- |
| Current terminal streaming | Already implemented, simple, testable | Not separate windows/panes |
| Windows Terminal tabs/panes | Native operator UX on Windows | Automation/control/capture semantics must be proven |
| `psmux`-style backend | Closer to tmux semantics | Extra dependency and Windows capability gate |
| Plain `Start-Process` windows | Simple process launch | Weak capture, cleanup, and pane identity semantics |

No backend should be selected only because it can open a window. The orchestrator needs reliable capture and cleanup, not just visual noise.

## Backend Contract

A future window backend must expose:

```text
ensure_backend_available()
open_lane_window(trace_id, lane_id, title, command, cwd, env)
send_input(window_id, text)
capture_output(window_id)
mark_status(window_id, status)
terminate(window_id)
cleanup(trace_id)
```

Minimum returned facts:

- backend name,
- backend version if available,
- trace id,
- lane id,
- process id,
- window/pane id if available,
- command shape,
- cwd,
- start/end timestamps,
- exit status,
- output artifact paths.

## Security Boundaries

Dedicated windows increase risk because they can:

- expose prompts or paths to the screen,
- run command strings through shell layers,
- leave orphan processes,
- confuse operator authority between lanes,
- capture less output than headless subprocess mode.

Therefore future dedicated window commands must prefer argument arrays over shell strings and must be covered by command-injection tests.

## Documentation Rules

Docs may say:

- current `windowed` is visible sequential execution,
- dedicated OS-window lanes are deferred,
- a future backend contract is required before that claim.

Docs must not say:

- current `/orch` spawns one OS window per provider,
- current `/orch` is a Codex-native slash-command shell,
- current provider panes are persistent interactive sessions.

## Current Implementation Status

The current product remains a working sequential v1 orchestrator. Dedicated windows are a product expansion, not a bug in the current baseline, as long as docs stay truthful.
