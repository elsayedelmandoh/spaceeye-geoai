# Dataset: SpaceEye (R7/R8 Inspection Priority Observatory)

Last updated: 25 Oct 2026 · Reference plan: `docs/plan/project-plan.md` · Generator design: `docs/plan/synthetic-data-plan.md` · Background and sources: `docs/plan/data-report.md`

> **In three lines**
> 1. Track A works on **29 real, named compounds in districts R7 and R8** of the New Administrative Capital, using public data only (satellite, statements, laws). No generated number touches a real compound.
> 2. Track B is a demo on **33 virtual twins** with **8 generated tables** that mirror data ACUD holds internally (escrow, installments, supervisor reports, meters, complaints, warnings). Every generated file is labelled **"Synthetic - for training only"**.
> 3. Every real fact has a source, a link and a quote, and was re-checked by an independent reviewer: **1,009 of 1,026 records usable (98%)**, 17 excluded, 0 invented.

The instructor approved the use of real public data and real compound names. No internal ACUD data is used.

---

## 1. Origin types (shown on every column, chart and slide)

| Mark | Type | Meaning |
| --- | --- | --- |
| 🟢 | Real | Published or observed, with source, link and quote; reviewed |
| 🔵 | Derived | Computed by us from real data with a documented method |
| 🟠 | Generated | Produced by the simulator for the virtual twins (Track B only) |
| 🟡 | Assumption | A number with no published reference, written in `cfg_assumptions.yaml` |
| ⚪ | Key | Identifier or join column |

A developer statement is 🟢 (the statement is real) but it is not an independent measurement: we always write "the developer announced".

---

## 2. Storage format

| Layer | Format | Why |
| --- | --- | --- |
| Inputs (real and generated tables) | **Parquet**, one file per table, in `data/raw/` and `data/sim/` | Typed columns (dates stay dates), small, fast, readable by pandas and DuckDB with no import step |
| Small hand-edited inputs | CSV (`locations_team.csv`, `cfg_*.yaml`) | Easy to edit and review in a pull request |
| Geometry | GeoJSON (`compound_boundaries.geojson`, EPSG:4326) | Standard for maps and Streamlit |
| Pipeline outputs | **One DuckDB file** `data/spaceeye.duckdb` (`kpi_values`, `cycle_list`, `run_log`, `quality_checks_log`, `ops_visits`, `ai_verification_log`) | Delete-then-insert per `run_id`, SQL with `$asof`, one file for the dashboard |

DuckDB reads Parquet in place: `SELECT * FROM 'data/raw/r_dynamic_world_quarterly.parquet'`.

**The data stays outside the repo.** `data/` is git-ignored. The repo holds code, configs, dictionaries and this document. Real files are copied from the team's shared folder (`real_data/`) by `src/ingest.py`; generated files are rebuilt by `simulate.py` from the fixed seed.

---

## 3. Inventory

| Group | Tables | Rows (approx.) |
| --- | --- | --- |
| A. Real (Track A + calibration of B) | 19 | ~70,000 (most in building heights) |
| B. Generated (Track B) | 8 + 2 side files | ~12,000 |
| C. Pipeline and operations | 7 | grows with each run |

### Removed or merged (and why)

| Item | Decision | Reason |
| --- | --- | --- |
| `r_satellite_monthly` (Sentinel-2 NDBI, spread) | Removed (archived) | Raw Sentinel-2 indices are out of scope; Dynamic World replaces them; v1 had an offset error |
| `r_weather_events` | Merged into `r_weather_daily` (`dust_event_confirmed`) | Weather is only a "review the scene" flag; heat waves are out of scope |
| `r_developers` | Merged into `r_compounds` (`developer_name`) | Display only; size-based checks are out of scope (no reliable size data) |
| `dw_grass_trees`, `dw_water` in `r_observed_stage` | Removed | Tested and failed (see section 4.8) |
| `built_label_share` in Dynamic World | Removed | The plan uses `built_prob_mean` only |
| `inflation_yoy` in `r_macro_monthly` | Removed | Inflation is out of scope |
| `dst_flag` and the daylight-saving clock defect | Removed | All data is monthly or quarterly; the clock gate was dropped in the plan (section 16) |
| 3 unnamed projects and 9 projects outside R7/R8 | Out of `r_compounds` (archived) | Scope is the 29 named R7/R8 compounds |

