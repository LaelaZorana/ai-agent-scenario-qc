# TODO

Things I want to add when I get back to this:

- [ ] Force FAIL verdict when any CRITICAL defect is present, regardless of weighted score.
      Currently a CRITICAL only knocks 10 points off the relevant criterion, so a scenario
      with 1 critical + perfect everything else still passes. Probably wrong.
- [ ] Detect cyclic step dependencies (step 3 depends on step 5 output etc.)
- [ ] Detect contradictions across success_criteria (e.g. "must CC manager" + "must not CC anyone")
- [ ] Per-rule enable/disable via CLI flag or config file
- [ ] HTML report output (Markdown is fine for me but pretty for sharing)
- [ ] Better token estimator — the current `len(text) // 4` is a rough heuristic. Maybe use tiktoken?
- [ ] CI: GitHub Actions to run pytest on push

Lower priority:
- [ ] Allow rubric weights to be expressed as ratios (e.g. 2:1:1) instead of percentages
- [ ] Cache schema loading (currently re-reads from disk on every review — fine for now)
