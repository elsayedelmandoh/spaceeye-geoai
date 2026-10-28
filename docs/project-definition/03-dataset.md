# Dataset: SpaceEye (R7 Digital Twin and Inspection Priority Observatory)

Last updated: 27 Oct 2026 · Plan, indicators and levels: [`01-specs.md`](../requirements/01-specs.md) · Plain-Arabic team explainer: `docs/.internal/archive/SpaceEye.md` (secondary; this file wins on conflict)

> **In three lines**
> 1. **R7 compounds only** (R8 removed to reduce scope): the R7 subset of the 22 compounds confirmed with boundary confidence ≥ 80% (count: open item 4 in `01-specs.md`). Codes only. No compound or developer name in any table. Counts below marked "first build" are for all 22 (R7 + R8) and shrink when the tables are rebuilt for R7.
> 2. Two tracks. **Track A (images)** reads satellite and image data into per-quarter indicators. **Track B (numbers)** joins those indicators with ACUD data into one ML dataset `ml_dataset` (X, y). **Public data** (satellite, statements, laws, economy) is real and used as published. **ACUD data** (escrow, installments, supervisor reports, meters, complaints, warnings) is **generated** today as a stand-in, consistent with each compound's real signals, labelled **"Synthetic - for training only"**; it is replaced by ACUD's real tables with the same columns when available.
> 3. **1,026 facts** collected from 12 domains, each with source, link and quote. An independent reviewer reopened every source: **1,009 usable (98%)**, 17 removed, **0 invented**.

---

## 1. Origin marks (on every column, chart and slide)

| Mark | Type | Meaning |
| --- | --- | --- |
| 🟢 | Real | Published or observed, with source, link and quote; reviewed |
| 🔵 | Derived | Computed by us from real data with a documented, tested method |
| 🟠 | Generated | Produced by the generator (missing register fields, or data only ACUD holds) |
| ⚪ | Key | Identifier or join column |

A developer statement is 🟢 (the statement is real) but it is not an independent measurement: we always write "the developer announced". Assumptions with no published value are 🟠 and are written in the config with `assumption: true`.

---

## 2. Where the data lives

Data is **outside the repo**. Paths are set in `configs/data.yaml` (`paths.real_data`, `paths.app_data`, `paths.private`).

| Folder | Content | Commit? |
| --- | --- | --- |
| `Project/real_data/` | Audited source files (`26_data_audit/...`). Never modified | No |
| `Project/app_data/raw/` | Coded copies of the sources used | No |
| `Project/app_data/real/` | Real tables (section 4) | No |
| `Project/app_data/sim/` | Generated tables + `dictionaries/` | No |
| `Project/app_data/spaceeye.duckdb` | All tables + `kpi_values`, `quality_checks_log`, `run_log` | No |
| `Project/private/` | Code map (codes ↔ names), `answer_key`, `defects_log`, private dictionaries | **Never** |

### Outside documents (team folder, not in the repo)

| File | Content |
| --- | --- |
| `Project/DATA_PLAN_FINAL.md` | Full data plan behind this file |
| `Project/team_ideas.md` | Every idea tried, its pre-written condition and result |
| `app_data/R1_REPORT.md` | Pipeline run report |
| `app_data/R2_REPORT.md` | Generator run report |
| `app_data/EW_REPORT.md` + `EW_PROTOCOL.md` | Early-warning results and the protocol written before the run |

When these disagree with this file or `01-specs.md`, the two repo files win.

---

## 3. How the data was collected and checked

1. **Collection:** 12 domains (compounds, statements, laws, satellites, weather, economy, night lights, benchmarks...). No number without an opened page + exact quote + link + date. Broker / real-estate sites are banned as sources for any number (dates, %, units, prices); they may help find a compound's **location only**, when satellite images confirm it and the method is logged per compound. Units kept as published.
2. **Review:** a second, independent agent reopened every source and tried to prove it wrong. PDFs re-downloaded, series re-pulled.
3. **Accepted verdicts:** `CONFIRMED`, `CONFIRMED_MINOR_FIX`, `AUDIT_LIVE_CHECKED`. Anything else is excluded by the `source` gate.

