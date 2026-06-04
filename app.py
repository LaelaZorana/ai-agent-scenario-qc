"""
Gradio demo for the AI Agent Scenario QC Reviewer.

Paste an agent-training scenario (JSON) and get back the same structured QC
report the CLI produces: a weighted rubric score, a severity-tagged defect log,
and recommended fixes. The UI is bespoke, drawn as custom HTML by the Python
function into a single gr.HTML panel: a score ring, an animated rubric bar
chart, and a defect log of severity-tagged cards. It runs the real package
code in qc_reviewer/, so this is the tool, not a reimplementation.

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


EMPTY_STATE = """
<div class="qc-empty">
  <div class="qc-empty-emoji">🔍</div>
  <div class="qc-empty-text">Pick an example or paste a scenario, then run the review.</div>
  <div class="qc-empty-sub">You get a weighted score, a rubric breakdown, and a defect log.</div>
</div>
"""


def _score_card_html(defects: list, score: dict) -> str:
    overall = score["overall_score"]
    threshold = score["pass_threshold"]
    passed = score["passed"]
    frac = max(0.0, min(1.0, float(overall) / 100.0))
    pill_cls = "qc-pass" if passed else "qc-fail"
    pill_text = "PASS" if passed else "FAIL"
    n = len(defects)
    defect_word = "defect" if n == 1 else "defects"
    return f"""
    <div class="qc-hero">
      <div class="qc-ring" style="--p:{frac:.4f}">
        <span><b>{escape(str(overall))}</b><small>/ 100</small></span>
      </div>
      <div class="qc-hero-body">
        <div class="qc-hero-top">
          <span class="qc-verdict {pill_cls}">{pill_text}</span>
          <span class="qc-hero-thresh">pass threshold {escape(str(threshold))}</span>
        </div>
        <div class="qc-hero-label">Scenario QC score</div>
        <div class="qc-hero-sub">{n} {defect_word} found across the rubric</div>
      </div>
    </div>
    """


def _chart_html(score: dict) -> str:
    rows = []
    for _cid, d in score["breakdown"].items():
        label = escape(str(d["label"]))
        weight = escape(str(d["weight"]))
        smax = float(d["max"]) or 1.0
        pct = max(0.0, min(100.0, float(d["score"]) / smax * 100.0))
        rows.append(f"""
        <div class="qc-row">
          <div class="qc-row-name">{label}<span class="qc-weight">weight {weight}%</span></div>
          <div class="qc-track">
            <div class="qc-fill" style="width:{pct:.2f}%"></div>
          </div>
          <div class="qc-score">{escape(str(d["score"]))}/{escape(str(d["max"]))}</div>
        </div>
        """)
    return f"""
    <div class="qc-chart">
      <div class="qc-chart-title">Rubric breakdown</div>
      {"".join(rows)}
    </div>
    """


def _defects_html(defects: list) -> str:
    if not defects:
        return """
        <div class="qc-clean">
          <div class="qc-clean-emoji">✅</div>
          <div class="qc-clean-text">No defects detected. Approve for inclusion.</div>
        </div>
        """
    cards = []
    for d in report._sort_defects(defects):
        sev = str(d["severity"])
        color = SEV_COLORS.get(sev, "#6b7280")
        cards.append(f"""
        <div class="qc-defect" style="--sev:{color}">
          <div class="qc-defect-top">
            <span class="qc-chip" style="background:{color}">{escape(sev)}</span>
            <code class="qc-loc">{escape(str(d["location"]))}</code>
          </div>
          <div class="qc-defect-msg">{escape(str(d["message"]))}</div>
        </div>
        """)
    return f"""
    <div class="qc-defects">
      <div class="qc-chart-title">Defect log</div>
      {"".join(cards)}
    </div>
    """


def _result_html(defects: list, score: dict) -> str:
    body = _score_card_html(defects, score) + _chart_html(score) + _defects_html(defects)
    return f'<div class="qc-result">{body}</div>'


def _notice(message: str) -> str:
    return f'<div class="qc-result"><div class="qc-notice">{message}</div></div>'


def review(scenario_text: str):
    if not scenario_text or not scenario_text.strip():
        return _notice("⚠️ Paste a scenario JSON, or pick an example."), ""
    try:
        scenario = json.loads(scenario_text)
    except json.JSONDecodeError as exc:
        return _notice("❌ Invalid JSON. " + escape(str(exc))), ""
    if not isinstance(scenario, dict):
        return _notice("❌ Top level must be a JSON object."), ""

    defects = validator.validate_structure(scenario) + defect_detector.detect_defects(scenario)
    score = rubric.score_scenario(RUBRIC, defects)
    scenario_id = scenario.get("scenario_id", "pasted_scenario")
    md = report.build_markdown("(pasted)", scenario_id, defects, score)
    return _result_html(defects, score), md


def load_example(name: str) -> str:
    return EXAMPLES.get(name, "")


CSS = """
:root {
  --qc-accent:#4f46e5; --qc-bg1:#eef2ff; --qc-bg2:#f5f3ff;
  --qc-ink:#1e1b2e; --qc-muted:#6b6880; --qc-card:#ffffff; --qc-line:rgba(20,16,40,.08);
  --qc-font:'Plus Jakarta Sans','Inter',system-ui,sans-serif;
}

