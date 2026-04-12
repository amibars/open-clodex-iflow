# PROVIDER_COMPATIBILITY.md

# Provider Compatibility

> Код поддерживает `claude`, `iflow`, `opencode` как runnable adapters. Эта матрица фиксирует не только code support, но и фактически подтвержденное runtime поведение.

---

## Adapter support matrix

| Provider | Adapter in code | Non-interactive surface used | Current live status | Notes |
| --- | --- | --- | --- | --- |
| `claude` | yes | `claude -p` | timeout in current environment | synthetic blocking review is produced correctly |
| `iflow` | yes | `iflow -p --plan -o <file>` | timeout in current environment | synthetic blocking review is produced correctly |
| `opencode` | yes | `opencode run --format json --dir <repo>` | intermittent in current environment | one earlier live success was followed by a later timeout-driven synthetic block |

---

## Verified on 2026-04-12

- `opencode` completed one earlier live smoke run, but a later smoke also demonstrated a timeout-driven synthetic blocking review.
- `claude` and `iflow` both exercised the timeout/synthetic-failure path successfully.
- synthetic failure handling writes `review.json`, `session.log`, and placeholder output files instead of crashing the orchestration run.

---

## Interpretation

- **Code support** means the adapter exists and is covered by tests.
- **Live success** means at least one real local smoke run completed with the installed CLI in this environment.
- **Timeout in current environment** does not mean the adapter is unusable everywhere; it means this machine/session did not yet produce a successful live review for that provider.
- `doctor` now reports `readiness` as one of `missing`, `binary-only`, or `binary+state` so the snapshot distinguishes "CLI found" from "CLI found and local reuse-state detected".
- `readiness` is still a discovery signal, not a full auth or provider-health guarantee; real runtime confirmation comes from a successful orchestration run.
