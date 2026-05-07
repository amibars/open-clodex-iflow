# Parallel Fan-Out Contract

Status: normative design gate before implementing parallel provider execution or debate loops.

Current v1 defaults to sequential execution and supports optional single-pass parallel lane fan-out. This document defines the safe expansion boundary: parallel fan-out without hidden write authority, hidden retries, or ambiguous aggregation.

## Scope

Applies to future `/orch` execution when more than one lane is run concurrently.

Does not imply:

- multi-pass debate is implemented,
- provider lanes can write code by default,
- dedicated OS windows are implemented,
- retry loops are automatic.

## Goals

- Reduce wall-clock time for multi-lane review.
- Preserve the existing `artifact.json`, `attempt.json`, `review.json`, and `consolidated_review.json` contracts.
- Keep each lane isolated and inspectable.
- Make missing/timeout/invalid lanes visible in the final verdict.

## Non-Goals

- No autonomous swarm.
- No hidden merge authority.
- No provider-to-provider private chat.
- No automatic retry by default.
- No write-capable lane in the default fan-out set.

## Execution Model

Parallel fan-out must use one independent worker per lane:

```text
artifact.json
  -> lane worker A -> providers/<lane-a>/attempt.json + review.json
  -> lane worker B -> providers/<lane-b>/attempt.json + review.json
  -> lane worker C -> providers/<lane-c>/attempt.json + review.json
  -> aggregator -> consolidated_review.json
```

Each worker owns only its lane output directory.

## Required Invariants

1. All lanes receive the same immutable `artifact.json`.
2. Each lane writes to a unique `providers/<lane-id>/` directory.
3. Each lane emits exactly one final `review.json`: runtime review or synthetic failure.
4. Each lane emits one `attempt.json` per provider attempt.
5. Provider stdout/stderr/raw output are never shared between lanes.
6. Aggregation waits for all selected lanes to finish, timeout, or fail.
7. Missing requested lanes are reported as dropped before execution.
8. Default fan-out lanes are planner/reviewer-only.
9. Write-capable lanes remain explicit opt-in.

## Debate Policy

Current allowed shape:

- single-pass fan-out,
- independent lane reviews,
- one consolidated aggregation.

Not allowed until separately specified:

- provider-to-provider debate,
- multiple review rounds,
- automatic self-correction loop,
- quorum retry,
- majority-vote override of blocking security/runtime findings.

## Aggregation Policy

Aggregation must remain conservative:

- any lane with `verdict=block` can block the consolidated result,
- synthetic failures must not be treated as valid provider opinions,
- timeout/invalid/failure lanes must be visible in `non_blocking_notes` or `blocking_findings`,
- missing requested coverage may block if the operator explicitly requested that lane,
- `proceed` requires successful normalized reviews from all required lanes or an explicit operator decision to accept partial coverage.

## Timeout Policy

Parallel execution must reuse `docs/ATTEMPT_TIMEOUT_RETRY_CONTRACT.md`:

- timeout creates `attempt.json` with `state=timeout_incomplete`,
- partial output is preserved,
- timeout is not automatically retried,
- retry, if later added, creates a new attempt record.

## Windowing Policy

Parallel fan-out does not automatically mean dedicated OS windows.

Allowed first implementation:

- parallel headless workers,
- parallel current-terminal progress summaries,
- artifacts for every lane.

Dedicated OS windows require `docs/WINDOWED_RUNTIME_CONTRACT.md` compliance first.

## Configuration Surface

Future CLI flags should be explicit:

```text
--execution sequential|parallel
--lane-set <id>
--lanes <lane-a,lane-b>
--timeout-seconds <n>
```

Default remains `sequential`; `parallel` must be requested explicitly.

## Tests Required Before Implementation Claim

- two fake providers run concurrently and total runtime proves parallelism,
- lanes that share one provider are serialized to avoid shared local state collisions,
- each lane writes isolated `attempt.json`, `review.json`, `stdout.txt`, `stderr.txt`, and `raw_output.txt`,
- one lane timeout does not kill successful sibling lanes,
- one invalid lane becomes synthetic failure without corrupting sibling lane outputs,
- aggregation is deterministic regardless of completion order,
- default `sequential` behavior remains unchanged.

## Current Implementation Status

Implemented for optional provider-aware single-pass parallel lane execution through `--execution parallel`. Different provider groups can run concurrently; lanes sharing one provider are serialized. Not implemented: debate loops, multi-pass review, or automatic retry.
