from __future__ import annotations

from dataclasses import dataclass

DEFAULT_LANE_SET_ID = "default-planners"
RECOMMENDED_LANE_SET_ID = "recommended-planners"


@dataclass(frozen=True, slots=True)
class LanePreset:
    lane_id: str
    provider: str
    description: str
    model: str | None = None
    agent: str | None = None
    variant: str | None = None
    plan: bool = False
    thinking: bool = False
    write_authority: str = "plan-only"
    included_in_default_set: bool = False


def list_lane_presets() -> dict[str, LanePreset]:
    return {
        "iflow-glm5-plan-thinking": LanePreset(
            lane_id="iflow-glm5-plan-thinking",
            provider="iflow",
            description="Legacy/API-key planner lane for GLM-5 with thinking requested.",
            model="GLM-5",
            plan=True,
            thinking=True,
            included_in_default_set=False,
        ),
        "iflow-qwen3coder-plan": LanePreset(
            lane_id="iflow-qwen3coder-plan",
            provider="iflow",
            description="Legacy/API-key planner lane for Qwen3-Coder-Plus without thinking toggle.",
            model="Qwen3-Coder-Plus",
            plan=True,
            thinking=False,
            included_in_default_set=False,
        ),
        "iflow-kimi-k25-plan-thinking": LanePreset(
            lane_id="iflow-kimi-k25-plan-thinking",
            provider="iflow",
            description="Legacy/API-key planner lane for Kimi-K2.5 with thinking requested.",
            model="Kimi-K2.5",
            plan=True,
            thinking=True,
            included_in_default_set=False,
        ),
        "iflow-minimax-plan-thinking": LanePreset(
            lane_id="iflow-minimax-plan-thinking",
            provider="iflow",
            description="Optional MiniMax-M2.5 planner lane through iflow.",
            model="MiniMax-M2.5",
            plan=True,
            thinking=True,
            included_in_default_set=False,
        ),
        "opencode-gpt5nano-plan-thinking": LanePreset(
            lane_id="opencode-gpt5nano-plan-thinking",
            provider="opencode",
            description="Optional fast planner lane through opencode using GPT-5 Nano with thinking requested; can over-penalize missing unplanned providers.",
            model="opencode/gpt-5-nano",
            agent="plan",
            plan=True,
            thinking=True,
            included_in_default_set=False,
        ),
        "opencode-minimax-plan": LanePreset(
            lane_id="opencode-minimax-plan",
            provider="opencode",
            description="Default fast MiniMax M2.5 Free planner lane through opencode without thinking.",
            model="opencode/minimax-m2.5-free",
            agent="plan",
            plan=True,
            thinking=False,
            included_in_default_set=True,
        ),
        "opencode-minimax-plan-thinking": LanePreset(
            lane_id="opencode-minimax-plan-thinking",
            provider="opencode",
            description="Optional MiniMax M2.5 Free planner lane through opencode with thinking requested; latency can vary.",
            model="opencode/minimax-m2.5-free",
            agent="plan",
            plan=True,
            thinking=True,
            included_in_default_set=False,
        ),
        "opencode-hy3-preview-plan-thinking": LanePreset(
            lane_id="opencode-hy3-preview-plan-thinking",
            provider="opencode",
            description="Optional Hy3 preview planner lane through opencode with thinking requested.",
            model="opencode/hy3-preview-free",
            agent="plan",
            plan=True,
            thinking=True,
            included_in_default_set=False,
        ),
        "opencode-big-pickle-plan-thinking": LanePreset(
            lane_id="opencode-big-pickle-plan-thinking",
            provider="opencode",
            description="Optional Big Pickle planner lane through opencode with thinking requested.",
            model="opencode/big-pickle",
            agent="plan",
            plan=True,
            thinking=True,
            included_in_default_set=False,
        ),
        "opencode-nemotron3-super-plan-thinking": LanePreset(
            lane_id="opencode-nemotron3-super-plan-thinking",
            provider="opencode",
            description="Optional Nemotron 3 Super planner lane through opencode with thinking requested; slower/flakier in local benchmark.",
            model="opencode/nemotron-3-super-free",
            agent="plan",
            plan=True,
            thinking=True,
            included_in_default_set=False,
        ),
        "nvidia-glm51-plan": LanePreset(
            lane_id="nvidia-glm51-plan",
            provider="opencode",
            description="Optional NVIDIA-routed GLM-5.1 planner lane through opencode; requires configured nvidia provider credentials.",
            model="nvidia/z-ai/glm-5.1",
            agent="plan",
            plan=True,
            thinking=False,
            included_in_default_set=False,
        ),
        "nvidia-devstral2-plan": LanePreset(
            lane_id="nvidia-devstral2-plan",
            provider="opencode",
            description="Optional NVIDIA-routed Devstral-2 planner lane through opencode; requires configured nvidia provider credentials.",
            model="nvidia/mistralai/devstral-2-123b-instruct-2512",
            agent="plan",
            plan=True,
            thinking=False,
            included_in_default_set=False,
        ),
        "nvidia-mistral-large3-plan": LanePreset(
            lane_id="nvidia-mistral-large3-plan",
            provider="opencode",
            description="Optional NVIDIA-routed Mistral Large 3 planner lane through opencode; requires configured nvidia provider credentials.",
            model="nvidia/mistralai/mistral-large-3-675b-instruct-2512",
            agent="plan",
            plan=True,
            thinking=False,
            included_in_default_set=False,
        ),
        "opencode-minimax-build-thinking": LanePreset(
            lane_id="opencode-minimax-build-thinking",
            provider="opencode",
            description="Explicit write-capable build lane through opencode using MiniMax M2.5 Free.",
            model="opencode/minimax-m2.5-free",
            agent="build",
            thinking=True,
            write_authority="write-capable",
            included_in_default_set=False,
        ),
    }


