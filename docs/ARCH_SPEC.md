# ARCH_SPEC.md

# Architecture Specification

project: open-clodex-iflow  
version: 1.0.0  
date: 2026-04-11  
author: karte  
status: draft

---

## 1. System Overview

### 1.1 Purpose

`open-clodex-iflow` is a Python CLI control plane that bootstraps Iron Dome-compatible workspaces and orchestrates local AI developer CLIs with a strict two-mode UX: `/solo` and `/orch`.

### 1.2 Key Stakeholders

| Role | Concerns |
| --- | --- |
| Human operator | UX simplicity, privacy of `/solo`, visibility of worker activity |
| Reviewer providers | stable packet contract, isolated responsibilities |
| Future contributors | reusable architecture and open-source-friendly layout |

### 1.3 High-level components

- `cli`: entrypoints and command parsing
- `adapters`: provider discovery and runtime bridge
- `orchestration`: packet assembly and aggregation
- `scaffold`: workspace bootstrap from templates
- `enforcement`: repo safety and quality gates

Dependency direction for runtime code is one-way: `cli -> orchestration -> adapters`. Adapter modules expose a stable bridge surface, while orchestration owns packet policy, verdict aggregation, and operator-facing flow.

---

## 2. Architecture Decisions

### ADR-001: Reuse-first runtime

**Decision:** prefer installed CLI + existing local state before any explicit OAuth/API flow.

**Consequences:**

- ✅ Matches terminal-native operator UX
- ✅ Reduces re-login friction
- ⚠️ Adapter layer must detect capabilities and partial state

### ADR-002: Two-mode public UX

**Decision:** expose only `/solo` and `/orch` to the user.

**Consequences:**

- ✅ Minimal cognitive load
- ✅ Keeps orchestration deterministic inside hidden internal stages
- ⚠️ Internal pipeline must remain explicit in code and docs

### ADR-003: Windowed default

**Decision:** `/orch` defaults to `windowed`, with `headless` as explicit opt-in.

**Consequences:**

- ✅ Better operator observability
- ⚠️ Requires window-spawn handling to be first-class on Windows

---

## 3. Data Contracts

### artifact.json

```json
{
  "trace_id": "trace-...",
  "generated_at": "2026-04-11T12:00:00Z",
  "mode": "solo | orch",
  "task": "short task summary",
  "runtime_mode": "windowed | headless | null",
  "packet_stage": "bootstrap-preflight | runtime-execution",
  "privacy_boundary": "codex-only | structured-packet-only",
  "fan_out_requested": true,
  "planned_providers": ["claude", "iflow"],
  "required_docs_gate_passed": true,
  "traceability_audit_path": "docs/GUIDE_TRACEABILITY_AUDIT.md",
  "provider_snapshot": {
    "claude": {
      "available": true,
      "binary": "claude",
      "state_dirs": ["..."]
    }
  },
  "notes": ["..."],
  "changed_files": [],
  "test_summary": [],
  "next_step": "..."
}
```

### review.json

```json
{
  "provider": "claude",
  "review_stage": "runtime | synthetic-failure",
  "verdict": "proceed | fix_code | fix_plan | block",
  "summary": "short normalized summary",
  "blocking_findings": ["..."],
  "non_blocking_notes": ["..."],
  "tests_to_add": ["..."],
  "plan_risks": ["..."],
  "confidence": "low | medium | high",
  "runtime_mode": "windowed | headless",
  "raw_output_file": "providers/claude/raw_output.txt",
  "log_file": "providers/claude/stdout.txt"
}
```

### consolidated_review.json

```json
{
  "trace_id": "trace-...",
  "generated_at": "2026-04-11T12:00:01Z",
  "review_stage": "preflight | runtime",
  "verdict": "proceed | fix_code | fix_plan | block",
  "blocking_findings": ["..."],
  "non_blocking_notes": ["..."],
  "provider_reviews": [
    {
      "provider": "claude",
      "status": "planned",
      "review_stage": "preflight"
    }
  ],
  "next_action": "..."
}
```

### Current execution boundary

- `/solo` writes only `artifact.json`
- `/orch` writes `artifact.json`, per-provider `review.json`, `session.log`, and `consolidated_review.json`
- runtime is sequential and uses only runnable providers with explicit adapter support
- custom API/base URL overrides remain out of scope for the current slice

---

## 4. Non-Functional Requirements

- Windows-first operator workflow
- provider reuse before re-auth
- no silent privacy leak from `/solo`
- all bootstrap docs exist before feature expansion
