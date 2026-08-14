"""ai-agent-scenario-qc.

Quality control for AI agent training scenarios. Point it at a scenario JSON file
and it runs two passes: a structural check against a JSON schema, and a set of
semantic rules (undeclared tools, undefined personas, non-sequential steps, empty
success criteria, token bloat, dead tools). It then scores the scenario against a
weighted rubric and writes a severity-tagged defect log.

The public API is re-exported here so you can write:

    from qc_reviewer import load_scenario, validate_structure, detect_defects, score_scenario
"""
from __future__ import annotations

from .defect_detector import detect_defects
from .report import build_markdown, write_reports
from .rubric import load_rubric, score_scenario
from .validator import load_scenario, load_schema, validate_structure

__version__ = "0.4.0"

__all__ = [
    # load + validate
    "load_scenario",
    "load_schema",
    "validate_structure",
    # semantic defects
    "detect_defects",
    # rubric scoring
    "load_rubric",
    "score_scenario",
    # reporting
    "build_markdown",
    "write_reports",
    "__version__",
]
