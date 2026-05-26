# Changelog

## [Unreleased]

- Consider making CRITICAL defects force a FAIL verdict regardless of weighted rubric score (see TODO)
- More semantic rules: cyclic step dependencies, contradictory success criteria
- Per-rule enable/disable via config

## 0.3.0 — 2026-05-25

- Added token-bloat heuristic (`description` length check)
- Added dead-tool detection (declared in `environment.tools` but never used in any step)
- Test coverage now 10 cases

## 0.2.1 — 2026-05-24

- Fix: `defect_detector` crashed on scenarios with non-dict entries in `task.steps`. Now skips and continues.
- Minor README fixes

## 0.2.0 — 2026-05-22

- Added `batch` CLI command (review every JSON file in a folder)
- Report writer now emits Markdown + JSON side-by-side
- Sorted defects by severity in reports

## 0.1.0 — 2026-05-20

- First working end-to-end version: validator → rubric → report
- Default rubric with 8 weighted criteria
- Sample scenarios (`good_email_triage`, `bad_calendar_booking`, `bad_invalid_step_order`)
