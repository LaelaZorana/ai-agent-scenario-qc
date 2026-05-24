from pathlib import Path
import pytest

from qc_reviewer import validator

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"


def test_good_scenario_has_no_structural_defects():
    s = validator.load_scenario(SCENARIOS / "good_email_triage.json")
    assert validator.validate_structure(s) == []


def test_invalid_json_raises_value_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ this is not valid JSON")
    with pytest.raises(ValueError):
        validator.load_scenario(bad)