---

## 4. Real tables (group A)

Time horizon: satellite series **2016-Q1 to 2026-Q3** (full history kept for the compound charts); statements and events as published; simulator drivers Jan 2023 to Sep 2026. Only records with verdict `CONFIRMED` or `CONFIRMED_MINOR_FIX` are loaded.

### 4.1 `r_compounds` (1 row = compound, 29 rows)
| Column | Type | Unit / values | Origin | Meaning |
| --- | --- | --- | --- | --- |
| `compound_id` | str | R7-P01.., R8-P01.. | ⚪ | Project id from the source register |
| `name_ar`, `name_en` | str | | 🟢 | Published name |
| `developer_name` | str | | 🟢 | Developer as published |
| `district` | str | R7 / R8 | 🟢 | Verified district |
| `land_area_value`, `land_area_unit` | float, str | feddan / acre / m² | 🟢 | Area exactly as published |
| `land_area_m2` | float | m² | 🔵 | Converted (1 feddan = 4,200.83 m², 1 acre = 4,046.86 m²) |
| `units_total` | int | units | 🟢 | Published unit count (null if unknown) |
| `launch_date` | date | | 🟢 | Launch (null if unknown) |
| `promised_delivery` | date | first day of the stated period | 🟢 | Last announced delivery date |
| `delivery_status` | str | none / started / completed / postponed | 🟢 | Latest announced status |
| `assessable` | bool | | 🔵 | K4 result for the latest quarter |
| `source_record_ids` | str | `;`-separated | ⚪ | Records behind the row |
| `confidence` | str | high / medium / low | 🟢 | Reviewer confidence |

### 4.2 `compound_boundaries.geojson` (1 feature = compound)
| Property | Type | Origin | Meaning |
| --- | --- | --- | --- |
| `compound_id`, `polygon_id` | str | ⚪ | Link to the register and to the satellite tables |
| `geometry` | Polygon, EPSG:4326 | 🔵 | OSM plot snapped to the located point, or a polygon drawn by the team |
| `area_m2`, `area_ratio` | float | 🔵 | Polygon area and its ratio to the published area (accepted 0.6-1.5) |
| `method` | str | 🟢 | osm_plot / drawn / developer_map |
| `confidence` | str | 🟢 | high / medium / low (accepted: medium or higher) |
| `signed_by_1`, `signed_by_2` | str | ⚪ | Two team members who checked it |

Input file `locations_team.csv`: `project_id, lat, lon, method, url, confidence` (broker sites not allowed).

### 4.3 `r_progress_announced` (1 row = statement, ~25 rows)
`compound_id` ⚪ · `published_date` date 🟢 · `progress_pct` float 0-100 🟢 · `qualifier` str (about / more_than / exactly) 🟢 · `scope` str (project / phase / concrete) 🟢 · `stated_by` str (developer / consultant / ACUD) 🟢 · `source_url` 🟢 · `record_id` ⚪

### 4.4 `r_project_events` (1 row = event, ~40 rows)
`compound_id` ⚪ · `event_type` str (launch / delivery_start / delivery_complete / postponement) 🟢 · `event_date` date (null if not stated) 🟢 · `published_date` date 🟢 · `value`, `unit` (e.g. 1,084 units) 🟢 · `source_url` 🟢 · `record_id` ⚪

Rule: a statement or event can be used at date T only if `published_date <= T` (no leakage).

### 4.5 `eval_outcomes` (1 row = compound, 6-10 rows): ground truth for the backtest
`compound_id` ⚪ · `outcome` str (delivered / delayed / postponed) 🟢 · `outcome_date` date 🟢 · `evidence` str 🟢 · `source_url` 🟢 · `record_id` ⚪
Current cases: Serrano (delivered), Catalan (1,084 of 1,765 delivered), Atika (delivered), Residence Eight (phase 1 handover Dec 2025, after the Q2 2024 date), Venia (postponed 2024 → 2026 → 2027), La Verde (promised early 2023, no handover announced).

