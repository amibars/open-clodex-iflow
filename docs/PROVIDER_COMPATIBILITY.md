# PROVIDER_COMPATIBILITY.md

# Provider Compatibility

> Код поддерживает `claude`, `iflow`, `opencode` как runnable adapters. Эта матрица фиксирует последнее документированное наблюдаемое runtime-поведение и рабочие non-interactive contracts, если provider оказался чувствителен к форме prompt или runtime flags.

---

## Adapter support matrix

| Provider | Adapter in code | Non-interactive surface used now | Last documented live snapshot (2026-04-15) | Notes |
| --- | --- | --- | --- | --- |
| `claude` | yes | `claude -p --no-session-persistence` | live success documented | runtime now uses a compact provider-specific prompt plus `--no-session-persistence`; live headless `/orch` produces a normalized provider review after the quota reset |
| `iflow` | yes | `iflow -p --max-turns 1 --timeout <n> --stream false` | live success documented | runtime now uses an `iflow`-specific compact review prompt, does not pass `--plan` or `-o`, and live headless `/orch` produces a normalized provider review |
| `opencode` | yes | `opencode run --format json --dir <repo>` | live success documented | current smoke completed with `review_stage=runtime` and `verdict=proceed` on a compatibility artifact snapshot |

---

## Last documented smoke snapshot (2026-04-15)

- `opencode`
  - `orch` completed successfully in headless mode.
  - The provider produced a valid `review.json` and `consolidated_review.json` with `review_stage=runtime`.
  - This smoke used a compatibility artifact with no changed files, so it proves the provider lane is runnable, not that it reviewed a complex code-change artifact.
- `claude`
  - `doctor` still reports `binary+state` readiness and local auth reuse is confirmed.
  - The old blocked reason was provider quota. After reset, a direct machine-readable probe succeeds again and a real headless `orch` run completes with `review_stage=runtime` and `verdict=proceed`.
  - The remaining caveat is contract-specific, not auth-specific: the older verbose multi-line prompt shape produced `{}` or follow-up questions, and plain `claude -p` could emit a valid review and still hang in isolated headless execution. The documented happy path is the compact provider-specific prompt plus `--no-session-persistence`.
  - Latest successful local smoke: `C:\Projects\open-clodex-iflow\.tmp\claude-compat-20260415-c`, with valid `review.json`, `raw_output.txt`, and `consolidated_review.json`.
- `iflow`
  - Runtime command now forces `--stream false` and no longer passes `--plan` or `-o/--output-file`; direct probes confirm that `-o` is an execution-metadata channel, not a stable review-payload channel.
  - Browser login is no longer the active blocker. A direct minimal non-interactive probe returns model text, and a real headless `orch` run now completes with `review_stage=runtime` and `verdict=proceed`.
  - The remaining caveat is contract-specific, not auth-specific: `iflow` still reacts poorly to the older verbose multi-line prompt shape and to `-o`. The documented happy path is the compact provider-specific prompt plus `--stream false`.
  - Latest successful local smoke: `C:\Projects\open-clodex-iflow\.tmp\iflow-compat-20260415-d`, with valid `review.json`, `raw_output.txt`, and `consolidated_review.json`.

---

## Interpretation rules

- **Code support** means the adapter exists and is covered by tests.
- **Live success** means a real local smoke completed and produced a provider review with `review_stage=runtime`.
- **Failure-path evidence** means the adapter reached a real provider execution path and produced checkable blocking artifacts, but did not complete a successful review.
- `doctor` readiness (`missing`, `binary-only`, `binary+state`) is a discovery signal only. It is not proof that a provider can complete a real review right now.
- For `claude`, this snapshot documents a successful live review completion on this machine, but the success currently depends on the compact `claude` prompt contract and `--no-session-persistence`.
- For `iflow`, this snapshot documents a successful live review completion on this machine, but the success currently depends on the compact `iflow` prompt contract and `--stream false`.
- Presence of `review.json`, `session.log`, `stdout.txt`, or other artifacts alone is not evidence of provider success; success requires a normalized provider review with `review_stage=runtime`.

## How to self-check a provider on this machine

1. Run `open-clodex-iflow orch "<task>" --providers <provider> --mode headless --output-dir <dir>`.
2. Open `<dir>/consolidated_review.json` and the provider-specific `review.json`.
3. Treat the provider as success-verified only if:
   - `verdict` is not a synthetic failure for transport/runtime reasons, and
   - the provider review has `review_stage=runtime`.
4. If you only see timeout, quota, control/status events, or synthetic blocking reviews, treat the provider as discovered-but-not-success-verified and update this file with the blocked reason.