### Foundation audit (`real_data/26_data_audit/`), with acceptance conditions written before the check

| Data | Verdict |
| --- | --- |
| Dynamic World (built probability) | ✅ 308 values recomputed with independent code and matched; correlation with Google Open Buildings 0.96 |
| Google Open Buildings height to 2023 | ✅ |
| Weather, USD/EGP, rebar, cement, night lights | ✅ Re-pulled, 100% match |
| Decree 2184 and Law 119 | ✅ Corrected from the full text: cover 20/15/10/5/3% (art. 3); certified progress that releases the condition 30/25/20/15/10% (art. 4) |
| ACUD building conditions | ✅ Ground floor ≤ 22.5%, ground + 7, floor-area ratio 1.6-1.8 |
| Sentinel-1 radar | ❌ Detects building in only 63%; removed |
| Compound locations and boundaries | First only 8 of 29; after searching every source (maps, developer pages, real-estate site maps for location only, matched with images), **22 confirmed with confidence ≥ 80%**, 7 removed |

---

## 4. Inventory

| Table | Origin | Grain | Content |
| --- | --- | --- | --- |
| `compounds` | 🟢 + 🟠 for missing fields | 1 row = compound (R7 only; first build 22) | Area, units, floors, cover class, first deadline |
| `compound_boundaries` | 🟢 | 1 feature = compound | Boundary polygon by code |
| `sat_quarterly` | 🟢 / 🔵 | compound × quarter, 2016Q1-2026Q3 (43) | DW series, class shares, K1, A, K2, K4 |
| `sat_yearly` | 🟢 / 🔵 | compound × year, 2016-2026 | Vegetation share, building height |
| `statements` | 🟢 | 1 row = statement | Promises, announced %, events |
| `eval_outcomes` | 🟢 | 1 row = case (8) | Real outcomes for the backtest |
| `drivers_monthly` | 🟢 / 🔵 | 1 row = month | USD/EGP, policy rate, rebar, cement, temperature, Ramadan/Eid |
| `rules` | 🟢 | 1 row = rule | Law and decree articles used |
| `kpi_values` | 🔵 | compound × quarter | Track A indicators (A, K2-K6), level, reason sentence |
| `ml_dataset` | 🔵 + 🟠 | compound × quarter | Track B: features X + label y (section 8.4) |
| `fin_monthly` | 🟠 | compound × month, R7 compounds × 45 (first build: 22 × 45 = 990 + 3 duplicate reports from defect 2 = 993) | Plan, supervisor reports, sales, collections, cover, land installments, roads, meters, electricity, status, warnings |
| `complaints` | 🟠 | 1 row = complaint (first build 2,379 for 22 compounds; ~100 with Arabic text) | Buyer complaints |
| `answer_key` (private) | 🟠 | compound × month | Hidden truth and the model label. **The model never reads it** |

---

## 5. Real tables

### 5.1 `compounds` (22 rows)

| Column | Origin | Meaning |
| --- | --- | --- |
| `code`, `developer_code` | ⚪ | `C01..C22`, `D01..` (random from the fixed seed; map in `private/`) |
| `district` | 🟢 | R7 (rows with R8 are filtered out when the tables are built) |
| `land_area_m2`, `units` | 🟢 or 🟠 | Real where published; otherwise generated (`land_area_origin`, `units_origin` say which). Feddan = 4,200.83 m² |
| `floors_allowed` | 🟠 | Ground + 7 = 8 (ACUD cap) unless published (`floors_origin`) |
| `coverage_max` | 🟢 | 0.225 ground-floor cap |
| `bua_m2` | 🔵 | Land × min(coverage × floors, FAR cap 1.8) |
| `cover_pct` | 🔵 | Decree 2184 class: 20% (< 50 feddan), 15% (50-< 100 feddan) |
| `first_deadline`, `first_deadline_published` | 🔵 | End date of the **earliest published** promise; later promises never replace it |
| `handover_first_published` | 🔵 | First date a handover start/progress/completion was published |
| `boundary_confidence`, `boundary_area_m2` | 🟢 | From the location audit (≥ 80% to enter) |

