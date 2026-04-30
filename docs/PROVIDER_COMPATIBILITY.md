# PROVIDER_COMPATIBILITY.md

# Provider Compatibility

> Код поддерживает `claude`, `iflow`, `opencode` как runnable adapters. Эта матрица фиксирует последнее документированное наблюдаемое runtime-поведение и рабочие non-interactive contracts, если provider оказался чувствителен к форме prompt или runtime flags.

---

## Adapter support matrix

| Provider | Adapter in code | Non-interactive surface used now | Last documented live snapshot (2026-04-15) | Notes |
| --- | --- | --- | --- | --- |
| `claude` | yes | `claude -p --no-session-persistence` | live success documented | runtime now uses a compact provider-specific prompt plus `--no-session-persistence`; live headless `/orch` produces a normalized provider review after the quota reset |
| `iflow` | yes | `iflow -m <model> -p --plan --max-turns 1 --timeout <n> --stream false [--thinking]` | historical success; now explicit legacy/API-key only | official iFlow CLI docs say the CLI was scheduled for shutdown on 2026-04-17 Beijing time; local settings now show an OpenAI-compatible API-key path, so iFlow is no longer safe as a default lane |
| `opencode` | yes | `opencode run --format json --dir <repo> [--agent <agent>] [--model <provider/model>] [--thinking]` | live success documented | runtime now supports `opencode` planner/build lanes through `--agent`; the default pack uses `opencode-minimax-plan`, while `opencode-minimax-build-thinking` stays explicit |

---

## Last documented smoke snapshot

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
  - Current status update (2026-04-30): official iFlow CLI docs now state that iFlow CLI was scheduled to shut down on 2026-04-17 Beijing time and recommend migration to Qoder. The local iFlow install and settings were removed on this machine, so `doctor` now reports `iflow` as missing.
  - Runtime command now forces `--stream false` and no longer passes `-o/--output-file`; direct probes confirm that `-o` is an execution-metadata channel, not a stable review-payload channel.
  - Historical local smoke evidence exists from before the shutdown/API-key drift, but it is no longer current operator truth for this machine.
  - Treat iFlow lanes as explicit paid/API-key or legacy lanes only. They are adapter-supported but not default free lanes.
  - Historical successful local smoke: `C:\Projects\open-clodex-iflow\.tmp\iflow-compat-20260415-d`, with valid `review.json`, `raw_output.txt`, and `consolidated_review.json`.
- `opencode`
  - `opencode` now has a documented lane contract around `--agent`, with `plan` and `build` exposed through non-interactive CLI surface rather than only through the TUI.
  - The default planner pack uses `opencode-minimax-plan`; the explicit write-capable path is `opencode-minimax-build-thinking`.
  - The 2026-04-30 OpenCode benchmark found `opencode/minimax-m2.5-free` without thinking to be the fastest correct `/orch` planner candidate. `opencode/gpt-5-nano` is fast but produced a false planning block against missing unplanned iFlow in one smoke. `opencode/nemotron-3-super-free` is capable but too slow/flaky for the default pack right now, and `opencode/big-pickle` produced a Windows runtime exit in one candidate smoke.
  - After adding an explicit prompt scope rule, the default `opencode-minimax-plan` smoke completed with `review_stage=runtime` and `verdict=proceed`; missing unplanned iFlow was treated as context only.
  - A full requested model pass was added to `docs/OPENCODE_MODEL_BENCHMARK.md`. NVIDIA models require explicit OpenCode provider config plus `NVIDIA_API_KEY` in the runtime environment; auth state alone is not enough for repo-root non-interactive lanes.
  - Current strongest NVIDIA candidates from the bounded pass are implemented as OpenCode-routed optional lanes: `nvidia-glm51-plan`, `nvidia-devstral2-plan`, and `nvidia-mistral-large3-plan`.
  - `recommended-planners` is the non-iFlow multi-review lane set. It uses `opencode-minimax-plan` plus the three verified NVIDIA winners. It is not the default because NVIDIA still requires explicit OpenCode provider config plus `NVIDIA_API_KEY` on the machine.
  - `nvidia-ministral3-plan` and `nvidia-glm5-plan` were intentionally not promoted: Mistral Large 3 is the stronger Mistral-family pick, and GLM-5.1 was faster than GLM5 in the bounded pass.
  - We currently treat `thinking` as requested behavior, not a universal backend guarantee; provider/model-specific semantics can still vary.

---

## Interpretation rules

- **Code support** means the adapter exists and is covered by tests.
- **Live success** means a real local smoke completed and produced a provider review with `review_stage=runtime`.
- **Failure-path evidence** means the adapter reached a real provider execution path and produced checkable blocking artifacts, but did not complete a successful review.
- `doctor` readiness (`missing`, `binary-only`, `binary+state`) is a discovery signal only. It is not proof that a provider can complete a real review right now.
- For `claude`, this snapshot documents a successful live review completion on this machine, but the success currently depends on the compact `claude` prompt contract and `--no-session-persistence`.
- For `iflow`, the old success snapshot is historical. Current operator truth is explicit opt-in only because the provider has shifted to shutdown/API-key behavior.
- For `iflow`, planner presets also depend on the selected model honoring `--plan` and, optionally, `--thinking`; the CLI does not expose a model capability matrix, so those toggles are best-effort outside the documented local smokes.
- For `opencode`, planner/build lane selection now depends on `--agent plan|build` rather than TUI-only mode selection.
- Presence of `review.json`, `session.log`, `stdout.txt`, or other artifacts alone is not evidence of provider success; success requires a normalized provider review with `review_stage=runtime`.

## How to self-check a provider on this machine

1. Run `open-clodex-iflow lanes` to inspect the current lane presets.
2. Run either `open-clodex-iflow orch "<task>" --mode headless --output-dir <dir>` for the default planner pack or `open-clodex-iflow orch "<task>" --lanes <lane-id> --mode headless --output-dir <dir>` for an explicit lane.
3. Open `<dir>/consolidated_review.json` and the provider-specific `review.json`.
4. Treat the provider as success-verified only if:
   - `verdict` is not a synthetic failure for transport/runtime reasons, and
   - the provider review has `review_stage=runtime`.
5. If you only see timeout, quota, control/status events, or synthetic blocking reviews, treat the provider as discovered-but-not-success-verified and update this file with the blocked reason.
