"""Semantic defect detection — beyond schema, catches logical issues."""
from __future__ import annotations

from typing import Any


def detect_defects(scenario: dict[str, Any]) -> list[dict[str, str]]:
    """Return a list of semantic / logical defects found in the scenario."""
    defects: list[dict[str, str]] = []

    personas = scenario.get("personas", []) or []
    persona_ids = {p.get("id") for p in personas if isinstance(p, dict)}

    env = scenario.get("environment", {}) or {}
    declared_tools = set(env.get("tools", []) or [])

    task = scenario.get("task", {}) or {}
    steps = task.get("steps", []) or []

    # Rule: every uses_tool must be declared
    for step in steps:
        tool = step.get("uses_tool")
        step_num = step.get("step", "?")
        if tool and tool not in declared_tools:
            defects.append({
                "severity": "CRITICAL",
                "category": "logical_consistency",
                "location": f"task.steps[{step_num}].uses_tool",
                "message": f"Tool '{tool}' referenced but not declared in environment.tools",
            })

    # Rule: every actor_persona must be declared
    for step in steps:
        actor = step.get("actor_persona")
        step_num = step.get("step", "?")
        if actor and actor not in persona_ids:
            defects.append({
                "severity": "HIGH",
                "category": "logical_consistency",
                "location": f"task.steps[{step_num}].actor_persona",
                "message": f"Persona '{actor}' referenced but not defined in personas[]",
            })

    return defects
