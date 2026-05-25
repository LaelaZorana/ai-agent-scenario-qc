from qc_reviewer import rubric


def test_perfect_scenario_scores_100():
    r = rubric.load_rubric()
    result = rubric.score_scenario(r, defects=[])
    assert result["overall_score"] == 100.0
    assert result["passed"] is True


def test_critical_defect_reduces_score():
    r = rubric.load_rubric()
    defects = [{"severity": "CRITICAL", "category": "logical_consistency",
                "location": "x", "message": "y"}]
    result = rubric.score_scenario(r, defects)
    assert result["overall_score"] < 100.0
