# Current repository structure

| Path | Current purpose |
| --- | --- |
| releases/ready-data | Current v5 ZIP/checksum and standalone usage guides |
| configs/data.yaml | Paths, thresholds, seed, scope, capacity and generator settings |
| configs/synthetic_sources.json | Context sources and explicit synthetic assumptions |
| src/pipeline | Source preparation, Track A, audits, current handoff/export/bundle commands |
| src/generator | Generated reconstruction and independent forward financial cases |
| src/analysis/current_evaluation.py | Current binary logistic/boosting, fixed-time/developer views and metrics |
| src/analysis/ew_features.py | Shared cutoff-safe feature/cleaning helpers; still required |
| src/analysis/early_warning.py, ew_eval.py, ew_report.py | Historical experiment/audit helpers; not the current CLI |
| src/pipeline/release.py | Historical workflow plus shared audit; current workflow uses team_run |
| tests | Regression/behavior checks for existing pipeline components |
| data | Current data contracts, source records, model/quality reports and scoped evidence |
| docs/requirements | Current specification, task/review board, program reference and timeline |
| docs/deliverables | Actual written deliverables plus their index; unfinished outputs are tasks |
| docs/REMAINING_TEAM_TASKS.md | Original-ID handoff for work still unresolved |
| CLAUDE.md, AGENTS.md | Current work, privacy, Git and task-marking instructions |

app.py currently prints settings and is not the planned Streamlit dashboard. src/inference/generate.py and src/models/build.py contain scaffolding, not the inspection agent or a new LLM implementation. Prompt scaffolds remain for planned AI tasks. No notebook contains a delivered execution workflow; empty notebook templates were retired.

External Project/real_data, Project/app_data and Project/private are configured local inputs/outputs, not ordinary Git content. Only the approved prepared ZIP is distributed. No raw/private/checkpoint directories are recreated in the repo to satisfy an outdated layout.

## Planned work

The [task board](../requirements/02-team-roles-and-tasks.md) and [remaining-task handoff](../REMAINING_TEAM_TASKS.md) define dashboard/agent/complaint-model/forms/presentation/KPI-value outputs. T-SA-02/T-SA-03 will create project-specific KPI/value configuration; old utility configs are not valid substitutes. Preserve IDs and update evidence/review marks when work is actually implemented.