### 5.2 `sat_quarterly` (compound × quarter)

| Column | Origin | Meaning |
| --- | --- | --- |
| `code`, `quarter`, `qi` | ⚪ | Quarter label and index (2016Q1 = 0) |
| `n_images` | 🟢 | DW images in the quarter |
| `built_prob_mean` | 🔵 | Mean DW built probability inside the boundary |
| `dw12_<class>` | 🔵 | 12-month DW class shares (water, trees, grass, flooded_vegetation, crops, shrub_and_scrub, built, bare, snow_and_ice) |
| `K1` | 🔵 | Last 4 quarters minus the 4 before; growth if > 0.02 |
| `activity_prob` (A), `active` | 🔵 | Activity score and active flag |
| `started`, `start_quarter` | 🔵 / ⚪ | Construction started: 4 consecutive active quarters or a published launch/delivery event |
| `K2` | 🔵 | Consecutive inactive quarters after the start |
| `K4` | 🔵 | ≥ 6 images and boundary accepted |

### 5.3 `sat_yearly` (compound × year)

| Column | Origin | Meaning |
| --- | --- | --- |
| `code`, `year` | ⚪ | |
| `veg_share` (`veg_origin`) | 🔵 | Share of Sentinel-2 pixels with NDVI > 0.2 (summer Jun-Sep); ≥ 0.10 → "may be complete" |
| `n_built_cells` | 🟢 | Built cells used for height |
| `height_mean_m`, `height_p90_m`, `share_built_ge20m` (`height_origin`) | 🟢 to 2023 / 🔵 2024 | Google Open Buildings to 2023; v4 built-mask estimate for 2024 (±2 m), labelled "estimate". Context only. Our 2024-2026 model (v8) failed its independent test (69-74%, target 80%) and is **not stored in this table** |

### 5.4 `statements` (1 row = statement, published dates only, no text)

`statement_id`, `code` ⚪ · `kind` (promise / progress / event), `subtype`, `detail`, `published_date`, `scope` (project / phase), `period_start`, `period_end`, `value`, `qualifier`, `verdict`, `origin`, `record_id` 🟢.

### 5.5 `eval_outcomes` (8 real cases)

`case`, `code` ⚪ · `outcome_type`, `promise_original_period`, `promise_original_published`, `promise_original_end`, `outcome_date`, `outcome_first_published`, `delay_months_vs_promise`, `evidence_gate`, `outcome_visible_by_2024Q2`, `outcome_visible_by_2025Q2` 🟢 · `first_deadline` 🔵.

### 5.6 `drivers_monthly` (1 row = month)

`month` ⚪ · `usd_egp`, `policy_rate_pct`, `rebar_egp_t`, `cement_egp_t`, `tmax_mean_c`, `days_tmax_ge40` 🟢 · `materials_index`, `shock_month` (USD rise ≥ 5% month on month), `ramadan_days`, `eid_days` 🔵.

### 5.7 `rules` and `compound_boundaries`

- `rules`: `rule_id` ⚪ · `source`, `article`, `rule`, `value`, `unit`, `origin` 🟢 (section 8).
- `compound_boundaries.geojson`: one polygon per code, properties include confidence. "Drawn by the team, not legal boundaries."

### 5.8 `kpi_values` (compound × quarter, 2019Q1 onward)

