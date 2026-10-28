# 02-team-roles-and-tasks.md

# SpaceEye-GeoAI: Team Roles and Task Board

ACUD AI & Data Readiness Program · Graduation project (Days 6-12) · Team of 5
Source: `01-specs.md` (section 14). Synthetic data only - for training only.

---

## 1. How to use this file

- Members are **M1 to M5**. Each maps to the role of the same number (M1 = R1, ..., M5 = R5).
- Task ID format: `T-<member>-<nn>`, for example `T-M3-02`. IDs never change, even if a task is cut.
- Tick the box when the task is **done and reviewed**: `- [x]`.
- Each task shows: **ID · owner · day · deliverable · depends on · reviewer**.
- Rule from the specs: all roles review each other's output; **one person owns each deliverable**.
- Cut order if behind at Day 10: **Could** first, then **Should** from the bottom. Tier is marked on each task: `[Must]`, `[Should]`, `[Could]`.

### 1.1 Cross-review pairs

| Owner                 | Reviewed by | Why this pairing                                                |
| --------------------- | ----------- | --------------------------------------------------------------- |
| M1 (pipeline)         | M2          | M2 knows the planted defects the gates must catch               |
| M2 (generator)        | M1          | M1 checks the data passes the gates and dictionaries match      |
| M3 (GIS)              | M5          | M5 checks the map is readable and consistent with the dashboard |
| M4 (ML)               | M1          | M1 checks no leakage and that features come from `kpi_values` |
| M5 (dashboard, brief) | M4          | M4 checks every number in the brief against the backtest        |

---

## 2. Roles in detail

### M1 · Pipeline and data quality (R1)

**Mission:** make the pipeline run from raw files to KPIs with one command, and make every number traceable.

| Area               | Detail                                                                                                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Owns               | DuckDB ELT (5 stages: ingest, gate, compute, store, log), quality gates, data trust score, `run_all.py` / `make run`                                           |
| Inputs from others | Tables and dictionaries from M2; polygons from M3                                                                                                                  |
| Outputs to others  | `kpi_values` and `run_log` for M4 and M5; gate results for the Data trust screen                                                                               |
| Key rules          | Load raw as it arrived; fix in views, never in raw. Count rows before and after every join; use LEFT JOIN, then check. Replace, never duplicate, in `kpi_values` |
| Gates to implement | Completeness, Validity, Uniqueness, Timeliness, Consistency, Accuracy (escrow unit, stuck NDBI), Clock (24 Apr 2026 phantom hour, 29 Oct 2026 repeated hour)       |
| Done when          | A second run gives the same numbers; every failing gate has an owner and an action (fix / flag / block)                                                            |

### M2 · Synthetic data and answer key (R2)

**Mission:** build realistic data with a known answer, so the team can measure.

| Area               | Detail                                                                                                                                                              |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Owns               | Generator code (fixed seed), 7 new tables, planted stories S1-S8, planted defects, answer key, data dictionaries                                                    |
| Tables             | `developers`, `compounds`, `sentinel_passes`, `milestone_plan`, `escrow_flows`, `buyer_complaints`, `shock_scenarios`                                 |
| Inputs from others | Polygon geometry from M3; milestone and cost assumptions agreed with M4 and M5                                                                                      |
| Outputs to others  | Tables to M1; answer key to M4; complaint text to M4 for Gemini                                                                                                     |
| Key rules          | Same seed = same data on every laptop. Every file labelled "synthetic - for training only". Planted phone numbers inside complaint text must be recorded in the key |
| Done when          | All 8 stories exist in the data with an expected result; all defects are listed with row counts; dictionaries cover every column (type, unit, valid range, meaning) |

### M3 · GIS and map (R3)

**Mission:** put every compound on the map correctly and make the map answer the right question.

