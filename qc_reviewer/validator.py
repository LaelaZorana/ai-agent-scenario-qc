"""JSON loading + schema validation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_scenario(path: str | Path) -> dict[str, Any]:
    """Load a scenario JSON file. Raises ValueError on invalid JSON."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e.msg} at line {e.lineno}") from e
