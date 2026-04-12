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
  - provider override config through `.open-clodex-iflow/providers.json` or `OPEN_CLODEX_IFLOW_PROVIDER_CONFIG`
- Not implemented yet:
  - parallel fan-out or debate loop
  - dedicated OS-window spawning for each worker lane

## Current state

This repository is now a working sequential v1 orchestrator baseline.
Provider success still depends on each installed CLI's auth/runtime health, but the repo no longer stops at preflight-only `/orch`.
As of the latest live smoke pass, all three reviewed providers remain environment-dependent in this machine/session: `claude` and `iflow` currently fall back to synthetic blocking reviews on timeout, and `opencode` has shown both a successful live run and a later timeout-driven synthetic block. The runtime path is implemented and verified; provider reliability still depends on the installed CLI state in the current environment.

## Guide adaptation status

The repo follows a repo-native adaptation of the Iron Dome guide rather than claiming a verbatim copy of every guide file.
All decisions about how the repo-native artifacts map back to the guide are captured in `docs/GUIDE_TRACEABILITY_AUDIT.md`.
The original bootstrap parity gaps have been closed; what remains in the repo is product scope that is intentionally out of the current v1 baseline, not unresolved guide debt.

Pre-commit hooks currently run the key enforcement scripts (`ruff check`, `enforcement/deps_rules.py`, `enforcement/tdd_guard.py`, `scripts/validate_story.py --all`, and `enforcement/secret_scan.py`) to keep that guard surface consistent with local enforcement policy; more comprehensive verification still happens through `make check` and CI.
