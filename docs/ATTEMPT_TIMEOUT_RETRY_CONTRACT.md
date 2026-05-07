# Attempt Timeout Retry Contract

Status: normative design gate for provider attempts, optional parallel fan-out, and future debate loops.

This document defines how `open-clodex-iflow` must describe provider attempts, timeouts, retries, and partial output. It exists to prevent a common orchestration bug: treating every timeout as a clean provider failure and losing the evidence needed to recover.

## Scope

Applies to:

- `/orch` runtime provider execution.
- Sequential v1 lanes.
- Optional single-pass parallel fan-out and future debate loops.
- Future visible OS-window worker lanes.

Does not imply that retry loops or debate loops are already implemented.

## Terms

| Term | Meaning |
| --- | --- |
| `LaneEndpoint` | The resolved lane/provider/model/mode target that receives a review request. |
| `ReviewMessage` | The structured prompt plus `artifact.json` context sent to a lane. |
| `AttemptRecord` | One execution attempt against one `LaneEndpoint`. |
| `ProviderRun` | The subprocess/API invocation and its captured runtime facts. |
| `ReviewRecord` | Normalized provider result written as `review.json`. |
| `SyntheticFailure` | A generated `review.json` that reports transport/runtime failure without pretending the provider gave a valid review. |

## Attempt States

Allowed attempt states:

- `planned`: lane was selected but not started.
- `started`: provider command/API call was launched.
- `completed`: provider returned a valid normalized review.
- `invalid_output`: provider completed but output could not be normalized into `review.json`.
- `timeout_incomplete`: timeout fired and the provider state is not known to be complete.
- `failed`: provider failed before a valid review could be produced.
- `cancelled`: operator/runtime deliberately stopped the attempt.
- `skipped`: lane was dropped before execution with an explicit reason.

`timeout_incomplete` is intentionally separate from `failed`.

## Invariants

1. A timeout must not silently erase partial output.
2. A timeout must not be reported as a provider review.
3. A retry must create a new `AttemptRecord`; it must not overwrite the prior attempt.
4. Provider adapters report runtime facts; orchestration decides policy.
5. Aggregation may use synthetic failure records, but those records must preserve the stage as `synthetic-failure`.
6. Dropped or skipped lanes must be visible in `session.log` and consolidated review notes.
7. No retry may be automatic by default until retry policy is explicit in docs and tests.

## Required Attempt Fields

Every provider attempt should be representable with:

```json
{
  "attempt_id": "attempt-...",
  "trace_id": "trace-...",
  "lane_id": "opencode-minimax-plan",
  "provider": "opencode",
  "model": "opencode/minimax-m2.5-free",
  "mode": "plan",
  "runtime_mode": "windowed",
  "state": "timeout_incomplete",
  "started_at": "2026-05-06T12:00:00Z",
  "ended_at": "2026-05-06T12:02:00Z",
  "timeout_seconds": 120,
  "process_terminated": true,
  "exit_code": null,
  "stdout_tail_file": "providers/opencode/stdout.txt",
  "stderr_tail_file": "providers/opencode/stderr.txt",
  "raw_output_file": "providers/opencode/raw_output.txt",
  "retryable": false,
  "operator_inspection_hint": "Open provider logs before retrying; prior output may contain useful partial analysis."
}
```

The current `review.json` contract remains the public normalized review artifact, while `attempt.json` records the runtime facts needed to explain it.

## Timeout Semantics

When timeout fires:

- Capture and persist stdout/stderr/raw output tails before returning.
- Record whether the provider process was terminated.
- Emit a synthetic failure review only if no valid normalized provider review exists.
- Use `timeout_incomplete` when the provider may have accepted the task but did not return a final captured review.
- Do not mark the lane as live-success verified.

Timeout summary wording should be operator-facing:

```text
provider timed out after 120s; partial output was preserved in providers/<lane>/raw_output.txt; no valid review.json was produced
```

## Retry Policy

Current v1 policy:

- No automatic retry.
- Manual retry is allowed by re-running `/orch`.
- Manual retry should use a new output directory or trace id.

Future retry policy must define:

- retry limit,
- backoff,
- whether context is replayed or continued,
- whether previous partial output is included,
- whether the provider is known to support continuation,
- how duplicate findings are deduplicated in aggregation.

## Aggregation Rules

Aggregation may proceed when one or more lanes fail, but it must:

- keep failed/timeout lanes visible,
- prefer `block` when requested review coverage is materially missing,
- distinguish provider runtime failure from code/design findings,
- include the artifact paths needed for operator inspection.

## Required Coverage

Runtime tests must cover:

- timeout preserves partial stdout/stderr,
- invalid nested/incidental JSON is rejected,
- skipped requested lanes are logged,
- manual retries create new output directories or attempt records before automatic retries are introduced,
- aggregation does not treat synthetic failures as real provider reviews,
- operator-visible paths are included in failure summaries.
- parallel execution preserves sibling lane results when another lane times out.

## Current Implementation Status

Current v1 writes `attempt.json` for provider lanes and preserves timeout/invalid/failure evidence separately from normalized `review.json`. Runtime remains sequential by default; optional `--execution parallel` runs selected lanes concurrently in a single pass. Retry loops and debate loops are still not implemented.