`code`, `quarter`, `qi` · `activity_prob`, `active`, `started`, `start_quarter`, `K2`, `K3`, `K4`, `may_be_complete` · **`K5_months`** (fine-eligible months: months past the first deadline with no start + months with K3 > 12) · **`K6`** (months since the first published launch / promise with no construction start; empty once started) · `level` (1-4, empty when not started / not assessable), `level_label`, `reason` (fixed template, codes only), `k3_first_deadline`, `cycle_rank` (top N with level 1-3; N = `cycle_capacity` ≈ a third of R7 compounds) · `origin` = derived, `run_id`, `computed_at`. The agent, dashboard and memo all read this table.

---

## 6. Generated tables: what each one stands in for

### How the tables form the R7 digital twin (light, compound level)

| Twin part | Tables | Updated |
| --- | --- | --- |
| Observed state (real) | `compounds`, `compound_boundaries`, `sat_quarterly`, `sat_yearly`, `statements`, `kpi_values` | Every quarter (Track A) |
| Simulated hidden state | generator → `fin_monthly`, `complaints`, private `answer_key` | Each run, fixed seed |
| What-if | generator re-run from the as-of quarter with one changed input (S1 USD/EGP +30%, S2 collections −25% for 6 months; S3 capacity N ± 2 re-ranks only; `01-specs.md` section 9) → levels in a scenario copy tagged `scenario_id`, never overwriting the base run | On demand (screen 5) |

**R8 data:** audited R8 files stay untouched in `real_data/` (sources are never modified, the 1,009/1,026 audit trail stays intact); every built table filters to `district = R7`.

The generated tables are a **stand-in with the same columns** as the data ACUD would hand over, so the rule and pipeline do not change when the real tables arrive (only the source and the origin mark change from 🟠 to 🟢). They feed the B signals in "public + ACUD data" mode only.

| Generated data | Real version held by |
| --- | --- |
| `planned_pct` (S-curve plan, B5) | Planning sector (contractual / approved schedule) |
| `reported_pct`, `report_date` | Supervising engineer quarterly reports (Law 119 art. 54) |
| `units_sold`, `collections_egp`, `cover_*` | Finance and the escrow banks |
| `land_*` | ACUD finance (land installments) |
| `meters_active`, `kwh` | Utility company (electricity only; **no water meters are generated**) |
| `status_level`, `warning_issued` | ACUD warning and termination records |
| `complaints` | Customer service |

---

## 7. The generator

### 7.1 Method

Random numbers per column or GAN/copulas were rejected: there is no real microdata to learn from, and random columns have no links. **Chosen: monthly process simulation + observation models.** We simulate what happens on site and in the bank (hidden truth), then each data owner "records" it in its own imperfect way. That is how real data is born, so the mess has the right structure.

```
Layer 0  Real drivers: calendar, Ramadan/Eid, USD/EGP, rebar, cement, policy rate, temperature, 6 Mar 2024 float, Decree 2184
Layer 1  Compounds: real sizes + hidden developer traits (strength, reporting style)
Layer 2  Monthly hidden truth: sales → collections → escrow → cash → spending → progress → handover → occupancy; land installments; status
Layer 3  Observation: supervisor report, escrow ledger, meters, complaint desk, ACUD warnings
Layer 4  Planted defects (logged)
Output   app_data/sim/{fin_monthly, complaints} + private/{answer_key, answer_key_complaints, defects_log}
```

Fixed seed 2026; simulated from 2017-01, written from 2023-01 to 2026-09 (45 months). Same seed → identical files.

### 7.2 Stories come from the compound's real signals

Story per compound, from the activity score A (majority vote over 3 quarters to remove flicker) and real events: `healthy`, `slow_late`, `partly_delivered` (phase 1 = 35-50% of the project), `gradual_stall` (≥ 4 trailing inactive quarters), `stall_recovery` (≥ 3 inactive quarters, then activity), `new_start` (first sustained activity from 2024Q3). The story biases behaviour; it does not hard-code the outcome.

**Anchors:** true progress passes within ±10 points of every real announced value and every handover; the satellite level never maps above 95% progress (finishing is invisible from space). **In every month with a real announced %, `reported_pct` equals it exactly.**

