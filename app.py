"""
Gradio demo for the AI Agent Scenario QC Reviewer.

Paste an agent-training scenario (JSON) and get back the same structured QC
report the CLI produces: a weighted rubric score, a severity-tagged defect log,
and recommended fixes. Runs the real package code in qc_reviewer/ — this is the
tool, not a reimplementation.

Run locally:   pip install -r requirements.txt && python app.py
On Hugging Face Spaces this file is the entry point (app_file: app.py).
"""
from __future__ import annotations

import json
import glob
from pathlib import Path

import gradio as gr

from qc_reviewer import validator, defect_detector, rubric, report

RUBRIC = rubric.load_rubric()


def _load_examples() -> dict:
    """Read every bundled scenario so reviewers can try one in a click."""
    examples = {}
    for path in sorted(glob.glob("scenarios/**/*.json", recursive=True)):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                examples[Path(path).name] = fh.read()
        except OSError:
            continue
    return examples


EXAMPLES = _load_examples()


def review(scenario_text: str):
    """Validate + score a pasted scenario; return the markdown report and a verdict."""
    if not scenario_text or not scenario_text.strip():
        return "⚠️ Paste a scenario JSON above, or pick an example.", ""

    try:
        scenario = json.loads(scenario_text)
    except json.JSONDecodeError as exc:
        return f"❌ **Invalid JSON** — {exc}", ""

    if not isinstance(scenario, dict):
        return "❌ **Top level must be a JSON object** describing one scenario.", ""

    defects = validator.validate_structure(scenario) + defect_detector.detect_defects(scenario)
    score = rubric.score_scenario(RUBRIC, defects)

    scenario_id = scenario.get("scenario_id", "pasted_scenario")
    md = report.build_markdown("(pasted)", scenario_id, defects, score)

    verdict = "✅ PASS" if score["passed"] else "❌ FAIL — needs revision"
    headline = (
        f"### {verdict} — {score['overall_score']} / 100  "
        f"·  {len(defects)} defect(s)  ·  pass threshold {score['pass_threshold']}"
    )
    return headline, md


def load_example(name: str) -> str:
    return EXAMPLES.get(name, "")


with gr.Blocks(title="AI Agent Scenario QC Reviewer") as demo:
    gr.Markdown(
        "# 🔍 AI Agent Scenario QC Reviewer\n"
        "Catch the defects that quietly break agent-training data **before** it reaches "
        "a labeling team. Paste a scenario (JSON describing personas, a tool environment, "
        "and multi-step tasks) and get a weighted rubric score plus a severity-tagged "
        "defect log — undeclared tools, undefined personas, out-of-order steps, empty "
        "success criteria, dead tools, and token bloat.\n\n"
        "*This runs the actual package (`qc_reviewer/`), the same code the CLI and the "
        "10-case pytest suite exercise.*"
    )

    with gr.Row():
        with gr.Column(scale=1):
            example_dd = gr.Dropdown(
                choices=list(EXAMPLES.keys()),
                label="Load an example scenario",
                value=("good_email_triage.json" if "good_email_triage.json" in EXAMPLES
                       else (list(EXAMPLES)[0] if EXAMPLES else None)),
            )
            scenario_box = gr.Code(
                label="Scenario JSON",
                language="json",
                value=load_example(example_dd.value) if example_dd.value else "",
                lines=22,
            )
            run_btn = gr.Button("Review scenario", variant="primary")

        with gr.Column(scale=1):
            headline = gr.Markdown(label="Verdict")
            report_md = gr.Markdown(label="QC report")

    example_dd.change(load_example, inputs=example_dd, outputs=scenario_box)
    run_btn.click(review, inputs=scenario_box, outputs=[headline, report_md])
    demo.load(review, inputs=scenario_box, outputs=[headline, report_md])


if __name__ == "__main__":
    demo.launch()