### 4.6 `r_dynamic_world_quarterly` (1 row = polygon × quarter; 29 compounds + 2 reference plots × 43 quarters)
| Column | Type | Unit | Origin | Meaning |
| --- | --- | --- | --- | --- |
| `polygon_id`, `compound_id` | str | | ⚪ | |
| `quarter` | str | 2016Q1..2026Q3 | ⚪ | |
| `built_prob_mean` | float | 0-1 | 🟢 | Mean Dynamic World "built" probability over the polygon |
| `n_images` | int | images | 🟢 | Images used (K4 needs ≥ 6) |
| `delta_b12` | float | probability | 🔵 | K1: mean of last 4 quarters − previous 4; active if > 0.03 |

Source: Google Dynamic World V1 (CC BY 4.0). Measured noise on stable plots: SD 0.065 per quarter; seasonal offsets Q1 +0.03, Q2 −0.05, Q3 0.00, Q4 +0.04 (this is why every comparison is year over year).

### 4.7 `r_sar_quarterly` (1 row = polygon × quarter; same grain as 4.6)
`polygon_id`, `quarter` ⚪ · `vv_db`, `vh_db` float dB 🟢 · `n_scenes` int 🟢 · `platforms` str (S1A / S1B / S1C) 🟢 · `delta_vv12` float dB 🔵 (K1b: last 4 quarters − previous 4; active if > 0.5 dB)
Source: Sentinel-1 RTC. Bare desert ≈ −19.6 dB VH; built plots −15 to −10 dB; quarterly noise SD 0.73 dB. Fewer scenes in 2022-2024 (Sentinel-1B ended Dec 2021). The signal saturates when the structure is complete.

### 4.8 `r_observed_stage` (1 row = polygon × year)
| Column | Type | Unit | Origin | Meaning | Status |
| --- | --- | --- | --- | --- | --- |
| `polygon_id`, `year` | | | ⚪ | | |
| `s2_veg_share` | float | 0-1 | 🔵 | Share of the polygon's Sentinel-2 pixels with NDVI > 0.2 (Jun-Sep composite): grass, trees, landscaping | ✅ passed (95% agreement) |
| `paved_frac` | float | 0-1 | 🔵 | Share of the open (non-building) area that looks like asphalt: dark, grey, smooth pixels | 🟡 supporting only (81%) |
| `observed_stage` | str | foundations / construction / stalled_structure / external_works / complete | 🔵 | Rule in `project-plan.md` section 3 | |

What "passed" and "failed" mean here: we labelled 50 plot-images by eye first (vegetation yes/no, roads paved yes/no, facades finished yes/no), split them in two halves, set the threshold on one half and tested once on the other. The gate was ≥ 80% agreement with the eye labels.
- `s2_veg_share`: 95% agreement → used as an automatic sign of external works.
- `paved_frac`: 81% (21 of 26), just over the gate; one wrong case would make it fail. It is kept as a supporting column, never on its own.
- Dynamic World grass/trees/water: stayed at ~0.03 in every plot, even green ones with lakes, because gardens and pools are smaller than a 10 m pixel. Removed.
- Exterior paint/plaster: 60%, the same as always guessing "not finished". Not measurable from images taken from above; checked by eye in the Wayback images only.

### 4.9 `r_buildings_yearly` (1 row = polygon × year, 2016-2023)
`polygon_id`, `year` ⚪ · `building_presence_frac` float 0-1 🟢 · `mean_height_m` float m 🟢
Source: Google Open Buildings 2.5D Temporal (CC BY 4.0). Independent check of Dynamic World (median correlation 0.95 on plots ≥ 2 ha).

### 4.10 `r_buildings_height_yearly` (1 row = building × year, 2016-2023)
Scope: only the buildings whose centre falls inside the 29 compound boundaries (a few thousand buildings). The full extract has 43,550 buildings: every Google Open Buildings V3 footprint with confidence ≥ 0.75 and area ≥ 40 m² inside the study box lon 31.60-31.95, lat 29.90-30.10 (the whole New Capital area); it stays archived for context.

