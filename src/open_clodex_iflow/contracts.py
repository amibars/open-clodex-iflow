from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def new_trace_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"trace-{timestamp}-{uuid4().hex[:8]}"


@dataclass(slots=True)
class ArtifactPacket:
    trace_id: str
    generated_at: str
    mode: str
    task: str
    runtime_mode: str | None
    packet_stage: str
    privacy_boundary: str
    fan_out_requested: bool
    planned_providers: list[str]
    provider_snapshot: dict[str, dict[str, object]]
    planned_lanes: list[str] = field(default_factory=list)
    required_docs_gate_passed: bool = True
    traceability_audit_path: str = "docs/GUIDE_TRACEABILITY_AUDIT.md"
    notes: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    test_summary: list[str] = field(default_factory=list)
    next_step: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProviderReview:
    provider: str
    review_stage: str
    verdict: str
    summary: str
    blocking_findings: list[str] = field(default_factory=list)
    non_blocking_notes: list[str] = field(default_factory=list)
    tests_to_add: list[str] = field(default_factory=list)
    plan_risks: list[str] = field(default_factory=list)
    confidence: str = "medium"
    lane_id: str | None = None
    runtime_mode: str | None = None
    raw_output_file: str | None = None
    log_file: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ConsolidatedReview:
    trace_id: str
    generated_at: str
    review_stage: str
    verdict: str
    blocking_findings: list[str] = field(default_factory=list)
    non_blocking_notes: list[str] = field(default_factory=list)
    provider_reviews: list[ProviderReview] = field(default_factory=list)
    next_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def write_json(
    path: Path,
    payload: ArtifactPacket | ProviderReview | ConsolidatedReview | Mapping[str, Any],
) -> Path:
    data = payload.to_dict() if hasattr(payload, "to_dict") else dict(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
