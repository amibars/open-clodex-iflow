# QUALITY_GATES.md

# Quality Gates

> Никакой LLM review не заменяет реальные гейты.

---

## Core commands

- `python -m pip install -e .[dev]`
- `make enforce`
- `make tdd`
- `make lint`
- `make test-unit`
- `make test-integration`
- `make scan`
- `make test-enforcement`
- `make test-skeleton`
- `make check-fast`
- `make check`

---

## Gate policy

### Pre-implementation

- START_HERE exists
- READ_FIRST exists
- execution principles exist
- AI project checklist exists
- PRD exists
- ARCH_SPEC exists
- BASELINE exists
- TASKS exists
- first epic and first story exist
- traceability audit is updated when guide-derived artifacts changed

### Traceability gate

- `docs/GUIDE_TRACEABILITY_AUDIT.md` exists
- matrix status matches the current repo state
- historical note is preserved when parity was restored after bootstrap
- if a guide-derived artifact changes, the audit is updated in the same change set

### Local fast gate

- `make lint`
- `make enforce`
- `make tdd`
- `make test-unit`

### Full gate

- `make check`
- CI workflow runs the same `make check` contract and then the standalone skeleton harness

### Human gate

- bootstrap docs reviewed
- risky auth/runtime decisions reviewed

---

## Current thresholds

- zero missing required docs
- zero layer-isolation violations
- zero detected secret patterns
- TDD guard green for governed modules
- all unit and integration smoke tests green
- story validator green
- standalone skeleton tester green
- `pre-commit` config exists and mirrors local enforcement commands
- `.github/workflows/ci.yml` mirrors the full local gate
