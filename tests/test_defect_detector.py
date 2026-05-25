from pathlib import Path

from qc_reviewer import validator, defect_detector

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"


def _defects(name):
    s = validator.load_scenario(SCENARIOS / name)
    return defect_detector.detect_defects(s)


def test_good_scenario_has_no_semantic_defects():
    assert _defects("good_email_triage.json") == []


def test_bad_calendar_detects_undeclared_tool():
    defects = _defects("bad_calendar_booking.json")
    msgs = [d["message"] for d in defects]
    assert any("calendar.create_event" in m for m in msgs)


def test_bad_calendar_detects_undefined_persona():
    defects = _defects("bad_calendar_booking.json")
    assert any("manager_2" in d["message"] for d in defects)


def test_bad_calendar_detects_empty_success_criteria():
    defects = _defects("bad_calendar_booking.json")
    assert any("success_criteria" in d["location"] for d in defects)


def test_non_sequential_steps_flagged():
    defects = _defects("bad_invalid_step_order.json")
    assert any("sequential" in d["message"] for d in defects)


def test_unused_declared_tool_flagged():
    defects = _defects("bad_invalid_step_order.json")
    assert any("drive.unused_tool" in d["message"] for d in defects)