`building_id` (Plus Code) ⚪ · `compound_id` ⚪ · `year` ⚪ · `height_m` float m 🟢 · `presence` float 0-1 🟢 · `height_class` str 🔵 (none: presence < 0.5 or < 3 m · low 3-8 m ≈ 1-2 floors · partial 8-20 m · full ≥ 20 m)
No height in metres exists after 2023 (laser, our own model and shadow measurement were all tested and failed their gates).

### 4.11 `r_wayback_images` (1 row = compound × image, 2 per compound)
`compound_id` ⚪ · `capture_date` date 🟢 (acquisition, not release) · `release_date` date 🟢 · `sensor` str 🟢 · `resolution_m` float 🟢 · `tile_url` str 🟢 · `local_file` str 🔵
Esri World Imagery Wayback: display only in the inspection file, with attribution; never used in a computation.

### 4.12 `r_night_lights_monthly` (1 row = zone × month, Jan 2019-Sep 2026)
`zone_id`, `month` ⚪ · `radiance_mean`, `radiance_median`, `radiance_p90` float nW/cm²/sr 🟢 · `valid_obs` int 🟢
NASA Black Marble. District context and occupancy calibration for Track B; never per compound (6-9 pixels only).

### 4.13 `r_weather_daily` (1 row = day, 2023-2026)
`date` ⚪ · `max_temp_c` 🟢 · `min_visibility_m` 🟢 · `max_wind_kt` 🟢 · `t2m_max_power` 🟢 (NASA POWER) · `dust_flag` bool 🔵 (airport METAR) · `dust_event_confirmed` bool 🔵 (one of the 8 announced storms, confirmed by METAR)

### 4.14 `r_macro_monthly` (1 row = month, 2022-01 to 2026-09)
`month` ⚪ · `usd_egp_avg` 🟢 (CBE) · `policy_rate` 🟢 (CBE) · `steel_ton_egp`, `cement_ton_egp` 🟢 (Ministry of Housing bulletin) · `material_cost_index` 🔵 (Jan 2023 = 100) · `shock_flag` 🔵 (6 Mar 2024 float)

### 4.15 Reference tables
| Table | Grain | Columns |
| --- | --- | --- |
| `r_regulations` | rule (~15) | `rule_id` ⚪ · `instrument`, `article`, `parameter`, `value`, `unit`, `source_url` 🟢 (Decree 2184/2022, Law 119/2008) |
| `r_acud_events` | event (~27) | `event_date`, `event_type`, `value`, `stated_by`, `source_url` 🟢 |
| `r_benchmarks` | parameter (~100) | `parameter` ⚪ · `value_low`, `value_high`, `unit`, `year` 🟢 · `confidence`, `record_ids` ⚪ |
| `ref_calendar` | month (2016-2026) | `month`, `quarter` ⚪ · `ramadan_days`, `eid_days` 🟢 · `season` 🔵 |

---

## 5. Generated tables (group B, Track B only)

33 twins × 45 months (Jan 2023 to Sep 2026). Each twin copies district, area and unit count from one real compound with known area and units, **with ±15% jitter**, so no twin equals a real compound. Developers are fictional (DEV-T01..T15). Full rules, noise models and defects: `docs/plan/synthetic-data-plan.md`.

