# reviewer-packet

Purpose: generate or verify normalized packets for external reviewer lanes without leaking raw private chat history.

## Trigger

Use when `/orch` needs a structured artifact for reviewer lanes or when a human wants to manually send a review packet to another model.

## Permission Boundary

Packet-only. This overlay may describe `artifact.json`, expected `review.json`, and `consolidated_review.json` shapes, but it must not grant write authority to reviewer lanes.

## Required Evidence

- `artifact.json` fields needed for the review task.
- Privacy boundary and whether `/solo` content is excluded.
- Planned providers and planned lanes.
- Expected reviewer output contract for `review.json`.
- Aggregation target for `consolidated_review.json`.

## Output Format

Return a packet plan:

```json
{
  "artifact_json": "required fields and source paths",
  "review_json": "required reviewer response keys",
  "consolidated_review_json": "aggregation rules",
  "privacy_boundary": "structured-packet-only",
  "write_authority": "none"
}
```

## Non-Goals

- Do not include raw private chat transcripts.
- Do not ask reviewer lanes to edit code.
- Do not bypass provider/lane timeout and validation contracts.
