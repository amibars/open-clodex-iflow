from scripts.run_skeleton_tester import run_scenarios


def test_skeleton_tester_scenarios_pass():
    results = dict(run_scenarios())
    assert results == {
        "forbidden-import": True,
        "layer-violation": True,
        "secret-detection": True,
        "tdd-guard": True,
    }
