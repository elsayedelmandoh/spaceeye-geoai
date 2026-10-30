> Current partial-task extension (28 October 2026): Arabic exports, full-run reproducibility and current observed-class diagnostics are now implemented. Read [PARTIAL_TASKS_CLOSURE.md](PARTIAL_TASKS_CLOSURE.md). Older no-fitting statements refer to the base data-only delivery. Binary distress prediction is the approved scope; no completion class/probability remains.

# Dataset: SpaceEye R7 final data contract

Updated: 28 October 2026. Implementation: [IMPLEMENTED_DATA_SPEC.md](IMPLEMENTED_DATA_SPEC.md). Handoff: [HANDOFF.md](HANDOFF.md).
User-requested imported-spec extension is implemented by src.pipeline.complete_data. Current handoff: Project/DATA_COMPLETION_FROM_SPECS.md. The binary dataset below is retained as historical evaluation evidence; the expanded dataset is the current data deliverable.
Latest missing-data extension: fine_assumptions.parquet also stores generated allocation dates bounded by the earliest public/observed anchor and vintage-based prices. Retrospectively generated allocation dates are excluded from X/public K6. Quarterly land values prefer already-available generated installments over the independent estimate. Optional50%discount and12-month scheduling amounts are separate scenarios gated at the2024-11-18news publication, with no universal entitlement or known expiry claimed. Exact1%monthly fine and6–18month allocation lead remain unsupported assumptions. Sources/limits: configs/synthetic_sources.json. Calibration context published in2026 is retrospective, not a fact available at old model cutoffs.
Generated tables and scenario paths carry **Synthetic - for training only**.

## Locations and origin

- Project/real_data: retained public sources, audits and experiment evidence.
- Project/app_data/raw: coded source copies.
- Project/app_data/real: public-observation/derived tables and run/quality logs.
- Project/app_data/sim: deliberately dirty historical simulation, realism checks, dictionaries and manifest.
- Project/app_data/sim_clean: prepared simulation and quarantined observations, quality report and manifest.
- Project/app_data/scenarios: separate hypothetical forward financial paths, initial assumptions, history and manifest.
- Project/app_data/ew: evaluation outputs and aggregate training-dataset summary.
- Project/private: code/name mapping, reconstruction truth, defects, training table and its metadata.
- Project/app_data/spaceeye.duckdb: R1 real/indicator/log tables only, not all simulation or private tables.

Real = source observation or published statement; derived = a documented calculation; generated = a simulation or unsupported register assumption; key = identifier.
A genuine statement is not an independently verified physical completion measurement.
Register fields have adjacent origin columns where values can be generated. Boundaries are reviewed working polygons, not legal survey boundaries.

## Public and derived tables

| Table | Grain | Current size | Principal contents |
| --- | --- | ---: | --- |
| compounds | compound | 12 | code, developer_code, district, land area/origin, floors/origin, coverage, BUA, units/origin, cover class, first deadline/publication, boundary confidence/area, handover publication |
| compound_boundaries.geojson | compound | 12 polygons | coded geometry and provenance |
| sat_quarterly | compound × quarter | 516 | 2016Q1–2026Q3; built probability, image count, DW class shares, K1, A/active, K2/K4, legacy start and new descriptive start fields |
| sat_yearly | compound × year | 132 | vegetation, built cells, mean/p90 height, share above20m, height/vegetation origin |
| statements | published fact | 57 | code, kind/subtype/detail, published date, scope, period, value, qualifier, record_id/verdict/origin |
| eval_outcomes | real backtest case | 6 | original promise, outcome and publication dates, delay, evidence gate |
| drivers_monthly | month | 45 | Jan2023–Sep2026; FX, rates, rebar, cement, material index, shock/calendar/weather |
| rules | sourced rule | 19 | source/article/text/value/unit/origin; no inferred project fine |
| kpi_values | compound × cutoff | 372 | 2019Q1–2026Q3; A, K2/K3/K4, start states, K6, may_be_complete, priority, reason, cycle rank, run identity |
| quality_checks_log / run_log | check / step | run-specific | rule, owner, action, result, impact and lineage |

