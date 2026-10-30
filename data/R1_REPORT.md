# R1 current release report,28October2026

Scope:R7only,12coded compounds. This supersedes historical26October reports.

| Table | Rows |
| --- | ---: |
| compounds | 12 |
| drivers_monthly | 45 |
| eval_outcomes | 6 |
| kpi_values | 372 |
| quality_checks_log | 11 |
| rules | 19 |
| run_log | 14 |
| sat_quarterly | 516 |
| sat_yearly | 132 |
| statements | 57 |

## Implemented policy

K2retains the evaluated legacy start convention. Separate observed start requires four assessable active quarters or published delivery. K6uses first known launch/promise publication, changes priority at13/24months and stays null when evidence is insufficient. K5is union-of-months screening exposure, not assessed contractual eligibility. Capacity4;capacity scenarios2/4/6select eligible priorities1–3. No generated EGP amount enters public KPI tables.

## Quality and evidence

- source: **PASS**;0 bad of 57.
- completeness: **PASS**;12 of 12 assessable at 2026Q3; 97.7% of all compound-quarters.
- validity: **PASS**;0 violations.
- uniqueness: **PASS**;0 duplicates.
- consistency: **PASS**;0 stray codes; counts ok=True.
- freshness: **PASS**;last quarter 2026Q3, 1 quarter(s) before 2026-10-30.
- separation: **PASS**;0 columns without origin, 0 generated tables.
- data_or_city: **FLAG**;1 quarters flagged: 2019Q2.
- stuck_series: **PASS**;0 stuck points.
- veg_pull_check: **PASS**;max diff 0.0000 on 24 rows.
- no_names: **PASS**;76 patterns, 344 files; files with a match: none.

DuckDB matches current real tables. The saved real-case backtest is documented in BACKTEST_CURRENT.md; full Track A reproducibility is in FULL_TRACK_A_REPRODUCIBILITY.json. This data-only report writer does not rerun fitting or retune the criterion. Activity mode remains q2hold; published heights are OBT where available (none for 2016-2019; 5-11 of 12 compounds per year for 2020-2023) and the v4 estimate for 2024 (10 of 12); see data/ANNUAL_CONTEXT_COVERAGE.csv. Public sources were not all re-opened during this release.

## Rebuild

`uv run --locked --offline python -m src.pipeline.complete_data` rebuilds from saved observations without fitting. `src.pipeline.delivery` verifies two data-only builds and writes this report/dictionaries. Full `src.pipeline.run_all` is separate and includes fitting. Source/code hashes and limitations are in local release_audit.json.