/* Light lock: HF Spaces default to dark mode, but this UI is designed light.
   Override Gradio's dark theme variables so it renders light everywhere. */
:root, .dark, gradio-app.dark {
  color-scheme: light !important;
  --body-background-fill:#ffffff !important;
  --background-fill-primary:#ffffff !important;
  --background-fill-secondary:#f6f6fb !important;
  --block-background-fill:#ffffff !important;
  --block-label-background-fill:#ffffff !important;
  --input-background-fill:#ffffff !important;
  --border-color-primary:rgba(20,16,40,.12) !important;
  --body-text-color:#16131f !important;
  --body-text-color-subdued:#6b6880 !important;
  --block-title-text-color:#16131f !important;
  --block-info-text-color:#6b6880 !important;
}
html, body, gradio-app, .dark { background:#ffffff !important; }

.gradio-container { max-width: 980px !important; background:
  radial-gradient(1200px 500px at 12% -10%, var(--qc-bg1), transparent 60%),
  radial-gradient(1000px 500px at 110% 8%, var(--qc-bg2), transparent 55%) !important; }
.gradio-container, .gradio-container * { font-family: var(--qc-font); }

/* Header */
#qc-head { text-align:center; padding: 18px 8px 4px; }
#qc-head .qc-pill { display:inline-block; background:#1e1b2e; color:#fff; border-radius:999px;
  padding:5px 13px; font-size:.7rem; font-weight:700; letter-spacing:.08em; margin-bottom:14px; }
#qc-head h1 { margin:0; font-size:2.0rem; font-weight:800; letter-spacing:-.02em; color:var(--qc-ink);
  background:linear-gradient(90deg,#4f46e5,#7c3aed,#2563eb); -webkit-background-clip:text;
  background-clip:text; -webkit-text-fill-color:transparent; }
#qc-head p { margin:10px auto 0; max-width:620px; color:var(--qc-muted); font-size:1.0rem; line-height:1.55; }

/* Input column */
#qc-input .cm-editor, #qc-input textarea { border-radius:16px !important; }
#qc-go { border-radius:14px !important; font-weight:800 !important; font-size:1rem !important;
  background:linear-gradient(135deg,#4f46e5,#7c3aed) !important; border:none !important; color:#fff !important;
  box-shadow:0 10px 26px rgba(79,70,229,.35) !important; transition:transform .12s ease, box-shadow .12s ease !important; }
#qc-go:hover { transform:translateY(-1px); box-shadow:0 14px 32px rgba(79,70,229,.45) !important; }

/* Results panel */
.qc-result { animation: qc-fade .35s ease both; }
@keyframes qc-fade { from{opacity:0; transform:translateY(8px)} to{opacity:1; transform:none} }

