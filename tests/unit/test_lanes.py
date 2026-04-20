from open_clodex_iflow.lanes import (
    DEFAULT_LANE_SET_ID,
    list_lane_presets,
    resolve_lane_selection,
)


def test_default_lane_set_prefers_single_minimax_source_and_planner_modes():
    snapshot = {
        "iflow": {"available": True, "binary": "iflow"},
        "opencode": {"available": True, "binary": "opencode"},
    }

    lanes, dropped = resolve_lane_selection(snapshot, lane_set=DEFAULT_LANE_SET_ID)

    assert dropped == []
    assert [lane.lane_id for lane in lanes] == [
        "iflow-glm5-plan-thinking",
        "iflow-qwen3coder-plan",
        "iflow-kimi-k25-plan-thinking",
        "opencode-minimax-plan-thinking",
    ]
    assert all(lane.write_authority == "plan-only" for lane in lanes)


def test_lane_catalog_exposes_optional_non_default_lanes():
    presets = list_lane_presets()

    assert "iflow-minimax-plan-thinking" in presets
    assert presets["iflow-minimax-plan-thinking"].included_in_default_set is False
    assert "opencode-minimax-build-thinking" in presets
    assert presets["opencode-minimax-build-thinking"].write_authority == "write-capable"
