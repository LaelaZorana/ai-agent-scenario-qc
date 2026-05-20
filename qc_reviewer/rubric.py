"""Rubric engine — weighted scoring across QC criteria."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_RUBRIC = Path(__file__).resolve().parent.parent / "rubrics" / "default_rubric.json"

# Severity → score-penalty mapping (per defect, capped at criterion max)
SEVERITY_PENALTY = {
    "CRITICAL": 10,
    "HIGH": 5,
    "MEDIUM": 3,
    "LOW": 1,
}


def load_rubric(path: str | Path = DEFAULT_RUBRIC) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def score_scenario(rubric: dict[str, Any], defects: list[dict[str, str]]) -> dict[str, Any]:
    """Score a scenario against the rubric, given the defect list.

    Each criterion starts at max and is reduced by penalties from defects whose
    category maps to that criterion. Returns per-criterion and overall scores.
    """
    # Map criterion id → starting score (max) and weight
    breakdown: dict[str, dict[str, Any]] = {}
    for crit in rubric["criteria"]:
        breakdown[crit["id"]] = {
            "label": crit["label"],
            "weight": crit["weight"],
            "max": crit["max"],
            "score": crit["max"],
            "penalties": [],
        }

    for defect in defects:
        category = defect.get("category", "completeness")
        # Map "schema" defects → completeness
        if category == "schema":
            category = "completeness"
        if category in breakdown:
            penalty = SEVERITY_PENALTY.get(defect["severity"], 1)
            breakdown[category]["score"] = max(0, breakdown[category]["score"] - penalty)
            breakdown[category]["penalties"].append(defect["severity"])

    weighted_total = 0.0
    for crit_id, data in breakdown.items():
        # weighted: (score / max) * weight
        contribution = (data["score"] / data["max"]) * data["weight"]
        data["contribution"] = round(contribution, 2)
        weighted_total += contribution

    return {
        "overall_score": round(weighted_total, 1),
        "pass_threshold": rubric.get("pass_threshold", 75),
        "passed": weighted_total >= rubric.get("pass_threshold", 75),
        "breakdown": breakdown,
    }