### 7.3 Monthly logic (hidden truth)

1. **Plan:** Weibull S-curve (shape 2-3): slow start (excavation, utilities, foundations), fast middle (repeated floors), slow finish (facades, finishing, landscaping); 100% exactly at the contractual delivery month; deadline = end of the first real promise, else plan start + 30-42 months.
2. **Cost:** BUA × USD/m² (720-1,270) × [40% follows the real dollar + 60% follows the real rebar/cement index].
3. **Sales:** launch spike + slow tail × demand (lower with higher policy rate and in Ramadan, **higher 2-4 months after the March 2024 float**). Launch price = cost × 1.4-2.0; list price +15-40% after the float.
4. **Collections:** 8.5% down payment + equal installments over 7-12 years; 3% late normally, 8% for 6 months after the float, weaker before a stall.
5. **Escrow cover:** all buyer money goes in; releases only after a quarterly report, capped by certified cost; required cover = class % × cost to complete until certified progress passes 30% / 25% (art. 4).
6. **Cash and spending:** spending = min(plan, available cash); shortfalls build contractor arrears and slow progress 1-2 months later.
7. **Progress:** capacity × season × AR(1) noise (ρ 0.5, σ 0.15). Season: Ramadan −20%, Jul-Aug −10%, Eid week −30%. True progress never falls.
8. **Handover and occupancy:** phased handover; slow move-in, 25-70% after 18 months (low occupancy matches real night lights).
9. **Land installments:** 16 quarterly, land price 2,500-12,000 EGP/m²; paid when cash covers it plus a month of spending; 1%/month penalty; arrears often cleared in one lump.
10. **Status** (ACUD review every 3 months): distressed if K3 > 24, or no reported progress for 6 months, or land arrears with cover below the minimum; late if K3 > 0; behind if reported is 10+ points under plan.

### 7.4 Observation models

| Source | How it records the truth |
| --- | --- |
| Supervisor report | Quarterly; 15-45 days after quarter end (late-style developers up to 75); 30% rounded to 5; optimistic developers +2-8 points; 5% missing, 35% while stalled (silence is a signal) |
| Escrow ledger | Monthly balance; lump releases show as steps |
| Meters | Active meters = handed-over units with a contract (0.5 → 0.92 in 12 months); kWh = occupied × 153 × real-temperature seasonality + empty-meter standby + site meter while building; 4% estimated reads. True occupancy stays hidden. Electricity only: water shows up in complaint texts, not in meters |
| Complaint desk | Count ∝ units sold × base rate × event multiplier (delay, stall, price rise); channels phone 50 / portal 35 / visit 15; 5% same buyer on two channels within 7 days; 10-15% filed under a wrong category; ~100 Arabic texts from templates (no LLM), with spelling slips and mixed topics; one viral spike |
| ACUD warnings | Grace expired (art. 5), or 3 months without reported progress at a review |

### 7.5 Planted defects (`defects_log`, with row counts)

| # | Defect | Gate that should catch it |
| --- | --- | --- |
| 1 | Escrow balance entered in thousand EGP for one developer (2 compounds) for 4 months | Accuracy (unit) |
| 2 | Supervisor report entered twice with a different date (~1%, at least 3) | Uniqueness |
| 3 | Report date before the end of the quarter it covers (5 rows) | Validity (date order) |
| 4 | Unknown compound code in the complaint feed (15 rows) | Consistency (foreign key) |
| 5 | Complaint dated before the compound launched (5 rows) | Validity (date range) |
| 6 | Fake phone numbers typed in Arabic texts (10 texts) | Privacy masking (`assert_zero_phones`) |

### 7.6 Realism checks (output used only if the hard checks pass; current run passes)

**Hard:** balances ≥ 0 · cumulative collections ≤ contract value sold · true progress and handed-over units never fall, occupied ≤ handed ≤ units · truth within ±10 of every announced value · truth ≥ handover floor · satellite-level anchor · BUA / land ≤ 1.8 · same seed → identical tables · 25-40% of reports are multiples of 5 · warning rules respected · reported = announced in every statement month · the 6 defects exist with the logged counts.

