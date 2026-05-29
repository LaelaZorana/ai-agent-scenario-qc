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
from html import escape
from pathlib import Path

import gradio as gr

from qc_reviewer import validator, defect_detector, rubric, report

RUBRIC = rubric.load_rubric()
ACCENT = "#4f46e5"  # indigo
SEV_COLORS = {"CRITICAL": "#b91c1c", "HIGH": "#ea580c", "MEDIUM": "#ca8a04", "LOW": "#2563eb"}

CSS = """
:root { --accent: %s; }
.gradio-container { max-width: 1120px !important; }
#hero { background: linear-gradient(135deg, var(--accent), #0f172a);
        color:#fff; border-radius:18px; padding:26px 30px; margin-bottom:6px; }
#hero h1 { margin:0 0 8px 0; font-size:1.75rem; font-weight:800; letter-spacing:-.01em; }
#hero p { margin:0; opacity:.93; font-size:1.02rem; line-height:1.5; max-width:760px; }
#hero .pill { display:inline-block; background:rgba(255,255,255,.16); border-radius:999px;
        padding:3px 11px; font-size:.74rem; font-weight:700; margin-bottom:12px; letter-spacing:.04em; }
.verdict { border-radius:12px; padding:14px 18px; font-size:1.12rem; font-weight:800; margin:2px 0 14px; }
.verdict.pass { background:#dcfce7; color:#166534; border:1px solid #86efac; }
.verdict.fail { background:#fee2e2; color:#991b1b; border:1px solid #fca5a5; }
table.qc { width:100%%; border-collapse:collapse; margin:8px 0 14px; font-size:.92rem; }
table.qc th { text-align:left; padding:7px 10px; border-bottom:2px solid var(--accent); font-weight:700; }
table.qc td { text-align:left; padding:7px 10px; border-bottom:1px solid rgba(128,128,128,.2); }
.sev { display:inline-block; padding:2px 10px; border-radius:999px; font-size:.7rem;
        font-weight:800; color:#fff; letter-spacing:.03em; }
.defect { margin:7px 0; line-height:1.5; }
.defect code { background:rgba(128,128,128,.16); padding:1px 6px; border-radius:5px; }
.footer { margin-top:20px; padding-top:14px; border-top:1px solid rgba(128,128,128,.25);
        font-size:.88rem; text-align:center; opacity:.92; }
.footer a { text-decoration:none; font-weight:700; color:var(--accent); }
""" % ACCENT

FOOTER = """
<div class="footer">
🧰 Part of an AI evaluation &amp; QC toolkit by <b>Laela Zorana</b> &nbsp;·&nbsp;
🔍 Scenario QC &nbsp;·&nbsp;
⚖️ <a href="https://huggingface.co/spaces/LaelaZ/rlhf-pairwise-rater">RLHF Rater</a> &nbsp;·&nbsp;
📦 <a href="https://huggingface.co/spaces/LaelaZ/scorm-qa-validator">SCORM QA</a> &nbsp;·&nbsp;
<a href="https://github.com/LaelaZorana/ai-agent-scenario-qc">Source on GitHub</a>
</div>
"""


def _load_examples() -> dict:
    examples = {}
    for path in sorted(glob.glob("scenarios/**/*.json", recursive=True)):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                examples[Path(path).name] = fh.read()
        except OSError:
            continue
    return examples


EXAMPLES = _load_examples()


