# OpenCode Model Benchmark

Last local benchmark: 2026-04-30 on the Windows workstation used for this repo.

This benchmark is not a universal provider guarantee. It answers one practical question for v1: which OpenCode-routed models are currently worth using as non-interactive planner/reviewer lanes on this Windows workstation.

## CLI-visible models

`opencode models` currently exposes these model ids:

| Model id | CLI-visible | Tested |
| --- | --- | --- |
| `opencode/gpt-5-nano` | yes | yes |
| `opencode/minimax-m2.5-free` | yes | yes |
| `opencode/hy3-preview-free` | yes | yes |
| `opencode/big-pickle` | yes | yes |
| `opencode/nemotron-3-super-free` | yes | yes |

`opencode models nvidia` returns `Provider not found: nvidia` unless an OpenCode provider config exists for `nvidia`. The local NVIDIA key exists in OpenCode auth state, but OpenCode still needs provider config or `NVIDIA_API_KEY` in the execution environment for non-interactive runs.

## Benchmark results

Two bounded probes were run with `opencode run --format json --agent plan --model <model> --dir <repo> ...`.

| Model | Probe | Result | Latency | Interpretation |
| --- | --- | --- | --- | --- |
| `opencode/gpt-5-nano` | plan + thinking, self-check | success | 23.46s | Fast first-pass planner response. |
| `opencode/gpt-5-nano` | plan + thinking, applied default-choice review | success | 35.53s | Fast, but not enough to make it default. |
| `opencode/minimax-m2.5-free` | plan + thinking, self-check | timeout | 120.13s | Thinking mode can stall on some prompt shapes. |
| `opencode/minimax-m2.5-free` | plan, no thinking | success | 7.90s | Good fast optional lane when thinking is not needed. |
| `opencode/minimax-m2.5-free` | plan + thinking, applied default-choice review | success | 9.62s | Not globally broken, but latency is prompt-sensitive. |
| `opencode/hy3-preview-free` | plan + thinking, self-check | success | 42.18s | Usable optional lane; preview stability caveat remains. |
| `opencode/hy3-preview-free` | plan + thinking, applied default-choice review | success | 28.67s | Good optional second opinion. |
| `opencode/big-pickle` | plan + thinking, self-check | success | 27.18s | Useful optional lane; output can be verbose. |
| `opencode/big-pickle` | plan + thinking, applied default-choice review | success | 43.03s | Useful optional second opinion, but not yet default. |
| `opencode/nemotron-3-super-free` | plan + thinking, self-check | success | 59.06s | Capable but slower. |
| `opencode/nemotron-3-super-free` | plan + thinking, applied default-choice review | timeout | 90.07s | Too flaky for the default pack right now. |

## Current recommendation

Additional `/orch` candidate smokes were then run against the real orchestrator packet:

| Lane | Result | Interpretation |
| --- | --- | --- |
| `opencode-minimax-plan` | `proceed` | Fastest correct current default candidate. |
| `opencode-hy3-preview-plan-thinking` | `proceed` | Usable optional second opinion, but still preview-tier. |
| `opencode-gpt5nano-plan-thinking` | `fix_plan` | Fast, but over-penalized missing unplanned iFlow in the provider snapshot. |
| `opencode-big-pickle-plan-thinking` | `block` | Hit Windows runtime exit `3221226505` in one candidate smoke. |

After tightening the reviewer prompt scope rule, the default lane was re-smoked:

| Lane | Result | Interpretation |
| --- | --- | --- |
| `opencode-minimax-plan` | `proceed` | Default lane completed with `review_stage=runtime`; missing unplanned iFlow was correctly treated as context only. |

Default v1 planner lane:

- `opencode-minimax-plan`

Explicit optional planner lanes:

- `opencode-minimax-plan-thinking`
- `opencode-gpt5nano-plan-thinking`
- `opencode-hy3-preview-plan-thinking`
- `opencode-big-pickle-plan-thinking`
- `opencode-nemotron3-super-plan-thinking`

Reasoning:

- The default lane should be fast, non-writing, and repeatable enough for routine `/orch` checks.
- `MiniMax M2.5 Free` is the best default through the no-thinking plan lane; its thinking lane remains opt-in because one bounded thinking probe hit timeout.
- `GPT-5 Nano` remains optional because speed did not translate into the best `/orch` judgment on the provider snapshot.
- `Nemotron 3 Super Free` is capable, but currently too slow/flaky for the default pack.
- `Big Pickle` remains optional because one candidate smoke hit a Windows runtime exit.
- TUI-only Nvidia/OpenCode Zen models are not product defaults until their CLI ids and non-interactive behavior are verified.

## 2026-04-30 Full Requested Model Pass

Prompt shape: one short read-only `/orch` reviewer prompt, `opencode run --format json --agent plan`, no explicit `--thinking`, 75s timeout.

Important setup detail:

