# OpenCode Model Benchmark

Last local benchmark: 2026-04-30 on the Windows workstation used for this repo.

This benchmark is not a universal provider guarantee. It answers one practical question for v1: which `opencode/*` models are currently worth using as non-interactive planner/reviewer lanes.

## CLI-visible models

`opencode models` currently exposes these model ids:

| Model id | CLI-visible | Tested |
| --- | --- | --- |
| `opencode/gpt-5-nano` | yes | yes |
| `opencode/minimax-m2.5-free` | yes | yes |
| `opencode/hy3-preview-free` | yes | yes |
| `opencode/big-pickle` | yes | yes |
| `opencode/nemotron-3-super-free` | yes | yes |

`opencode models nvidia` currently returns `Provider not found: nvidia`. Models visible only in the OpenCode TUI/Nvidia picker are not enabled as default lanes until a valid non-interactive model id is verified.

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

## Re-run checklist

1. Run `opencode models`.
2. Smoke each candidate with `opencode run --format json --agent plan --model <model> --dir <repo> "<prompt>"`.
3. Test thinking separately from non-thinking.
4. Promote a model to the default lane only after it completes at least one bounded applied-review prompt without timeout.
