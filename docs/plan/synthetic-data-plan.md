# SpaceEye: Synthetic Data Plan (Track B generator)

Version 1, 25 Oct 2026 · Owner: R2 (generator) · Reviewer: R1 (gates) · Builds on `project-plan.md` section 5 and `data-report.md` sections 5-8.

> Every generated file carries the label **"Synthetic - for training only"**. No generated number is ever attached to a real compound or developer name.

---

## 1. Goal

Generate the 8 tables that ACUD holds internally and does not publish (escrow, land installments, supervisor progress reports, meters, complaints, warnings). The data must:

1. **Behave like the real thing.** It follows the same causes, the same seasons and the same shocks as the real 2023-2026 economy in the New Capital.
2. **Be anchored to our real data.** Sizes come from real R7/R8 compounds. Prices, exchange rate, temperature and the 2024 shock come from the real series. The satellite columns copy the noise of our real Dynamic World and radar series.
3. **Be messy like real records.** It has noise, lags, rounding, missing months, entry errors and rare surprises, so the pipeline, the gates and the model are tested honestly.
4. **Have a known answer.** Every twin has a story (`cfg_scenarios.yaml`) and every planted defect is logged, so we can measure the model and the gates.

What "100% realistic" means here: no one can prove a synthetic set is identical to reality. We aim for the next best thing: **every pattern is either taken from a real series or written down as an assumption, and the output passes the realism checks in section 9**, including a test where a classifier tries to tell real and synthetic satellite series apart.

---

## 2. Why this method (process simulation + observation models)

| Option | Why not / why |
| --- | --- |
| Random numbers per column | No links between tables. A model would learn nothing real. Rejected. |
| GAN / CTGAN / copulas trained on data | Needs real microdata to learn from. We have none for escrow, meters or complaints. Rejected. |
| **Process simulation (agent-based, monthly) + observation models** | **Chosen.** We simulate what really happens on site and in the bank (the hidden truth). Then each data owner "records" that truth in its own imperfect way. This is how real data is born, so the messiness has the right structure. |

Two layers, kept strictly apart:

- **Hidden truth** (never shown to the model): true progress, true cash, true occupancy.
- **Recorded data** (the `g_*` tables): what the supervisor reported, what the bank statement says, what the meter read, what the satellite saw. Each has its own noise, lag, rounding and gaps.

---

## 3. Architecture

```
Layer 0  Real drivers (from real tables, not generated)
         calendar, Ramadan/Eid, EGP/USD, steel and cement prices, CBE rate,
         inflation, daily temperature, 6 Mar 2024 float, Decree 2184 rules
              |
Layer 1  Twins (g_twins): sizes copied from real compounds + fictional developer
              |
Layer 2  Monthly simulation of the hidden truth, per twin
         sales -> collections -> escrow -> cash -> spending -> progress
         -> handover -> occupancy ; land installments ; status rules
              |
Layer 3  Observation models (one per data owner)
         supervisor report, bank statement, meter reading, complaint desk,
         ACUD warning letters, Dynamic World, Sentinel-1 radar
              |
Layer 4  Realistic defects (logged in defects_log.csv)
         duplicates, unit mistakes, stuck meters, late entries, unknown ids ...
              |
Outputs  data/synthetic/g_*.csv + answer_key.csv + defects_log.csv + dictionaries
```

One script, `simulate.py`, with one function per layer. Fixed seed (`seed: 2026` in `cfg_assumptions.yaml`). Same seed gives the same files on every laptop.

---

## 4. Real anchors (Layer 0)

All values below are already in our real data folder. The generator reads them; it does not invent them.