**Calibration:** complaints 2,000-3,000 · 10-15% wrong category · ~100 texts · report lag 15-75 days · ~5% / 35% missing reports · post-float sales ≥ ×1.15 · list price +15-40% · Aug/Jan kWh 1.3-1.8 · 140-170 kWh per occupied unit · 1-7 of 22 compounds ever distressed in the first build (ACUD: ~8% seriously late); the range is rescaled to the R7 count when regenerated.

**Model sanity:** if a model scores perfectly, the data is too clean: add noise.

---

## 8. Generated table columns

### 8.1 `fin_monthly` (compound × month; R7 compounds × 45; first build 990 + 3 defect-2 duplicates = 993)

| Column | Origin | Meaning |
| --- | --- | --- |
| `code`, `month` | ⚪ | `C01..C22`; YYYY-MM, 2023-01..2026-09 |
| `planned_pct` | 🟠 | Contractual plan 0-100% |
| `reported_pct`, `report_date` | 🟠 | Supervisor report (mostly empty between quarters); equals the real announced % in statement months |
| `units_sold`, `avg_price_egp`, `collections_egp` | 🟠 | Sales and buyer payments |
| `cover_required_egp`, `cost_to_complete_egp` | 🔵 | Decree cover required; cost still to spend on certified progress |
| `cover_balance_egp` | 🟠 | Escrow cash + posted cover |
| `land_due_egp`, `land_paid_egp` | 🟠 | Land installment due / paid |
| `land_months_late` | 🔵 | Age of the oldest unpaid installment |
| `roads_paved_share` | 🟠 | Internal roads paved (follows progress above 35%, 2-month lag) |
| `meters_active`, `kwh` | 🟠 | Residential meters and billed electricity |
| `status_level` | 🔵 | on_plan / behind / late / distressed (last quarterly review) |
| `warning_issued` | 🟠 | Warning letter this month |

### 8.2 `complaints`

`complaint_id`, `code` ⚪ · `created_at` (Africa/Cairo, office-hours heavy), `channel`, `category` (as filed by the desk), `text_ar` (~100 rows, e.g. "المياه ضعيفة في الدور الأخير", "المصعد مش شغال") 🟠. 2,379 rows.

### 8.3 Private files

- `answer_key` (compound × month): `story`, `story_reason`, `developer_strength`, `reporting_style`, `true_progress_pct`, `true_cash_egp`, `contractor_arrears_egp`, `bank_debt_egp`, `true_cost_to_complete_egp`, `escrow_cash_egp`, `handed_over_units`, `true_occupied_units`, `true_distress`, **`label_distress_next_6m`** (training label; `label_censored` when < 6 months remain).
- `answer_key_complaints`: `complaint_id`, `true_code`, `true_category`, `true_cause` (base, postponement, handover, price, stall, grace_expiry, stall_review, viral), `duplicate_of`, `desk_category_wrong`, `has_text`.
- `defects_log`: `defect_id`, `table`, `column`, `rows_affected`, `description`, `expected_gate`, `detail`.
- Dictionaries: one markdown per table (column, type, unit/range, meaning, origin, how made) in `app_data/sim/dictionaries/` and `private/dictionaries/`.

### 8.4 `ml_dataset` (Track B: 1 row = compound × quarter)

Built by joining `kpi_values` (Track A) with `fin_monthly` and `complaints` aggregated to the quarter (last month of the quarter for balances, sums for flows). Labelled **"Synthetic - for training only"** (it holds generated columns).

