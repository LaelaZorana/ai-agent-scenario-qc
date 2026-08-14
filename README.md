# ai-agent-scenario-qc

[![CI](https://github.com/LaelaZorana/ai-agent-scenario-qc/actions/workflows/ci.yml/badge.svg)](https://github.com/LaelaZorana/ai-agent-scenario-qc/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/ai-agent-scenario-qc.svg)](https://pypi.org/project/ai-agent-scenario-qc/)
[![Python](https://img.shields.io/pypi/pyversions/ai-agent-scenario-qc.svg)](https://pypi.org/project/ai-agent-scenario-qc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Quality control for the JSON scenarios used to train AI agents. These are the files where an agent gets a persona, a simulated environment (Gmail, Slack, Drive, a fake CRM), and a multi-step task with expected outcomes. They break in subtle ways: a step references a tool that was never declared, a persona is mentioned but never defined, the success criteria are empty, or the JSON is technically valid but semantically broken. This catches those.

**Live demo:** [try it on Hugging Face Spaces](https://huggingface.co/spaces/LaelaZ/ai-agent-scenario-qc). Paste a scenario, get the QC report in your browser, no install.

## What it does

For a scenario JSON file it runs two passes and then scores the result:

1. **Structural validation** against a JSON schema (Draft 7).
2. **Semantic checks** that the schema cannot express:
   - tools referenced in a step but never declared in `environment.tools`
   - personas used as an actor but never defined in `personas[]`
   - non-sequential or duplicate step numbers
   - empty or trivially short success criteria
   - tools declared but never used (dead context)
   - token-bloated descriptions
3. **Rubric scoring**: a weighted rubric (8 criteria by default, pass threshold 75) turns the defect list into a single score out of 100, plus a severity-tagged defect log.

## Install

```bash
pip install ai-agent-scenario-qc
```

That gives you the `qc_reviewer` Python package and the `scenario-qc` command-line tool. The default schema and rubric ship inside the package, so it works straight out of the box. The only runtime dependency is `jsonschema`.

## Use it as a library

```python
from qc_reviewer import (
    load_scenario, validate_structure, detect_defects,
    load_rubric, score_scenario,
)

scenario = load_scenario("my_scenario.json")

# Two passes: structural (schema) + semantic (logic rules).
defects = validate_structure(scenario) + detect_defects(scenario)

# Score against the built-in rubric (or pass your own loaded dict).
result = score_scenario(load_rubric(), defects)

print(result["overall_score"], "PASS" if result["passed"] else "FAIL")
for d in defects:
    print(d["severity"], d["location"], d["message"])
```

`detect_defects` returns a list of dicts, each with `severity` (CRITICAL / HIGH / MEDIUM / LOW), `category`, `location`, and `message`. `score_scenario` returns the overall score, the pass flag, the threshold, and a per-criterion breakdown.

## Use it from the command line

```bash
# Review one scenario (writes a Markdown + JSON report to ./reports).
scenario-qc review my_scenario.json

# Review every .json file in a folder.
scenario-qc batch scenarios/ --out reports/

# Score against a custom rubric.
scenario-qc review my_scenario.json --rubric my_rubric.json
```

Example run on the bundled sample scenarios:

```
PASS  good_email_triage     100.0/100  defects=0
PASS  bad_calendar_booking   77.0/100  defects=3
```

and the defect log for that second one:

```
[CRITICAL]  task.steps[3].uses_tool      Tool 'calendar.create_event' referenced but not declared in environment.tools
[HIGH]      task.steps[2].actor_persona  Persona 'manager_2' referenced but not defined in personas[]
[MEDIUM]    success_criteria             success_criteria is empty, scenario has no measurable outcome
```

(That second scenario has real defects but still clears the threshold on weighted score alone. See "Known rough edge" below.)

## The rubric

The default rubric lives at `qc_reviewer/data/default_rubric.json`: 8 weighted criteria, each scored 0 to 10. The overall score is the weighted sum out of 100, and the pass threshold is 75. To use your own, copy that file, edit the weights and criteria, and pass it with `--rubric path/to/yours.json` (or `load_rubric("path/to/yours.json")` in code).

## Why I built it

I come from a quality-assurance and training background (LMS and SCORM testing, compliance content review), and I worked through the *AI Agents and Agentic AI Architecture in Python* course at Vanderbilt. What struck me was how much of building good agents is really about reviewing scenarios: making sure the tasks, environments, and tools hang together logically before a model ever sees them. That is QA. The first version was just a schema validator. Then I kept finding scenarios where the schema passed but the scenario was still broken, so I added semantic rules. The rubric scoring came last, because I wanted one number I could compare scenarios on.

## Known rough edge

A CRITICAL defect can arguably force a FAIL verdict regardless of the weighted score. Right now a scenario with one critical defect can still pass if everything else is perfect (as the `bad_calendar_booking` example above shows). The behavior is intentional for now and tracked in [TODO.md](TODO.md); a future version may make CRITICAL a hard fail.

## Public API

| Import | What it does |
| --- | --- |
| `load_scenario(path)` | Load a scenario JSON file. Raises `ValueError` on invalid JSON. |
| `load_schema()` | Return the bundled scenario JSON schema. |
| `validate_structure(scenario)` | Structural defects from schema validation (empty if valid). |
| `detect_defects(scenario)` | Semantic / logical defects the schema cannot catch. |
| `load_rubric(path=None)` | Load the bundled rubric, or a custom one from `path`. |
| `score_scenario(rubric, defects)` | Weighted score, pass flag, and per-criterion breakdown. |
| `build_markdown(...)`, `write_reports(...)` | Render and write the Markdown + JSON report. |

## Development

```bash
git clone https://github.com/LaelaZorana/ai-agent-scenario-qc
cd ai-agent-scenario-qc
pip install -e ".[dev]"
pytest -v
```

Build the distribution artifacts:

```bash
pip install build
python -m build      # writes dist/*.whl and dist/*.tar.gz
```

CI runs the suite on Python 3.9 through 3.12.

## Layout

```
qc_reviewer/
  __init__.py          public API
  __main__.py          the scenario-qc command line (review / batch)
  validator.py         JSON-schema validation and safe loading
  defect_detector.py   the semantic rules (the interesting part)
  rubric.py            weighted scoring
  report.py            Markdown + JSON output
  data/
    scenario.schema.json   the bundled scenario schema
    default_rubric.json    the bundled 8-criterion rubric
scenarios/             sample good and intentionally-broken scenarios
tests/
app.py                 the Gradio demo that runs on Hugging Face Spaces
```

## License

MIT. See [LICENSE](LICENSE).

---

**Links:** [GitHub](https://github.com/LaelaZorana) · [Hugging Face](https://huggingface.co/LaelaZ) · [Kaggle](https://www.kaggle.com/laelazorana)