| Driver | Real value used | Source table / file |
| --- | --- | --- |
| Horizon | Jan 2023 to Sep 2026, monthly (45 months) | `ref_calendar` |
| Exchange rate | 28.8 EGP/USD (Jan 2023) → 30.94 (Feb 2024) → 45.46 (Mar 2024) → 47.8 (Jun 2024) → 50.47 (Jan 2025) → 53.25 (Oct 2026) | `07_macro_prices/egp_usd_monthly.csv` |
| Materials | Rebar 28,600 → 46,000 EGP/t (Jan 2023 → Jan 2024), 38,200 (Jun 2025); cement 1,925 → 4,200 EGP/t (Jan 2023 → Jun 2025) | `07_macro_prices/construction_material_prices.csv` |
| Interest and inflation | CBE policy rate (+600 bp on 6 Mar 2024 to 27.25%), urban headline inflation | `cbe_policy_rates_monthly_derived.csv`, `inflation_monthly.csv` |
| Temperature | Mean daily max by month: 19.5 °C (Jan) → 38.5 °C (Jul); ~15 days/year ≥ 40 °C | `06_weather_dust/nasa_power_daily_NAC_tidy.csv` |
| Legal rules | Escrow 20/15/10/5/3% by area class; 12-month grace; refund after 24 months; 6-month regularization | Decree 2184/2022 (`r_regulations`) |
| Market | Down payment 8.5%, installments 7.7 years (range 7-12); cost 720-1,270 USD/m²; coverage 18-22.5% (ACUD cap 22.5%), floor area ratio ≤ 1.6, ground + 7 max | `12_simulation_benchmarks/benchmarks_summary.csv`, `13_acud_rfp_conditions` (RFP-0002) |
| Utilities | 153 kWh/residential subscriber/month; 280-300 l/person/day; household 3.8 persons | `16_utility_benchmarks/benchmarks_utilities_summary.csv` |
| Calibration targets | ~8% of developers seriously late (ACUD); R8 average progress 44% (Jun 2025) | `r_acud_events`, `r_progress_announced` |
| Satellite statistics | see section 7.7 (computed from our real series) | `25_synthetic_calibration/calibration_stats.json` |

Ramadan months (work slows, sales pause, complaints shift): 23 Mar-21 Apr 2023, 11 Mar-9 Apr 2024, 1-30 Mar 2025, 18 Feb-19 Mar 2026 (written in `ref_calendar`).

---

## 5. The twins (Layer 1)

- **Count:** 33 twins (one per real reference compound with known area and units in R7/R8).
- **Copied from the real compound (🟢):** district, land area, total units. Nothing else.
- **Fictional (🟠):** `twin_id` (TW-01..TW-33), `developer_id` (DEV-T01..DEV-T15, so some developers own 2-3 twins and share cash problems, like real groups), launch date, land handover date.
- **Developer archetype (hidden, 🟠):** `financial_strength` ∈ {strong, medium, weak} with shares 30/50/20%, and `reporting_style` ∈ {accurate, optimistic, late}. These drive behaviour; they are in the answer key only.
- **Story (answer key):** assigned by `cfg_scenarios.yaml` with the shares in `project-plan.md` section 5 (healthy 55%, slow but healthy 15%, gradual stall 10%, stall after the 2024 shock 8%, stall then recovery 7%, complete but empty 5%). The story biases the drivers; it does not hard-code the outcome. A weak developer in a "healthy" story can still slip, as in real life.

---

## 6. Monthly simulation of the hidden truth (Layer 2)

For each twin and each month `t`:

0. **Warm-up.** Twins launch in 2021-2023. The simulation starts at each twin's launch, but only months from Jan 2023 are written out. Real FX and materials series start in Jan 2022; before that they are held at their Jan 2022 value.
1. **Plan.** `planned_pct(t) = 100 · min(1, F(x) / F(1))` with `x = (t - t_handover) / T`, where F is a Weibull CDF (shape k = 2-3). Dividing by F(1) makes the plan reach 100% exactly at the contractual delivery date. Duration `T ~ U(30, 42)` months.
2. **Total cost.** `cost(t) = BUA × cost_m2_usd × [0.4 · FX(t) + 0.6 · FX(t0) · M(t)/M(t0)]`. The 40% imported share follows the dollar; the 60% local share follows the real rebar/cement index `M(t)`. `cost_m2_usd ~ U(720, 1270)`, fixed per twin.
3. **Sales.** `units_sold(t) = remaining_units · h(t)`. `h(t)` has a launch spike, then a slow decay, × demand multiplier.
   - Demand multiplier from real drivers: lower when the CBE rate rises, **higher for 2-4 months after the March 2024 float** (buyers move cash into property as a hedge; a real Egyptian pattern), lower in Ramadan.
   - Launch price per m² = cost per m² at launch × U(1.4, 2.0) (developer margin, 🟡). The price list then jumps 15-40% after the float (🟡, lagged 1-3 months).
