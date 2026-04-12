from __future__ import annotations

from pathlib import Path

from open_clodex_iflow.adapters.runtime import run_provider_review, runnable_provider_names
from open_clodex_iflow.contracts import ArtifactPacket, ConsolidatedReview
from open_clodex_iflow.orchestration.preflight import (
    aggregate_provider_reviews,
    build_artifact_packet,
    build_consolidated_review,
)


def write_session_log(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_orchestration(
    *,
    task: str,
    runtime_mode: str,
    provider_snapshot: dict[str, dict[str, object]],
    requested_providers: list[str] | None = None,
    timeout_seconds: int = 180,
    output_dir: Path,
    python_executable: Path | None = None,
) -> tuple[ArtifactPacket, ConsolidatedReview]:
    runnable_providers = runnable_provider_names(provider_snapshot, requested_providers)
    artifact = build_artifact_packet(
        mode="orch",
        task=task,
        provider_snapshot=provider_snapshot,
        planned_providers=runnable_providers,
        runtime_mode=runtime_mode,
        packet_stage="runtime-execution",
        next_step="Inspect provider reviews and consolidated verdict.",
    )

    output_dir = output_dir.resolve()
    session_log_lines = [
        f"trace_id={artifact.trace_id}",
        f"runtime_mode={runtime_mode}",
        f"planned_providers={','.join(runnable_providers) if runnable_providers else 'none'}",
    ]

    if not artifact.task or not runnable_providers:
        review = build_consolidated_review(artifact)
        session_log_lines.append(f"result={review.verdict}")
        write_session_log(output_dir / "session.log", session_log_lines)
        return artifact, review

    provider_reviews = []
    providers_root = output_dir / "providers"
    for provider in runnable_providers:
        session_log_lines.append(f"provider_start={provider}")
        provider_review = run_provider_review(
            provider,
            artifact=artifact,
            metadata=provider_snapshot[provider],
            output_dir=providers_root / provider,
            runtime_mode=runtime_mode,
            timeout_seconds=timeout_seconds,
            python_executable=python_executable,
        )
        provider_reviews.append(provider_review)
        session_log_lines.append(
            f"provider_finish={provider}:{provider_review.review_stage}:{provider_review.verdict}"
        )

    review = aggregate_provider_reviews(artifact, provider_reviews)
    session_log_lines.append(f"result={review.verdict}")
    write_session_log(output_dir / "session.log", session_log_lines)
    return artifact, review
