# ORCHESTRATED.md

# Workflow Orchestration

> Основной UX deliberately сокращен до двух пользовательских режимов: `/solo` и `/orch`, но внутренний orchestration pattern описан шире, чем пользовательские команды.

---

## User-visible modes

### `/solo`

- private Codex-only mode
- no fan-out
- no external packet emission

### `/orch`

- Codex remains control plane
- runtime slice sends packet to the runnable reviewer pool through provider adapters
- writes per-provider `attempt.json`, `review.json`, raw outputs, and one consolidated review
- default runtime mode: `windowed`
- optional runtime mode: `headless`
- explicit Windows-only runtime mode: `dedicated-windows`
- default execution mode: `sequential`
- optional execution mode: `parallel`
- default lane set: `default-planners`
- recommended multi-review lane set: `recommended-planners`
- explicit lane inspection: `lanes`

---

## Generic orchestration pattern

1. Intake: определить scope, risk и packet boundary
2. Preflight: обнаружить providers, runtime mode и reusable auth/state
3. Fan-out: отправить normalized packet в reviewer lane
4. Review collection: собрать per-provider `review.json`
5. Aggregation: свести finding-ы и verdict в `consolidated_review.json`
6. Handback: вернуть решение в Codex/human control plane

Этот repo сейчас реализует `intake + preflight + sequential or optional parallel provider execution + aggregation`.

---

## Internal pipeline for `/orch`

1. Build artifact packet from current task
2. Discover providers and reusable auth/state
3. Resolve lane set or explicit lanes
4. Select runtime mode (`windowed` default)
5. Select execution mode (`sequential` default, `parallel` explicit)
6. Filter down to runnable providers with explicit adapter support
7. Execute lanes sequentially or as independent parallel workers
8. Collect per-provider review outputs
9. Aggregate into consolidated review
10. Hand result back to Codex

---

## Artifact contract

- `artifact.json`: source task, privacy boundary, runtime mode, provider snapshot, intended next step
- `attempt.json`: one provider execution attempt, state, command shape, timeout facts, exit code, and evidence paths
- `review.json`: one reviewer’s findings, verdict, confidence, missing evidence
- `consolidated_review.json`: grouped findings, final verdict, recommended next action

---

## Runtime rules

- system CLIs first
- local state/auth reuse first
- custom API/custom URL only as explicit override
- explicit override config is loaded from `.open-clodex-iflow/providers.json` or `OPEN_CLODEX_IFLOW_PROVIDER_CONFIG`
- default planner lane pack is:
  - `opencode-minimax-plan`
- recommended planner lane pack is:
  - `opencode-minimax-plan`
  - `nvidia-glm51-plan`
  - `nvidia-devstral2-plan`
  - `nvidia-mistral-large3-plan`
- recommended planner lanes use hybrid review lenses:
  - every lane reviews the full artifact
  - every lane may report any blocker
  - each lane gets extra attention instructions for its primary lens
  - `opencode-minimax-plan`: fast sanity/default reviewer
  - `nvidia-glm51-plan`: plan correctness reviewer
  - `nvidia-devstral2-plan`: implementation/code/runtime/test reviewer
  - `nvidia-mistral-large3-plan`: architecture/senior reviewer
- optional OpenCode planner lanes are:
  - `opencode-minimax-plan-thinking`
  - `opencode-gpt5nano-plan-thinking`
  - `opencode-hy3-preview-plan-thinking`
  - `opencode-big-pickle-plan-thinking`
  - `opencode-nemotron3-super-plan-thinking`
  - `nvidia-glm51-plan`
  - `nvidia-devstral2-plan`
  - `nvidia-mistral-large3-plan`
- `iflow` lanes remain available only as explicit legacy/API-key lanes after the April 2026 iFlow CLI shutdown notice:
  - `iflow-glm5-plan-thinking`
  - `iflow-qwen3coder-plan`
  - `iflow-kimi-k25-plan-thinking`
  - `iflow-minimax-plan-thinking`
- explicit write-capable lane is `opencode-minimax-build-thinking`
- no raw chat history handoff; only structured packets
- no silent downgrade from `/orch` to `/solo`
- no hidden reviewer with write authority over repo truth
- `windowed` means operator-visible execution in the current terminal flow
- `headless` means capture-first execution without the current terminal as the primary review surface
- `dedicated-windows` means explicit Windows-only one-shot lane windows with JSON request/status capture; it does not mean persistent TUI panes or native Codex slash-mode
- timeout and retry semantics are governed by `docs/ATTEMPT_TIMEOUT_RETRY_CONTRACT.md`
- `iflow` lane presets request `--plan`; `--thinking` is best-effort because `iflow` only enables it when the selected model supports it
- OpenCode benchmark evidence is tracked in `docs/OPENCODE_MODEL_BENCHMARK.md`; TUI-only models are not defaults until their CLI ids and non-interactive behavior are verified
- NVIDIA lane presets are routed through OpenCode and require an OpenCode `nvidia` provider config plus `NVIDIA_API_KEY`; they replace iFlow in the recommended planner set, not in the legacy adapter layer
- legacy `--providers` remains available as a compatibility path when operator wants raw provider routing instead of lane presets
- `--execution parallel` runs selected lanes concurrently in a single pass; it does not enable debate, retry loops, or write authority

---

## Current slice truth

- `doctor` and orchestration preflight already reuse system discovery and known state dirs
- `/solo` is a real packet-producing command and does not emit external packets
- `/orch` now executes runnable lanes sequentially and writes normalized provider reviews
- `/orch --execution parallel` runs selected lanes concurrently while preserving per-lane artifact directories and deterministic aggregation order
- `/orch --mode dedicated-windows` opens explicit Windows console lane windows while preserving stdout/stderr/status artifacts
- `recommended-planners` now has explicit hybrid review lenses; lanes are not restricted to their lens and still review the whole artifact
- provider failures are normalized into synthetic blocking reviews instead of crashing the whole run
- current live compatibility is versioned in `docs/PROVIDER_COMPATIBILITY.md`
- debate loops, persistent/attachable OS-window sessions, memory, MCP, and plugin-style expansion remain gated by their docs/security contracts

---

## Consensus policy (v1)

- single-pass fan-out, sequential by default and parallel only when explicitly requested
- no debate loop in v1
- consolidated verdict:
  - `proceed`
  - `fix_code`
  - `fix_plan`
  - `block`

## Non-goals for bootstrap slice

- no background autonomous agent swarm
- no hidden merge authority outside human gate
- no multi-pass debate protocol before stable adapter runtime exists
