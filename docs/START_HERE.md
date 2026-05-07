# START_HERE.md

# Start Here

> Это project-native day-0 протокол для `open-clodex-iflow`. Он отвечает на вопрос: в каком порядке читать, что запускать и что считать обязательным до расширения runtime.

---

## Day-0 order

1. Прочитать [`docs/READ_FIRST.md`](./READ_FIRST.md) и зафиксировать продуктовые решения до изменения runtime.
2. Прочитать [`docs/PRD.md`](./PRD.md), [`docs/ARCH_SPEC.md`](./ARCH_SPEC.md) и [`docs/ORCHESTRATED.md`](./ORCHESTRATED.md), чтобы не спорить о контракте посреди реализации.
3. Проверить роли и границы в [`docs/AGENTS.md`](./AGENTS.md), [`docs/SKILLS.md`](./SKILLS.md) и [`reviewer.md`](../reviewer.md).
4. Если меняется runtime/orchestration scope на базе внешних проектов, прочитать [`docs/REUSE_RESEARCH_AUDIT.md`](./REUSE_RESEARCH_AUDIT.md) и явно отделить reference ideas от code reuse.
5. Если меняются fan-out/debate, timeout/retry, windowed behavior, provider subprocesses, memory, MCP или plugin-style expansion, прочитать соответствующие контракты: [`docs/PARALLEL_FANOUT_CONTRACT.md`](./PARALLEL_FANOUT_CONTRACT.md), [`docs/ATTEMPT_TIMEOUT_RETRY_CONTRACT.md`](./ATTEMPT_TIMEOUT_RETRY_CONTRACT.md), [`docs/WINDOWED_RUNTIME_CONTRACT.md`](./WINDOWED_RUNTIME_CONTRACT.md), [`docs/SECURITY_THREAT_MODEL.md`](./SECURITY_THREAT_MODEL.md).
6. Проверить quality gates в [`docs/QUALITY_GATES.md`](./QUALITY_GATES.md) и выполнить `make check`.
7. Только после зеленых gates расширять runtime behavior или adapter layer.

---

## Three defensive layers

### Layer 1: local repo gates

- `make lint`
- `make enforce`
- `make generated-pack`
- `make tdd`
- `make test-unit`
- `make test-integration`
- `make scan`
- `make test-skeleton`

### Layer 2: pre-commit minimum guardrail

- `.pre-commit-config.yaml` содержит минимальный набор критических enforcement-скриптов (`ruff check`, `enforcement/deps_rules.py`, `enforcement/tdd_guard.py`, `scripts/validate_story.py --all`, `scripts/check_generated_pack.py`, `enforcement/secret_scan.py`) для быстрого локального отсева.
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
- `docs/GENERATED_PACK_MANIFEST.json`
- `docs/REUSE_RESEARCH_AUDIT.md`
- `docs/PARALLEL_FANOUT_CONTRACT.md`
- `docs/ATTEMPT_TIMEOUT_RETRY_CONTRACT.md`
- `docs/WINDOWED_RUNTIME_CONTRACT.md`
- `docs/SECURITY_THREAT_MODEL.md`
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
