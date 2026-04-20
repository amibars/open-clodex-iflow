from __future__ import annotations

from pathlib import Path

from open_clodex_iflow.adapters.discovery import load_provider_override_config
from open_clodex_iflow.adapters.runtime import run_provider_review, runnable_provider_names
from open_clodex_iflow.contracts import ArtifactPacket, ConsolidatedReview
from open_clodex_iflow.lanes import (
    DEFAULT_LANE_SET_ID,
    LanePreset,
    resolve_lane_selection,
)
from open_clodex_iflow.orchestration.preflight import (
    aggregate_provider_reviews,
    build_artifact_packet,
    build_consolidated_review,
)


def write_session_log(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def dropped_provider_note(dropped_requested_providers: list[str]) -> str:
    return (
        "Dropped requested providers that are not runnable in the current session: "
        + ", ".join(dropped_requested_providers)
        + "."
    )


def dropped_lane_note(dropped_requested_lanes: list[str]) -> str:
    return (
        "Dropped requested lanes that are not runnable in the current session: "
        + ", ".join(dropped_requested_lanes)
        + "."
    )


def run_orchestration(
    *,
    task: str,
    runtime_mode: str,
    provider_snapshot: dict[str, dict[str, object]],
    requested_providers: list[str] | None = None,
    requested_lanes: list[str] | None = None,
    lane_set: str | None = None,
    timeout_seconds: int = 180,
    output_dir: Path,
    python_executable: Path | None = None,
) -> tuple[ArtifactPacket, ConsolidatedReview]:
    execution_lanes: list[LanePreset] = []
    dropped_requested_lanes: list[str] = []
    if requested_providers:
        runnable_providers = runnable_provider_names(provider_snapshot, requested_providers)
        execution_lanes = [
            LanePreset(
                lane_id=provider,
                provider=provider,
                description="Legacy provider-only execution lane.",
                write_authority="provider-default",
            )
            for provider in runnable_providers
        ]
    else:
        execution_lanes, dropped_requested_lanes = resolve_lane_selection(
            provider_snapshot,
            requested_lane_ids=requested_lanes,
            lane_set=lane_set or DEFAULT_LANE_SET_ID,
        )
        runnable_providers = sorted({lane.provider for lane in execution_lanes})
    provider_overrides = load_provider_override_config()
    artifact = build_artifact_packet(
        mode="orch",
        task=task,
        provider_snapshot=provider_snapshot,
        planned_providers=runnable_providers,
        planned_lanes=[lane.lane_id for lane in execution_lanes],
        runtime_mode=runtime_mode,
        packet_stage="runtime-execution",
        next_step="Inspect provider reviews and consolidated verdict.",
    )
    dropped_requested_providers = [
        provider
        for provider in (requested_providers or [])
        if provider not in runnable_providers
    ]
    if dropped_requested_providers:
        artifact.notes.append(dropped_provider_note(dropped_requested_providers))
    if dropped_requested_lanes:
        artifact.notes.append(dropped_lane_note(dropped_requested_lanes))
    if not requested_providers:
        artifact.notes.append(
            f"Lane selection active: {lane_set or DEFAULT_LANE_SET_ID}."
        )
    configured_override_providers = [
        provider for provider in runnable_providers if provider_overrides.get(provider)
    ]
    if configured_override_providers:
        artifact.notes.append(
            "Provider override config detected for: "
            + ", ".join(configured_override_providers)
            + "."
        )

    output_dir = output_dir.resolve()
    session_log_lines = [
        f"trace_id={artifact.trace_id}",
        f"runtime_mode={runtime_mode}",
        f"planned_providers={','.join(runnable_providers) if runnable_providers else 'none'}",
        f"planned_lanes={','.join(artifact.planned_lanes) if artifact.planned_lanes else 'none'}",
    ]
    if dropped_requested_providers:
        session_log_lines.append(
            f"dropped_requested_providers={','.join(dropped_requested_providers)}"
        )
    if dropped_requested_lanes:
        session_log_lines.append(
            f"dropped_requested_lanes={','.join(dropped_requested_lanes)}"
        )
    for provider in configured_override_providers:
        override = provider_overrides[provider]
        base_url = override.get("base_url") or "unset"
        env_map = override.get("env", {})
        env_keys = ",".join(sorted(env_map.keys())) if isinstance(env_map, dict) and env_map else "none"
        session_log_lines.append(
            f"provider_override={provider}:base_url={base_url}:env_keys={env_keys}"
        )

    if not artifact.task or not execution_lanes:
        review = build_consolidated_review(artifact)
        if dropped_requested_providers:
            review.non_blocking_notes.append(dropped_provider_note(dropped_requested_providers))
        if dropped_requested_lanes:
            review.non_blocking_notes.append(dropped_lane_note(dropped_requested_lanes))
        session_log_lines.append(f"result={review.verdict}")
        write_session_log(output_dir / "session.log", session_log_lines)
        return artifact, review

    provider_reviews = []
    providers_root = output_dir / "providers"
    for lane in execution_lanes:
        provider = lane.provider
        session_log_lines.append(f"lane_start={lane.lane_id}:{provider}")
        provider_review = run_provider_review(
            provider,
            artifact=artifact,
            metadata=provider_snapshot[provider],
            output_dir=providers_root / lane.lane_id,
            runtime_mode=runtime_mode,
            timeout_seconds=timeout_seconds,
            python_executable=python_executable,
            provider_override=provider_overrides.get(provider),
            lane=lane,
        )
        provider_reviews.append(provider_review)
        session_log_lines.append(
            f"lane_finish={lane.lane_id}:{provider_review.review_stage}:{provider_review.verdict}"
        )

    review = aggregate_provider_reviews(artifact, provider_reviews)
    if dropped_requested_providers:
        review.non_blocking_notes.append(dropped_provider_note(dropped_requested_providers))
    if dropped_requested_lanes:
        review.non_blocking_notes.append(dropped_lane_note(dropped_requested_lanes))
    session_log_lines.append(f"result={review.verdict}")
    write_session_log(output_dir / "session.log", session_log_lines)
    return artifact, review
