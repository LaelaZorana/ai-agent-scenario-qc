# Changelog

## [Unreleased]

- Consider making CRITICAL defects force a FAIL verdict regardless of weighted rubric score (see TODO)
- More semantic rules: cyclic step dependencies, contradictory success criteria
- Per-rule enable/disable via config

## 0.4.0: 2026-05-31

- Packaged for PyPI: added `pyproject.toml`, so the project installs with
  `pip install ai-agent-scenario-qc` instead of a manual clone.
- Moved the default schema and rubric inside the package (`qc_reviewer/data/`)
  and ship them as package data, so the validator and rubric work after a plain
  pip install (previously they loaded from the repo root and broke once
  installed). Behavior and contents are unchanged.
- Public API: the key functions are now re-exported from the top level, so you
  can write `from qc_reviewer import load_scenario, detect_defects, score_scenario`.
- Console entry point: the CLI is now available as the `scenario-qc` command,
  alongside the existing `python -m qc_reviewer`.
- Continuous integration: GitHub Actions runs the test suite on Python 3.9
  through 3.12.

## 0.3.0: 2026-05-25

- Added token-bloat heuristic (`description` length check)
- Added dead-tool detection (declared in `environment.tools` but never used in any step)
- Test coverage now 10 cases

## 0.2.1: 2026-05-24

- Fix: `defect_detector` crashed on scenarios with non-dict entries in `task.steps`. Now skips and continues.
- Minor README fixes

## 0.2.0: 2026-05-22

- Added `batch` CLI command (review every JSON file in a folder)
- Report writer now emits Markdown + JSON side-by-side
- Sorted defects by severity in reports

## 0.1.0: 2026-05-20

- First working end-to-end version: validator → rubric → report
- Default rubric with 8 weighted criteria
- Sample scenarios (`good_email_triage`, `bad_calendar_booking`, `bad_invalid_step_order`)
