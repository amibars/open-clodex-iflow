# PRD.md

# Product Requirements Document (PRD)

**Epic:** Bootstrap reusable orchestration and scaffold tool

**Version:** 1.0

**Status:** DRAFT

**Owner:** karte

**Last Updated:** 2026-04-11

---

## 1. Контекст и Scope

### Цель

Создать reusable Windows-first инструмент, который поднимает Iron Dome-compatible workspace и оркестрирует локально установленные `Codex`, `Claude Code`, `iFlow` и `OpenCode` через два пользовательских режима: `/solo` и `/orch`.

### User Story

Как инженер-оператор, я хочу запускать приватную или оркестровую AI-разработку из терминала без повторного логина в каждый CLI, чтобы быстро переходить от одиночной работы к multi-review loop.

### Anti-Goals (Что НЕ делаем)

- Не строим full plugin platform в v1
- Не делаем обязательную зависимость от WSL или ClawTeam в v1
- Не строим web UI или dashboard в первой версии

---

## 2. Функциональные требования

| ID | Требование | Acceptance Criteria | Приоритет | Bootstrap status |
| --- | --- | --- | --- | --- |
| FR-01 | Bootstrap scaffold | Команда scaffold создает Iron Dome-compatible структуру проекта с обязательными docs и tasks | P0 | Implemented |
| FR-02 | Solo mode | `/solo` не делает fan-out и не отправляет контекст другим LLM | P0 | Implemented as packet-only flow |
| FR-03 | Orch mode | `/orch` собирает artifact packet, запускает runnable provider adapters, пишет per-provider `review.json` и возвращает один consolidated review | P0 | Implemented as sequential runtime with synthetic failure fallback |
| FR-04 | System discovery | `doctor` показывает найденные CLI и локальные state/auth директории | P0 | Implemented |
| FR-05 | Existing auth reuse | Оркестратор сначала пытается использовать уже существующие системные CLI и их local state | P0 | Implemented for discovery/preflight |
| FR-06 | Runtime mode toggle | `/orch` поддерживает `windowed` и `headless`, при этом по умолчанию используется `windowed` | P1 | Implemented |
| FR-07 | Custom API fallback | Можно задать custom API/base URL как override, если reuse existing auth невозможен | P1 | Planned |

---

## 3. Нефункциональные требования

- **Производительность:** orchestration preflight должен укладываться в < 3s без запуска провайдеров
- **Безопасность:** токены и секреты не храним в repo и не логируем в чистом виде
- **Наблюдаемость:** каждая orchestration session имеет trace id, `session.log` и per-provider raw outputs
- **Соответствие:** конфиги и docs должны жить в repo и быть пригодны для open-source публикации

---

## 4. Vibe & UI/UX

- **Тон:** строгий, инженерный, terminal-first
- **Референс:** operator UX, где `Codex` остается главным control plane, а остальные агенты работают как backend workers

---

## 5. Инструкции для AI-агента

<aside>
⚠️

**Критично для агента:**

- не предполагать повторную авторизацию, пока не проверены локальные CLI/state dirs
- не отправлять историю `/solo` в reviewer pool
- не смешивать orchestration logic с provider-specific business logic
- писать tests и enforcement раньше расширения runtime behavior
</aside>

---

## 6. Definition of Done (DoD)

### Bootstrap slice

- [x] scaffold repo и обязательные docs созданы
- [x] `doctor` показывает найденные системные CLI/state dirs
- [x] `solo` и `orch` команды существуют и проходят smoke checks
- [x] `/orch` пишет per-provider `review.json` и `consolidated_review.json`
- [x] `make check` проходит
- [ ] human reviewed и approved

### Next implementation slice

- [ ] parallel fan-out policy и dedicated window spawning зафиксированы как stable contract
- [ ] custom API/base URL override покрыт тестами
- [ ] live provider compatibility matrix подтверждена для всех supported CLIs

---

## 7. Риски

| Риск | Вероятность | Воздействие | Mitigation |
| --- | --- | --- | --- |
| Headless/TUI несовместимость у отдельных CLI | Высокая | Высокое | Ввести reuse-first detection и dual runtime mode |
| Случайная утечка приватного контекста из `/solo` | Средняя | Высокое | Жестко разделить packet builders для `/solo` и `/orch` |
| Слишком ранняя plugin-архитектура | Средняя | Среднее | Держать internal adapter API, но не выносить в plugins в v1 |

---

## 8. Ограничения

- **Время:** сначала bootstrap и starter docs, потом runtime logic
- **Зависимости:** Python 3.11+, локально установленные CLI providers
- **Запреты:** no hardcoded secrets, no mandatory WSL dependency, no implicit fan-out from `/solo`

---

## 9. Ссылки

- Guide source: `C:\Projects\Iron Dome [GUIDE]`
- Runtime focus: `Codex`, `Claude Code`, `iFlow`, `OpenCode`
