# GUIDE_TRACEABILITY_AUDIT.md

# Iron Dome Guide Traceability Audit

**Audit date:** 2026-04-14  
**Source guide:** `C:\Projects\Iron Dome [GUIDE]`  
**Target repo:** `C:\Projects\open-clodex-iflow`

---

## Verdict

Нет, guide не был скопирован в проект целиком и не был полностью заполнен по принципу `каждый guide-file -> отдельный project-file` до начала первой разработки.

Что было сделано по факту:

- ключевые guide-документы были использованы как reference и адаптированы под продукт
- часть protocol-level требований была внедрена уже в remediation pass
- исходно несколько guide-файлов были reference-only или не были приняты в проект как отдельные артефакты; ниже зафиксировано уже текущее исправленное состояние repo

README.md, TODO.md и этот audit теперь формируют единую authoritative snapshot, который описывает, какие адаптации уже сделаны и как repo-native baseline соотносится с guide без притворства о verbatim copy.

---

## Status legend

- `covered` — смысл guide-файла перенесен в проектный артефакт достаточно полно
- `partial` — смысл использован, но покрыт упрощенно или не полностью
- `reference-only` — файл использовался как внешний reference, но не получил собственного project-equivalent
- `not-adopted` — файл не был перенесен как часть baseline или оказался вне текущего product scope

---

## File-by-file matrix

| Guide file | Main purpose | Project mapping | Status | Notes |
| --- | --- | --- | --- | --- |
| `0. READ-FIRST.md` | pre-build discovery questions and architecture discussion checklist | `docs/READ_FIRST.md`, `docs/PRD.md`, `docs/ARCH_SPEC.md`, `docs/JTBD.md` | `covered` | Repo-native discovery gate now exists and points to the concrete project decisions |
| `02_ARCH_SPEC md ff00fbec53364a9fa19e155b38f993e9.md` | formal architecture template | `docs/ARCH_SPEC.md` | `covered` | Adapted into a project-specific spec with packet contracts and ADRs |
| `1. START-HERE.md` | Iron Dome protocol, three defensive layers, starter structure | `docs/START_HERE.md`, `README.md`, `Makefile`, `enforcement/*`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `skeleton-tester/README.md`, `docs/QUALITY_GATES.md` | `covered` | Repo-native day-0 protocol and three defensive layers are now explicit |
| `AGENTS md 2e7fded2356580bdb196e916ea215b65.md` | role system and agent-as-code methodology | `docs/AGENTS.md` | `covered` | Repo-native role matrix, responsibilities, forbiddens, and handoff rules are now explicit |
| `ARCHITECTURE_BASELINE md 2e7fded23565801185eafa8166ac25e9.md` | executable architectural rules | `docs/ARCHITECTURE_BASELINE.md`, `enforcement/deps_rules.py` | `covered` | Product-specific architectural rules and their enforcement focus are now explicit and executable for this repo |
| `HABIT_TRACKER md 2e7fded235658036a3e6cefdc246f177.md` | metrics and retrospective template | `HABIT_TRACKER.md` | `covered` | Daily template, metrics, and current log now exist in repo-native form |
| `INTRO.md` | umbrella principles for AI execution discipline | `docs/EXECUTION_PRINCIPLES.md`, `README.md`, `docs/QUALITY_GATES.md`, `docs/JTBD.md` | `covered` | Core execution discipline now has a dedicated repo-native equivalent |
| `ORCHESTRATED md 2e7fded235658043b118c90541066c19.md` | agent orchestration patterns | `docs/ORCHESTRATED.md` | `covered` | Document now covers both the generic orchestration pattern and the product-specific `/solo`/`/orch` mapping |
| `PRD md 2e7fded2356580f3bcf0c40317a5be8e.md` | product requirements template | `docs/PRD.md` | `covered` | Fully adapted as a product-specific PRD |
| `QUALITY_GATES md 2e7fded2356580ea815bcbc26aae11f5.md` | command center and CI gates | `docs/QUALITY_GATES.md`, `Makefile`, `.github/workflows/ci.yml` | `covered` | Local and CI gate layers use an equivalent quality contract |
| `reviewer.md` | repo forensics / audit reviewer persona | `reviewer.md` | `covered` | A project-native reviewer profile now exists in the repo |
| `Skeleton Enforcement TESTER 2e7fded2356580bab51ee461d456bc22.md` | prove enforcement with intentional violations before real work | `scripts/run_skeleton_tester.py`, `skeleton-tester/README.md`, `Makefile`, `tests/unit/test_skeleton_tester.py` | `covered` | Standalone negative-validation harness now exists and is executable |
| `SKILLS md 2e7fded2356580d8bd8fd6523a1a9486.md` | skills matrix and escalation boundaries | `docs/SKILLS.md` | `covered` | Competency matrix, tools, and escalation rules are now explicit |
| `TASKS.md` | task/repository decision-system architecture | `TASKS.md`, `tasks/epics/*`, `tasks/stories/*`, `TODO.md` | `covered` | Repo-native task system now defines how backlog, stories, and Linear stay aligned |
| `TODO md (Quick Start) 2e7fded2356580a4984ff1dd94078cee.md` | day-0 setup checklist | `TODO.md`, `Makefile`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `HABIT_TRACKER.md` | `covered` | Setup artifacts are now present in repo-native form |
| `Чек-лист для разработки с ИИ.md` | broad AI project planning checklist | `docs/AI_PROJECT_CHECKLIST.md`, `docs/READ_FIRST.md`, `docs/PRD.md`, `docs/ARCH_SPEC.md` | `covered` | Checklist has been reduced to a repo-native gate for this product |

