# TASKS.md

# Task System

> Как `open-clodex-iflow` декомпозирует работу в repo-native artifacts и Linear.

---

## Task hierarchy

1. **PRD** задает product truth и anti-goals.
2. **Epic files** в `tasks/epics/` фиксируют крупные delivery lanes.
3. **Story files** в `tasks/stories/` задают implementation slice с тестами и acceptance criteria.
4. **Linear project/issues** отражают delivery status и owner-facing tracking.

---

## Task rules

- один story = один проверяемый implementation slice
- story не должен расширять scope эпика скрытым образом
- acceptance criteria должны быть проверяемыми локальными командами
- если change меняет runtime contract, story и docs обновляются вместе
- если task не проходит через quality gates, он не считается готовым

---

## Required story contents

- контекст
- outcome
- architecture integration
- step-by-step plan
- test cases
- edge cases
- acceptance criteria
- verification commands
- anti-goals

---

## Sync policy with Linear

- проект в Linear отражает текущий delivery state, но repo остается source of truth для технического контракта
- doc/process parity, runtime parity и publication gates ведутся как отдельные issues
- если issue закрыт, это должно соответствовать реальному состоянию repo, а не только обсуждению
