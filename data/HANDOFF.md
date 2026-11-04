# Current SpaceEye data handoff

For a new device, use [REVIEW_SETUP](../docs/REVIEW_SETUP.md) and `python -m src.pipeline.setup_review`. The [seven saved review artifacts](../releases/ready-data/review/README.md) supplement the v6 ZIP; the distributed ZIP is now v7 ([releases/ready-data/README.md](../releases/ready-data/README.md)). Complete source/cache requirements are now listed in [REBUILD_INPUTS.csv](REBUILD_INPUTS.csv): 84 files, including the 13 inputs missed by the historical 71-file inventory. Paths are checkout-relative or relocated with `SPACEEYE_DATA_ROOT`.

Current prepared release: **v7** (file name dated 2026-10-31). Scope: 12 R7 codes, six public check cases, capacity 4. Binary distressed/not_distressed prediction is implemented; completion prediction is removed. See [approved scope](BINARY_SCOPE_DECISION.md).

Observed imagery is a separate local context handoff: [guide](imagery/README.md), [comparison](IMAGERY_COMPARISON.md), [metadata](imagery/wayback_timeline.csv). There are 100 Wayback and 528 Sentinel figures; Esri pixels stay outside Git. The numerical v6 ZIP is unchanged by imagery. T-AH-15 is implemented locally, with independent review pending.

## Read first

- [Download and use v7](../releases/ready-data/README.md); [package validation](READY_V6_VALIDATION.json).
- [Implemented specification](IMPLEMENTED_DATA_SPEC.md), [dataset contract](DATASET_CONTRACT.md), [sources/generation](DATA_SOURCES_AND_GENERATION.md).
- [Task implementation/review board](../docs/requirements/02-team-roles-and-tasks.md), [remaining work](../docs/REMAINING_TEAM_TASKS.md), [current closure](PARTIAL_TASKS_CLOSURE.md).
- [Current model report](EW_REPORT_CURRENT.md), [protocol](EW_PROTOCOL_CURRENT.md), [model card](../docs/deliverables/method-card.md).
- [Scenario contract](SCENARIO_CONTRACT_CURRENT.md), [component inputs](COMPONENT_DATA_PROTOCOL.md), [technical operations](../docs/deliverables/technical-track-a.md).

## What is delivered

The standalone ZIP has 23 ready tables and 293 files, plus an integrity manifest. It contains prepared public/derived observations, generated operations, a separate 180-row/40-feature training export, Arabic cycle lists, complaint corpora, inspection contexts, synthetic visit exercises and hypothetical financial-priority outputs. Only the current v7 ZIP/checksum are distributed in the checkout. Retired material remains in Git history and the external local backup.

Raw sources and private evaluation inputs live outside Git under Project/real_data, Project/app_data and Project/private, configured in configs/data.yaml. Name mappings, hidden truth and checkpoints are never public inputs to the agent or model X.

## Evidence and limits

| Evidence | Scope |
| --- | --- |
| [R1 report](R1_REPORT.md) / [R2 report](R2_REPORT.md) | Saved data audits, counts, assumptions and preparation |
| [Full Track A reproducibility](FULL_TRACK_A_REPRODUCIBILITY.json) | Two full Track A runs; 276 identical manifest entries |
| [Current model reproducibility](CURRENT_MODEL_REPRODUCIBILITY.json) | 13 identical fitted-output files, including local checkpoints and secondary split |
| [Current metrics](CURRENT_MODEL_METRICS.csv) | Primary and developer-holdout views identified separately |
| [Real-case check](BACKTEST_CURRENT.md) | One of six after start; zero of six at cutoff; original minimum five cases not achieved |
| [Defect audit](DEFECT_AUDIT_CURRENT.json) | Six planted defects matched; pre-launch verification is private-generator audit only |
| [Annual coverage](ANNUAL_CONTEXT_COVERAGE.csv) | Missing years/values preserved; heights only through the approved 2024 product |
| [Current ZIP validation](READY_V6_VALIDATION.json) | CRC and all 292 manifest hashes; model contracts are covered by their separate tests/reports |

Latest integrated imagery/v6 test suite: 240 passed (30 October 2026). The 2019Q2 source-event FLAG remains visible. Report rendering does not rerun source checks; freshness is relative to the configured computation date. Different evidence files describe different scoped runs, not interchangeable project-wide certifications.

Labels are generated future distress events, not real-world diagnoses. Not_distressed does not imply completed or guaranteed healthy. Fine rates, allocation dates, land values and relief eligibility are assumptions. K5 never becomes a verified legal assessment. S1/S2 use explicit frozen public context; S3 changes capacity selection only. Generated visits are not field evidence.

## Commands

```powershell
uv sync --locked
uv run --locked --offline python -m src.pipeline.team_run
uv run --locked --offline pytest -q
```

Use team_run --full only when a full Track A refit is intended. The data-only complete_data/component_data commands are documented in the technical guide. The delivery module can generate a fresh scoped data-only two-build proof when needed; old proof snapshots and historical delivery narratives have been retired from current documentation.

## Still to implement

The Streamlit dashboard (app.py: five screens, `ops_visits` form, floating button to the hybrid RAG chatbot in chatbot/, knowledge in chatbot/knowledge/) and the presentation/intro video under docs/deliverables/01-presentation and 02-video are implemented; items still open (for example the stored inspection reports, rehearsals and pending reviews) are in [REMAINING_TEAM_TASKS](../docs/REMAINING_TEAM_TASKS.md) and the original-ID task board. Existing evidence does not auto-sign reviewer acceptance. Actual contractual inputs, water/gas connection data and independent real field validation remain unavailable unless explicitly obtained or scoped.