| Group | Columns | Origin |
| --- | --- | --- |
| Keys | `code`, `developer_code`, `quarter`, `qi` | ⚪ |
| X: images (Track A) | `activity_prob`, `K1`, `K2`, `K4`, `veg_share`, `height_mean_m` (to 2024), finishing flag (only if its test passes) | 🔵 |
| X: statements | `K3`, `K5_months`, `K6`, `may_be_complete` | 🔵 |
| X: ACUD data | `cover_ratio` (B1), `land_months_late` (B2), complaints per 1,000 units over 90 days and its own-history percentile (B3), kWh per active meter (B4), `planned_pct` − `reported_pct` (B5), months since the last supervisor report, `K5_egp` | 🟠 |
| **y** | **`y_outcome_6m`**: `distressed` (true distress in any of the next 6 months) / `completed` (handover reached in the next 6 months) / `ongoing` (neither). Censored when fewer than 6 months remain | 🟠, from `answer_key` |

- `K5_egp` = `K5_months` × `fine_rate_month` × land value (`land_area_m2` × land price). `fine_rate_month` is in `configs/data.yaml` with `assumption: true` (value: open item 3 in `01-specs.md`).
- **No leakage:** features use only data published / recorded by the quarter end; `answer_key` columns never enter X; split by time (train to 2024Q4) and by held-out developers.
- **Real check set:** the `eval_outcomes` cases in R7, mapped to the same 3 classes, are scored but never trained on.
- **Size:** R7 compounds × ~15 quarters ≈ 150 rows. Time split; developer holdout only if ≥ 3 developers stay in the test set; no R8 rows and no extra virtual compounds.

---

## 9. Key real values the design depends on

| Value | Source |
| --- | --- |
| Escrow cover 20/15/10/5/3% of construction cost by area class (art. 3); condition released at certified progress 30/25/20/15/10% (art. 4); 12-month handover grace (art. 5); refund after 24 months; 6-month regularization | Prime Minister's Decree 2184/2022 |
| Quarterly supervisor reports (art. 54); occupancy certificate (art. 62); permit number and licensed floors in sales contracts (art. 67) | Building Law 119/2008 |
| Ground floor ≤ 22.5% of the plot; apartments ground + 7 (max 30 m); villas ground + 1; floor-area ratio 1.6 average, 1.8 cap (Decision 483/2023) | ACUD 2018 building conditions; Official Gazette |
| 7-8% of developers seriously late; 6 mutual terminations; field review every 3 months | ACUD chairman statements (Sep-Oct 2026) |
| 6 Mar 2024 float: USD 30.94 → 49.44 EGP; policy rate +600 bp to 27.25% | Central Bank of Egypt |
| Rebar 28,600 → 46,000 EGP/t (Jan 2023 → Jan 2024); cement 1,925 → 4,200 EGP/t (Jan 2023 → Jun 2025) | Ministry bulletin |
| Down payment 8.5%, installments 7.7 years average; cost 720-1,270 USD/m² | Knight Frank Q1 2025 |
| ACUD land price ~2,500 to 10-12 thousand EGP/m² | ACUD chairman |
| ~153 kWh/month per residential subscriber; household 3.8 urban (water 280-300 l/person/day kept for reference only; no water meters generated) | EEHC annual report; DHS 2014; HCWW |
| R8 average progress 44% (Jun 2025) | Etqan study (Daily News Egypt). R8 is out of scope; kept **only** as the generator's progress calibration reference |

### Official source links

| Data | Source | Link |
| --- | --- | --- |
| Plot polygons | OpenStreetMap (Overpass API) | `https://overpass-api.de/api/interpreter` |
| Sentinel-2 L2A (vegetation, indices) | Microsoft Planetary Computer | `https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a` |
| Building heights 2016-2023 | Google Open Buildings 2.5D Temporal (CC BY 4.0) | `https://sites.research.google/open-buildings/` |
| Built probability | Google Dynamic World (Brown et al. 2022, CC BY 4.0) | via Earth Engine |
| Before/after images (0.3 m) | Esri Wayback: display with capture date; input of the finishing vision-model experiment only after the Esri terms are checked | |
| Weather | NASA POWER daily | |

---

## 10. Wording rules

