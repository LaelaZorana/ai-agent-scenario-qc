---
title: AI Agent Scenario QC Reviewer
emoji: 🔍
colorFrom: indigo
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false
license: mit
---

# AI Agent Scenario QC Reviewer

Catch the defects that quietly break agent-training data **before** it reaches a
labeling team. Paste a scenario (JSON describing personas, a tool environment, and
multi-step tasks) and get a weighted rubric score plus a severity-tagged defect log:
undeclared tools, undefined personas, out-of-order steps, empty success criteria,
dead/unused tools, and token bloat.

This Space runs the actual package (`qc_reviewer/`) — the same code exercised by the
project's 10-case pytest suite, not a reimplementation.

**Source & full docs:** https://github.com/LaelaZorana/ai-agent-scenario-qc
