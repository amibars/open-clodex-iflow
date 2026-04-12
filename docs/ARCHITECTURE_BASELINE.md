# ARCHITECTURE_BASELINE.md

# Architecture Baseline

> Исполняемые правила для open-clodex-iflow. Если правило можно проверить программно, оно должно быть частью enforcement.

---

## Core rules

1. `src/open_clodex_iflow/orchestration` может зависеть от adapter surface, но не знает provider-specific CLI деталей напрямую
2. `src/open_clodex_iflow/adapters` не принимают product decisions, только bridge к конкретному CLI/API
3. Dependency edge разрешен только в одну сторону: `orchestration -> adapters`; обратный импорт запрещен
4. `/solo` и `/orch` используют разные packet builders
5. Секреты и токены не коммитятся и не пишутся в логи в чистом виде
6. Любой custom API/base URL идет через explicit config, не hardcoded
7. Bootstrap/docs artifacts описываются в repo и генерируются через `scaffold`, а не через ad-hoc runtime side effects
8. Planning artifacts (`TASKS.md`, stories, TODO) обновляются вместе с поведением, если меняется contract truth

---

## Forbidden patterns

- hardcoded provider tokens
- implicit fan-out from `solo`
- provider-specific parsing outside adapter layer
- adapter code importing orchestration to recover product decisions
- silent fallback на другой provider без trace/log note
- runtime write в docs/task artifacts
- docs claims that exceed the implemented runtime slice

---

## Required docs before feature work

- `docs/START_HERE.md`
- `docs/READ_FIRST.md`
- `docs/EXECUTION_PRINCIPLES.md`
- `docs/AI_PROJECT_CHECKLIST.md`
- `docs/PRD.md`
- `docs/ARCH_SPEC.md`
- `docs/QUALITY_GATES.md`
- `docs/AGENTS.md`
- `docs/ORCHESTRATED.md`
- `docs/JTBD.md`
- `TASKS.md`

---

## Enforcement focus for v1

- required docs exist
- forbidden imports absent
- layer isolation enforced for `adapters`, `orchestration`, and `scaffold`
- secret scan clean
- TDD guard maps governed modules to tests
- story files keep required sections
- pre-commit mirrors the same local defenses
- CI workflow mirrors `make check`
- skeleton tester proves negative validation outside the main repo path
- traceability audit is versioned whenever guide-derived artifacts change
