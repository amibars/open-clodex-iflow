# TODO.md

# Quick Start Backlog

## P0

- [x] Create starter repo structure
- [x] Fill mandatory Iron Dome docs
- [x] Add initial enforcement scripts
- [x] Add smoke tests for scaffold
- [x] Implement provider discovery details in adapters
- [x] Implement artifact packet contract
- [x] Implement consolidated review aggregator preflight

## P1

- [x] Implement `doctor`
- [x] Implement `solo`
- [x] Implement `orch`
- [x] Add layer isolation, TDD guard, and pre-commit baseline
- [x] Add custom API/custom URL override config

## P2

- [x] Add headless/windowed runner abstraction
- [x] Add session logging and trace ids
- [x] Replace preflight-only `/orch` with real provider subprocess execution
- [x] Add richer tests and CI

## Guide adaptation deltas

- [x] Repository documents guide intent through repo-native artifact names and crosswalk mapping (not verbatim one-file parity).
- [x] Pre-commit is documented as a minimum critical guardrail, while full verification remains `make check` + CI.
- [x] Runtime baseline is explicitly scoped to sequential `/orch`; parallel/debate lanes are out of current v1 scope.
- [x] Provider compatibility wording distinguishes adapter support from environment-dependent live success.
- [ ] Every change to guide-derived docs/process must update `README.md`, `docs/START_HERE.md`, `docs/QUALITY_GATES.md`, `docs/GUIDE_TRACEABILITY_AUDIT.md`, and `docs/PROVIDER_COMPATIBILITY.md` in the same change set.
