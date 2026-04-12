# open-clodex-iflow

`open-clodex-iflow` is a Windows-first orchestration and scaffold tool for local AI development loops.
It bootstraps Iron Dome-compatible project structure and provides a reuse-first control plane for `Codex`, `Claude Code`, `iFlow`, and `OpenCode` without forcing a fresh login flow.

## Design goals

- Keep `Codex` as the human-facing control plane
- Support only two user modes: `solo` and `orch`
- Reuse installed CLIs and existing auth/session state from the system first
- Allow `windowed` and `headless` execution, with `windowed` as the default
- Generate and maintain the Iron Dome planning and quality artifacts before code-heavy development starts

## Commands

- `solo`: private work mode that writes a local `artifact.json` packet and never fans out
- `orch`: sequential runtime orchestration that writes `artifact.json`, per-provider `review.json`, `session.log`, and `consolidated_review.json`
- `doctor`: inspect installed CLIs and available local state
- `scaffold`: bootstrap an Iron Dome-compatible workspace in a target directory

Live provider status is tracked in `docs/PROVIDER_COMPATIBILITY.md`.
Guide parity and source-of-truth coverage are tracked in `docs/GUIDE_TRACEABILITY_AUDIT.md`.

## Install for local development

```powershell
python -m pip install -e .[dev]
```

## Quick start

```powershell
open-clodex-iflow doctor
open-clodex-iflow solo "Summarize the current task"
open-clodex-iflow orch "Review repository readiness" --providers opencode --mode headless
open-clodex-iflow scaffold C:\Projects\my-new-workspace
```

## Required repo docs before runtime expansion

- `docs/START_HERE.md`
- `docs/READ_FIRST.md`
- `docs/EXECUTION_PRINCIPLES.md`
- `docs/AI_PROJECT_CHECKLIST.md`
- `docs/PRD.md`
- `docs/ARCH_SPEC.md`
- `docs/AGENTS.md`
- `docs/JTBD.md`
- `docs/ORCHESTRATED.md`
- `docs/ARCHITECTURE_BASELINE.md`
- `docs/QUALITY_GATES.md`
- `TASKS.md`

## Bootstrap slice status

- Implemented now:
  - `doctor` provider discovery with local state detection
  - `scaffold` workspace bootstrap
  - `/solo` packet generation with explicit privacy boundary
  - `/orch` runnable-provider execution for `claude`, `iflow`, and `opencode`
  - per-provider `review.json`, `session.log`, and consolidated aggregation with synthetic failure fallback
  - `--providers` and `--timeout-seconds` operator controls for runtime execution
- Not implemented yet:
  - parallel fan-out or debate loop
  - custom API/base URL override path
  - dedicated OS-window spawning for each worker lane

## Current state

This repository is now a working sequential v1 orchestrator baseline.
Provider success still depends on each installed CLI's auth/runtime health, but the repo no longer stops at preflight-only `/orch`.
As of the latest live smoke pass, `opencode` is confirmed end-to-end, while `claude` and `iflow` currently fall back to synthetic blocking reviews on timeout in this environment.
