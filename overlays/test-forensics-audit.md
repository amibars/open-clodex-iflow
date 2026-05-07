# test-forensics-audit

Purpose: read-only audit of tests, gates, false positives, weak assertions, and missing negative validation.

## Trigger

Use when tests are green but the operator needs to know whether they actually protect the repo.

## Permission Boundary

Read-only. Do not rewrite tests from this overlay. Recommend test changes as findings or follow-up tasks.

## Required Evidence

- Test file paths and exact behavior under review.
- What failure class each test can detect.
- What failure class each test cannot detect.
- Negative-validation coverage for enforcement, packet contracts, provider failures, and CLI entrypoints.

## Output Format

Return:

```text
tested_claim:
current_test_evidence:
gap:
risk:
recommended_negative_case:
priority:
```

Group the strongest false-green risks first.

## Non-Goals

- Do not add broad coverage metrics without explaining behavioral risk.
- Do not equate file-existence tests with runtime validation.
- Do not mark a gate strong unless it fails on an intentional violation.
