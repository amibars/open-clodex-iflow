from __future__ import annotations

from open_clodex_iflow.contracts import (
    ArtifactPacket,
    ConsolidatedReview,
    ProviderReview,
    new_trace_id,
    utc_now_iso,
)

VERDICT_PRIORITY = {
    "proceed": 0,
    "fix_plan": 1,
    "fix_code": 2,
    "block": 3,
}


def build_artifact_packet(
    *,
    mode: str,
    task: str,
    provider_snapshot: dict[str, dict[str, object]],
    planned_providers: list[str] | None = None,
    planned_lanes: list[str] | None = None,
    runtime_mode: str | None = None,
    packet_stage: str | None = None,
    next_step: str | None = None,
) -> ArtifactPacket:
    normalized_task = task.strip()
    if mode == "solo":
        effective_providers = []
    elif planned_providers is not None:
        effective_providers = sorted(planned_providers)
    else:
        effective_providers = sorted(
            name
            for name, metadata in provider_snapshot.items()
            if bool(metadata.get("available"))
        )
    effective_lanes = sorted(planned_lanes or [])
    notes = [
        "System CLI discovery was captured before execution.",
        "Packet contains structured fields only; no raw transcript handoff.",
    ]

    if mode == "solo":
        notes.append("Privacy boundary preserved: no fan-out beyond Codex.")
        resolved_next_step = (
            next_step or "Continue private Codex execution or promote the task to orch explicitly."
        )
        resolved_packet_stage = packet_stage or "bootstrap-preflight"
    else:
        if packet_stage == "runtime-execution":
            notes.append("Runtime slice executes runnable provider adapters and aggregates reviews.")
            resolved_next_step = next_step or "Inspect provider reviews and the consolidated verdict."
        else:
            notes.append("Bootstrap slice stops at orchestration preflight and packet generation.")
            resolved_next_step = (
                next_step or "Review consolidated preflight output before implementing provider execution."
            )
        resolved_packet_stage = packet_stage or "bootstrap-preflight"

    return ArtifactPacket(
        trace_id=new_trace_id(),
        generated_at=utc_now_iso(),
        mode=mode,
        task=normalized_task,
        runtime_mode=runtime_mode,
        packet_stage=resolved_packet_stage,
        privacy_boundary="codex-only" if mode == "solo" else "structured-packet-only",
        fan_out_requested=mode == "orch",
        planned_providers=effective_providers,
        planned_lanes=effective_lanes,
        provider_snapshot=provider_snapshot,
        notes=notes,
        next_step=resolved_next_step,
    )


def build_consolidated_review(artifact: ArtifactPacket) -> ConsolidatedReview:
    blocking_findings: list[str] = []
    notes: list[str] = []

    if not artifact.task:
        verdict = "fix_plan"
        blocking_findings.append("Task summary is empty; packet is structurally valid but underspecified.")
        next_action = "Provide a concrete task summary before invoking provider execution."
    elif not artifact.planned_providers:
        verdict = "block"
        blocking_findings.append(
            "No installed providers were detected for orch mode; reuse-first execution cannot continue."
        )
        next_action = "Install or expose at least one supported provider CLI in PATH."
    else:
        verdict = "proceed"
        notes.append(
            "Preflight packet is ready; external provider execution remains a separate next slice."
        )
        next_action = "Implement provider adapters to replace preflight-only aggregation."

    provider_reviews = [
        ProviderReview(
            provider=provider,
            review_stage="preflight",
            verdict="fix_plan" if verdict == "fix_plan" else "proceed",
            summary="Provider review is planned but not yet executed.",
        )
        for provider in artifact.planned_providers
    ]

    return ConsolidatedReview(
        trace_id=artifact.trace_id,
        generated_at=utc_now_iso(),
        review_stage="preflight",
        verdict=verdict,
        blocking_findings=blocking_findings,
        non_blocking_notes=notes,
        provider_reviews=provider_reviews,
        next_action=next_action,
    )


def choose_verdict(verdicts: list[str]) -> str:
    if not verdicts:
        return "block"
    return max(verdicts, key=lambda verdict: VERDICT_PRIORITY.get(verdict, VERDICT_PRIORITY["block"]))


def next_action_for_verdict(verdict: str) -> str:
    if verdict == "proceed":
        return "Proceed with the change after reviewing provider notes."
    if verdict == "fix_code":
        return "Address code-level findings before proceeding."
    if verdict == "fix_plan":
        return "Tighten the plan or task framing before another orchestration pass."
    return "Resolve blocking findings before continuing."


def aggregate_provider_reviews(
    artifact: ArtifactPacket,
    provider_reviews: list[ProviderReview],
) -> ConsolidatedReview:
    verdict = choose_verdict([review.verdict for review in provider_reviews])
    blocking_findings = [
        finding
        for review in provider_reviews
        for finding in review.blocking_findings
    ]
    notes = [
        note
        for review in provider_reviews
        for note in review.non_blocking_notes
    ]
    return ConsolidatedReview(
        trace_id=artifact.trace_id,
        generated_at=utc_now_iso(),
        review_stage="runtime",
        verdict=verdict,
        blocking_findings=blocking_findings,
        non_blocking_notes=notes,
        provider_reviews=provider_reviews,
        next_action=next_action_for_verdict(verdict),
    )
