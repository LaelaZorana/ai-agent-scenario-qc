# ai-agent-scenario-qc

A small Python toolkit I built to **QC the kind of JSON scenarios that get used to train AI agents** — the ones where an agent is given a persona, a simulated environment (Gmail, Slack, Drive, a fake CRM), and a multi-step task with expected outcomes.

If you've ever looked at one of those scenarios, you know how easy it is for them to break in subtle ways: a step references a tool that wasn't declared, a persona is mentioned but never defined, success criteria are empty, JSON is technically valid but semantically broken. This catches those things.

## Why I built this

I'm coming from a quality-assurance and training background (LMS / SCORM testing, compliance content review) and I picked up the *AI Agents and Agentic AI Architecture in Python* course at Vanderbilt at the end of 2025. After working through the course, the thing that struck me was how much of the work of building good agents was actually *reviewing scenarios* — making sure the tasks, environments, and tools all hang together logically before you ever feed them to a model.

That's basically QA. So I wrote my own little reviewer to practice the workflow.

The first version was just a JSON-schema validator. Then I kept finding scenarios in my own notes where the schema passed but the scenario was still broken (a step using a tool that wasn't declared, for example), so I started adding semantic rules. The rubric scoring came last — I wanted a single number I could compare scenarios on.

## What it does

- Loads a scenario `.json` file
- Validates it against [`schema/scenario.schema.json`](schema/scenario.schema.json) (structural checks)
- Runs semantic checks (see [`qc_reviewer/defect_detector.py`](qc_reviewer/defect_detector.py)) for things like:
  - Undeclared tools referenced in task steps
  - Undefined personas referenced as actors
  - Non-sequential or duplicate step numbers
  - Empty / trivial success criteria
  - Declared-but-unused tools (dead context)
  - Token-bloated descriptions
- Scores against a weighted rubric (default: 8 criteria, pass threshold 75)
- Writes a Markdown + JSON review report per scenario

## Quickstart

```bash
pip install -r requirements.txt

# Review one scenario
python -m qc_reviewer review scenarios/good_email_triage.json

# Batch-review a folder
python -m qc_reviewer batch scenarios/ --out reports/

# Run tests
pytest -v
```

Example output (truncated):

```
PASS  good_email_triage          100.0/100  defects=0
FAIL  bad_calendar_booking        62.0/100  defects=3
  [CRITICAL] task.steps[3].uses_tool — Tool 'calendar.create_event' not in environment.tools
  [HIGH]     task.steps[2].actor_persona — Persona 'manager_2' not defined
  [MEDIUM]   success_criteria — empty
```

A full sample report lives in [`reports/sample_bad_calendar_booking_review.md`](reports/sample_bad_calendar_booking_review.md).

## Rubric

The default rubric is in [`rubrics/default_rubric.json`](rubrics/default_rubric.json) — 8 weighted criteria, each scored 0–10. The overall score is the weighted sum out of 100; the pass threshold is 75.

You can drop a custom rubric in `rubrics/` and pass `--rubric path/to/yours.json`.

## Project layout

```
qc_reviewer/
├── __main__.py          CLI: review / batch
├── validator.py         JSON-schema validation + safe loading
├── defect_detector.py   Semantic rules (the interesting bit)
├── rubric.py            Weighted scoring
└── report.py            Markdown + JSON output

schema/scenario.schema.json
rubrics/default_rubric.json
scenarios/               sample good + intentionally-bad scenarios
tests/                   pytest suite
```

## What's still rough

There's a real list in [TODO.md](TODO.md). The big one: a CRITICAL defect should arguably force a `FAIL` verdict regardless of weighted score — right now a scenario with 1 critical defect can still pass if everything else is perfect. I went back and forth on this; for now I left it weighted, but I'd probably change my mind in v2.

## Reading order

If you want to understand the code, I'd read in this order:
1. `schema/scenario.schema.json` — what a "good" scenario looks like
2. `scenarios/good_email_triage.json` — a concrete example
3. `qc_reviewer/validator.py` — easy, just JSON-schema wrap
4. `qc_reviewer/defect_detector.py` — the actual semantic logic
5. `qc_reviewer/rubric.py` — how scores get computed
6. `qc_reviewer/report.py` — output formatting

## License

MIT. See [LICENSE](LICENSE).

---

**Links:** [GitHub](https://github.com/LaelaZorana) · [HuggingFace](https://huggingface.co/LaelaZ) · [Kaggle](https://www.kaggle.com/laelazorana)
