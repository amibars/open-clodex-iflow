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

- `iflow-glm5-plan-thinking`
- `iflow-qwen3coder-plan`
- `iflow-kimi-k25-plan-thinking`
- `opencode-minimax-plan-thinking`

This is the recommended default because:

- `Codex` stays the human-facing control plane
- `iflow` lanes request `--plan`
- only one `MiniMax` source is used by default
- the explicit write-capable lane is excluded unless requested on purpose

## 4. Explicit planner or build lanes

Run only the lanes you want:

```powershell
open-clodex-iflow /orch "Review the current task" --lanes iflow-glm5-plan-thinking,opencode-minimax-plan-thinking --mode headless
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
- `iflow --thinking` is best-effort; the CLI itself says it only works when the selected model supports it.
- `opencode` planner/build lanes are driven through `--agent`, not through TUI automation.
- This repo does not currently patch Codex or add a native slash mode inside the Codex app itself.