| Area               | Detail                                                                                                                                                                                                                 |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Owns               | H7/H8 polygons (33 compounds: H7 = 20, H8 = 13), area in feddan, spatial joins, the risk map                                                                                                                           |
| Inputs from others | Compound ids from M2; risk scores from M4                                                                                                                                                                              |
| Outputs to others  | `compounds` geometry to M2 and M1; map layer to M5 for Screen 1                                                                                                                                                      |
| Key rules          | EPSG:4326, point-in-polygon with `sjoin`; compare registry zone vs map zone and report differences. Map a **rate or score, not a raw count**. Title in English and Arabic, unit in the legend, freshness shown |
| Also owns          | Built footprint ÷ allowed built area input for `P_actual` (with M2); the "satellite says built, utilities show none" check (S8) on the GIS side                                                                     |
| Done when          | Zero compounds without a polygon; spatial-join row counts match before/after; map shows green/amber/red with last-pass freshness                                                                                       |

### M4 · ML, analytics and GenAI (R4)

**Mission:** answer "can the model beat a simple rule?" honestly, with no leakage.

| Area               | Detail                                                                                                                                                                                                                             |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Owns               | Baseline rule, model (logistic regression or small gradient boosting), backtest, model card, monitoring plan, explainable alerts, EGP value estimate, Gemini complaint classification, AI verification log                         |
| Inputs from others | `kpi_values` from M1; answer key and complaints from M2; map output from M3                                                                                                                                                      |
| Outputs to others  | Risk score and reason sentence to M5; backtest numbers to M5 for the brief                                                                                                                                                         |
| Key rules          | Time split: train Jan 2023 to Jun 2025, test Jul 2025 to Oct 2026; also hold out about 20% of compounds. No feature may use data after the prediction date. If the model does not beat the rule, **the rule is the product** |
| GenAI rules        | Mask phones by regex **before** any AI tool; the regex check, not the AI, decides if a file is safe. Prompts hold column names and masked synthetic text only. Every number a model writes is verified in the log            |
| Done when          | Precision, recall, lead time, false-alarm rate and calibration reported against the rule and the blanket round; every red/amber alert has a one-sentence reason whose numbers equal the data                                       |

### M5 · Dashboard, KPIs, brief and presentation (R5)

**Mission:** make the result usable by a committee and convincing to the panel.

| Area               | Detail                                                                                                                                                                                                                                                              |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Owns               | KPI cards TP-01..06, KPI tree, Streamlit dashboard (4 screens), operations workflow (severity levels, tickets, handover), decision brief, one-page executive brief, final presentation, user guide                                                                  |
| Inputs from others | KPI values from M1; map from M3; score, reasons and value range from M4                                                                                                                                                                                             |
| Outputs to others  | Layout needs back to M1 and M3 (what the screens must show)                                                                                                                                                                                                         |
| Key rules          | Apply the 5-step routine: scan status, check freshness, compare, drill down, decide. No percentage without its base, no truncated axis, correct comparison period, show spread, note coverage changes. Every KPI has an owner role, baseline, target and thresholds |
| Done when          | Brief is bilingual (English/Arabic); every number on slides traces to a file; demo runs as a deterministic replay with a recorded backup                                                                                                                            |

---

## 3. Task board

Legend: `[ ]` open · `[x]` done. Days follow section 14.2 of the specs. **Day 9 has no project work** (shift simulation).

### 3.1 M1 tasks (pipeline, gates, trust score)