4. **Collections.** Down payment 8.5% at sale + equal installments over 7-12 years. Buyer late-payment rate 2-4% normally, 6-10% for 6 months after the float (🟡).
5. **Escrow.** All buyer payments go into escrow: deposits = collections. Releases to the developer happen **in lumps after each quarterly engineer report**, not every month (a real bank practice). The release is capped by certified progress. The minimum balance is the Decree 2184 % of remaining phase cost.
6. **Developer cash and spending (the link).** `cash(t+1) = cash(t) + releases + financing - spending - land_installment - overheads`. Collections reach the developer **only through escrow releases** (never counted twice). Spending = min(planned spending, available cash). If cash is short, contractor dues pile up and progress slows (with a 1-2 month delay).
7. **Progress.** `Δprogress = capacity × season × exp(ε_t)` limited by spending. `capacity` depends on the developer. `season`: −20% in Ramadan, −10% in Jul-Aug heat, −30% during the Eid week (🟡). `ε_t` is AR(1) noise (ρ = 0.5, σ = 0.15) so good and bad months come in runs. True progress never goes down.
8. **Handover.** Units can be handed over when progress ≥ 85% and facades ≥ 85% (the facades rule). Handover is in batches (phases), not one unit at a time.
9. **Occupancy.** After handover, move-in follows a slow logistic curve: start 2-6 months after handover, final occupancy only 25-70% after 18 months. This matches the low occupancy seen in the New Capital (night lights rose from 12.4 to 37.0 mean radiance between Jun 2021 and Jun 2025, still low per built area). The "complete but empty" story caps occupancy at 5-15%.
10. **Land installments.** Quarterly, equal. Paid in full when cash ≥ installment + 1 month of spending; otherwise late. Arrears pay a penalty (🟡) and are cleared when cash recovers, often in one big payment.
11. **Status rules** (the same rule as `data-report.md` section 7). Applied by an "ACUD reviewer" every 3 months (the real review cycle), not every month:
    - 3 months with no progress (one review cycle) → **warning letter**, level stays "behind plan".
    - delivery date passed → **late** (12-month grace period).
    - **6 months in a row with no progress**, or > 24 months late, or land arrears plus escrow below minimum → **distressed**.
    - termination is rare (about 1 in 3 distressed twins, 🟡).
12. **Story calibration in twins, not percent.** With 33 twins, the target is **2-3 twins distressed** and **~8 twins late at some point** (ACUD ~8%). So of the 8 "stall" twins, most slow down heavily but do not stop for 6 full months. Only 2-3 stop long enough to become distressed. The "stall then recovery" twins stop for **4-5 months**: they get a warning, then recover (they test false alarms).

---

## 7. Observation models: how each table is "recorded" (Layer 3)

This is where realism comes from. Each source sees the truth through its own lens.

### 7.1 Supervisor progress report (`g_progress_monthly.reported_progress_pct`)
- **Cadence:** quarterly (Law 119/2008 art. 54); the monthly row is empty between reports.
- **Lag:** the report date is 15-45 days after the quarter ends.
- **Rounding:** whole percent; 30% of reports rounded to 5 (developer announcements are 100% multiples of 5 in our real data).
- **Bias:** `optimistic` developers report true + U(2, 8) points, more when they stall. `accurate` developers report true ± 1.
- **Missing not at random:** in a stall, the chance of a missing report rises from 5% to 35%. Silence itself is a signal, as in real life.

### 7.2 Escrow ledger at ACUD (`g_escrow_monthly`)
- Copied monthly into ACUD's ledger from the bank statements. The bank figures are accurate; the copy can carry clerical errors (see defect 1).
- Balance is end of month. Lump releases show as steps.

### 7.3 Land installments ledger (`g_land_installments`)
- One row per due installment. `paid_date` is empty while unpaid.