| ❌ We do not say | ✅ We say |
| --- | --- |
| "Progress is 70%" | "The developer announced 70%" + date + scope |
| "Compound C07 is distressed" | "No building activity for 4 quarters" / "first announced date passed by 27 months" |
| "ACUD reviews all projects every 3 months" | "According to the ACUD chairman's statement" |
| "10-12 companies are distressed" | "Those seriously late are about 7-8%" |
| "The official building coverage is 20%" | "ACUD caps the ground floor at 22.5% (2018 conditions)" |
| "Height is 8 floors" | "Observed height 2023 ≈ 24 m (estimated)" |
| "The market price of steel" | "The indicative price in the ministry's bulletin" |
| "The model is 92% accurate" | "recall@8 on generated data, first build R7+R8: 92% (satellites + company data) vs 62% (satellites alone) vs 37% (random)" |
| "A 3D / real-time digital twin of R7" | "A compound-level digital twin of R7: quarterly sync from satellites, simulated finance until ACUD's data arrives" |
| "Risk level 1" / "high-risk developer" | "Priority level 1: visit first" |
| "C07 was fined 3 million EGP" | "Eligible for review under contract terms for 14 months"; EGP only on generated data, "assumed rate" |
| "Land speculator" | "No construction start 30 months after the first launch" |
| "Height in 2025 is 26 m" | Nothing: 2024-2026 heights from our model are not approved |

---

## 11. Values rejected while merging

| Value | From | Why rejected |
| --- | --- | --- |
| Decree 2184 "S-curve" 15/45/75/100% by year | TerraPulse draft | Not in the decree text; art. 4 uses 30/25/20/15/10% |
| Apartment footprint 20%, villas 22-22.5% | TerraPulse draft | Audited cap is 22.5% ground floor |
| Developer and dates from Property Finder / Nawy | TerraPulse draft | Broker sites are banned as sources |
| `table_1_parcels` ... `master_r7_chronological_timeseries` | TerraPulse draft | Replaced by the tables in section 4 |
| 29 named compounds, `r_*` / `g_*` tables, 33 twins | 24-25 Oct drafts | Replaced by 22 coded compounds and the tables in section 4 |
| `r_sar_quarterly` (Sentinel-1) | 24-25 Oct drafts | Radar removed (63%) |
| Cover 10-30% | Old specs | Factual error; 30% figures are progress thresholds |
| "Risk level" for the 1-4 level | `SpaceEye.md` | Term is "priority level" |
| Our 2024-2026 heights as data | `SpaceEye.md` (marked "estimate") | Failed the 80% test; not stored, slide only |
| Boundaries from real-estate sites (unqualified) | `SpaceEye.md` | Location only, image-confirmed, method logged |
| R8 compounds | Earlier scope (R7 + R8) | R8 removed to reduce scope (27 Oct); R7 only |
| `table_3_sentinel2_chronological` (`mean_ndbi`, `mean_ndvi`, `built_pixels_area_sqm`, `optical_footprint_ratio`) and `table_4_google_buildings_chronological` (`mean/max_building_height_m`, `roof_slab_uniformity_ratio`, `detected_building_count`, `total_structural_volume_est_m3`) | TerraPulse notebook (archived) | **Generated, not observed:** the notebook queries the APIs but writes values from formulas + `np.random` noise. Not used as data |
| `master_r7_chronological_timeseries` (25 × 438 = 10,950 rows, every 5 days, 2018-2023) | TerraPulse notebook | Built from the generated tables above; cadence below the noise floor (quarterly only) |
| `table_2_contractual_metadata` (developer names, launch / handover year, typology, cost from Property Finder / Nawy) | TerraPulse notebook | Names banned; broker sites banned as number sources; typology tested (all apartments). Contract dates come from `statements` |
| `contractual_progress_target_pct`, `schedule_variance_raw` from a Decree 2184 S-curve | TerraPulse notebook | No such milestones in the decree; schedule variance = `planned_pct` − `reported_pct` (B5) |