- [ ] **T-M1-01** · M1 · Day 6 · `[Must]` Set up repo structure (`raw/`, `sql/kpis/`, `pipeline.py`, `kpi_store.duckdb`, `logs/`, `config/`). Deliverable: empty repo that runs. Reviewer: M2
- [ ] **T-M1-02** · M1 · Day 6 · `[Must]` Agree the table list and key columns with M2 (data dictionary format). Deliverable: signed-off column list. Depends on: T-M2-01. Reviewer: M2
- [ ] **T-M1-03** · M1 · Day 7 · `[Must]` Stage 1 Ingest: load all raw CSV/Parquet into DuckDB unchanged, print row counts. Depends on: T-M2-03. Reviewer: M2
- [ ] **T-M1-04** · M1 · Day 7 · `[Must]` Stage 2 Gates v1: validity, uniqueness, consistency, completeness, each with rule, threshold, owner, action. Reviewer: M2
- [ ] **T-M1-05** · M1 · Day 7 · `[Must]` Clock gate: drop phantom rows in 24 Apr 2026 00:xx; keep the repeated 29 Oct 2026 23:xx hour with timezone-aware handling. Reviewer: M2
- [ ] **T-M1-06** · M1 · Day 7 · `[Must]` Stage 3 Compute: first KPI SQL for TP-01 with `$start`, `$end`, optional `$zone`. Depends on: T-M5-02. Reviewer: M4
- [ ] **T-M1-07** · M1 · Day 8 · `[Must]` Accuracy gates: escrow unit check (EGP vs thousand EGP) and stuck NDBI (same value for 6+ passes) as a view that turns stuck passes into missing. Reviewer: M2
- [ ] **T-M1-08** · M1 · Day 8 · `[Must]` Stage 4 Store: `kpi_values` with `source`, `run_id`, `computed_at`; delete-then-insert so a rerun never duplicates. Reviewer: M4
- [ ] **T-M1-09** · M1 · Day 8 · `[Must]` Stage 5 Log: `run_log` with run id, KPI, period, rows, gates failed, seconds. Reviewer: M4
- [ ] **T-M1-10** · M1 · Day 8 · `[Must]` Compute TP-02, TP-03, TP-04, TP-06 as SQL, one file per card. Depends on: T-M5-02. Reviewer: M4
- [ ] **T-M1-11** · M1 · Day 10 · `[Must]` Data trust score per output (share of gates passed, coverage, stale flags). Reviewer: M5
- [ ] **T-M1-12** · M1 · Day 10 · `[Must]` Join row-count check: log rows before and after every join; fail loudly if LEFT JOIN changes the count. Reviewer: M3
- [ ] **T-M1-13** · M1 · Day 10 · `[Must]` Reproducibility test: run twice, same rows and same numbers. Reviewer: M4
- [ ] **T-M1-14** · M1 · Day 11 · `[Must]` `run_all.py` / `make run`: rebuild data, gates, KPIs, model, backtest and dashboard data in one command. Depends on: T-M2-10, T-M4-08. Reviewer: M5
- [ ] **T-M1-15** · M1 · Day 11 · `[Must]` Technical documentation for the pipeline (stages, gates, how to rerun, how to add a gate). Reviewer: M2
- [ ] **T-M1-16** · M1 · Day 11 · `[Should]` Scheduling note: how `run()` would be called by cron or a scheduler (concept only). Reviewer: M5

### 3.2 M2 tasks (synthetic data, stories, answer key)

