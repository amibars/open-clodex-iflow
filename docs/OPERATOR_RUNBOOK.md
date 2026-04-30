# OPERATOR_RUNBOOK.md

# Operator Runbook

> This runbook describes the current v1 workflow of `open-clodex-iflow` as it exists today: Windows-first, external sidecar CLI, sequential `/orch`, and lane presets instead of Codex patching.

---

## 1. Open the project and install the tool

```powershell
cd C:\Projects\open-clodex-iflow
python -m pip install -e .[dev]
```

## 2. Verify local discovery

```powershell
open-clodex-iflow doctor
open-clodex-iflow lanes
```

Use `doctor` to confirm which CLIs and local state directories are currently visible.
Use `lanes` to see the default planner pack and the optional lanes that are intentionally not enabled by default.

## 3. Default planner workflow

```powershell
open-clodex-iflow /orch "Review repository readiness" --mode windowed
```

Without `--providers` or `--lanes`, `/orch` resolves the `default-planners` lane set:

- `opencode-minimax-plan`

This is the recommended default because:

- `Codex` stays the human-facing control plane
- the default path avoids iFlow after its April 2026 shutdown/API-key drift
- the default uses the fastest correct OpenCode planner from the 2026-04-30 local benchmark
- the explicit write-capable lane is excluded unless requested on purpose

## 4. Explicit planner or build lanes

Use the stronger non-iFlow planner pack when OpenCode's NVIDIA provider is configured:

```powershell
open-clodex-iflow /orch "Review the current task" --lane-set recommended-planners --mode headless
```

This runs:

- `opencode-minimax-plan`
- `nvidia-glm51-plan`
- `nvidia-devstral2-plan`
- `nvidia-mistral-large3-plan`

Do not use this pack unless `opencode run --model nvidia/...` works on the machine. The lane set is implemented through OpenCode, not through a separate NVIDIA adapter.

Run only the lanes you want:

```powershell
open-clodex-iflow /orch "Review the current task" --lanes opencode-minimax-plan-thinking --mode headless
```

Use `gpt-5-nano` or `hy3` when you want an extra OpenCode opinion:

```powershell
open-clodex-iflow /orch "Review the current task" --lanes opencode-gpt5nano-plan-thinking --mode headless
open-clodex-iflow /orch "Review the current task" --lanes opencode-hy3-preview-plan-thinking --mode headless
```

Use the verified NVIDIA winners individually when you do not want the whole recommended set:

```powershell
open-clodex-iflow /orch "Review the current task" --lanes nvidia-glm51-plan --mode headless
open-clodex-iflow /orch "Review the current task" --lanes nvidia-devstral2-plan --mode headless
open-clodex-iflow /orch "Review the current task" --lanes nvidia-mistral-large3-plan --mode headless
```

Use iFlow lanes only when you intentionally want to use the configured API-key path:

```powershell
open-clodex-iflow /orch "Review with iFlow Kimi" --lanes iflow-kimi-k25-plan-thinking --mode headless
```

If you want a write-capable lane, request it explicitly:

```powershell
open-clodex-iflow /orch "Implement the approved fix" --lanes opencode-minimax-build-thinking --mode headless
```

The build lane is not part of the default pack by design.

## 5. Legacy raw-provider mode

If you want the old provider-only path instead of lane presets:

```powershell
open-clodex-iflow /orch "Review only through Claude" --providers claude --mode headless
```

Use this only when raw provider routing is more important than the planner/build policy encoded in lane presets.

## 6. How to read artifacts

Each run writes:

- `artifact.json`
- `consolidated_review.json`
- `session.log`
- one directory per executed lane under `providers/<lane-id>/`

Treat a lane as genuinely successful only if its `review.json` shows:

- `review_stage = runtime`
- a non-synthetic verdict

Synthetic failures are still useful operational evidence, but they do not prove that the lane completed a trustworthy review.

## 7. Important caveats

- `windowed` means operator-visible execution in the current terminal, not dedicated OS windows per lane.
- `iflow` is explicit opt-in after the April 2026 shutdown/API-key drift; `--thinking` is still best-effort when you use an iFlow lane.
- `opencode` planner/build lanes are driven through `--agent`, not through TUI automation.
- This repo does not currently patch Codex or add a native slash mode inside the Codex app itself.
