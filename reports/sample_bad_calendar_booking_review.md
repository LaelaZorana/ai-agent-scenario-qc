# QC Review Report — `bad_calendar_booking`

**Source:** `scenarios/bad_calendar_booking.json`

**Overall score:** 77.0 / 100 — **PASS**
**Defects found:** 3

## Rubric breakdown

| Criterion | Weight | Score | Contribution |
|---|---|---|---|
| Logical consistency across steps | 20% | 0/10 | 0.0 |
| Factual accuracy of references | 15% | 10/10 | 15.0 |
| All required fields populated | 15% | 10/10 | 15.0 |
| Task goal is clear and specific | 10% | 10/10 | 10.0 |
| Tools and context are plausible | 10% | 10/10 | 10.0 |
| Measurable success criteria | 10% | 7/10 | 7.0 |
| Low ambiguity (penalized) | 10% | 10/10 | 10.0 |
| Concise without bloat | 10% | 10/10 | 10.0 |

## Defects

- **[CRITICAL]** `task.steps[3].uses_tool` — Tool 'calendar.create_event' referenced but not declared in environment.tools
- **[HIGH]** `task.steps[2].actor_persona` — Persona 'manager_2' referenced but not defined in personas[]
- **[MEDIUM]** `success_criteria` — success_criteria is empty — scenario has no measurable outcome

## Recommended actions

1. Resolve defect at `task.steps[3].uses_tool`: Tool 'calendar.create_event' referenced but not declared in environment.tools
2. Resolve defect at `task.steps[2].actor_persona`: Persona 'manager_2' referenced but not defined in personas[]
3. Resolve defect at `success_criteria`: success_criteria is empty — scenario has no measurable outcome