---

## Section-level crosswalk

| Guide file | Project section / artifact | Evidence artifact | Owner | Update trigger |
| --- | --- | --- | --- | --- |
| `0. READ-FIRST.md` | `docs/READ_FIRST.md` sections `Already decided`, `Questions to answer before changing runtime` | repo-native pre-build decision gate | human + orchestrator docs pass | runtime scope or packet contract changes |
| `1. START-HERE.md` | `docs/START_HERE.md` + `docs/QUALITY_GATES.md` + `Makefile` | three defensive layers and day-0 order | repo maintainer | any gate/process change |
| `INTRO.md` | `docs/EXECUTION_PRINCIPLES.md` | repo-first execution principles | repo maintainer | process policy change |
| `AGENTS ...` | `docs/AGENTS.md` | role matrix and handoff rules | repo maintainer | role/handoff change |
| `ARCHITECTURE_BASELINE ...` | `docs/ARCHITECTURE_BASELINE.md` + `enforcement/deps_rules.py` | executable baseline and required paths | repo maintainer | layer/enforcement change |
| `ORCHESTRATED ...` | `docs/ORCHESTRATED.md` | orchestration pattern and mode mapping | runtime owner | `/solo` or `/orch` contract change |
| `QUALITY_GATES ...` | `docs/QUALITY_GATES.md` + `.github/workflows/ci.yml` | local/CI quality contract equivalence | repo maintainer | gate change |
| `TASKS.md` | `TASKS.md` + `tasks/epics/*` + `tasks/stories/*` | task system and story format | product owner | backlog/task-system change |
| `Чек-лист ...` | `docs/AI_PROJECT_CHECKLIST.md` | bounded implementation checklist | repo maintainer | new implementation lane or risk class |

---

## Source guide snapshot and history

- **Guide location used:** `C:\Projects\Iron Dome [GUIDE]`
- **Snapshot basis:** current local file set and names observed on `2026-04-14`
- **Historical note:** initial bootstrap did not start from full one-to-one guide parity; parity was restored later through repo-native equivalents and enforcement/gate updates
- **Current-state claim:** the matrix above describes the repo as it exists now, not the state of the very first bootstrap pass

---

## Coverage summary

| Status | Count |
| --- | --- |
| `covered` | 16 |
| `partial` | 0 |
| `reference-only` | 0 |
| `not-adopted` | 0 |

---

## Confirmed gaps

1. Guide parity was not completed before the first bootstrap pass; remediation happened afterwards.
2. Repo-native equivalents are product-specific adaptations and should not be read as verbatim guide copies.
3. There are explicit repo-native deltas vs guide; they are tracked below and treated as accepted product/process choices unless marked otherwise.

## Explicit deltas vs guide

| Delta area | Guide-oriented expectation | Repo-native state | Status |
| --- | --- | --- | --- |
| Artifact naming/layout | Near one-file-to-one-file naming convention | Intent preserved through repo-native artifact names and crosswalk mapping | accepted repo adaptation |
| Pre-commit scope | Often interpreted as "parity with full local gates" | Pre-commit keeps only minimum critical enforcement scripts; full gate is `make check` + CI | accepted process split |
| CI execution form | Single canonical command path | Unix CI runs `make check`; Windows CI runs explicit equivalent steps + standalone skeleton step | accepted platform adaptation |
| Runtime orchestration scope | Broader orchestration pattern in guide discussions | Current baseline is sequential `/orch` without parallel debate loop and without dedicated OS-window lanes | accepted product scope limit |
| Provider live behavior claims | Stable live success may be implied by adapter presence | Adapter support exists in code; live success remains environment-dependent and must be confirmed by smoke runs | accepted runtime constraint |

---

## Recommended closure plan

1. Keep this matrix and delta register versioned; update both whenever guide-derived artifacts or gate semantics change.
2. Treat undocumented docs/runtime divergence as process debt and classify it explicitly (`accepted adaptation` or `needs remediation`) in the same change set.