def _result_html(scenario_id: str, defects: list, score: dict) -> str:
    passed = score["passed"]
    cls = "pass" if passed else "fail"
    icon = "✅" if passed else "❌"
    verdict = "PASS" if passed else "FAIL — needs revision"
    parts = [
        f'<div class="verdict {cls}">{icon} {verdict} &nbsp;·&nbsp; '
        f'{score["overall_score"]} / 100 &nbsp;·&nbsp; {len(defects)} defect(s) '
        f'&nbsp;·&nbsp; pass threshold {score["pass_threshold"]}</div>'
    ]
    parts.append('<table class="qc"><tr><th>Criterion</th><th>Weight</th>'
                 '<th>Score</th><th>Contribution</th></tr>')
    for _cid, d in score["breakdown"].items():
        parts.append(f'<tr><td>{escape(str(d["label"]))}</td><td>{d["weight"]}%</td>'
                     f'<td>{d["score"]}/{d["max"]}</td><td>{d["contribution"]}</td></tr>')
    parts.append("</table>")

    if defects:
        parts.append("<h4>Defects</h4>")
        for d in report._sort_defects(defects):
            color = SEV_COLORS.get(d["severity"], "#6b7280")
            parts.append(
                f'<div class="defect"><span class="sev" style="background:{color}">'
                f'{escape(d["severity"])}</span> <code>{escape(str(d["location"]))}</code> '
                f'— {escape(str(d["message"]))}</div>'
            )
    else:
        parts.append("<p>✅ No defects detected — approve for inclusion.</p>")
    return "\n".join(parts)


def review(scenario_text: str):
    if not scenario_text or not scenario_text.strip():
        return '<div class="verdict fail">⚠️ Paste a scenario JSON, or pick an example.</div>', ""
    try:
        scenario = json.loads(scenario_text)
    except json.JSONDecodeError as exc:
        return f'<div class="verdict fail">❌ Invalid JSON — {escape(str(exc))}</div>', ""
    if not isinstance(scenario, dict):
        return '<div class="verdict fail">❌ Top level must be a JSON object.</div>', ""

    defects = validator.validate_structure(scenario) + defect_detector.detect_defects(scenario)
    score = rubric.score_scenario(RUBRIC, defects)
    scenario_id = scenario.get("scenario_id", "pasted_scenario")
    md = report.build_markdown("(pasted)", scenario_id, defects, score)
    return _result_html(scenario_id, defects, score), md


def load_example(name: str) -> str:
    return EXAMPLES.get(name, "")


theme = gr.themes.Soft(primary_hue="indigo", neutral_hue="slate",
                       font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"])

with gr.Blocks(title="AI Agent Scenario QC Reviewer", theme=theme, css=CSS) as demo:
    gr.HTML(
        '<div id="hero"><span class="pill">AI TRAINING-DATA QC</span>'
        "<h1>🔍 AI Agent Scenario QC Reviewer</h1>"
        "<p>Catch the defects that quietly break agent-training data <b>before</b> it reaches "
        "a labeling team. Paste a scenario — personas, a tool environment, multi-step tasks — "
        "and get a weighted rubric score plus a severity-tagged defect log: undeclared tools, "
        "undefined personas, out-of-order steps, empty success criteria, dead tools, token bloat.</p></div>"
    )

    with gr.Row():
        with gr.Column(scale=1):
            example_dd = gr.Dropdown(
                choices=list(EXAMPLES.keys()),
                label="① Load an example",
                value=("good_email_triage.json" if "good_email_triage.json" in EXAMPLES
                       else (list(EXAMPLES)[0] if EXAMPLES else None)),
            )
            scenario_box = gr.Code(
                label="② Scenario JSON (edit freely)", language="json",
                value=load_example(example_dd.value) if example_dd.value else "", lines=22,
            )
            run_btn = gr.Button("Review scenario ▶", variant="primary", size="lg")

        with gr.Column(scale=1):
            result_html = gr.HTML(label="Result")
            with gr.Accordion("📄 Full text report (copy / paste)", open=False):
                report_md = gr.Markdown()

    gr.HTML(FOOTER)
    gr.Markdown("*Runs the actual package (`qc_reviewer/`) — the same code the 10-case "
                "pytest suite exercises. Not a reimplementation.*")

    example_dd.change(load_example, inputs=example_dd, outputs=scenario_box)
    run_btn.click(review, inputs=scenario_box, outputs=[result_html, report_md])
    demo.load(review, inputs=scenario_box, outputs=[result_html, report_md])


if __name__ == "__main__":
    demo.launch()
