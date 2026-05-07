# repo-forensics-review

Purpose: read-only due-diligence audit for repo claims, architecture boundaries, docs/runtime truth, and quality gates.

## Trigger

Use when a claim about repository readiness, guide parity, runtime behavior, architecture enforcement, or release status needs evidence.

## Permission Boundary

Read-only. Do not edit code, docs, Linear, GitHub, or local configuration from this overlay.

## Required Evidence

- Exact file paths for every finding.
- Command output or test result when claiming a gate passes or fails.
- Clear separation between confirmed fact, inference, and missing evidence.
- Comparison between docs claims and runtime implementation when relevant.

## Output Format

Return findings first, ordered by severity:

```text
severity:
evidence:
impact:
confidence:
next_check:
```

Then return residual risks and explicitly missing evidence.

## Non-Goals

- Do not write patches.
- Do not redefine product requirements.
- Do not claim guide parity without file-level evidence.
- Do not treat green smoke tests as full product readiness.
