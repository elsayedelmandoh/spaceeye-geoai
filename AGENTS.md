# Repository working guide

## Git workflow

- Work and commit on a feature branch only. Never edit,commit or push directly on main.
- Fetch and review teammates' changes before publishing. Use pull requests;never force-push or overwrite unreviewed work.
- Use the configured human Git author/committer identity. No assistant attribution or co-author trailers.

## Current scope and references

- SpaceEye monitors12coded R7compounds. R8is out of scope. Inspection capacity is4.
- Product design: docs/requirements/01-specs.md. The team retired docs/project-definition/03-dataset.md; use current data contracts rather than restoring it.
- Actual implemented data: data/HANDOFF.md,IMPLEMENTED_DATA_SPEC.md,DATASET_CONTRACT.md and current reports/dictionaries.
- Component inputs: data/COMPONENT_DATA_PROTOCOL.md. Retired docs/plan drafts must not be restored.
- Keep repository instructions current;Git history and external local backups retain superseded material.

## Data and implementation

- Use uv and the checked-in lockfile;Python>=3.12. Run uv sync --locked for setup.
- Real sources,raw outputs and private evaluation truth live outside the repo under Project;paths are in configs/data.yaml.
- Only the explicitly approved prepared team bundle is distributed in releases/ready-data. Never publish raw inputs,name maps,hidden answer keys,credentials or model checkpoints.
- Distinguish public observations,derived indicators and generated assumptions. Generated products carry Synthetic - for training only.
- Keep codes only in outputs. Mask phone text. Never use private truth to repair observations or as model features.
- Use publication/availability cutoffs. Unknown observations stay unknown. Fit preprocessing only on training data.
- Preserve module structure: src/pipeline for data,src/generator for simulation,src/analysis for evaluation.
- Financial fine rates,allocation dates and simulated visits are assumptions,not actual contracts,assessed fines or fieldwork.
- No post2024height or finishing product was approved by the prior experiments.

## Validation and communication

- Maintain docs/requirements/02-team-roles-and-tasks.md after each verified implementation. The team lead defines the main checkbox as implemented/ready for review; tick the separate Review accepted checkbox only after an independent review recorded in logs/review-NN.md (or the PR), then set the label to "Done; review accepted". Record the log, date, related commits and caveats on the task and keep its other information; the board names no agent, model or lane.
- Keep evidence links and docs/REMAINING_TEAM_TASKS.md in sync. Do not sign a review without a recorded review log, mark partial tasks complete, or restore superseded scope from an older pasted task board.

- Relevant tests: uv run --locked --offline pytest -q. Lint touched code with ruff;check diffs before commit.
- Data-only build: python -m src.pipeline.complete_data. Two-build delivery: python -m src.pipeline.delivery.
- Component preparation: python -m src.pipeline.component_data. None of these component tasks requires new model fitting.
- Full src.pipeline.run_all and src.pipeline.release include existing fitting/evaluation;do not rerun them for documentation-only edits.
- Current end-to-end entry: python -m src.pipeline.team_run --full. Current evaluation protocol/results: data/EW_PROTOCOL_CURRENT.md and EW_REPORT_CURRENT.md. Current target is binary distressed/not_distressed; completion prediction is removed by the team lead. See data/BINARY_SCOPE_DECISION.md.
- Record multi-step plans/review and lessons in docs/.internal/plan;publish current team-facing status in data.
- Supporting documentation,code and helpers are English. Original Arabic complaint text remains data.
- Keep scope focused. Delegate a read-only review when useful;do not duplicate its work. Do not claim completion without execution evidence.
