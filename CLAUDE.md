# CLAUDE.md

## Current references

Read data/HANDOFF.md, docs/requirements/02-team-roles-and-tasks.md and docs/REMAINING_TEAM_TASKS.md first. The current prepared release is v5 only; current source contracts live in data. Do not restore retired plans, empty scaffold documents, utility-demo configs or earlier ZIP versions.

Scope: 12 R7 compounds, six real check cases, inspection capacity 4. The classifier predicts distressed/not_distressed; completion prediction is removed. Height is approved context through 2024, without a fixed error guarantee. See data/BINARY_SCOPE_DECISION.md. Dashboard and inspection-agent functionality remain unfinished.

## Required task-board updates

- Use docs/requirements/02-team-roles-and-tasks.md as the single task board; preserve IDs/owners.
- After implementing/verifying a task, mark its main checkbox [x], add evidence and set the label to "Implemented; review pending". After an independent review recorded in logs/review-NN.md (or the PR), tick its separate Review accepted checkbox and set the label to "Done; review accepted". Human acceptance is not required.
- Main [x] means implemented/ready for review, not accepted. On the board record the review log reference, date, related commits and any caveat; keep all other task information; never write an agent, model or lane name, never name a person who did not perform the review, and never tick the box without a recorded review.
- Keep partial/open tasks unchecked and failed/excluded experiments labelled. Synchronize docs/REMAINING_TEAM_TASKS.md in the same branch/PR.
- Do not infer completion from a placeholder, available input data or a successful unrelated test.

## Git workflow

Work/commit/push only on a feature branch and merge through a PR. Fetch/review teammates' changes; never force-push or overwrite their work. Use the configured human Git author/committer; no assistant attribution or co-author trailers. A cleanup must have clear user authorization; do not ask again for deletions the user explicitly authorized.

## Commands and implementation

Use uv sync --locked. Current cached-source workflow: uv run --locked --offline python -m src.pipeline.team_run. It includes current small binary fits. Add --full only for an intended Track A refit. make data is data-only; make current and make run mirror the current cached/full workflows.

Tests: uv run --locked --offline pytest -q. Lint touched Python with Ruff and check Git whitespace. For documentation-only changes, validate links/status consistency without rerunning fitting. The historical early_warning/ew_eval/release modules remain for audit/shared dependencies; do not use their old N=8 experiment as the current report or delete needed helpers.

Track A modules are under src/pipeline; synthetic reconstruction/forward cases under src/generator; current model evaluation under src/analysis/current_evaluation.py. Keep this module structure. External source/app/private paths are configured in configs/data.yaml. app.py and some model/inference helpers remain explicitly unimplemented scaffolds, not a working dashboard/agent.

## Data and claims

Use codes only in exported data; the no_names gate logs paths/counts, not matching names. Keep public, derived and generated origins separate. Retain Synthetic - for training only on generated outputs. Never publish raw data, private mappings/truth, credentials or checkpoints. Publish only the approved prepared ZIP.

Use publication/availability cutoffs; targets/hidden truth are never X. Fit preprocessing on training data only. Keep seeds/computation date fixed and missing observations unknown. Do not change thresholds, data or noise after looking at a score. No unsupported height/finishing/roads product enters the observed data.

K5 is screening exposure with assumed monetary inputs, not an assessed contractual fine. Generated visits are not fieldwork. Future what-if context is explicitly frozen, not observed or validated forecasts. Not_distressed does not imply completion or financial health. The rule, not fitted probabilities, selects the operational cycle list.

English for code/docs/helpers; original Arabic complaint text and committee-facing Arabic reason fields are data. Preserve both. Mask text before models/providers; real-text review and actual provider/budget approval remain separate AI tasks.

## Work discipline

Record multi-step work/review/lessons under ignored docs/.internal/plan. Do not upload that internal planning directory. Verify relevant behavior and document evidence before claiming implementation complete. Keep current public docs concise and maintain their links; Git history/local backups preserve superseded material.
