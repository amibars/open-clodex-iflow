# PROVIDER_COMPATIBILITY.md

# Provider Compatibility

> Код поддерживает `claude`, `iflow`, `opencode` как runnable adapters. Эта матрица фиксирует последнее документированное наблюдаемое runtime-поведение; для части провайдеров это может быть только failure-path evidence, а не успешный live review.

---

## Adapter support matrix

| Provider | Adapter in code | Non-interactive surface used now | Last documented live snapshot (2026-04-14) | Notes |
| --- | --- | --- | --- | --- |
| `claude` | yes | `claude -p` | blocked by provider quota | `claude auth status` confirms reuse-first auth, but live non-interactive review is currently rejected by `rate_limit_event` / `You're out of extra usage` until reset |
| `iflow` | yes | `iflow -p --max-turns 1 --timeout <n>` | invalid payload observed | runtime no longer uses `--plan`; current live run still returns control/status payloads or empty fenced JSON instead of a valid review, so successful end-to-end review is not documented in this snapshot |
| `opencode` | yes | `opencode run --format json --dir <repo>` | live success documented | current smoke completed with `review_stage=runtime` and `verdict=proceed` on a compatibility artifact snapshot |

---

## Last documented smoke snapshot (2026-04-14)

- `opencode`
  - `orch` completed successfully in headless mode.
  - The provider produced a valid `review.json` and `consolidated_review.json` with `review_stage=runtime`.
  - This smoke used a compatibility artifact with no changed files, so it proves the provider lane is runnable, not that it reviewed a complex code-change artifact.
- `claude`
  - `doctor` still reports `binary+state` readiness and local auth reuse is confirmed.
  - A direct machine-readable probe with `claude -p --verbose --no-session-persistence --output-format stream-json --include-hook-events ...` produced `rate_limit_event` with `status=rejected`, `rateLimitType=five_hour`, `overageDisabledReason=out_of_credits`.
  - The same probe returned `You're out of extra usage · resets 2am (Europe/Moscow)`, so the current blocked reason is provider quota, not missing auth or a broken adapter path.
- `iflow`
  - Runtime command no longer includes `--plan`; that earlier flag combination was confirmed to trigger a different control/ready mode and was removed from the adapter.
  - A direct no-`--plan` probe can return a non-interactive JSON answer, so the adapter is no longer blocked on the original `--plan` misuse.
  - The latest full `orch` smoke still did not complete a valid review: the provider emitted only `{"status":"ready", ...}` or fenced `{}` plus stderr diagnostics such as `Error fetching iFlow user info`, and no valid review payload was normalized.
  - Therefore this snapshot documents failure-path evidence only; a successful live end-to-end `iflow` review is still not documented.

---

## Interpretation rules

- **Code support** means the adapter exists and is covered by tests.
- **Live success** means a real local smoke completed and produced a provider review with `review_stage=runtime`.
- **Failure-path evidence** means the adapter reached a real provider execution path and produced checkable blocking artifacts, but did not complete a successful review.
- `doctor` readiness (`missing`, `binary-only`, `binary+state`) is a discovery signal only. It is not proof that a provider can complete a real review right now.
- For `claude` and `iflow`, this snapshot does **not** document a successful live review completion. It documents explicit blocked reasons and synthetic-failure handling.
- Presence of `review.json`, `session.log`, `stdout.txt`, or other artifacts alone is not evidence of provider success; success requires a normalized provider review with `review_stage=runtime`.

## How to self-check a provider on this machine

1. Run `open-clodex-iflow orch "<task>" --providers <provider> --mode headless --output-dir <dir>`.
2. Open `<dir>/consolidated_review.json` and the provider-specific `review.json`.
3. Treat the provider as success-verified only if:
   - `verdict` is not a synthetic failure for transport/runtime reasons, and
   - the provider review has `review_stage=runtime`.
4. If you only see timeout, quota, control/status events, or synthetic blocking reviews, treat the provider as discovered-but-not-success-verified and update this file with the blocked reason.
