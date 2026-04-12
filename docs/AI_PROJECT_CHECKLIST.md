# AI_PROJECT_CHECKLIST.md

# AI Project Checklist

> Короткий project-native checklist перед началом нового implementation slice. Он не заменяет PRD, а помогает не стартовать в тумане.

---

## Problem and scope

- Какая конкретная user/job проблема решается?
- Что является anti-goal для этого slice?
- Что остается planned и не должно быть случайно “обещано” в docs?

## Architecture and contracts

- Какие слои будут затронуты: `cli`, `contracts`, `adapters`, `orchestration`, `scaffold`, `enforcement`?
- Меняется ли `artifact.json`, `review.json`, `consolidated_review.json`?
- Сохраняется ли privacy boundary между `/solo` и `/orch`?

## Runtime and provider reality

- Есть ли подтвержденный invocation path для нужного provider CLI?
- Что известно о `windowed` vs `headless` behavior на Windows?
- Reuse existing auth/state проверен или это только предположение?

## Quality and safety

- Какие tests должны упасть до реализации?
- Какие enforcement rules должны остаться зелеными?
- Может ли change привести к утечке секретов, raw transcript handoff или silent fallback?

## Docs and release readiness

- Какие docs обновляются вместе с change?
- Нужно ли изменить `TASKS.md`, epic/story, `TODO.md` или `HABIT_TRACKER.md`?
- После merge состояние репозитория будет понятно внешнему open-source читателю?
