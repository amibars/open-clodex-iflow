from open_clodex_iflow.lanes import (
    DEFAULT_LANE_SET_ID,
    RECOMMENDED_LANE_SET_ID,
    lane_set_catalog,
    list_lane_presets,
    resolve_lane_selection,
)


def test_default_lane_set_prefers_fast_single_opencode_planner_lane():
    snapshot = {
        "iflow": {"available": True, "binary": "iflow"},
        "opencode": {"available": True, "binary": "opencode"},
    }

    lanes, dropped = resolve_lane_selection(snapshot, lane_set=DEFAULT_LANE_SET_ID)

    assert dropped == []
    assert [lane.lane_id for lane in lanes] == [
        "opencode-minimax-plan",
    ]
    assert all(lane.write_authority == "plan-only" for lane in lanes)
    assert all(lane.agent == "plan" for lane in lanes)


def test_recommended_lane_set_replaces_iflow_with_opencode_routed_winners():
    snapshot = {
        "iflow": {"available": True, "binary": "iflow"},
        "opencode": {"available": True, "binary": "opencode"},
    }

    lanes, dropped = resolve_lane_selection(snapshot, lane_set=RECOMMENDED_LANE_SET_ID)

    assert dropped == []
    assert [lane.lane_id for lane in lanes] == [
        "opencode-minimax-plan",
        "nvidia-glm51-plan",
        "nvidia-devstral2-plan",
        "nvidia-mistral-large3-plan",
    ]
    assert all(lane.provider == "opencode" for lane in lanes)
    assert all(lane.agent == "plan" for lane in lanes)
    assert all(lane.write_authority == "plan-only" for lane in lanes)
    assert "iflow-glm5-plan-thinking" not in lane_set_catalog()[RECOMMENDED_LANE_SET_ID]


def test_lane_catalog_exposes_optional_non_default_lanes():
    presets = list_lane_presets()

    assert "iflow-minimax-plan-thinking" in presets
    assert presets["iflow-minimax-plan-thinking"].included_in_default_set is False
    assert presets["iflow-glm5-plan-thinking"].included_in_default_set is False
    assert presets["iflow-qwen3coder-plan"].included_in_default_set is False
    assert presets["iflow-kimi-k25-plan-thinking"].included_in_default_set is False
    assert "opencode-gpt5nano-plan-thinking" in presets
    assert presets["opencode-gpt5nano-plan-thinking"].included_in_default_set is False
    assert "opencode-minimax-plan" in presets
    assert presets["opencode-minimax-plan"].thinking is False
    assert presets["opencode-minimax-plan"].included_in_default_set is True
    assert presets["opencode-minimax-plan-thinking"].included_in_default_set is False
    assert "opencode-hy3-preview-plan-thinking" in presets
    assert "opencode-big-pickle-plan-thinking" in presets
    assert "opencode-nemotron3-super-plan-thinking" in presets
    assert "opencode-minimax-build-thinking" in presets
    assert presets["opencode-minimax-build-thinking"].write_authority == "write-capable"
    assert presets["nvidia-glm51-plan"].model == "nvidia/z-ai/glm-5.1"
    assert presets["nvidia-devstral2-plan"].model == "nvidia/mistralai/devstral-2-123b-instruct-2512"
    assert (
        presets["nvidia-mistral-large3-plan"].model
        == "nvidia/mistralai/mistral-large-3-675b-instruct-2512"
    )
