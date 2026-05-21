"""Report writers — Markdown for humans, JSON for pipelines."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def _sort_defects(defects: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(defects, key=lambda d: SEVERITY_ORDER.get(d.get("severity", "LOW"), 99))


def build_markdown(scenario_path: str, scenario_id: str,
                   defects: list[dict[str, str]], score: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# QC Review Report — `{scenario_id}`")
    lines.append("")
    lines.append(f"**Source:** `{scenario_path}`")
    lines.append("")
    verdict = "PASS" if score["passed"] else "FAIL — needs revision"
    lines.append(f"**Overall score:** {score['overall_score']} / 100 — **{verdict}**")
    lines.append(f"**Defects found:** {len(defects)}")
    lines.append("")
    lines.append("## Rubric breakdown")
    lines.append("")
    lines.append("| Criterion | Weight | Score | Contribution |")
    lines.append("|---|---|---|---|")
    for crit_id, data in score["breakdown"].items():
        lines.append(
            f"| {data['label']} | {data['weight']}% | {data['score']}/{data['max']} | {data['contribution']} |"
        )
    lines.append("")
    lines.append("## Defects")
    lines.append("")
    if not defects:
        lines.append("_No defects detected._")
    else:
        for d in _sort_defects(defects):
            lines.append(f"- **[{d['severity']}]** `{d['location']}` — {d['message']}")
    lines.append("")
    lines.append("## Recommended actions")
    lines.append("")
    if not defects:
        lines.append("Scenario passed all checks. Approve for inclusion.")
    else:
        for i, d in enumerate(_sort_defects(defects), 1):
            lines.append(f"{i}. Resolve defect at `{d['location']}`: {d['message']}")
    lines.append("")
    return "\n".join(lines)


def write_reports(out_dir: str | Path, scenario_id: str,
                  scenario_path: str, defects: list[dict[str, str]],
                  score: dict[str, Any]) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md_path = out / f"{scenario_id}_review.md"
    json_path = out / f"{scenario_id}_review.json"
    md_path.write_text(build_markdown(scenario_path, scenario_id, defects, score), encoding="utf-8")
    json_path.write_text(
        json.dumps({"scenario_id": scenario_id, "source": scenario_path,
                    "score": score, "defects": defects}, indent=2),
        encoding="utf-8"
    )
    return md_path, json_path