| Table | Grain | Columns (type key in section 4) |
| --- | --- | --- |
| `g_twins` | twin | `twin_id`, `template_compound_id`, `developer_id` ⚪ · `district`, `land_area_m2`, `units_total` 🟢 (jittered) · `building_coverage_pct` 🟡 · `floors`, `bua_m2` 🔵 · `escrow_class_pct` 🟢 · `launch_date`, `land_handover_date`, `contractual_delivery_date` 🟠 |
| `g_plan_monthly` | twin × month | `twin_id`, `month` ⚪ · `planned_progress_pct` 🟠 |
| `g_progress_monthly` | twin × month | `twin_id`, `month` ⚪ · `reported_progress_pct`, `report_date`, `facades_pct`, `dw_built_obs`, `dw_n_images`, `sar_vh_obs` 🟠 · `stall_flag` 🔵 |
| `g_escrow_monthly` | twin × month | `twin_id`, `month` ⚪ · `units_sold`, `avg_unit_price_egp`, `collections_egp`, `deposits_egp`, `withdrawals_egp`, `balance_egp`, `cost_to_complete_egp` 🟠 · `required_min_pct`, `material_cost_index` 🟢 · `coverage_ratio` 🔵 |
| `g_land_installments` | installment | `twin_id`, `installment_no` ⚪ · `due_date`, `amount_egp`, `paid_date`, `paid_egp` 🟠 · `months_late` 🔵 |
| `g_utilities_monthly` | twin × month | `twin_id`, `month` ⚪ · `meter_type`, `meters_active`, `kwh`, `m3`, `read_type` 🟠 · `t2m_max_mean` 🟢 · `occupancy_gap` 🔵 |
| `g_status_events` | event or month | `twin_id`, `date` ⚪ · `event_type` 🟠 · `status_level` 🔵 |
| `g_complaints` | complaint | `complaint_id`, `twin_id`, `created_at` (Africa/Cairo) ⚪ · `channel`, `category`, `text_ar` 🟠 · `category_llm`, `complaints_per_1000_units` 🔵 |

