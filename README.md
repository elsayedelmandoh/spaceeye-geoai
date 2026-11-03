# SpaceEye: R7 inspection priority observatory
رادار العاصمة الجديدة: شركة تمتلك مدينة. (New Capital radar: a company that owns a city.)

**Observed imagery:** [view/rebuild guide](data/imagery/README.md), [source comparison](data/IMAGERY_COMPARISON.md) and [frame metadata](data/imagery/wayback_timeline.csv). The 100 Wayback / 528 Sentinel figures stay outside Git; the numerical v6 release is separate.

**New device or review:** follow [REVIEW_SETUP](docs/REVIEW_SETUP.md). Run `uv sync --locked`, then `uv run --locked python -m src.pipeline.setup_review`. Paths are checkout-relative; `SPACEEYE_DATA_ROOT` relocates the workspace without requiring a specific drive. The [84-file source manifest](data/REBUILD_INPUTS.csv) and source-cache tool cover full rebuilds.

[Download the current v7 data](releases/ready-data/SpaceEye_R7_READY_DATA_2026-10-31_v7.zip?raw=1) ? [Data guide](releases/ready-data/DATA_GUIDE.md) ? [Task board and human reviews](docs/requirements/02-team-roles-and-tasks.md) ? [Remaining work](docs/REMAINING_TEAM_TASKS.md)

SpaceEye supports deciding which coded R7 compounds the inspection committee should visit first. The current delivery is a prepared-data/rule/model workflow. The five-screen dashboard, inspection agent, real visit form and final presentation remain separate tasks.

## Current scope

| Item | Current state |
| --- | --- |
| Geography | 12 coded R7 compounds; R8 excluded |
| Public real-case check | Six cases; one detected under the after-start reading, zero at the frozen cutoff; the target of five cases was not met |
| Operational capacity | Four eligible inspections; comparisons at two/four/six |
| Training export | 180 compound-quarter rows, 40 declared features |
| Classifier | distressed / not_distressed in the next six months; completion is not predicted |
| Evaluation | 96 primary training rows, 48 time-test rows, fixed parameters and a separate chronological developer holdout |
| Heights | Available OBT observations through 2023 and approved 2024 estimate; contextual, without a fixed error guarantee |

Use [the current report](data/EW_REPORT_CURRENT.md) for method-specific counts and random comparison. Synthetic repeated-quarter results do not establish real-world accuracy. Published statements, derived indicators and generated assumptions have separate origins. Generated outputs retain **Synthetic - for training only**. No real compound or developer name is published.

## Indicators and decisions

A is the derived building-activity score. K2 counts inactivity after the legacy start state; K3 measures elapsed months after the first available announced deadline; K4 records assessability. K6 measures time from a known launch/promise reference without confirmed observed start and remains unknown when evidence is insufficient. K5 is screening exposure, not verified contractual fine eligibility.

The rule uses the worst applicable K2/K3/K6 signal, assessability and the may-be-complete cap. Selection uses eligible levels 1-3, then level, descending K2/K3 and code. Project thresholds live in configs/data.yaml. Illustrative monetary fines and financial/priority what-if outputs are generated assumptions, not actual assessments or forecasts. See the [implemented specification](data/IMPLEMENTED_DATA_SPEC.md).

## Use the ready data

Extract the complete v6 ZIP and open its README.md. Use CSV, Parquet or spaceeye_ready.duckdb; run verify_package.py to check the file manifest. Only the current ZIP is distributed in this checkout. Earlier files remain in Git history and a local retirement backup.

The package supplies Arabic committee lists, complaint-training corpora, 180 inspection contexts, synthetic visit exercises, current binary predictions and S1/S2/S3 handoff. Contexts are not finished inspection reports; synthetic visits are not fieldwork. Raw inputs, private name mappings/truth, credentials and checkpoints are excluded.

## Rebuild from configured local inputs

```powershell
uv sync --locked
uv run --locked --offline python -m src.pipeline.team_run
```

The command prepares cached data and fits current small binary diagnostics. It requires the external inputs/private evaluation data configured in configs/data.yaml; the ready ZIP alone is sufficient for reading and interface development, but not source rebuilding.

`python -m src.pipeline.team_run --full` additionally fits/rebuilds Track A. With Make installed: `make data` is data-only, `make current` is the cached current workflow, and `make run` includes full Track A fitting. Tests: `uv run --locked --offline pytest -q`. Run appropriate checks after behavior changes; do not refit models for documentation-only work.

The historical early_warning/release modules remain for saved experiment audits and shared dependencies. They are not the current team entrypoint. Current operations and monitoring are documented in [technical-track-a](docs/deliverables/technical-track-a.md).

## Documentation and collaboration

- [Current handoff](data/HANDOFF.md), [dataset contract](data/DATASET_CONTRACT.md), [sources and generation](data/DATA_SOURCES_AND_GENERATION.md).
- [Product requirements](docs/requirements/01-specs.md), [actual repository structure](docs/project-definition/08-structure.md).
- [Approved binary scope](data/BINARY_SCOPE_DECISION.md), [model card](docs/deliverables/method-card.md), [package validation](data/READY_V6_VALIDATION.json).

Work only on feature branches/PRs, preserve teammates' work and use the configured human Git identity. A checked main task means implemented/ready for review; its separate review checkbox requires actual human acceptance. Keep evidence and the remaining-task handoff synchronized. Current unresolved work is not represented by empty placeholder deliverables.

## Authors

- **elsayed elmandoh** - NLP / LLM Engineer
- **verina fouad** - Applied AI / Machine Learning Engineer
- **ahmed abdelhamid** - Generative AI Engineer
- **nada shady** - AI Engineer
- **salma magdy** - Data Scientist

[![linkedin](https://img.shields.io/badge/elsayed-linkedin-0077b5?style=for-the-badge&logo=linkedin&logocolor=white)](https://www.linkedin.com/in/elsayed-elmandoh-b5849a1b8/)
[![linkedin](https://img.shields.io/badge/verina-linkedin-0077b5?style=for-the-badge&logo=linkedin&logocolor=white)](https://www.linkedin.com/in/verina-fouad/)
[![linkedin](https://img.shields.io/badge/ahmed-linkedin-0077b5?style=for-the-badge&logo=linkedin&logocolor=white)](https://www.linkedin.com/in/ahmed-abdelhameed-ai/)
[![linkedin](https://img.shields.io/badge/nada-linkedin-0077b5?style=for-the-badge&logo=linkedin&logocolor=white)](https://www.linkedin.com/in/nadashady/)
[![linkedin](https://img.shields.io/badge/salma-linkedin-0077b5?style=for-the-badge&logo=linkedin&logocolor=white)](https://www.linkedin.com/in/salma-magdy-ml/)
[![github](https://img.shields.io/badge/GitHub-repo-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/elsayedelmandoh/spaceeye-geoai)
