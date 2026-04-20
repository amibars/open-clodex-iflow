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
- `lanes`: inspect default lane presets, optional lanes, and the operator toggles that control them
- `doctor`: inspect installed CLIs and available local state
- `scaffold`: bootstrap an Iron Dome-compatible workspace in a target directory

Live provider status is tracked in `docs/PROVIDER_COMPATIBILITY.md`.
Guide adaptation traceability and source-of-truth coverage are tracked in `docs/GUIDE_TRACEABILITY_AUDIT.md`.
`docs/PROVIDER_COMPATIBILITY.md` tracks the latest documented live evidence per provider, including blocked or synthetic-failure snapshots when no successful review completed.

## Install for local development

```powershell
python -m pip install -e .[dev]
```

## Open-source package

- License: MIT
- Contribution guide: `CONTRIBUTING.md`
- Security policy: `SECURITY.md`
- Conduct policy: `CODE_OF_CONDUCT.md`
- Change history: `CHANGELOG.md`
- Release notes: `docs/releases/v0.1.0.md`

## Quick start

```powershell
open-clodex-iflow doctor
open-clodex-iflow lanes
open-clodex-iflow solo "Summarize the current task"
open-clodex-iflow orch "Review repository readiness" --mode headless
open-clodex-iflow orch "Review repository readiness" --lanes opencode-minimax-build-thinking --mode headless
open-clodex-iflow scaffold C:\Projects\my-new-workspace
```

The default `/orch` path now resolves a planner-oriented lane pack instead of a raw provider list. Today that means:

- `iflow-glm5-plan-thinking`
- `iflow-qwen3coder-plan`
- `iflow-kimi-k25-plan-thinking`
- `opencode-minimax-plan-thinking`

`iflow` presets request `--plan` and, where configured, `--thinking`; the latter remains best-effort because `iflow` only enables it when the selected model supports it. The explicit write-capable lane is currently `opencode-minimax-build-thinking`; it is never part of the default pack and must be requested on purpose.
Recent local evidence now covers all four default planner lanes on this machine, but two `iflow` lanes (`GLM-5` and `Qwen3-Coder-Plus`) may emit a valid review payload before the process exits cleanly. The runtime now preserves that payload instead of downgrading it to a synthetic failure.
Check `docs/PROVIDER_COMPATIBILITY.md` for the latest live snapshot before treating any provider or lane as success-verified on a different machine.

## Platform support

- Primary product truth: Windows
- Secondary engineering guardrail: Ubuntu CI for Python/enforcement drift detection
- This repo does not currently claim Linux desktop runtime parity for visible/windowed orchestration
- Current `windowed` truth: operator-visible execution in the current terminal, not dedicated OS windows per lane

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
  - lane presets with a default planner pack and explicit optional write-capable lanes
  - per-provider `review.json`, `session.log`, and consolidated aggregation with synthetic failure fallback
  - `lanes`, `--lanes`, `--lane-set`, legacy `--providers`, and `--timeout-seconds` operator controls for runtime execution
  - provider override config through `.open-clodex-iflow/providers.json` or `OPEN_CLODEX_IFLOW_PROVIDER_CONFIG`
- Not implemented yet:
  - parallel fan-out or debate loop
  - dedicated OS-window spawning for each worker lane

## Current state

This repository is a working sequential v1 orchestrator baseline.
The runtime path for `/orch` is implemented for runnable providers (`claude`, `iflow`, `opencode`) and no longer stops at preflight-only orchestration.
Adapter support in code is not the same as guaranteed live success. The current documented live evidence is now success-documented for all three runnable providers on this machine: `opencode`, `iflow`, and `claude`.
See `docs/PROVIDER_COMPATIBILITY.md` for the latest documented smoke snapshot and interpretation rules.
See `docs/OPERATOR_RUNBOOK.md` for the step-by-step operator flow of the current v1.

## Guide adaptation status

The repo follows a repo-native adaptation of the Iron Dome guide and does not claim a verbatim one-file-to-one-file copy.
Mapping decisions and explicit adaptation deltas are tracked in `docs/GUIDE_TRACEABILITY_AUDIT.md`.
`TODO.md` tracks follow-up process work when guide-derived docs/process change.

Pre-commit hooks run a minimal local guardrail (`ruff check`, `enforcement/deps_rules.py`, `enforcement/tdd_guard.py`, `scripts/validate_story.py --all`, `enforcement/secret_scan.py`).
This pre-commit layer is intentionally narrower than the full quality gate; comprehensive verification is `make check` plus CI.
CI is split intentionally: `windows-latest` is the primary product-truth lane, while `ubuntu-latest` is a secondary Python/enforcement guardrail rather than a claim of Linux runtime parity.
