# SpaceEye: R7 Digital Twin and Inspection Priority Observatory

**Team handoff:** [remaining tasks, owners and dependencies](docs/REMAINING_TEAM_TASKS.md).

**Team data:** [download the ready-data ZIP](releases/ready-data/SpaceEye_R7_READY_DATA_2026-10-28_v4.zip?raw=1) and follow the [three-step guide](releases/ready-data/README.md). Includes complaint-classification data,inspection contexts,generated visit exercises and hypothetical financial-priority outputs. No raw downloads or pipeline rebuild are needed.

> Data release, 28 October 2026: R1/R2 now include K5/K6, capacity4, prepared data,180-row/40-feature expanded data and separate financial scenarios. Start with [the current handoff](docs/data/HANDOFF.md), [R1 report](docs/data/R1_REPORT.md), [R2 report](docs/data/R2_REPORT.md) and [delivery plan](docs/data/DELIVERY_PLAN.md). The product design below is retained; it includes work beyond this data-only release.

Graduation project for the New Administrative Capital (ACUD AI Data Lab program). It answers one question: **which compounds in district R7 should the inspection committee visit first this cycle, and why?** The system recommends; the committee decides.

> **Synthetic data - for training only** applies to every generated table, chart and slide. Real public data (satellites, published statements, decrees) is used as published, with its source. Compounds and developers appear as codes only (`C..`, `D..`), never by name.

The full product plan is in [`docs/requirements/01-specs.md`](docs/requirements/01-specs.md); data design is in [`docs/project-definition/03-dataset.md`](docs/project-definition/03-dataset.md). For the implemented R1/R2 release, [the implementation contract](docs/data/IMPLEMENTED_DATA_SPEC.md) and [dataset contract](docs/data/DATASET_CONTRACT.md) identify current behavior and supersede older implementation-status claims.


## Table of Contents
- [Overview](#overview)
- [How it works](#how-it-works)
- [Results so far](#results-so-far)
- [Setup](#setup)
- [Usage](#usage)
- [Project structure](#project-structure)
- [Contributing](#contributing)
- [Authors](#authors)


## Overview
- **Problem:** ACUD follows hundreds of developers and projects with a field review every 3 months; seriously late projects are found late.
- **Goal:** rank R7 compounds by **priority level** so the committee visits the right ones first, with a reason for each.
- **Product:** dashboard + **cycle list** sized to inspection capacity + an **inspection file** per compound + a form to record each visit result.
- **Digital twin (light, compound level):** observed state from satellites and statements, simulated hidden state (finance until ACUD shares its data), and what-if scenarios. Not a 3D or real-time twin.


## How it works

**Track A: images (all real).** Dynamic World, Sentinel-2, Google Open Buildings and published statements give, per compound and quarter:

| Signal | Meaning |
| --- | --- |
| A | activity score: probability the compound is building this quarter |
| K2 | quarters with no activity (after construction started) |
| K3 | months since the **first** announced handover date passed |
| K4 | assessability (enough images, boundary confidence >= 80%) |
| K5 | months in a fine-eligible state |
| K6 | months since launch with no construction start |

**Priority level = the worst of K2, K3 and K6** (no weights): 1 inspect now, 2 inspect this cycle, 3 document review, 4 routine. Thresholds are fixed in `configs/data.yaml` and follow Decree 2184/2022.

**Track B: numbers (generated).** A generator simulates the ACUD data we do not have yet (escrow cover, land arrears, complaints, meters, plan vs reported progress) from each compound's real signals. A classifier (logistic regression vs gradient boosting) learns the outcome in the next 6 months (`distressed` / `completed` / `ongoing`) from Track A outputs + these numbers.

**AI component:** an inspection file agent (code fills the numbers, Gemini writes one paragraph and 3 visit questions, every number is checked against the source) and a complaints classifier with regex masking of personal data before any model.


## Results so far

First build, R7 + R8 (22 compounds), being re-run on R7 only:

- **Backtest:** the satellite rule alone warned at least 6 months early on **1 of 8** real late cases (target 5). The criterion failed: all 8 kept building, and their delay was in finishing and handover, which satellites cannot see.
- **Early warning on generated data:** recall@8 for distressed compounds: **satellites + company data 92%, satellites alone 62%, random 37%.** These are generated data; they show the idea works, not accuracy on reality.

> "Satellites see that buildings exist, but not the delay. ACUD's data completes the picture."


## Setup

Prerequisites: Git, Python 3.12, [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/elsayedelmandoh/spaceeye-geoai
cd spaceeye-geoai
make install            # uv sync + nbstripout git hook
cp .env.example .env    # set MASK_SALT, GEMINI_API_KEY, GEMINI_MODEL
```

**Data lives outside the repo.** Set `paths:` in `configs/data.yaml` to your copies of `real_data` (audited sources, read only), `app_data` (built outputs) and `private` (code map, hidden truth). None of them are committed.


## Usage

```bash
python -m src.pipeline.run_all          # real tables, activity score, KPIs, levels, backtest, quality gates, duckdb (exit 1 if a gate stops)
python -m src.generator.simulate        # generated ACUD data + realism checks (needs run_all first)
python -m src.analysis.early_warning    # Track B early-warning comparison -> app_data/EW_REPORT.md
make test                               # unit tests
```

Two runs give identical outputs (`seed` and `computed_on` are fixed in `configs/data.yaml`). Earth Engine downloads (`src/pipeline/pulls/`) need `uv sync --extra pulls`; their results are already cached in `app_data/raw`. The Streamlit dashboard is the next step.


## Project structure

```text
configs/        data.yaml (paths, thresholds, seed), kpis.yaml, cost_assumptions.yaml
src/pipeline/   Track A: codify -> build_real -> activity -> kpis -> backtest_check -> gates (run_all)
src/generator/  Track B: generated ACUD data (simulate)
src/analysis/   Track B: early-warning features, evaluation, report
tests/          unit tests
docs/           requirements/ (plan), project-definition/ (dataset, constraints)
notebooks/      exploration
```


## Contributing
1. Read `docs/requirements/01-specs.md` section 14 (rules that never break).
2. Work on a branch; run `make lint` and `make test`.
3. No compound or developer name in any output (the `no_names` gate stops the run), no generated number joined into a real table, and every generated output labelled `Synthetic - for training only`.
4. Never change a threshold after seeing a result.


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

Current partial-task extension: [implementation and remaining conditions](docs/data/PARTIAL_TASKS_CLOSURE.md), [capacity-4 diagnostics](docs/data/EW_REPORT_CURRENT.md). Completion has no training support; no operational three-class accuracy claim is made.