### 7.4 Utility meters (`g_utilities_monthly`)
- **During construction:** temporary site meter, `kwh ∝ activity` (Δprogress × site size) + a base load; it drops sharply in a stall (a useful hidden signal).
- **What the utility sees:** the number of active residential meters (`meters_active` = handed-over units with a contract) and the consumption. It does **not** see how many units are really lived in; true occupancy stays in the answer key. Low consumption per meter is the visible sign of empty units.
- **After handover:** `kwh = occupied_units × 153 × s(T) × LogNormal(0, 0.08)` + a small standby load per empty meter, where the seasonal factor `s(T)` comes from the real monthly max temperature (normalised so the yearly mean is 1; Aug ≈ 1.35, Jan ≈ 0.8).
- **Water:** `m3 = occupied_units × 3.8 × 0.29 × days × LogNormal(0, 0.10)` + 1% chance per month of a leak spike (× 1.5-3).
- **Estimated reads:** 4% of meter-months are "estimated" (copy of last month, `read_type = estimated`), then a catch-up read the next month.

### 7.5 Complaint desk (`g_complaints`)
- **Count:** Negative Binomial (over-dispersed Poisson), `mean = units_sold × base_rate × m(events)`. `base_rate` is a declared assumption (no published rate). `m` rises × 2-5 in the 3 months after a delay, stall, late reply or price increase.
- **Surprises:** a viral spike in a healthy twin (one social-media post → 3-6× for one month, 1-2 twins); a quiet distressed twin (buyers gave up).
- **Channel mix:** phone 50%, portal 35%, visit 15%. 5% are the same buyer on two channels within 7 days (true duplicates).
- **Desk category is imperfect:** 10-15% of complaints are filed under the wrong category by the desk (the true cause stays in the answer key). This keeps the classifier test honest.
- **Text:** Arabic text only for a sample of ~100, written from templates with varied wording (dialect, spelling mistakes, mixed topics). No real names or phones, except **planted fake phone numbers** for the masking test (logged).

### 7.6 ACUD warnings (`g_status_events`)
- An event row only when a letter is issued: warning, grace period start, termination. Letters go out 0-2 months after the quarterly review that triggered them.
- `status_level` is the monthly level as ACUD would record it. The model target `label_distress_next_6m` is **not** in this table; it lives in `answer_key.csv` and is joined only at training time, so no feature can see it.

### 7.7 Satellite observations of twins (`g_progress_monthly.dw_built_obs`, `sar_vh_obs`)
Copied statistics from our real series (`calibration_stats.json`, 225 real polygons):

| Statistic | Real value | How the generator uses it |
| --- | --- | --- |
| DW built probability, bare land | median 0.106 | starting level |
| DW plateau when complete | p10 0.54 · median 0.68 · p90 0.73 | final level, sampled per twin |
| DW noise on stable plots | SD 0.065, lag-1 autocorrelation −0.1 | added each quarter |
| DW quarter effect | Q1 +0.027 · Q2 −0.055 · Q3 −0.003 · Q4 +0.040 | seasonal offset |
| DW images per quarter | p10 10 · median 15 · p90 19; 2.3% of quarters < 6 | image count; value set to missing when < 6 |
| DW quarterly rise | p95 0.15 | cap on how fast the curve can rise |
| Radar VH, bare land | −19.6 dB (SD 2.2 across sites) | starting level |
| Radar VH, built | median −14.9 dB, p90 −9.8 dB | final level; **saturates once the structure is complete** (finishing does not change it) |
| Radar quarterly change noise | SD 0.73 dB | added each quarter |

The DW curve follows **built footprint** (it rises early, in the structure phase). The radar follows **structure volume** (it rises with floors and then stops). Finishing work changes neither, as in reality; that is why we need the supervisor report and the meters.

---

## 8. Realistic defects and surprises (Layer 4)

Planted on purpose, each with its row count in `defects_log.csv`, so the quality gates (R1) have something real to catch:

| # | Defect | Where | Size | Gate that should catch it |
| --- | --- | --- | --- | --- |
| 1 | ACUD clerk copies one developer's escrow statements in thousand EGP for 4 months | `g_escrow_monthly` | 1 developer × 4 months | Accuracy (unit) |
| 2 | Supervisor report entered twice with a different date | `g_progress_monthly` | ~1% of reports | Uniqueness |
| 3 | Stuck meter: same reading 6+ months while meters_active rises | `g_utilities_monthly` | 2 twins | Accuracy (stuck series) |
| 4 | Unknown twin id in the complaint feed | `g_complaints` | 1 id, ~15 rows | Consistency (foreign key) |
| 5 | Complaint dated before the twin was launched (date entry error) | `g_complaints` | ~5 rows | Validity (date range) |
| 6 | Planted phone numbers inside complaint text | `g_complaints.text_ar` | ~10 texts | Masking test (`assert_zero_phones`) |

Missing DW quarters (< 6 images, ~2-3%) are **not** a planted defect: they come naturally from the image-count model and the completeness gate flags them.

**Surprises that are real behaviour, not errors** (the model must not be fooled):
- Stall then recovery (7% of twins): looks distressed for 6-9 months, then work restarts after new financing.
- Sales boom right after the 2024 float while costs jump.
- A healthy twin with a one-month complaint spike (viral post).
- A big one-off escrow deposit (bank loan or bulk sale to an investor).
- A developer with 3 twins: trouble in one spreads cash stress to the others 2-4 months later.
- Summer heat and Ramadan slow work every year; the model must not read that as a stall.

---

## 9. Realism checks (the output is used only if these pass)

**Hard consistency (fail = do not use):** escrow balance ≥ 0 · collections ≤ value of units sold · true progress never decreases · occupied ≤ handed over ≤ units total · BUA per unit 90-250 m² · BUA ÷ land ≤ 1.6 · each story within ±1 twin of target · same seed → same files (hash check).

**Calibration targets (compare with real):**

| Check | Target | Real source |
| --- | --- | --- |
| Twins reaching "distressed" | 2-3 of 33 | ACUD statement (~8% seriously late) |
| Twins late at some point | 6-10 of 33 | ACUD statement |
| Median true progress of twins in June 2025 | 35-55% | R8 average 44% |
| kWh per occupied unit per month | yearly mean 140-170 | 153 national |
| Aug/Jan electricity ratio | 1.3-1.8 | temperature seasonality |
| DW obs: noise SD, quarter effect, plateau | within ±20% of real values | section 7.7 |
| Reported progress values that are multiples of 5 | 25-40% | announcement pattern |

**Discriminator test (optional, only if time allows on D4):** train a small classifier (level, slope, noise, seasonality) to tell real DW/radar series from synthetic twin series. Target AUC ≤ 0.65. If higher, adjust the observation model, not the truth. The required check is the ±20% statistics table above.

**Model sanity:** the simple rule and the model must find the planted stories at a realistic rate, not 100%. If the model scores perfectly, the data is too clean: add noise.

---

## 10. Table schemas

Type key: `str` text, `int`, `float`, `date` (YYYY-MM-DD), `month` (YYYY-MM), `bool`. Origin: 🟢 real · 🔵 derived · 🟠 generated · 🟡 assumption · ⚪ key. Every table also has `synthetic_label` = "Synthetic - for training only" in the file header.

### 10.1 `g_twins` (1 row = twin, ~33 rows)
| Column | Type | Unit / range | Origin | How it is made |
| --- | --- | --- | --- | --- |
| `twin_id` | str | TW-01..TW-33 | ⚪ | sequence |
| `template_compound_id` | str | real project_id | ⚪ | one per real compound |
| `developer_id` | str | DEV-T01..DEV-T15 | 🟠 | fictional; 15 developers, some own 2-3 twins |
| `district` | str | R7 / R8 | 🟢 | copied |
| `land_area_m2` | float | m² | 🟢 | copied (feddan/acre converted) |
| `units_total` | int | units | 🟢 | copied |
| `building_coverage_pct` | float | 18-22.5 | 🟡 | U(18, 22.5); 22.5% is the ACUD cap (RFP-0002), 18% one developer's design (RFP-0008) |
| `floors` | int | 5-8 | 🟡 | chosen so BUA per unit is 90-250 m²; ground + 7 = 8 is the ACUD cap |
| `bua_m2` | float | m² | 🔵 | land × min(coverage × floors, 1.6): the ACUD average occupancy factor 1.6 caps total floor area (22.5% × 8 floors = 1.8 would break it) |
| `escrow_class_pct` | float | 3-20 | 🟢 | Decree 2184 class by area |
| `launch_date` | date | 2021-2023 | 🟠 | sampled; real launch year where known and inside the range |
| `land_handover_date` | date | | 🟠 | launch + 3-12 months |
| `contractual_delivery_date` | date | | 🟠 | handover + T |

