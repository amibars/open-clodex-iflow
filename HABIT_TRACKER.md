# HABIT_TRACKER.md

# Habit Tracker

> Метрики и ретроспектива нужны, чтобы улучшать execution system, а не спорить постфактум, почему “казалось нормальным”.

---

## Daily Log Template

### Project

- Name:
- Phase:
- Goal for the day:

### Tooling

- IDE / shell:
- Active models / agents:
- TDD Guard: on/off
- Pre-commit: on/off
- CI parity: local-only / local+workflow

### Time distribution

| Phase | Hours | Target | Status |
| --- | --- | --- | --- |
| Research |  | 40% |  |
| Plan |  | 30% |  |
| Build |  | 20% |  |
| Review |  | 10% |  |

### Execution metrics

| Metric | Value | Target |
| --- | --- | --- |
| Success rate |  | >= 80% |
| Loop count |  | <= 4 |
| Intervention count |  | <= 2 |
| Diff size |  | <= 25 files |

### Wins

- 

### Pains

- 

### Next

- 

---

## Current log: 2026-04-11

### Project

- Name: open-clodex-iflow
- Phase: bootstrap + docs/process parity
- Goal for the day: remove false confidence in guide parity before runtime expansion

### Tooling

- IDE / shell: Codex desktop + PowerShell
- Active models / agents: Codex as implementer, Linear as planning system
- TDD Guard: on
- Pre-commit: on
- CI parity: local + workflow spec

### Execution metrics

| Metric | Value | Target |
| --- | --- | --- |
| Success rate | local gates green | >= 80% |
| Loop count | low | <= 4 |
| Intervention count | low | <= 2 |
| Diff size | moderate | <= 25 files |

### Wins

- created Iron Dome-compatible starter layout
- fixed console entrypoint and shipped working `scaffold`, `/solo`, and `/orch` preflight commands
- raised enforcement from file-existence smoke to layer checks, TDD guard, skeleton tester, and CI workflow parity

### Pains

- real provider execution is still not implemented
- guide parity required an explicit audit because bootstrap happened before full parity

### Next

- replace preflight-only `/orch` with real provider adapters
- freeze `review.json` contract
- publish to GitHub only after docs/process parity is accepted
