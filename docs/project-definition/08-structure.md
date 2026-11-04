# Current repository structure

| Path | Current purpose |
| --- | --- |
| releases/ready-data | Current v7 ZIP/checksum and standalone usage guides |
| app.py, src/dashboard | Streamlit dashboard (five screens, track switch, `ops_visits` form) and its helpers |
| src/chatbot | Document Q&A chatbot (retrieval, citations) shown in the dashboard sidebar |
| data/knowledge | Source documents for the chatbot (SOURCES.csv, external/) |
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
| docs/deliverables/01-presentation | presentation.md/.html/.pptx (built by make/build_pptx.js), palette.md, rubric-map.md |
| docs/deliverables/02-video | intro.mp4, intro.md, partner logos, rebuild kit in make/ |
| docs/REMAINING_TEAM_TASKS.md | Original-ID handoff for work still unresolved |
| CLAUDE.md, AGENTS.md | Current work, privacy, Git and task-marking instructions |

app.py is the Streamlit dashboard. src/models/build.py and parts of src/inference/generate.py remain scaffolding, not a new LLM implementation. Prompt scaffolds remain for planned AI tasks. No notebook contains a delivered execution workflow; empty notebook templates were retired.

External Project/real_data, Project/app_data and Project/private are configured local inputs/outputs, not ordinary Git content. Only the approved prepared ZIP is distributed. No raw/private/checkpoint directories are recreated in the repo to satisfy an outdated layout.

## Planned work

The [task board](../requirements/02-team-roles-and-tasks.md) and [remaining-task handoff](../REMAINING_TEAM_TASKS.md) define dashboard/agent/complaint-model/forms/presentation/KPI-value outputs. T-SA-02/T-SA-03 will create project-specific KPI/value configuration; old utility configs are not valid substitutes. Preserve IDs and update evidence/review marks when work is actually implemented.