### 10.2 `g_plan_monthly` (twin × month, ~33 × 45)
| Column | Type | Unit | Origin | How |
| --- | --- | --- | --- | --- |
| `twin_id`, `month` | str, month | | ⚪ | |
| `planned_progress_pct` | float | 0-100 | 🟠 | S-curve, section 6.1 |

### 10.3 `g_progress_monthly` (twin × month)
| Column | Type | Unit | Origin | How |
| --- | --- | --- | --- | --- |
| `twin_id`, `month` | | | ⚪ | |
| `reported_progress_pct` | float | 0-100, mostly empty between quarters | 🟠 | observation model 7.1 |
| `report_date` | date | | 🟠 | quarter end + 15-45 days |
| `facades_pct` | float | 0-100 | 🟠 | starts when structure ≥ 60% |
| `dw_built_obs` | float | 0-1, quarterly | 🟠 | observation model 7.7 |
| `dw_n_images` | int | | 🟠 | sampled from the real distribution |
| `sar_vh_obs` | float | dB, quarterly | 🟠 | observation model 7.7 |
| `stall_flag` | bool | | 🔵 | no reported/observed progress for ≥ 2 quarters |

Hidden truth (`true_progress_pct`, `true_cash_egp`) goes to `answer_key.csv`, never to this table.

### 10.4 `g_escrow_monthly` (twin × month)
| Column | Type | Unit | Origin | How |
| --- | --- | --- | --- | --- |
| `twin_id`, `month` | | | ⚪ | |
| `units_sold` | int | units/month | 🟠 | section 6.3 |
| `avg_unit_price_egp` | float | EGP | 🟠 | price list, jumps after float |
| `collections_egp` | float | EGP | 🟠 | section 6.4 |
| `deposits_egp`, `withdrawals_egp`, `balance_egp` | float | EGP | 🟠 | section 6.5 (lump releases) |
| `required_min_pct` | float | % | 🟢 | Decree 2184 |
| `cost_to_complete_egp` | float | EGP | 🟠 | section 6.2 with real FX and materials |
| `material_cost_index` | float | Jan 2023 = 100 | 🟢 | real rebar + cement |
| `coverage_ratio` | float | | 🔵 | balance ÷ cost to complete (TP-03) |

### 10.5 `g_land_installments` (1 row = installment, ~33 × 16)
| Column | Type | Unit | Origin | How |
| --- | --- | --- | --- | --- |
| `twin_id`, `installment_no` | | | ⚪ | |
| `due_date` | date | quarterly | 🟠 | from handover |
| `amount_egp` | float | EGP | 🟠 | land price × area ÷ n (real price range 2,500-12,000 EGP/m²) |
| `paid_date` | date | empty while unpaid | 🟠 | section 6.10 |
| `months_late` | int | | 🔵 | paid_date − due_date |

### 10.6 `g_utilities_monthly` (twin × month)
| Column | Type | Unit | Origin | How |
| --- | --- | --- | --- | --- |
| `twin_id`, `month` | | | ⚪ | |
| `meter_type` | str | site / residential | 🟠 | switches at first handover |
| `meters_active` | int | residential meters with a contract | 🟠 | = handed-over units with a contract (true occupancy is hidden) |
| `kwh` | float | kWh/month | 🟠 | model 7.4 |
| `m3` | float | m³/month | 🟠 | model 7.4 |
| `read_type` | str | actual / estimated | 🟠 | 4% estimated |
| `t2m_max_mean` | float | °C | 🟢 | real monthly mean of daily max |
| `occupancy_gap` | float | | 🔵 | 1 − kWh ÷ (meters_active × expected kWh per lived-in unit) |

