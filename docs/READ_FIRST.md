# READ_FIRST.md

# Read First

> Этот документ фиксирует pre-build decisions для `open-clodex-iflow`, чтобы не начинать реализацию с плавающих предпосылок.

---

## Product framing

- **Product type:** Windows-first orchestration and scaffold CLI.
- **Primary operator:** один инженер/PM/operator, работающий из терминала.
- **Control plane:** `Codex`.
- **Reviewer pool:** `Claude Code`, `iFlow`, `OpenCode`.
- **Default orchestration mode:** `windowed`.
- **Fallback mode:** `headless`.

---

## Already decided

1. Внешний продуктовый UX сокращен до двух режимов: `/solo` и `/orch`.
2. `scaffold` обязан создавать disciplined engineering baseline, а не пустой каталог.
3. Discovery идет по принципу reuse-first: сначала системные CLI и локальные state dirs, потом уже OAuth/API overrides.
4. `/solo` не делает fan-out и не передает приватный контекст наружу.
5. `/orch` должен работать через structured packets, а не через raw transcript handoff.
6. GitHub publication идет после docs/process parity и рабочего runtime, а не раньше.

---

## Non-goals for the bootstrap slice

- не строить plugin framework
- не делать обязательную зависимость от WSL
- не добавлять web dashboard
- не превращать reviewer lane в write-capable code lane

---

## Questions to answer before changing runtime

1. Что именно меняется: discovery, adapter execution, packet schema или aggregation?
2. Какая privacy boundary затронута: `/solo`, `/orch`, custom API override или human gate?
3. Какие docs надо обновить вместе с кодом: `PRD`, `ARCH_SPEC`, `ORCHESTRATED`, `QUALITY_GATES`, `TASKS`?
4. Какие tests доказывают change: unit, integration, skeleton, contract smoke?
5. Остается ли поведение пригодным для open-source публикации без скрытого локального знания?

---

## Open questions for the next runtime slice

- единый transport contract для `review.json`
- стабильная стратегия запуска provider workers на Windows TTY/GUI
- explicit policy для custom API/base URL overrides
- trace/log format для multi-provider execution
