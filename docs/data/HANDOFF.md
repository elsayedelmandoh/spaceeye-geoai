# R1/R2 data handoff

Current release: 28 October 2026. Scope: 12 coded R7 compounds. Data preparation only; no dashboard, agent or new model evaluation is included.

Delivery is merged into main at `b397f5e`,following the reviewed branch `feat/r1-r2-data-finalization`. Final evidence:47tests,touched-code lint and whitespace checks PASS;21table dictionaries;129equal artifacts across two data-only builds;protected inputs unchanged. See the completed delivery plan for integration decisions and commit history.

## Read first

- [Small-task additions and remaining product work](SMALL_TASKS_STATUS.md), including technical operations, handover, quality, governance, responsible use and the proposed ACUD data request.

- [Data sources and generation logic](DATA_SOURCES_AND_GENERATION.md),with coded source registry,input hashes and exact parameter exports.

- [Implemented specifications](IMPLEMENTED_DATA_SPEC.md) and [dataset contract](DATASET_CONTRACT.md).
- Generated [R1 report](R1_REPORT.md), [R2 report](R2_REPORT.md), [actual-schema dictionaries](dictionaries/README.md), and [two-build evidence](REPRODUCIBILITY.json).
- [Delivery plan](DELIVERY_PLAN.md), including remote-integration decisions.

The full product specifications in `docs/requirements/01-specs.md` and `docs/project-definition/03-dataset.md` are retained from the team's latest main. Their older counts, percentages and future deliverables are not proof of the current implementation. This directory is the current data release contract.

## Data locations and boundaries

The approved prepared team bundle is now available under [releases/ready-data](../../releases/ready-data/README.md), including a separate training export and simple English usage instructions. Use it directly without the original external input folders. It excludes raw inputs, hidden answer keys, name mappings, models and credentials.

For rebuilding the full source pipeline, edit `configs/data.yaml` paths on another machine and obtain the additional external inputs separately. Those paths currently point to `Project/real_data`, `Project/app_data` and `Project/private`; the complete source/private directories are not committed. Only the explicitly approved ready-data ZIP is an exception.

Public/derived R1 tables live in `app_data/real`. Deliberately dirty historical operations stay in `app_data/sim`; cleaned and quarterly tables in `app_data/sim_clean`. Financial scenarios are separate in `app_data/scenarios`. Every generated product is labelled `Synthetic - for training only`.

The current expanded data table is `private/ml_dataset_extended.parquet`: 180 rows, 40 explicitly listed features, binary and three-class targets. Metadata records keys, origins, censoring, source hashes and exact feature names. The older `ml_dataset.parquet` (132 rows, 26 features) belongs to the historical binary experiment.

## Important implementation decisions

1. Legacy `started` still feeds K2; separate observed start excludes marketing launch and requires valid activity persistence or published delivery. K6 uses a known launch/promise publication and may remain null with missing evidence. K6 now enters priority at the imported 13/24-month thresholds.
2. K5 stores the union of no-start/post-grace screening months, not duplicate months or verified contractual fine eligibility. EGP uses assumed land value and a configurable illustrative 1% monthly rate. It is not a cash deduction in the historical/forward engines.
3. Synthetic allocation dates respect evidence anchors but are retrospectively calibrated and excluded from model X/public K6. Price assumptions depend on contract vintage; available generated installments take precedence. News supports context, not exact individual contracts. See `configs/synthetic_sources.json`.
4. Relief at 50% and 12-month scheduling are optional scenarios after the 18 November 2024 publication, not universal permanent entitlement.
5. Inspection capacity is 4, with stored selections for 2/4/6. Only eligible levels 1–3 are selected. Capacity does not change levels, cash or progress.
6. Financial flows, including monthly units sold, sum over a quarter; stocks use its last month. The expanded complaint diagnostic divides 90-day complaints by units sold in the cutoff month, not cumulative sold inventory; do not describe it as buyer incidence.
7. Three-class labels are data only: future distress takes precedence; completion requires new full-project handover. Censored targets are null and already-completed rows are separately flagged. There are zero completed training examples and one completed time-test example. No classifier was fitted for this schema.
8. Historical progress is anchored reconstruction. The independent forward engine uses cutoff-only reports/finance, common productivity draws, finite assumed liquidity/credit and accounting invariants. It does not forecast handover or occupancy and need not show an effect when cash does not bind.

## Validation and commands

```powershell
uv sync --locked
uv run --locked --offline pytest -q
uv run --locked --offline python -m src.pipeline.complete_data
uv run --locked --offline python -m src.pipeline.delivery
```

The last command performs two complete **data-only** builds, compares all scoped artifact hashes and logical DuckDB table contents, protects saved raw/simulation/model/legacy evaluation files, and refreshes current reports/dictionaries. It does not fit models. Aggregate reproducibility evidence is tracked here; full per-file hashes stay local.

`src.pipeline.run_all` and `src.pipeline.release` include existing model fitting/evaluation. Do not use them for a documentation-only or current data-only refresh. If you deliberately change data behavior, re-run relevant tests and delivery evidence after that change.

The prior N=8 binary scores are historical: 4/4 positive rows for the combined rule versus 3/4 for satellite-only, with one independent new onset. They do not validate capacity 4, the expanded feature schema or a three-class classifier. The historical real-case backtest remains 1/6 after-start and 0/6 at cutoff. Existing 2019Q2 coverage FLAG remains visible; missing data and failed research are not erased by a passing release audit.

The saved R1 `run_log` and `quality_checks_log` retain the full-pipeline run history. Current data-only lineage/gate results are in `data_completion/audit.json`, `data_completion/quality_checks.csv` and `release_audit.json`; the delivery does not relabel old fitting logs as new fitting runs.

## Work outside this delivery

Component data is now supplied by src.pipeline.component_data:100gold-labeled feed texts,a separate296-text complaint benchmark,180inspection contexts,58explicitly synthetic visit exercises and648hypothetical financial-priority rows. See COMPONENT_DATA_PROTOCOL.md and the current ready-data bundle. Existing source tables are unchanged;no hidden cause/answer key enters inspection inputs. Generated visits are not actual fieldwork or independent validation.

Remaining product work: UI,agent/complaint-classifier implementation,three-class fitting/model comparison at capacity4,actual field data collection and deployment. Financial-to-priority DATA now exists under the declared hypothetical frozen-context/projected-B5rule;it is not validated operational forecasting. Actual contractual rates/eligibility and allocation records remain unknown despite synthetic stand-ins.

Published heights remain OBT 2016–2023 and the approved v4 estimate for 2024. Later height/finishing/roads experiments did not justify a new approved product. Earlier local handoff contains server/archive history; no new server training was launched for the current data updates.

## Collaboration and preservation

Integration preserves the team's richer full product documents, renamed project metadata, added dependency group and `CLAUDE.md`. It also retains R7 filtering and previously validated simulation parameters from the local work. Archived plans remain available and clearly marked. Never force-push, overwrite unreviewed teammate changes, or commit private tables/secrets. Commits use the maintainer's configured human Git identity without assistant attribution.
