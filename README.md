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
Guide adaptation traceability and source-of-truth coverage are tracked in `docs/GUIDE_TRACEABILITY_AUDIT.md`.

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

This repository is a working sequential v1 orchestrator baseline.
The runtime path for `/orch` is implemented for runnable providers (`claude`, `iflow`, `opencode`) and no longer stops at preflight-only orchestration.
Live provider reliability is still environment-dependent and must be confirmed per machine/session; adapter support in code is not the same as guaranteed live success.
See `docs/PROVIDER_COMPATIBILITY.md` for the latest documented smoke snapshot and interpretation rules.

## Guide adaptation status

The repo follows a repo-native adaptation of the Iron Dome guide and does not claim a verbatim one-file-to-one-file copy.
Mapping decisions and explicit adaptation deltas are tracked in `docs/GUIDE_TRACEABILITY_AUDIT.md`.
`TODO.md` tracks follow-up process work when guide-derived docs/process change.

Pre-commit hooks run a minimal local guardrail (`ruff check`, `enforcement/deps_rules.py`, `enforcement/tdd_guard.py`, `scripts/validate_story.py --all`, `enforcement/secret_scan.py`).
This pre-commit layer is intentionally narrower than the full quality gate; comprehensive verification is `make check` plus CI.
