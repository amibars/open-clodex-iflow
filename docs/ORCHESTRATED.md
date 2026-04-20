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
- writes per-provider `review.json`, raw outputs, and one consolidated review
- default runtime mode: `windowed`
- optional runtime mode: `headless`
- default lane set: `default-planners`
- explicit lane inspection: `lanes`

---

## Generic orchestration pattern

1. Intake: определить scope, risk и packet boundary
2. Preflight: обнаружить providers, runtime mode и reusable auth/state
3. Fan-out: отправить normalized packet в reviewer lane
4. Review collection: собрать per-provider `review.json`
5. Aggregation: свести finding-ы и verdict в `consolidated_review.json`
6. Handback: вернуть решение в Codex/human control plane

Этот repo сейчас реализует `intake + preflight + sequential provider execution + aggregation`.

---

## Internal pipeline for `/orch`

1. Build artifact packet from current task
2. Discover providers and reusable auth/state
3. Resolve lane set or explicit lanes
4. Select runtime mode (`windowed` default)
5. Filter down to runnable providers with explicit adapter support
6. Execute lanes sequentially
7. Collect per-provider review outputs
8. Aggregate into consolidated review
9. Hand result back to Codex

---

## Artifact contract

- `artifact.json`: source task, privacy boundary, runtime mode, provider snapshot, intended next step
- `review.json`: one reviewer’s findings, verdict, confidence, missing evidence
- `consolidated_review.json`: grouped findings, final verdict, recommended next action

---

## Runtime rules

- system CLIs first
- local state/auth reuse first
- custom API/custom URL only as explicit override
- explicit override config is loaded from `.open-clodex-iflow/providers.json` or `OPEN_CLODEX_IFLOW_PROVIDER_CONFIG`
- default planner lane pack is:
  - `iflow-glm5-plan-thinking`
  - `iflow-qwen3coder-plan`
  - `iflow-kimi-k25-plan-thinking`
  - `opencode-minimax-plan-thinking`
- explicit write-capable lane is `opencode-minimax-build-thinking`
- no raw chat history handoff; only structured packets
- no silent downgrade from `/orch` to `/solo`
- no hidden reviewer with write authority over repo truth
- `windowed` means operator-visible execution; `headless` means capture-only execution
- `iflow` lane presets request `--plan`; `--thinking` is best-effort because `iflow` only enables it when the selected model supports it
- legacy `--providers` remains available as a compatibility path when operator wants raw provider routing instead of lane presets

---

## Current slice truth

- `doctor` and orchestration preflight already reuse system discovery and known state dirs
- `/solo` is a real packet-producing command and does not emit external packets
- `/orch` now executes runnable lanes sequentially and writes normalized provider reviews
- provider failures are normalized into synthetic blocking reviews instead of crashing the whole run
- current live compatibility is versioned in `docs/PROVIDER_COMPATIBILITY.md`

---

## Consensus policy (v1)

- single-pass fan-out
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