- OpenCode Zen free models worked through the built-in `opencode/*` ids.
- NVIDIA models required a local provider config for `nvidia` plus `NVIDIA_API_KEY` in the execution environment.
- Running NVIDIA ids from the repo root without that provider config returned `Model not found`.
- The temporary benchmark config stayed under `.tmp/` and was not added to git.

### OpenCode Zen Free Models

| Requested model | Runtime id | Result | Latency | Stack note |
| --- | --- | --- | --- | --- |
| Hy3 preview Free | `opencode/hy3-preview-free` | success, valid JSON, `proceed` | 41.86s | Correctly treated missing unplanned iFlow as non-blocking; good optional planner lane, but preview-tier. |
| MiniMax M2.5 Free | `opencode/minimax-m2.5-free` | success, extra prose before JSON | 72.79s | Correct reasoning but slow on this prompt and did not return JSON-only; keep default on the shorter smoke evidence, not this long-form prompt. |
| Nemotron 3 Super Free | `opencode/nemotron-3-super-free` | timeout | 75.08s | Too slow/flaky for default planner work. |

### NVIDIA Models

| Requested model | Runtime id | Result | Latency | Stack note |
| --- | --- | --- | --- | --- |
| DeepSeek V4 Flash | `nvidia/deepseek-ai/deepseek-v4-flash` | timeout | 75.13s | Not usable as a default lane in the current OpenCode/NVIDIA path. |
| DeepSeek V4 Pro | `nvidia/deepseek-ai/deepseek-v4-pro` | timeout | 75.07s | Not usable as a default lane in the current OpenCode/NVIDIA path. |
| Devstral-2-123B-Instruct-2512 | `nvidia/mistralai/devstral-2-123b-instruct-2512` | success, valid JSON, `proceed` | 9.83s | Strong candidate for an optional NVIDIA planner lane. Returned score as `0.8` despite requested 1-10 scale, so the prompt contract needs normalization. |
| Gemma-4-31B-IT | `nvidia/google/gemma-4-31b-it` | timeout | 75.10s | Not usable as default in the current path. |
| GLM-5.1 | `nvidia/z-ai/glm-5.1` | success, valid JSON, `proceed` | 9.22s | Strong candidate for an optional NVIDIA planner lane. Returned score as `0.85` despite requested 1-10 scale. |
| GLM5 | `nvidia/z-ai/glm5` | success, valid JSON, `proceed` | 32.33s | Usable but slower than GLM-5.1 and Devstral. Returned score as `0.8` despite requested 1-10 scale. |
| Kimi K2.5 | `opencode/kimi-k2.5` | model not found | 2.33s | Exact OpenCode Zen id is not available through the current account/cache. |
| Kimi K2.5 | `nvidia/moonshotai/kimi-k2.5` | gone / 410 | 3.01s | NVIDIA returned end-of-life: model reached EOL on 2026-04-30 and is no longer available. |
| MiniMax-M2.7 | `nvidia/minimaxai/minimax-m2.7` | timeout with partial prose | 75.06s | Started reasoning but did not finish; not default-safe. |
| Ministral 3 14B Instruct 2512 | `nvidia/mistralai/ministral-14b-instruct-2512` | success, valid JSON, `proceed` | 18.57s | Good optional lane candidate; slower than Devstral/GLM-5.1 but clean. |
| Mistral Large 3 675B Instruct 2512 | `nvidia/mistralai/mistral-large-3-675b-instruct-2512` | success, valid JSON, `proceed` | 14.82s | Good optional lane candidate; clean output and reasonable latency. |
| Nemotron 3 Nano Omni | `nvidia/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | timeout | 75.07s | Not usable as default in the current path. |
| Qwen3S-397B-A17B | `nvidia/qwen/qwen3.5-397b-a17b` | timeout with partial prose | 75.07s | Not usable as default in the current path. |

### Full-Pass Recommendation

Keep default:

- `opencode-minimax-plan`

Add only as explicit optional lanes after provider-config support is documented/implemented:

- `nvidia-glm51-plan`
- `nvidia-devstral2-plan`
- `nvidia-mistral-large3-plan`
- `nvidia-ministral3-plan`
- `nvidia-glm5-plan`

Do not add as default now:

- DeepSeek V4 Flash/Pro: timed out.
- Gemma-4-31B-IT: timed out.
- MiniMax-M2.7: timed out.
- Nemotron 3 Nano Omni: timed out.
- Qwen3S-397B-A17B: timed out.
- Kimi K2.5: exact runtime id unavailable/EOL in checked paths.

## Re-run checklist

1. Run `opencode models`.
2. Smoke each candidate with `opencode run --format json --agent plan --model <model> --dir <repo> "<prompt>"`.
3. Test thinking separately from non-thinking.
4. Promote a model to the default lane only after it completes at least one bounded applied-review prompt without timeout.