Side files: `answer_key.parquet` (hidden truth: story, archetype, true progress, true cash, true occupied units, `label_distress_next_6m`, each complaint's true cause) and `defects_log.csv` (6 planted defects with row counts). **The answer key is never joined into features.**

---

## 6. Pipeline and operations tables (group C, in `spaceeye.duckdb`)

| Table | Columns |
| --- | --- |
| `kpi_values` | `entity_id`, `entity_type` (compound / twin), `kpi_id` (K1-K4, B1-B5), `asof_quarter`, `value`, `unit`, `level`, `origin_type`, `source`, `run_id`, `computed_at` |
| `cycle_list` | `run_id`, `asof_quarter`, `rank`, `compound_id`, `level`, `observed_stage`, `reason_sentence`, `may_be_complete_flag`, `inspection_file_path` |
| `run_log` | `run_id`, `started_at`, `step`, `rows_in`, `rows_out`, `gates_failed`, `duration_s` |
| `quality_checks_log` | `gate`, `dimension`, `rule`, `threshold`, `result`, `rows_affected`, `owner`, `decision` (fix / flag / stop), `impact_on_kpi`, `run_id` |
| `ops_visits` | `visit_id`, `compound_id`, `visit_date`, `result` (progressing / stalled / complete / not_done), `note`, `recorded_by`, `recorded_at` |
| `ai_verification_log` | `file_id`, `claim`, `claim_type`, `value_in_text`, `value_in_data`, `method`, `verdict` (correct / wrong_number / unsupported / missing_context), `correction` |
| `kpi_cards` | the 10 fields + 2 tags per KPI (schema of `kpi_reference.csv`) |

---

## 7. Three ways to look at the same data

The tables are stored in **long tabular form** (one row per entity × time). Depending on the task, the same data is reshaped.

### 7.1 Tabular (the default: rules, SQL, gradient boosting)
One row = entity × as-of date, one column per feature. Every feature is computed only from rows dated on or before the as-of date.

```sql
-- K1 for every compound as of 2024-Q2 (only quarters <= as-of are visible)
WITH q AS (
  SELECT compound_id, quarter, built_prob_mean,
         ROW_NUMBER() OVER (PARTITION BY compound_id ORDER BY quarter DESC) AS k
  FROM 'data/raw/r_dynamic_world_quarterly.parquet'
  WHERE quarter <= $asof
)
SELECT compound_id,
       AVG(built_prob_mean) FILTER (WHERE k <= 4)
     - AVG(built_prob_mean) FILTER (WHERE k BETWEEN 5 AND 8) AS delta_b12
FROM q GROUP BY compound_id;
```

Use for: the priority rule (Track A), B1-B5, the optional logistic regression in Track B.

### 7.2 Time series (charts, deltas, seasonality, stall runs)
One series per entity, indexed by quarter or month: `df.pivot(index="quarter", columns="compound_id", values="built_prob_mean")`.
- Compare year over year (`series - series.shift(4)` for quarters), never quarter to quarter: Dynamic World has a seasonal swing (Q2 is lowest).
- Rolling windows: K1 and K1b are 4-quarter means; K2 counts the latest run of "not active" quarters.
- Missing quarters (fewer than 6 images) stay missing; do not interpolate before computing K2.

### 7.3 Tensor (only if a sequence model is tried)
Shape **(entities, time steps, features)** plus a mask for missing values:
- Track A: 29 compounds × 43 quarters × 3 features (`built_prob_mean`, `vh_db`, `s2_veg_share` repeated per quarter of its year).
- Track B: 33 twins × 45 months × F features (reported progress, DW, radar, escrow coverage, arrears, complaints, kWh per meter).

```python
import numpy as np, pandas as pd
long = pd.read_parquet("data/raw/r_dynamic_world_quarterly.parquet")
feats = ["built_prob_mean"]
wide = long.pivot_table(index="compound_id", columns="quarter", values=feats)   # entities x (feature, time)
X = np.stack([wide[f].to_numpy() for f in feats], axis=-1)                       # (29, 43, 1)
mask = ~np.isnan(X)
X = np.nan_to_num(X)                                                              # keep `mask` for the model
```

Rule of thumb: with 29 compounds and 33 twins, a tensor model has far too few samples to beat the simple rule. Tabular + time-series features is the main route; the tensor form is for an optional experiment only.

---

## 8. How to test with this data

| Test | Data | How | Pass criterion |
| --- | --- | --- | --- |
| **Backtest of the rule (Track A)** | real tables + `eval_outcomes` | Freeze the clock at 2024-Q2 and 2025-Q2: keep only quarters ≤ as-of and statements with `published_date` ≤ as-of; compute levels; compare with what happened later | ≥ 2 of 3 delayed cases (Venia, La Verde, Residence Eight) in level 1-2, and Serrano, Catalan, Atika not in level 1 |
| **Sensitivity** | same | Rerun with K1 = 0.02 / 0.04 and without radar | Report how the level 1-2 list changes (no pass/fail) |
| **Rule vs rule + B signals (Track B)** | `g_*` + answer key | Walk forward quarter by quarter; at each quarter take the top N; count how many become distressed in the next 6 months and how early | Rule + B finds more cases earlier than the rule alone |
| **Optional model (Track B)** | `g_*` + answer key | Time split: train Jan 2023-Jun 2025, test Jul 2025-Sep 2026; also hold out ~20% of twins entirely (group split by `developer_id`, so twins of one developer are not on both sides) | Must beat the rule on the test part; otherwise the rule is the product |
| **Realism of generated data** | `g_*` vs real | Calibration targets in `synthetic-data-plan.md` section 9 | All inside range |
| **Quality gates** | everything | 9 gates + the 6 planted defects | Each planted defect is caught by its gate |
| **Reproducibility** | everything | Run `run_all.py` twice | Same rows and same numbers (hash) |

Never shuffle rows across time, never fit a threshold on the backtest quarters, and never read `answer_key` inside a feature.

---

## 9. Data quality gates (summary)

Source (100% have an accepted record) · Completeness (≥ 6 DW images per quarter, else "not assessable") · Validity (probabilities 0-1, dB in range, dates valid) · Uniqueness (entity, period) · Consistency (every id in its register; row counts equal before/after joins) · Freshness (latest quarter ≤ 1 quarter old) · Separation (no `g_*` row joined to a real compound) · "Data or city?" (> 30% of compounds turn "no change" in one quarter → source event) · Stuck series (identical value 4 quarters in a row). Owners and decisions: `project-plan.md` section 9.

---

## 10. Wording rules

| Allowed | Not allowed |
| --- | --- |
| "No observed change from above or in height for X quarters" | "Distressed" about a real compound |
| "Passed the announced date by Y months" | "Completion 60%" or "finishing percentage" from images |
| "Observed height 2023 ≈ 24 m (≈ 7-8 floors, estimated)" | "8 floors built" as a fact |
| "Synthetic - for training only" on every generated output | Any generated number next to a real name |
