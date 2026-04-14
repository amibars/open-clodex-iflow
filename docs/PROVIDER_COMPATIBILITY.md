# PROVIDER_COMPATIBILITY.md

# Provider Compatibility

> Код поддерживает `claude`, `iflow`, `opencode` как runnable adapters. Эта матрица фиксирует не только code support, но и фактически подтвержденное runtime поведение.

---

## Adapter support matrix

| Provider | Adapter in code | Non-interactive surface used | Last documented smoke snapshot (2026-04-12) | Notes |
| --- | --- | --- | --- | --- |
| `claude` | yes | `claude -p` | timeout was observed | synthetic blocking review path produced output artifacts |
| `iflow` | yes | `iflow -p --plan -o <file>` | timeout was observed | synthetic blocking review path produced output artifacts |
| `opencode` | yes | `opencode run --format json --dir <repo>` | mixed outcome (success + timeout) | one earlier live success was followed by a later timeout-driven synthetic block |

---

## Last documented smoke snapshot (2026-04-12)

- `opencode` completed one earlier live smoke run, but a later smoke also demonstrated a timeout-driven synthetic blocking review.
- `claude` and `iflow` both exercised the timeout/synthetic-failure path successfully.
- synthetic failure handling writes `review.json`, `session.log`, and placeholder output files instead of crashing the orchestration run.
- This documentation pass did not run new live provider smoke tests; treat the table as historical evidence until a new run updates it.

---

## Interpretation

- **Code support** means the adapter exists and is covered by tests.
- **Live success** means at least one real local smoke run completed with the installed CLI in this environment.
- **Historical timeout observation** does not mean the adapter is unusable everywhere; it means that snapshot captured timeout behavior for that machine/session.
- `doctor` now reports `readiness` as one of `missing`, `binary-only`, or `binary+state` so the snapshot distinguishes "CLI found" from "CLI found and local reuse-state detected".
- `readiness` is still a discovery signal, not a full auth or provider-health guarantee; real runtime confirmation comes from a successful orchestration run.
- If current live status is required, rerun smoke checks and update this file in the same change set.