.qc-notice { padding:18px 20px; border-radius:18px; background:var(--qc-card); border:1px solid var(--qc-line);
  color:var(--qc-ink); font-weight:700; box-shadow:0 10px 30px rgba(30,27,46,.05); }

/* Score hero */
.qc-hero { display:flex; align-items:center; gap:20px; padding:22px 24px; border-radius:20px;
  background:var(--qc-card); border:1px solid var(--qc-line); position:relative; overflow:hidden;
  box-shadow:0 18px 44px rgba(79,70,229,.16); }
.qc-hero::before { content:""; position:absolute; inset:0; opacity:.10;
  background:radial-gradient(420px 160px at 8% 0%, var(--qc-accent), transparent 70%); }
.qc-ring { width:92px; height:92px; border-radius:50%; display:grid; place-items:center; flex-shrink:0;
  background:conic-gradient(var(--qc-accent) calc(var(--p)*360deg), #e7e5f7 0); }
.qc-ring span { width:72px; height:72px; border-radius:50%; background:var(--qc-card); display:grid; place-items:center;
  text-align:center; line-height:1.1; color:var(--qc-ink); }
.qc-ring b { font-size:1.5rem; font-weight:800; }
.qc-ring small { display:block; font-size:.6rem; font-weight:700; color:var(--qc-muted); }
.qc-hero-body { flex:1; }
.qc-hero-top { display:flex; align-items:center; gap:10px; margin-bottom:6px; }
.qc-verdict { display:inline-block; padding:3px 12px; border-radius:999px; font-size:.78rem; font-weight:800; letter-spacing:.04em; }
.qc-verdict.qc-pass { background:#dcfce7; color:#166534; border:1px solid #86efac; }
.qc-verdict.qc-fail { background:#fee2e2; color:#991b1b; border:1px solid #fca5a5; }
.qc-hero-thresh { font-size:.82rem; color:var(--qc-muted); font-weight:700; }
.qc-hero-label { font-size:1.4rem; font-weight:800; color:var(--qc-ink); letter-spacing:-.01em; }
.qc-hero-sub { color:var(--qc-muted); font-size:.95rem; margin-top:2px; }

/* Rubric chart */
.qc-chart { margin-top:14px; padding:18px 22px; border-radius:18px; background:var(--qc-card);
  border:1px solid var(--qc-line); box-shadow:0 10px 30px rgba(30,27,46,.05); }
.qc-chart-title { font-weight:800; color:var(--qc-ink); font-size:1.02rem; margin-bottom:10px; }
.qc-row { display:flex; align-items:center; gap:14px; padding:7px 0; }
.qc-row-name { width:200px; font-weight:700; color:var(--qc-ink); font-size:.9rem; display:flex; flex-direction:column; }
.qc-weight { font-weight:600; color:var(--qc-muted); font-size:.74rem; margin-top:1px; }
.qc-track { flex:1; height:14px; border-radius:999px; background:#eceaf8; overflow:hidden; }
.qc-fill { height:100%; border-radius:999px; background:linear-gradient(90deg,#4f46e5,#7c3aed);
  transform-origin:left; animation: qc-grow .65s cubic-bezier(.2,.8,.2,1) both; }
@keyframes qc-grow { from{transform:scaleX(0)} to{transform:scaleX(1)} }
.qc-score { width:54px; text-align:right; font-variant-numeric:tabular-nums; font-weight:700; color:var(--qc-muted); font-size:.88rem; }

/* Defect log */
.qc-defects { margin-top:14px; }
.qc-defect { padding:13px 16px; border-radius:14px; background:var(--qc-card); border:1px solid var(--qc-line);
  border-left:5px solid var(--sev); box-shadow:0 8px 24px rgba(30,27,46,.05); margin-top:10px;
  animation: qc-fade .35s ease both; }
.qc-defect-top { display:flex; align-items:center; gap:10px; margin-bottom:6px; }
.qc-chip { display:inline-block; padding:2px 10px; border-radius:999px; font-size:.68rem; font-weight:800;
  color:#fff; letter-spacing:.04em; }
.qc-loc { font-family:'SFMono-Regular',ui-monospace,Menlo,Consolas,monospace; font-size:.8rem;
  background:rgba(20,16,40,.06); padding:2px 7px; border-radius:6px; color:var(--qc-ink); }
.qc-defect-msg { color:var(--qc-ink); font-size:.94rem; line-height:1.5; }

.qc-clean { text-align:center; padding:30px 20px; margin-top:14px; border-radius:18px; background:var(--qc-card);
  border:1px solid var(--qc-line); }
.qc-clean-emoji { font-size:2.2rem; }
.qc-clean-text { margin-top:8px; font-weight:700; color:#166534; font-size:1.0rem; }

/* Empty state */
.qc-empty { text-align:center; padding:42px 20px; border-radius:20px; background:var(--qc-card);
  border:1px dashed var(--qc-line); }
.qc-empty-emoji { font-size:2.6rem; }
.qc-empty-text { margin-top:10px; font-weight:700; color:var(--qc-ink); font-size:1.05rem; }
.qc-empty-sub { margin-top:4px; color:var(--qc-muted); font-size:.92rem; }

/* Footer */
.qc-footer { margin-top:22px; padding-top:16px; border-top:1px solid var(--qc-line);
  text-align:center; font-size:.88rem; color:var(--qc-muted); line-height:1.9; }
.qc-footer a { text-decoration:none; font-weight:700; color:var(--qc-accent); }
.qc-meta { text-align:center; color:var(--qc-muted); font-size:.82rem; margin-top:10px; }
"""

FOOTER = """
<div class="qc-footer">
🧰 Part of an AI evaluation &amp; QC toolkit by <b>Laela Zorana</b><br>
<a href="https://github.com/LaelaZorana/ai-agent-scenario-qc">Source on GitHub</a> &middot;
<a href="https://huggingface.co/spaces/LaelaZ/rlhf-pairwise-rater">RLHF Rater</a> &middot;
<a href="https://huggingface.co/spaces/LaelaZ/scorm-qa-validator">SCORM QA</a> &middot;
<a href="https://huggingface.co/spaces/LaelaZ/distilbert-emotion">Emotion Classifier</a>
</div>
"""

theme = gr.themes.Soft(
    primary_hue="indigo", neutral_hue="slate",
    font=[gr.themes.GoogleFont("Plus Jakarta Sans"), gr.themes.GoogleFont("Inter"),
          "system-ui", "sans-serif"],
)

with gr.Blocks(title="AI Agent Scenario QC Reviewer", theme=theme, css=CSS) as demo:
    gr.HTML(
        '<div id="qc-head"><span class="qc-pill">AI TRAINING-DATA QC</span>'
        "<h1>AI Agent Scenario QC Reviewer</h1>"
        "<p>Catch the defects that quietly break agent-training data before it reaches a "
        "labeling team. Paste a scenario with personas, a tool environment, and multi-step "
        "tasks, then read a weighted rubric score plus a severity-tagged defect log: "
        "undeclared tools, undefined personas, out-of-order steps, empty success criteria, "
        "dead tools, token bloat.</p></div>"
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
                label="② Scenario JSON (edit freely)", language="json", elem_id="qc-input",
                value=load_example(example_dd.value) if example_dd.value else "", lines=22,
            )
            run_btn = gr.Button("Review scenario", elem_id="qc-go", variant="primary", size="lg")

        with gr.Column(scale=1):
            result_html = gr.HTML(EMPTY_STATE, label="Result")
            with gr.Accordion("📄 Full text report (copy / paste)", open=False):
                report_md = gr.Markdown()

    gr.HTML(FOOTER)
    gr.HTML('<div class="qc-meta">Runs the actual package (qc_reviewer/), the same code the '
            '10-case pytest suite exercises. Not a reimplementation.</div>')

    example_dd.change(load_example, inputs=example_dd, outputs=scenario_box)
    run_btn.click(review, inputs=scenario_box, outputs=[result_html, report_md])
    demo.load(review, inputs=scenario_box, outputs=[result_html, report_md])


if __name__ == "__main__":
    demo.launch()