Height values used by the application are OBT2016–2023 and the approved v4 estimate for2024. Later rows do not imply approved later heights.
The yearly height product is a model/observation product, not ground surveying or a per-building ±2m guarantee.
Later model experiments are closed and none is published:
- The v8/v9 Sentinel-2 building and height model (selected combiner C7) gives built area and heights for 2024-2026 as **candidates only**. It failed the independent Wayback test: agreement 0.69 for 2023->2025 and 0.74 for 2025->2026, against a gate of 0.80.
- The v10 two-year change-head retrain lost the pre-registered 2 % rule against C7 on 2022 validation (S 4.628 vs 4.677) and was not tested further.
- Finishing detection (Sentinel-2 0.674; Qwen3-VL-32B 0.559) and paved-road timing (1 of 12 events) were rejected.

The candidate values stay outside this repository with their protocols and results (`Project/real_data/29_height_final/`). A coded R7 copy for optional display is in `app_data/candidates/compound_satellite_candidates_2024_2026.csv` (36 rows). It is not part of the ready bundle and is never an input to indicators or models. Any display must label it "candidate, not validated".
The current accepted activity mode is q2hold; the quarterly feature table is not an independent fresh physical observation every quarter.

## Start fields

| Field | Meaning |
| --- | --- |
| started, start_quarter | Legacy evaluated rule state; includes published launch/delivery events. Retained for K2/priority comparability. |
| observed_started | Four consecutive quality-valid active quarters, or an already-published delivery event; launch alone excluded. |
| observed_start_quarter | First quarter established by that evidence, visible only when the evidence is known. |
| observed_start_source | activity_run or published_delivery. |
| launch_date_asof / launch_first_published | Earliest known launch event date/publication, using only facts published by the cutoff. |
| start_observation_sufficient | Positive start evidence or complete assessable history from known launch through cutoff. |
| start_reference_date_asof / start_reference_published / start_reference_source | Earliest known launch/promise reference. Promise fallback uses publication date, not future delivery date. |
| K6 | Months since that reference without confirmed observed start; null when start is confirmed or evidence/reference is insufficient. >24 adds priority1;13–24 adds priority2. |
| K5_no_start_months / K5_post_grace_months / K5_overlap_months / K5_months | Cumulative research screening months, union of conditions. Stops accruing at first published handover. Unknowns stay null; not a contract/legal fine assessment. |

Do not equate K6 with a finding that construction never happened. Missing images remain unknown.
K6 enters the requested priority policy; capacity is4. K5/K6 enter the expanded data-only feature schema, not the frozen binary evaluation schema.

## Historical simulation

One month is one row per compound, January2023–September2026. Warmup starts2017.
The raw financial table has540 unique months plus intentionally duplicated reports.
Raw complaints, fake phone text, unknown codes and incorrect dates are documented test inputs, not clean operational observations.

fin_monthly fields:

- code, month: keys.
- planned_pct, reported_pct, report_date: planned/reported execution and availability time.
- units_sold, avg_price_egp, collections_egp: sales and payments.
- cover_required_egp, cover_balance_egp, cost_to_complete_egp: recorded coverage and remaining reported cost.
- land_due_egp, land_paid_egp, land_months_late: land payments and age of arrears.
- roads_paved_share, meters_active, kwh: generated paving, electricity meters and consumption.
- status_level, warning_issued: simulated administrative observations; excluded from ML X.

complaints fields: complaint_id, code, created_at, channel, category, text_ar.
Electricity meters only; there is no generated water-meter table.

The reconstruction matches public statements and known handovers with seasonal/noisy progress and imperfect reports.
This anchored historical path is not generated by a causal cash-to-progress feedback loop. Use the separate forward scenario engine for that mechanistic question.

## Prepared simulation

sim_clean/fin_monthly.parquet preserves the monthly financial schema with unique keys and repaired detectable thousand-EGP balances.
A report date must belong to its recorded month. Invalid reported_pct/report_date observations become null; no replacement date is invented.
Duplicate monthly rows keep the first recorded row.

sim_clean/complaints.parquet contains known-code/time-valid complaints with phones masked.
quarantine_complaints.parquet retains rejected records with dq_reason; phones are masked there too.
rejected_reports.parquet retains invalid report observations and their rejection reason.
quality_report.json records counts, checks and exact input/source hashes. Its launch-validation limitation is explicit.
Public evidence does not supply every launch date, so not all planted pre-launch complaints can be identified independently; no hidden truth is used to repair them.

The raw simulation is retained alongside these outputs. Its six planted defects are not silently removed from the exercise data.

## Private truth and training

### Current expanded data deliverable

