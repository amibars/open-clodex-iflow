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

### Layer 2: pre-commit minimum guardrail

- `.pre-commit-config.yaml` содержит минимальный набор критических enforcement-скриптов (`ruff check`, `enforcement/deps_rules.py`, `enforcement/tdd_guard.py`, `scripts/validate_story.py --all`, `enforcement/secret_scan.py`) для быстрого локального отсева.
- Этот слой намеренно уже, чем полный gate (`make check` + CI), и не должен описываться как полная эквивалентность всех проверок.
- Если меняется критический enforcement-скрипт или добавляется новый обязательный guard, обновляйте `pre-commit` в том же change set.

### Layer 3: CI quality gate

- `.github/workflows/ci.yml` должен поддерживать эквивалентный quality contract: на Unix через `make check`, на Windows — через явный список тех же базовых проверок и отдельный skeleton step.
- CI не должен быть слабее локального quality gate.
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
- Если есть guide adaptation deltas, это фиксируется в `docs/GUIDE_TRACEABILITY_AUDIT.md` как факт, а не как маркетинговое утверждение.
