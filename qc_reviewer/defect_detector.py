"""Semantic defect detection — beyond schema, catches logical issues."""
from __future__ import annotations

from typing import Any

TOKEN_SOFT_LIMIT = 1500  # rough heuristic: 1 token ~= 4 chars
# TODO: replace with tiktoken once I'm ready to add the dep — see TODO.md


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def detect_defects(scenario: dict[str, Any]) -> list[dict[str, str]]:
    """Return a list of semantic / logical defects found in the scenario."""
    defects: list[dict[str, str]] = []

    personas = scenario.get("personas", []) or []
    persona_ids = {p.get("id") for p in personas if isinstance(p, dict)}

    env = scenario.get("environment", {}) or {}
    declared_tools = set(env.get("tools", []) or [])

    task = scenario.get("task", {}) or {}
    # task may be a plain string description rather than a structured dict
    if isinstance(task, str):
        task = {}
    steps = task.get("steps", []) or []

    # Rule: every uses_tool must be declared
    for step in steps:
        if not isinstance(step, dict):
            continue
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
        if not isinstance(step, dict):
            continue
        actor = step.get("actor_persona")
        step_num = step.get("step", "?")
        if actor and actor not in persona_ids:
            defects.append({
                "severity": "HIGH",
                "category": "logical_consistency",
                "location": f"task.steps[{step_num}].actor_persona",
                "message": f"Persona '{actor}' referenced but not defined in personas[]",
            })

    # Rule: step numbers must be unique and sequential
    step_nums = [s.get("step") for s in steps if isinstance(s, dict)]
    if step_nums and step_nums != list(range(1, len(step_nums) + 1)):
        defects.append({
            "severity": "MEDIUM",
            "category": "logical_consistency",
            "location": "task.steps",
            "message": f"Step numbers are not sequential starting from 1: {step_nums}",
        })

    # Rule: success_criteria must be non-empty and non-trivial
    criteria = scenario.get("success_criteria", []) or []
    if not criteria:
        defects.append({
            "severity": "MEDIUM",
            "category": "success_criteria",
            "location": "success_criteria",
            "message": "success_criteria is empty — scenario has no measurable outcome",
        })
    else:
        trivial = [c for c in criteria if isinstance(c, str) and len(c.strip()) < 10]
        if trivial:
            defects.append({
                "severity": "LOW",
                "category": "success_criteria",
                "location": "success_criteria",
                "message": f"{len(trivial)} success criterion(a) are too short to be measurable",
            })

    # Rule: token-bloat check on description
    desc = scenario.get("description", "") or ""
    tokens = _approx_tokens(desc)
    if tokens > TOKEN_SOFT_LIMIT:
        defects.append({
            "severity": "LOW",
            "category": "token_efficiency",
            "location": "description",
            "message": f"Description ~{tokens} tokens, exceeds soft limit of {TOKEN_SOFT_LIMIT}",
        })

    # Rule: declared tool never used (dead context)
    used_tools = {s.get("uses_tool") for s in steps if isinstance(s, dict) and s.get("uses_tool")}
    unused = declared_tools - used_tools
    if unused:
        defects.append({
            "severity": "LOW",
            "category": "completeness",
            "location": "environment.tools",
            "message": f"Tools declared but never used in task: {sorted(unused)}",
        })

    return defects
