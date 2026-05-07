# SKILLS.md

# Agent Skills & Competencies

> Матрица нужна не для красоты, а чтобы не путать execution lane, audit lane и human authority.

## Competency matrix

| Skill | Orchestrator | Debug Analyst | Reviewer Pool | Human |
| --- | --- | --- | --- | --- |
| Product scoping | ⚪ | ⚪ | ❌ | ✅ |
| Architecture decisions | ⚪ | ✅ | ⚪ | ✅ |
| Write production code | ✅ | ❌ | ❌ | ⚪ |
| Packet design | ✅ | ⚪ | ⚪ | ⚪ |
| Root-cause analysis | ⚪ | ✅ | ⚪ | ⚪ |
| Review and audit | ⚪ | ✅ | ✅ | ⚪ |
| Secret / risk escalation | ⚪ | ✅ | ⚪ | ✅ |
| Final merge / publish decision | ❌ | ❌ | ❌ | ✅ |

**Легенда:** ✅ primary | ⚪ supporting | ❌ forbidden

---

## Role-specific tools and outputs

| Role | Main tools | Expected output |
| --- | --- | --- |
| Orchestrator | local repo, tests, enforcement, adapters | code, docs, packets, final next step |
| Debug Analyst | repo map, logs, specs, audit persona | evidence-based findings, RCA, contradictions |
| Reviewer Pool | normalized packet + provider lens | `review.json` findings |
| Human | Linear, repo docs, review outputs | scope decisions, approval, reprioritization |

---

## Provider lenses

- `Claude Code`: RCA, architecture, docs-vs-runtime deltas, audit
- `iFlow`: correctness, regression, edge cases, performance skepticism
- `OpenCode`: compatibility lane, alternative review angle, implementation sanity
- `Codex`: control plane, integration, final repository changes

## Recommended planner hybrid lenses

- `opencode-minimax-plan`: fast sanity/default reviewer
- `nvidia-glm51-plan`: plan correctness reviewer
- `nvidia-devstral2-plan`: implementation/code/runtime/test reviewer
- `nvidia-mistral-large3-plan`: architecture/senior reviewer

These lenses are emphasis instructions, not scope restrictions. Each lane still reviews the full artifact and may report any blocker.

---

## Escalation rules

1. Reviewer disagreement above threshold -> human gate
2. Missing provider binary/auth state -> degrade gracefully and report explicitly
3. Security-critical finding -> stop normal flow and escalate
4. Docs/runtime contradiction -> fix the contradiction before expanding feature scope
5. Failing quality gate -> no “continue anyway” by default
