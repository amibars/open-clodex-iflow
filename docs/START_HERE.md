# START_HERE.md

# Start Here

> Это project-native day-0 протокол для `open-clodex-iflow`. Он отвечает на вопрос: в каком порядке читать, что запускать и что считать обязательным до расширения runtime.

---

## Day-0 order

1. Прочитать [`docs/READ_FIRST.md`](./READ_FIRST.md) и зафиксировать продуктовые решения до изменения runtime.
2. Прочитать [`docs/PRD.md`](./PRD.md), [`docs/ARCH_SPEC.md`](./ARCH_SPEC.md) и [`docs/ORCHESTRATED.md`](./ORCHESTRATED.md), чтобы не спорить о контракте посреди реализации.
3. Проверить роли и границы в [`docs/AGENTS.md`](./AGENTS.md), [`docs/SKILLS.md`](./SKILLS.md) и [`reviewer.md`](../reviewer.md).
4. Проверить quality gates в [`docs/QUALITY_GATES.md`](./QUALITY_GATES.md) и выполнить `make check`.
5. Только после зеленых gates расширять runtime behavior или adapter layer.

---

## Three defensive layers

### Layer 1: local repo gates

- `make lint`
- `make enforce`
- `make tdd`
- `make test-unit`
- `make test-integration`
- `make scan`
- `make test-skeleton`

### Layer 2: pre-commit parity

- `.pre-commit-config.yaml` должен отражать те же локальные проверки, которые ожидаются до публикации.
- Если локальные правила меняются, `pre-commit` обновляется в том же change set.

### Layer 3: CI parity

- `.github/workflows/ci.yml` должен воспроизводить `make check`.
- CI не должен быть слабее локального gate.
- standalone skeleton harness остается отдельным доказательством, что enforcement ловит намеренные нарушения.

---

## Mandatory repo artifacts

- `docs/START_HERE.md`
- `docs/READ_FIRST.md`
- `docs/EXECUTION_PRINCIPLES.md`
- `docs/AI_PROJECT_CHECKLIST.md`
- `docs/PRD.md`
- `docs/ARCH_SPEC.md`
- `docs/AGENTS.md`
- `docs/SKILLS.md`
- `docs/ORCHESTRATED.md`
- `docs/ARCHITECTURE_BASELINE.md`
- `docs/QUALITY_GATES.md`
- `docs/JTBD.md`
- `TASKS.md`
- `TODO.md`
- `HABIT_TRACKER.md`
- `reviewer.md`

---

## Truthfulness policy

- Если capability еще не реализована, это должно быть явно помечено в docs.
- Если runtime поведение спорит с docs, сначала исправляется противоречие, потом расширяется scope.
- Если guide parity восстановлен только частично, это фиксируется в `docs/GUIDE_TRACEABILITY_AUDIT.md` как факт, а не как маркетинговое утверждение.
