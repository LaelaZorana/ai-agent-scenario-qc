"""JSON structural validation against the scenario schema."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "scenario.schema.json"


def load_schema() -> dict[str, Any]:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_scenario(path: str | Path) -> dict[str, Any]:
    """Load a scenario JSON file. Raises ValueError on invalid JSON."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e.msg} at line {e.lineno}") from e


def validate_structure(scenario: dict[str, Any]) -> list[dict[str, str]]:
    """Validate scenario against the JSON schema.

    Returns a list of structural defects (empty if scenario is structurally valid).
    """
    schema = load_schema()
    validator = Draft7Validator(schema)
    defects = []
    for err in sorted(validator.iter_errors(scenario), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in err.path) or "<root>"
        defects.append({
            "severity": "CRITICAL",
            "category": "schema",
            "location": path,
            "message": err.message,
        })
    return defects
