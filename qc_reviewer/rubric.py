"""Rubric engine — weighted scoring across QC criteria."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_RUBRIC = Path(__file__).resolve().parent.parent / "rubrics" / "default_rubric.json"


def load_rubric(path: str | Path = DEFAULT_RUBRIC) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