def default_lane_ids() -> list[str]:
    return [
        lane.lane_id
        for lane in list_lane_presets().values()
        if lane.included_in_default_set
    ]


def lane_set_catalog() -> dict[str, list[str]]:
    return {
        DEFAULT_LANE_SET_ID: default_lane_ids(),
        RECOMMENDED_LANE_SET_ID: [
            "opencode-minimax-plan",
            "nvidia-glm51-plan",
            "nvidia-devstral2-plan",
            "nvidia-mistral-large3-plan",
        ],
    }


def supported_lane_set_ids() -> list[str]:
    return list(lane_set_catalog().keys())


def resolve_lane_selection(
    provider_snapshot: dict[str, dict[str, object]],
    *,
    requested_lane_ids: list[str] | None = None,
    lane_set: str = DEFAULT_LANE_SET_ID,
) -> tuple[list[LanePreset], list[str]]:
    catalog = list_lane_presets()
    requested = requested_lane_ids or lane_set_catalog().get(lane_set, [])
    resolved: list[LanePreset] = []
    dropped: list[str] = []

    for lane_id in requested:
        preset = catalog.get(lane_id)
        if preset is None:
            dropped.append(lane_id)
            continue
        metadata = provider_snapshot.get(preset.provider, {})
        if not (metadata.get("available") and metadata.get("binary")):
            dropped.append(lane_id)
            continue
        resolved.append(preset)

    return resolved, dropped


def render_lane_catalog() -> str:
    presets = list_lane_presets()
    lane_sets = lane_set_catalog()
    lines = [
        "Lane sets:",
    ]
    for lane_set_id, lane_ids in lane_sets.items():
        lines.append(f"- {lane_set_id}: {', '.join(lane_ids)}")
    lines.extend(["", "Lane presets:"])
    for preset in presets.values():
        default_marker = " [default]" if preset.included_in_default_set else ""
        model = preset.model or "provider-default"
        agent = preset.agent or "provider-default"
        thinking = "on" if preset.thinking else "off"
        plan_mode = "on" if preset.plan else "off"
        lines.append(
            f"- {preset.lane_id}{default_marker}: provider={preset.provider} model={model} "
            f"agent={agent} plan={plan_mode} thinking={thinking} write={preset.write_authority}"
        )
    lines.extend(
        [
            "",
            "CLI toggles:",
            "- /orch uses the default-planners lane set unless you pass --providers or --lanes.",
            "- --lane-set recommended-planners selects MiniMax M2.5 plus the strongest verified NVIDIA planner lanes.",
            "- --lanes laneA,laneB selects explicit lanes.",
            "- iFlow lanes are explicit legacy/API-key lanes after the April 2026 CLI shutdown notice.",
            "- --providers claude,iflow,opencode keeps the legacy provider-only path.",
        ]
    )
    return "\n".join(lines)