private/ml_dataset_extended.parquet:180rows over15cutoffs (2023Q1–2026Q3),40declared features, keys code/developer_code/quarter/qi/month. Includes the proposed K1/K4, vegetation, approved height, K5/K6, completion-context and financial observations. No failed finishing feature is invented. See ml_dataset_extended_metadata.json and dictionaries/ml_dataset_extended.md for exact X, origins, missingness, source hashes and labels.

Both label_distress_next_6m and y_outcome_6m are evaluation-only encodings of the same binary next-six-month distress event. y_outcome_6m is distressed/not_distressed; handover without distress maps to not_distressed. Censored targets are null. Already-handed-over cutoff rows are excluded from the modelling cohort; source handover facts remain context.

Expanded complaint rate uses complaints over90days per1000units SOLD at cutoff, with own-history percentile requiring12prior valid months. The older binary experiment used total register units; its results are not copied onto this schema.

sim_clean/fin_quarterly.parquet:180rows, flows summed over the quarter, stocks at its last month, latest valid supervisor report available by cutoff, K5/K6 and generated-only fine EGP. sim_clean/fine_assumptions.parquet stores12explicit assumed land values and the illustrative1%monthly rate. No real fine amount is asserted.

data_completion/inspection_capacity.csv stores quarter/code selections for capacities2/4/6. It changes selection only, never levels, finance or progress. cycle_list.csv is the current latest selection; ops_visits_template.csv is an empty future-data schema, not fabricated visit records.

### Frozen binary evaluation data

answer_key: hidden monthly progress/cash/debt/arrears/handover/occupancy/distress, story, future-distress label and censor flag.
answer_key_complaints: correct code/category/cause and planted defects. Both are evaluation-only.

private/ml_dataset.parquet is a persisted binary training dataset, one row per compound-quarter.
Keys: code, developer_code, quarter, month. X is exactly the features listed in ml_dataset_metadata.json:

- Public-derived: A, active, K2, K3, level, started, d_A, d_K2.
- Generated-operations-derived: cover_ratio, cover_req0, cover_ctc, land_late, cmp_rate90, cmp_pctl, gap, report_age,
  meters, kwh_per_meter, kwh_ratio, plus six-month changes of cover_ratio, cover_ctc, land_late, cmp_rate90, gap, meters and kwh_ratio.

y = label_distress_next_6m: distress in any of the next six months, excluding the cutoff month.
label_censored marks incomplete horizons; y is null for those rows.
No story, true_*, administrative warning/status, fitted probability or answer-key feature enters X.

Current design:132 rows over11quarterly cutoffs, 2023Q4–2026Q2.
Training through2024Q4; embargo2025Q1; labelled time test2025Q2–2026Q1; 2026Q2censored.
The exporter records exact split/class/missing counts, dtypes, source hashes and feature groups.
The public ew/dataset_summary.json contains aggregates only, not private row-level labels.
This historical experiment remains binary. The expanded current deliverable supplies binary targets and current fixed-split model comparisons.

## Forward scenarios

scenarios/history.parquet preserves raw observations through the cutoff. initial_state.parquet records the assumed state.
paths.parquet holds scenario_id, code, cutoff, month, progress/capacity, collections, released/restricted cash, costs/spending,
opening/closing cash and debt, credit limit, obligations/arrears and accounting residuals.
summary.csv compares final state with baseline. assumptions.json and provenance.json record assumptions and hashes.

Default cutoff2025-03, horizon18months. Three paths: baseline, collections−25% for6months, imported cost impact of a30% FX shock.
The same initial state and productivity draws are used for comparisons.
Progress is constrained by construction spending after declared obligations and finite credit.
Financial guarantees are never treated as available cash. No future observations or private truth determine the path.

Working cash, opening bank debt/arrears, release fraction and future capacity/collections are illustrative declared assumptions.
No observed causal effect, legal fine, handover date or occupancy forecast is claimed.
Scenario outputs are generated and separate from the historical training labels.

## Validation and rebuilding

    uv run --locked --offline --with matplotlib python -m src.pipeline.complete_data

This reuses saved observations and builds the requested data extension without model fitting, then runs a data-only release audit. Historical evaluation is marked explicitly. No live Earth Engine pulls.
release_audit.json and the output manifests are the completion evidence. Unresolved calibration or coverage flags remain visible.
The unchanged real-case backtest and regenerated binary results are reported honestly with event counts; a handful of synthetic positives is not operational accuracy.

K5 amounts are assumed policy scenarios, not contract fines. Binary labels are generated evaluation targets, not real-world diagnoses. K6 thresholds and capacity4 were explicitly requested before rebuilding. No newly approved post2024height is introduced.