### 10.7 `g_status_events` (1 row = event or month)
| Column | Type | Unit | Origin | How |
| --- | --- | --- | --- | --- |
| `twin_id`, `date` | | | ⚪ | |
| `event_type` | str | warning / grace_start / termination / none | 🟠 | section 6.11 + 7.6 |
| `status_level` | str | on_plan / behind / late / distressed / terminated | 🔵 | rules in section 6.11 (= `data-report.md` section 7) |

### 10.8 `g_complaints` (1 row = complaint, a few thousand)
| Column | Type | Unit | Origin | How |
| --- | --- | --- | --- | --- |
| `complaint_id`, `twin_id`, `created_at` | str, str, datetime (Africa/Cairo) | | ⚪ | |
| `channel` | str | phone / portal / visit | 🟠 | 50/35/15 |
| `category` | str | delay / stoppage / payment / quality / other | 🟠 | as filed by the desk: from the causing event, 10-15% wrong |
| `text_ar` | str | sample of ~100 | 🟠 | varied templates, no personal data except planted test phones |
| `category_llm` | str | | 🔵 | classifier output |
| `complaints_per_1000_units` | float | per month | 🔵 | TP-04 |

### 10.9 Side files
| File | Content |
| --- | --- |
| `answer_key.csv` | twin × month hidden truth: story (`scenario_id`), archetype, true progress, true cash, true occupied units, `label_distress_next_6m`; plus each complaint's true cause (`linked_event`) |
| `defects_log.csv` | defect id, table, rows affected, description, expected gate |
| `dictionaries/<table>.md` | every column: type, unit, valid range, meaning, origin |
| `cfg_assumptions.yaml` | every parameter with value + source record_id, or `assumption: true` |
| `cfg_scenarios.yaml` | story per twin + story shares |

---

## 11. Config example

```yaml
seed: 2026
horizon: {start: 2023-01, end: 2026-09}
twins: {n: 33, developers: 15}
cost:
  usd_per_m2: {low: 720, high: 1270, source: BEN-0004}
  imported_share: {value: 0.40, assumption: true}
sales:
  down_payment: {value: 0.085, source: Knight Frank Q1 2025}
  installment_years: {low: 7, high: 12, source: Knight Frank Q1 2025}
  post_float_demand_boost: {months: 3, factor: 1.4, assumption: true}
progress:
  ar1: {rho: 0.5, sigma: 0.15, assumption: true}
  season: {ramadan: -0.20, jul_aug: -0.10, eid_week: -0.30, assumption: true}
observation:
  dw: {noise_sd: 0.065, quarter_effect: [0.027, -0.055, -0.003, 0.040], source: calibration_stats.json}
  sar: {bare_db: -19.6, built_db_median: -14.9, noise_sd_db: 0.73, source: calibration_stats.json}
  report_missing: {normal: 0.05, stalled: 0.35, assumption: true}
utilities:
  kwh_per_unit: {value: 153, source: UTL-0001}
  persons_per_unit: {value: 3.8, source: DHS 2014}
  litres_per_person_day: {value: 290, source: HCWW}
complaints:
  base_rate_per_1000_units_month: {value: 4, assumption: true}
```

---

## 12. Build order and owners

| Day | Task | Owner | Reviewer |
| --- | --- | --- | --- |
| D1 (day 6) | `cfg_assumptions.yaml`, `cfg_scenarios.yaml`, `g_twins` | R2 | R1 |
| D2 (day 7) | Layer 2 truth + tables 1-5 (`g_twins`, `g_plan_monthly`, `g_progress_monthly`, `g_escrow_monthly`, `g_land_installments`) + hard consistency checks | R2 | R1 |
| D3 (day 8) | Tables 6-8 (`g_utilities_monthly`, `g_status_events`, `g_complaints`), observation models, the 6 defects, realism checks | R2 | R1, R4 |
| D4 (day 10) | Dictionaries for every table; realism report (one page: targets vs results); optional discriminator test | R2 | R5 |

**Done when:** all hard checks pass · calibration targets inside range · every defect logged with its row count · second run gives identical files.