- [ ] **T-M2-01** · M2 · Day 6 · `[Must]` Draft data dictionary skeleton for the 7 tables (column, type, unit, valid range, meaning). Reviewer: M1
- [ ] **T-M2-02** · M2 · Day 6 · `[Must]` Write `config/` files: developers list (D01-D14), compound list (C01-C33), milestone schedule (editable assumption), 2026 calendar dates (Ramadan, Eid, DST), cost assumptions placeholder. Reviewer: M4
- [ ] **T-M2-03** · M2 · Day 7 · `[Must]` Generator v1 with fixed seed: `developers`, `compounds`, `milestone_plan`. Reviewer: M1
- [ ] **T-M2-04** · M2 · Day 7 · `[Must]` Generator: `sentinel_passes` (about 9,000-9,500 rows, `ndbi`, `ndvi`, `cloud_pct`, `quality_flag`) with weather and cloud patterns. Reviewer: M3
- [ ] **T-M2-05** · M2 · Day 7 · `[Must]` Generator: `escrow_flows` (about 1,500 rows) with `coverage_ratio`. Reviewer: M1
- [ ] **T-M2-06** · M2 · Day 8 · `[Must]` Plant stories S1-S8 and write the **answer key** (compound, story, expected result, expected lead time). Reviewer: M4
- [ ] **T-M2-07** · M2 · Day 8 · `[Must]` Plant defects: clouds, dust-induced false NDBI, duplicate passes, one developer's escrow unit mismatch, repeated 23:xx hour on 29 Oct 2026, one unregistered compound id in complaints. Log each with row count. Reviewer: M1
- [ ] **T-M2-08** · M2 · Day 8 · `[Must]` Generator: `buyer_complaints` (a few thousand; Arabic and Franco text, category, compound, source system) with hidden phone numbers in free text, recorded in the key. Reviewer: M4
- [ ] **T-M2-09** · M2 · Day 8 · `[Should]` Generator: `shock_scenarios` (collection drop, material cost rise, delay 8-12 weeks). Reviewer: M4
- [ ] **T-M2-10** · M2 · Day 10 · `[Must]` Make the generator callable from `run_all.py` with the seed in config; same seed gives identical files. Reviewer: M1
- [ ] **T-M2-11** · M2 · Day 10 · `[Must]` Validation plots that prove each planted pattern (one plot per story). Reviewer: M5
- [ ] **T-M2-12** · M2 · Day 10 · `[Must]` Final data dictionaries (EN + AR), every file labelled "synthetic - for training only". Reviewer: M1
- [ ] **T-M2-13** · M2 · Day 11 · `[Must]` Story table: for each of S1-S8, expected vs observed result (fill in with M4's backtest). Depends on: T-M4-06. Reviewer: M4
- [ ] **T-M2-14** · M2 · Day 11 · `[Must]` Knowledge-transfer pack: how the data was generated, limits (synthetic realism), how to regenerate. Reviewer: M5

### 3.3 M3 tasks (GIS and map)

- [ ] **T-M3-01** · M3 · Day 6 · `[Must]` Define the 33 compound polygons for H7 (20) and H8 (13) as GeoJSON with EPSG:4326. Deliverable: `compounds.geojson`. Reviewer: M5
- [ ] **T-M3-02** · M3 · Day 6 · `[Must]` Agree compound ids (C01-C33) and area in feddan with M2. Reviewer: M2
- [ ] **T-M3-03** · M3 · Day 7 · `[Must]` Spatial join: assign every compound to its district (H7/H8); compare registry vs map; report differences (target: 0). Reviewer: M1
- [ ] **T-M3-04** · M3 · Day 7 · `[Must]` Allowed built area per compound, so `P_actual` = built footprint ÷ allowed built area can be computed. Depends on: T-M2-03. Reviewer: M4
- [ ] **T-M3-05** · M3 · Day 8 · `[Must]` First map: polygons coloured by a test KPI (TP-01), English + Arabic title, unit in legend. Reviewer: M5
- [ ] **T-M3-06** · M3 · Day 8 · `[Must]` Map utilities (electricity, water) per H-zone to the compound level for the S8 check (satellite says built, utilities show none). Reviewer: M4
- [ ] **T-M3-07** · M3 · Day 10 · `[Must]` Risk map layer: green / amber / red by score, with freshness of last pass (days since last pass). Depends on: T-M4-05. Reviewer: M5
- [ ] **T-M3-08** · M3 · Day 10 · `[Must]` Map shows **rate or score, not count**; add a second view by count only if it is labelled as a count. Reviewer: M5
- [ ] **T-M3-09** · M3 · Day 10 · `[Should]` Compound drill-down geometry: zoom to one compound with its last-pass NDBI/NDVI. Reviewer: M5
- [ ] **T-M3-10** · M3 · Day 11 · `[Must]` Export the map as PNG and as a data layer for the Streamlit app; row counts checked before and after joins. Reviewer: M1
- [ ] **T-M3-11** · M3 · Day 11 · `[Should]` Fairness view by district (H7 vs H8) in the map data for the fairness check. Depends on: T-M4-10. Reviewer: M4
- [ ] **T-M3-12** · M3 · Day 11 · `[Must]` GIS section of the technical documentation (CRS, joins, limits). Reviewer: M2

### 3.4 M4 tasks (ML, analytics, GenAI)

- [ ] **T-M4-01** · M4 · Day 6 · `[Must]` Write the label definition: stall or default in the next 8-12 weeks, taken from the answer key. Reviewer: M2
- [ ] **T-M4-02** · M4 · Day 6 · `[Must]` Draft feature list (ΔP, velocity 90 d, escrow coverage, complaint rate, satellite completeness, developer size) and the no-leakage rule. Reviewer: M1
- [ ] **T-M4-03** · M4 · Day 7 · `[Must]` Prepare questions on expected results for the doctor discussion (Day 7). Reviewer: M5
- [ ] **T-M4-04** · M4 · Day 8 · `[Must]` Baseline rule: alert when ΔP exceeds amber/red **and** velocity is below its own history; exclude announced dust/heat days. Reviewer: M1
- [ ] **T-M4-05** · M4 · Day 8 · `[Must]` Model v1 (logistic regression): fit on train period, produce score 0-100 per compound. Reviewer: M1
- [ ] **T-M4-06** · M4 · Day 8 · `[Must]` First measured result: precision, recall, lead time, false-alarm rate vs the baseline rule (honest, with sample size). Reviewer: M2
- [ ] **T-M4-07** · M4 · Day 10 · `[Must]` Backtest with time split (train Jan 2023 to Jun 2025; test Jul 2025 to Oct 2026) plus 20% compounds held out entirely. Reviewer: M1
- [ ] **T-M4-08** · M4 · Day 10 · `[Must]` Calibration check and comparison with the blanket quarterly inspection round. Reviewer: M5
- [ ] **T-M4-09** · M4 · Day 10 · `[Must]` Explainable alerts: top 2-3 contributing features (coefficient × value) into a fixed sentence template; test that every number in the sentence equals the data. Reviewer: M5
- [ ] **T-M4-10** · M4 · Day 10 · `[Should]` Fairness check by developer size class and by district (H7/H8). Depends on: T-M4-07 (backtest predictions), T-M2-03 (developer size class), T-M3-03 (H7/H8 district assignment). Reviewer: M3
- [ ] **T-M4-11** · M4 · Day 10 · `[Must]` EGP value estimate in `config/cost_assumptions.yaml`: low / base / high range, with missed-default cost included. Reviewer: M5
- [ ] **T-M4-12** · M4 · Day 10 · `[Should]` Gemini complaint classification (delay, work stopped, payment, quality, other) vs a keyword baseline, scored on the answer key; phones masked first by regex. Depends on: T-M2-08. Reviewer: M2
- [ ] **T-M4-13** · M4 · Day 10 · `[Must]` AI verification log: every number written by an AI assistant checked against the data. Reviewer: M1
- [ ] **T-M4-14** · M4 · Day 10 · `[Should]` Liquidity-shock simulation: apply shock to a group of compounds, recompute ΔP and risk, count how many cross amber/red and how late. Depends on: T-M2-09. Reviewer: M5
- [ ] **T-M4-15** · M4 · Day 11 · `[Must]` Model card (purpose, data, metrics, limits, fairness, "needs calibration on real imagery") and monitoring plan (drift, data completeness, re-training trigger). Reviewer: M5
- [ ] **T-M4-16** · M4 · Day 11 · `[Must]` Verify the story table: for S1-S8, observed result recorded (S3 dust storm flagged as weather, not default). Reviewer: M2
- [ ] **T-M4-17** · M4 · Day 11 · `[Could]` Per-compound lead-time estimate. Reviewer: M1

### 3.5 M5 tasks (dashboard, KPIs, brief, presentation)

- [ ] **T-M5-01** · M5 · Day 6 · `[Must]` Fill the use-case canvas (8 checks) and send the summary to the doctor before or at the start of Day 6. Reviewer: M4
- [ ] **T-M5-02** · M5 · Day 6 · `[Must]` KPI cards TP-01..06 with all 10 fields + parent + 2 tags (purpose, formula, unit, source, frequency, owner role, baseline, target, thresholds, direction, theme). Reviewer: M1
- [ ] **T-M5-03** · M5 · Day 6 · `[Must]` Draw the KPI tree (goal → TP-05 → TP-01..04, TP-06 under TP-02). Reviewer: M4
- [ ] **T-M5-04** · M5 · Day 7 · `[Must]` Decide baselines and thresholds: agreed limits, or history (median = baseline, worst 20% amber, worst 5% red); check the baseline period (Ramadan trap). Depends on: T-M1-06. Reviewer: M1
- [ ] **T-M5-05** · M5 · Day 7 · `[Should]` Map each KPI to an ISO 37120 / 37122 / ITU U4SSC theme (theme names only, no clause numbers). Reviewer: M3
- [ ] **T-M5-06** · M5 · Day 8 · `[Must]` Define pairs and guard rails (velocity with completeness; escrow with progress; complaints with units delivered) and log which KPIs are gameable. Reviewer: M4
- [ ] **T-M5-07** · M5 · Day 8 · `[Must]` Operations workflow: severity levels 1-4, ticket life cycle, one parent ticket per compound, weekly handover template. Reviewer: M1
- [ ] **T-M5-08** · M5 · Day 8 · `[Must]` Dashboard wireframe for 4 screens (risk map, drill-down, data trust, simulation); every tile shows value, unit, period, comparison, target, status colour, freshness. Reviewer: M3
- [ ] **T-M5-09** · M5 · Day 10 · `[Must]` Build Streamlit Screens 1-3 with real data (risk map, compound drill-down with one-sentence reason, data trust). Depends on: T-M3-07, T-M4-09, T-M1-11. Reviewer: M4
- [ ] **T-M5-10** · M5 · Day 10 · `[Should]` Screen 4: simulation sliders and before/after comparison. Depends on: T-M4-14. Reviewer: M4
- [ ] **T-M5-11** · M5 · Day 10 · `[Should]` Optional compliance index per compound (min-max, weights A equal vs B 40/35/25) and rank-change report. Reviewer: M4
- [ ] **T-M5-12** · M5 · Day 10 · `[Must]` Mid-review (10 minutes): a measured result, early dashboard, risks. Reviewer: all
- [ ] **T-M5-13** · M5 · Day 10 · `[Must]` First self-score against the best-guess rubric (section 15 of the specs). Reviewer: M1
- [ ] **T-M5-14** · M5 · Day 11 · `[Must]` **One-page executive brief** (problem, result in numbers, EGP range with assumptions, recommendation, risks, next step), English + Arabic. Depends on: T-M4-08, T-M4-11. Reviewer: M4
- [ ] **T-M5-15** · M5 · Day 11 · `[Must]` Bilingual decision brief (the one-pager is its front page). Reviewer: M4
- [ ] **T-M5-16** · M5 · Day 11 · `[Must]` Risk and responsible-AI note (section 13) and user guide. Reviewer: M2
- [ ] **T-M5-17** · M5 · Day 11 · `[Must]` Final presentation (12-15 min, 8 parts, section 16) with the demo replay and recorded video as backup. Reviewer: all
- [ ] **T-M5-18** · M5 · Day 11 · `[Must]` Second self-score against the rubric; replace with the official rubric if received. Reviewer: M1

### 3.6 Shared tasks (everyone)

Owner is the person named; the others review.

- [ ] **T-ALL-01** · M5 · Day 6 · `[Must]` Day 6 sign-off of the canvas; confirm roles M1-M5 and data dictionary format. Reviewers: all
- [ ] **T-ALL-02** · M4 · Day 7 · `[Must]` Discuss expected results with the doctor on Day 7; record the answers. Reviewers: all
- [ ] **T-ALL-03** · M1 · Day 11 · `[Must]` **Code freeze** and a clean run of the one command on a fresh machine. Reviewers: all
- [ ] **T-ALL-04** · M5 · Day 11 · `[Must]` Full rehearsal with timing; every member answers at least one mock Q&A question (section 17). Reviewers: all
- [ ] **T-ALL-05** · M2 · Day 11 · `[Must]` Definition-of-done check (section 18): one command, gates documented, 8 stories with expected and observed result, honest backtest, AI log verified, every file labelled "synthetic - for training only". Reviewers: all
- [ ] **T-ALL-06** · M5 · Day 12 · `[Must]` Present to the idea evaluation panel; live one-command run with replay as fallback. Reviewers: all

---

## 4. Critical path

If one of these slips, the whole project slips. Review them first each day.

1. `T-M2-03` to `T-M2-08` (tables, stories, answer key) block everything.
2. `T-M1-04`, `T-M1-08`, `T-M1-10` (gates and `kpi_values`) block M4's model.
3. `T-M4-06` (first measured result) sets what M5 can claim.
4. `T-M1-14` (one command) must work before Day 11 freeze.
5. `T-M5-14` (one-page brief) needs `T-M4-08` and `T-M4-11` first.

---

## 5. Risks to the plan

Each risk has one owner (with a supporting member where noted), an early sign, a fix to do now, and a fallback if the fix is not enough. If a fix moves a task to another member, the task ID stays the same, and the reviewer changes so nobody reviews their own work.

| #  | Risk                                       | Early sign (check when)                                                                                        | Owner            | Fix now                                                                                                                                                                                                                   | Fallback                                                                  |
| -- | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| 1  | Everyone blocked by the generator          | No tables by midday Day 7 (T-M2-03)                                                                            | M2               | M1 and M3 build against the columns in the dictionary (T-M2-01) using 5 fake rows, so their code is ready when real tables land                                                                                           | Ship 10 compounds first, then scale to 33                                 |
| 2  | `sentinel_passes` late                   | T-M2-04 not done by 15:00 on Day 7 (Day 8 work waits for it)                                                   | M2               | Generate fewer passes per compound first; keep the seed in config so scaling up is one change                                                                                                                             | Run gates and model on the smaller set; say so in the model card          |
| 3  | Model does not beat the rule               | No gain in T-M4-06 (Day 8), confirmed in T-M4-07                                                               | M4               | Report it honestly; the rule is the product (specs 8.3). M5 writes the brief (T-M5-14) so it works for either outcome. Model results go in the model card (T-M4-15)                                                       | Present the rule, with the model as a tested alternative                  |
| 4  | Too few defaulters in the test period      | Fewer than about 5 planted events after Jul 2025                                                               | M2 (support: M4) | M2 adds events in the test window of the answer key (T-M2-06) early on Day 8, before T-M4-06 runs; M4 reports results with the sample size                                                                                | State the limit on the slide; do not claim precision to the decimal       |
| 5  | Data leakage                               | Recall or lead time looks too good; a feature uses data after the prediction date                              | M4 (support: M1) | M1 reviews the feature list at T-M4-05 (Day 8, before the first result) and again at T-M4-07; M4 adds a test that no feature date is after the prediction date                                                            | Drop the suspect feature and rerun the backtest                           |
| 6  | Clock handling deletes real readings       | Row count drops in the repeated 23:xx hour on 29 Oct 2026                                                      | M1               | T-M1-05: timezone-aware duplicate handling, with a gate that keeps the repeated hour and drops the 24 Apr 2026 00:xx hour. T-M2-07 plants both cases so the gate has something to catch                                   | Flag instead of delete until the rule is proven                           |
| 7  | Day 10 is overloaded (22 tasks)            | More than 60% of Day 10 Must tasks still open at midday                                                        | M5               | Move the six `[Should]` tasks (T-M3-09, T-M4-10, T-M4-12, T-M4-14, T-M5-10, T-M5-11) to Day 11 morning. Keep the order: T-M4-10 before T-M3-11 and T-M4-15 (the model card has a fairness part); T-M4-14 before T-M5-10 | Cut order: `[Could]` first (T-M4-17), then `[Should]` from the bottom |
| 8  | M4 and M5 carry the most tasks (17 and 18) | A member carries more than 3 open tasks over from the previous day                                             | M5               | M3 (12 tasks) takes T-M5-05 (Day 7) and T-M5-11 (Day 11, after the move in risk 7). M2 takes the user-guide part of T-M5-16 once T-M2-14 is done. Reviewers change: T-M5-05 to M5, the user-guide part to M4              | Review `[Must]` tasks only; skip reviews of `[Should]` tasks          |
| 9  | Gemini is slow or unavailable              | No answer by midday on the day T-M4-12 runs (Day 10, or Day 11 if moved by risk 7)                             | M4               | Score the keyword baseline first; cache every Gemini output as a file                                                                                                                                                     | Present the baseline plus the cached Gemini answers                       |
| 10 | Official rubric not received               | Nothing by Day 10 (T-M5-13)                                                                                    | M5               | Self-score with the best-guess rubric twice (T-M5-13, T-M5-18); ask the doctor on Day 7 (T-ALL-02) when it will arrive                                                                                                    | Replace the rubric as soon as it arrives                                  |
| 11 | Live demo fails                            | `run_all.py` fails at T-M1-13, in the fresh-machine run at the freeze (T-ALL-03), or in rehearsal (T-ALL-04) | M1 (support: M5) | M1 keeps a stub `run_all.py` from Day 8 that calls the stages built so far, so Day 11 only adds model and backtest; run it on a fresh machine at the freeze                                                             | Deterministic replay and the recorded video                               |
| 12 | 2026 Eid and Ramadan dates move            | Official dates announced and different from the config                                                         | M2               | Keep the dates in config (T-M2-02), not in code                                                                                                                                                                           | Update config and rerun the one command                                   |
