# JTBD

# Jobs To Be Done

> Этот документ фиксирует не feature wish-list, а реальные рабочие jobs, которые должен закрывать bootstrap и следующий implementation slice.

---

## Core jobs

1. Я хочу переключаться между приватной работой и orchestration review loop из терминала без нового auth dance.
2. Я хочу reuse already-installed CLI providers вместо ручной перенастройки каждого инструмента.
3. Я хочу, чтобы scaffold создавал дисциплинированный engineering baseline, а не пустую папку.
4. Я хочу по умолчанию видеть работу оркестра в окнах и только осознанно уходить в `headless`.

---

## Current baseline coverage

| Job | Current status | Evidence |
| --- | --- | --- |
| Переключение `/solo` vs `/orch` | Implemented | `/solo` stays private; `/orch` executes runnable reviewer adapters and aggregates their output |
| Reuse existing CLI/auth state | Implemented for discovery/runtime selection | `doctor` and runtime adapter selection reuse installed binaries and known state dirs |
| Scaffold disciplined starter workspace | Implemented | `scaffold` writes the full current repo-native bootstrap document set |
| Windowed default orchestration | Implemented | `/orch` defaults to `windowed`; runtime uses an operator-visible execution lane by default |

---

## Non-jobs

- Не строить plugin platform раньше стабильного adapter contract
- Не делать обязательный WSL dependency в bootstrap slice
- Не отправлять raw `/solo` transcript во внешний reviewer pool

---

## Next slice decisions

- Freeze dedicated OS-window spawning policy vs shared-console visible mode on Windows
- Expand live compatibility coverage across all supported provider CLIs
- Add custom API/base URL override path without breaking reuse-first defaults
