# SpaceEye: Final Project Plan (Inspection Priority Observatory, R7/R8)

English translation of the Arabic master plan (`PROJECT_PLAN.md`), 25 Oct 2026.

Paths under `real_data/` refer to the team's shared data folder (not in this repo).

**Final team version:** 24 October 2026
**Read with:** `data-report.md` (data and column details) · it replaces `01-specs.md` where the two differ (the reasons are in section 16).
**Team:** 5 people · **Remaining:** 6 working days (program days 6, 7, 8, 10, 11, 12; day 9 has no project work).

> **Read this first (one minute)**
> 1. We build a tool that tells the inspection committee **whom to visit first and why**, with evidence from space and from published statements. No guessing and no invented numbers on a real compound.
> 2. **Two tracks:** (A) real, on 29 compounds in R7/R8; (B) a "with your data" demo on virtual twins. It shows what the tool would add if ACUD gave us its internal data.
> 3. ✅ **The instructor approved** the use of real public data and compounds by name.
> 4. Any part marked **🧪 under testing** is not used as a base until its result is announced (section 6).

---

## 0. The plan on one page

| | |
| --- | --- |
| **The decision we serve** | Which compounds in R7/R8 should the inspection committee visit first in the next cycle, and why? |
| **Decision owner** | The Buildings & Facilities pillar lead; execution through the inspection committee. The system **recommends** and the committee **decides**. |
| **Cell (Project Compass)** | Type: **preventive** (an early-warning rule tested on the past) · Pillar: **Buildings & Facilities** · Condition: **normal** · Goal: **stability** (early detection of delay protects handover to residents and investor trust) |
| **Product** | A dashboard + **cycle list** (sized to inspection capacity) + a documented **inspection file** for each compound + a form to record the result of each visit. |
| **Track A: real** | 29 named compounds, classified into 4 priority levels from two signals: **"no observed change"** (from above: Google Dynamic World + for height and volume: Sentinel-1 radar) and **"announced handover date passed"** (statements + the deadlines of Decree 2184/2022). Together with them, the **"observed stage"** (structure / external works / complete), to tell "stalled" from "complete". **No generated number here.** |
| **Track B: "with your data"** | The same system on ~33 virtual twins + 8 generated tables that match data **owned by ACUD** (escrow, installments, approved schedule, supervisor reports, meters, complaints, warnings). A demo of capability, not proof of accuracy. |
| **Success criterion (measurable)** | (1) When the clock is frozen at 2024-Q2, the rule puts **≥ 2 of 3** confirmed delay cases (Venia, La Verde, Residence Eight) in level 1–2, **and does not** put Serrano, Catalan or Atika in level 1; (2) two runs = the same numbers; (3) 100% of AI numbers are matched in the log. *(Counts, not percentages: the sample is small.)* |
| **What we do not promise** | No "distress prediction" (توقع تعثر) for a real developer, and no "completion percentage" or "finishing percentage" from images. |
| **Closing message** | "This is what was possible with public data alone. Give us this data, and the demo parts become real operation." |

> ✅ **Instructor approval:** The program Compass (`07_Project_Compass.docx` §6) originally says "synthetic data only", **and the instructor gave the team permission** to use real public data and compounds by name. We still follow the controls: no internal ACUD data, every generated part is labelled "Synthetic - for training only", no generated number on a real name, and the list is a recommendation, not a verdict. *(The permission is mentioned in the use-case canvas on day 6.)*

---

## 1. Scope

### In scope
| Item | Why |
| --- | --- |
| 29 named compounds (R7: 12, R8: 17); 3 projects with no published name are excluded unless they are identified | The unit of analysis that management knows |
| **Google Dynamic World** quarterly 2016 → 2026-Q3 (✅ reviewed: GO with reservations) | Change **from above** up to 2026 |
| **Sentinel-1 radar** 2016 → 2026 (✅ initial test passed; independent review on D1) | It sees **height and volume**: it tells "standing still" from "building upward" when the area seen from above stays fixed; it is not affected by dust and clouds |
| **Google Open Buildings** 2016 → 2023 (✅ reviewed) | Independent confirmation + **building height in metres** up to 2023 (context; no free alternative after 2023) |
| **Observed stage** from vegetation (✅ NDVI from Sentinel-2) and paved roads (🟡 supporting) | Tells "stalled structure" from "external works/complete" with evidence from images, not only from the developer's word |
| Published statements and events (completion percentages, handover dates, start/completion of handover, postponement) | The second signal + the ground truth for the backtest |
| Decree 2184/2022 (12-month deadline, recovery after 24, 6-month regularization (توفيق أوضاع), deposit percentages) | Legal thresholds in force |
| Esri Wayback before/after images (visual display only) | Paint, windows, roads and landscaping are seen by eye in the inspection file |
| Dust days (8 confirmed storms) | A "review the scene" flag only |
| Operating loop: cycle list + recording the visit result | A real work tool, and it builds real ground truth over time |
| Simulator (8 tables) for Track B | Shows the value of ACUD's internal data |
| Inspection file agent + complaints classifier | The AI component |
| Value in EGP as a scenario with three settings | Required in the specs |

### Out of scope (even if we have the data)
| Item | Why |
| --- | --- |
| **"Finishing percentage" and "completion percentage" as numbers** | Interior plaster, ceramics and electrical work inside the apartments can never be seen from space; they belong in supervisor reports and meter connections (data request) |
| Talaat Moustafa disclosures, inflation, full interest-rate series, general market figures | They do not feed a decision in R7/R8 |
| Raw Sentinel-2 indices (NDBI, contrast (التباين)) as a main indicator | Dynamic World is clearer; they stay as a backup |
| Night lights per compound | 6–9 pixels; they stay at district level (context + occupancy calibration in the simulator) |
| Heat days as an indicator | No rule stops construction, and no proven effect |
| A 0–100 priority score with weights | It suggests precision that does not exist; replaced with levels |
| EOG, GHSL, WorldCover, Microsoft footprints | They add nothing to the decision |
| Generated inspections, ticketing system | Real visit results are recorded in `ops_visits` |
| Fairness check by developer size | No reliable size data; mentioned as a limitation |
| Any live online computation during the presentation | Everything comes from stored files |

---

## 2. Data used (summary)

Details are in `data-report.md`. We use only records marked `CONFIRMED` and `CONFIRMED_MINOR_FIX`.

| Data | Track | Feeds | Status |
| --- | --- | --- | --- |
| Compound register + boundaries | A + B | Unit of analysis, map, twin templates | ✅ (boundaries: 3 drawn, 6 with a location, 23 located by the team on D1) |
| Dynamic World: `built` + `grass`/`trees`/`water` | A (+ B calibration) | K1, K2, K4, observed stage | ✅ built reviewed · 🧪 the other classes |
| Sentinel-1 radar (VV/VH) | A | K1b (vertical change), K2 | ✅ initial test · D1 review |
| Open Buildings (built share + height) | A | Trend confirmation + height up to 2023 (context) | ✅ |
| Sentinel-2: vegetation share (NDVI > 0.2) | A | Observed stage | ✅ 95% |
| Sentinel-2 / 30 cm images: paved road share (asphalt) | A | Observed stage | 🟡 supporting (81%) |
| GEDI / ICESat-2 laser (height 2024–2026) | - | - | ❌ tried, not enough (section 6) |
| Statements and events | A + B | K3, completion rule, backtest, curve calibration | ✅ |
| Decree 2184 + Building Law 119 | A + B | Levels and escrow rules | ✅ |
| ACUD statements (7–8%, 6 terminations, review every 3 months) | A + B | Problem slide, comparison baseline, share of distressed stories | ✅ |
| Dust days | A | "Review the scene" flag | ✅ |
| Esri Wayback | A | Before/after images (display only) | ✅ |
| Black Marble night lights (district) | A (context) + B (calibration) | One chart + occupancy speed | ✅ |
| March 2024 shock + steel and cement + exchange rate | B | The shock and cost inflation | ✅ |
| Simulation references (land, installments, cost per m², building ratio ≤ 22.5% and occupancy factor 1.6 (ACUD 2018), down payment 8.5%/7.7 years, electricity and water) | B | Simulator parameters | ✅ |

---

## 3. Indicators and priority levels

### Track A (real)

**Method rules:** every comparison is **year over year** (Dynamic World is seasonal); we use `built_prob_mean` only; we say "observed built probability", not "area".

| # | Indicator | Formula | Type |
| --- | --- | --- | --- |
| K1 | Change from above (12 months) | ΔB₁₂ = mean `built_prob_mean` of the last 4 quarters − the previous four; "active" if > 0.03 (measured noise 0.01–0.03) | 🔵 derived |
| K1b | Vertical/volume change (12 months) | ΔVV₁₂ = mean radar VV signal (dB) of the last 4 quarters − the previous four; "active" if > 0.5 dB (the reference desert moves ±0.3; the threshold is fixed on D1) | 🔵 derived |
| K2 | Quarters with no observed change | Number of the latest consecutive quarters in which **neither** K1 **nor** K1b is "active" (if radar is not available for the compound: K1 alone, and this is written down) | 🔵 derived |
| K3 | Handover date clock | Months since the last announced handover date with no handover announcement (only what was published before the computation date); "not announced" if there is no date | 🟢 real |
| K4 | Assessability | ≥ 6 Dynamic World images in the last quarter + boundaries with confidence ≥ medium; otherwise "not assessable" | 🟢 real |

**Why K1b?** If the developer builds the ground floor and then continues upward, the area seen from above stays fixed, so the compound looks "standing still" unfairly. Radar bounces off walls and vertical surfaces, so it keeps rising as long as the building grows. A real example: plot 819189945. Open Buildings: built area fixed at ~18% from 2021 to 2023, while the radar rose from −9.4 to −7.5 dB, then stayed flat in 2024–2026 when the building was complete. **Its limit:** the signal saturates, so it says "changing or not", not "how many floors".

| From above (K1) | Radar (K1b) | Meaning |
| --- | --- | --- |
| Changing | Changing | Construction in progress |
| Flat | Changing | **Building upward / closing up the buildings: not stalled** |
| Flat | Flat | **No observed change** → counted in K2 |

### Observed stage (context column for each compound: vegetation ✅, roads 🟡, finishing by eye)

| Stage | Signs |
| --- | --- |
| Earthworks and foundations | `built` starts rising; radar starts rising |
| Construction in progress | K1 or K1b active |
| **Stalled structure** ⚠️ | No observed change **and** no signs of external works |
| External works | **Vegetation: share of NDVI > 0.2 from Sentinel-2** (✅ passed: 95% on the test sample, covers up to 2026) or **paved roads** (🟡 supporting evidence only: 81% from 30 cm images, barely met the condition) |
| Complete and occupied | External works + district lighting increases + handover announcement |

**Paint and external plaster:** ❌ **tested automatically and failed** (60% = the same as a blind guess): images from above do not show facades, and roof colour changes between satellites. They stay **by eye** in the two Wayback images inside the inspection file. Details: `real_data/24_surface_signals/results.md`.

**Height of each building up to 2023 (✅ real data):** footprints of 43,550 buildings from Google Open Buildings V3, with their yearly height from Open Buildings Temporal 2016–2023, classified as: low 3–8 m (1–2 floors) · partial 8–20 m · full ≥ 20 m. For each compound: the number of buildings and how many of them reached full height (example, Catalan 2023: 31 full, 20 partial, 1 low, out of 59). **It reveals "built one floor and stopped" at building level up to 2023.** Files: `real_data/22_height_model/`.

**Height (context, not an indicator):** "Mean observed height 2023: ~24 m (≈ 7–8 floors, estimated)" from Open Buildings, against the planned/permitted height: **ground + 7 floors, max 30 m** (official Decision 483/2023 for plot Ri8 in R8, Official Gazette). This is announced for only 7 compounds, from developer pages (Moraya, Residence Eight, LA REVA, LAYAL, Anakaji, Madai, Ri8). The usual floor height (~3–3.3 m) is **an assumption with no source yet**. **There is no free source of height after 2023** (the GEDI laser was tried and was not enough, and **shadow measurement in 30 cm images** was tried and did not pass the condition: compound error 5.8 m, correlation 0.45, `real_data/23_shadow_height/results.md`). So after 2023 we rely on radar ("is it still growing?") and a manual check with Wayback images. The only accurate solution: **stereo images (stereo)**: Pléiades Neo ~1,375 USD, or free through an ESA program with a request from the instructor.

### Priority level = the worse of two signals (no weights)

| Level | Condition | Action | Reference |
| --- | --- | --- | --- |
| 1 🔴 Inspect now | K2 ≥ 4 quarters, or K3 > 24 months, or (K2 ≥ 2 and K3 > 12) | Visit within two weeks + inform the pillar lead | 24 months = right of recovery (2184) |
| 2 🟠 Inspect this cycle | K2 = 2–3, or K3 = 13–24 | Within the cycle visits | 6 months = regularization; 12 = handover deadline |
| 3 🟡 Document review | K2 = 1, or K3 = 1–12 | Request the supervisor report and documents | Within the deadline |
| 4 🟢 Routine follow-up | Otherwise | Next cycle | - |
| ⚪ Not assessable | K4 failed | Locate the site/boundaries first | - |

- **Probable completion rule:** if the compound is "no change" **and** (observed stage "external works" or higher, **or** last statement ≥ 90%, **or** start/completion of handover was announced) → capped at level 3 with the flag "may be complete: confirm". **But "no change" without any sign of external works = stalled structure, and it rises as normal.**
- **Order within a level:** K2 descending, then K3 descending.
- **Cycle list:** the top N compounds according to **inspection capacity** (a parameter in `cfg_assumptions.yaml`, for example 8).

**Reason sentence** (a fixed template, filled by code):
"Level 1: no observed change from above or in height for 4 quarters; no signs of external works (no vegetation and no paved roads); the announced handover date (Q2 2024) passed by 28 months; the developer's last announcement 60% (September 2024, whole project); observation complete (11 images in the quarter)."

### KPI cards (10 fields + 2 tags, program format)

| Field | K1 from above | K1b radar | K2 no change | K3 handover clock | K4 assessability |
| --- | --- | --- | --- | --- | --- |
| Purpose | Is the built area increasing? | Is the building growing vertically? | For how long has there been no change? | Has it passed its commitment? | Do we trust the signal? |
| Unit | Probability difference (0–1) | dB | Quarters | Months | Yes/No |
| Source | Dynamic World | Sentinel-1 RTC | DW + Sentinel-1 | Statements + Decree 2184 | DW + boundaries |
| Frequency | Quarterly | Quarterly | Quarterly | At each statement/quarter | Quarterly |
| Owner (role) | Spatial data analyst | Spatial data analyst | Spatial data analyst | Developer follow-up officer | Data engineer |
| Baseline | Noise 0.01–0.03 (2016–2023) | Desert noise ±0.3 | 0 | The announced date | - |
| Target | Set by the owner (higher is better until completion) | Set by the owner | 0–1 | ≤ 0 | 100% |
| Thresholds | 0.03 | 0.5 dB | 2 / 4 quarters | 12 / 24 months | ≥ 6 images |
| Leading/lagging | Leading | Leading | Leading | Lagging | Guard |
| International axis | Urban planning | Urban planning | Urban planning | Housing | Governance/data |

Cards B1–B5 have the same fields in `kpi_cards.csv` (schema from `kpi_reference.csv` in the program pack). Axis names only, no ISO clause numbers.

### KPI tree
```
Strategic:    reliable handover in R7/R8                                   (owner: Buildings & Facilities pillar lead)
Tactical:     share of compounds in level 1–2  ·  K3 overruns             (owner: head of the inspection committee)
Operational:  K1 · K1b · K2 · K4 (guard) · share of cycle-list visits carried out   (owner: observatory team)
```

### Track B (virtual twins): 5 extra signals

| # | Indicator | Formula | Added to the levels as (🟡 stated assumption) |
| --- | --- | --- | --- |
| B1 | Escrow coverage | Escrow balance ÷ remaining cost; + is it ≥ the minimum in Decree 2184 | < 0.5 or below the minimum → level 2; with K2 ≥ 2 → level 1 |
| B2 | Land installment arrears | Number of late installments | ≥ 2 → level 2 |
| B3 | Complaint rate | 90-day complaints per 1000 units sold, against the twin's own history | Worst 5% → level 2 |
| B4 | Occupancy gap | Share of occupied units ≥ 6 months after handover | < 30% → "built with no residents" |
| B5 | Deviation from the approved schedule | Planned − actual progress (points) | > 20 → level 2 |

---

## 4. Analytical core

1. **The rule = the levels in section 3.** It is the product in Track A.
2. **Dynamic World: ✅ GO with reservations:** 36 values were recomputed with independent code and matched; the median correlation with Open Buildings is **0.95** on plots ≥ 2 hectares. Binding: year over year; `built_prob_mean` only; "probability", not "area"; 2024–2026 have no independent reference after 2023 (we rely on radar + Wayback + statements); the cloud filter is fixed.
3. **Radar: ✅ initial test passed:** it rises with construction (correlation 0.72–0.99 with Open Buildings on 8 plots), and the reference desert is stable. **Before adoption:** independent review on D1 + running it on the plots of the located compounds. Its limits: it saturates; fewer images in 2022–2024 (one satellite).
4. **Ground truth `eval_outcomes`:** Serrano (handover complete), Catalan (1,084 of 1,765), Atika (handed over), Residence Eight (phase 1 handover announced December 2025, after the Q2 2024 date), Venia (postponed 2024→2026→2027), La Verde (promised early 2023, no handover announcement). Any addition only with a confirmed source.
5. **Backtest:** we freeze the clock at 2024-Q2 and 2025-Q2 and apply the levels with data from before that date only. By name: where the rule placed each compound, what happened after, and by how many months the warning came before the postponement announcement. For each case, one line "what happened / why / what next" **and a competing explanation rejected with a number** (for example: "not completion: last statement 50%, and no vegetation and no paved roads"). Sample ~6–10: **no decimal percentages.**
6. **Simple sensitivity:** does the level 1–2 list change if the K1 threshold = 0.02 or 0.04, or if radar is removed? (One table: it shows what radar adds.)
7. **Track B comparison:** the rule with the two Track A signals only, against the rule + B triggers. Metric: of the top N each quarter, how many actually became distressed, and how many months earlier. **The statistical model is optional** (the Compass requires a measured model only for the predictive type, and we are preventive): a small logistic regression if time allows, with a time split + separation by twin.
8. **March 2024 event study (optional, the first thing to cut):** distribution of ΔB₁₂ before/after the shock. Wording: "Observed change slowed: completion or stagnation?".
9. **No leakage:** `published_date` filters statements; quarters ≤ computation date; boundaries are fixed (this is mentioned).

| Allowed to say | Not allowed to say |
| --- | --- |
| "No observed change from above or in height for X quarters" | "Distressed" (متعثر) about a real compound |
| "No signs of external works (vegetation/roads/water)" | "Completion 60%" or "finishing percentage" from images |
| "Passed the announced date by Y months" | "The model predicts distress with X% accuracy" |
| "Observed height 2023 ≈ 24 m (≈ 7–8 floors, estimated)" | "8 floors built" as a fact |
| "The rule would have put it in level 1 N months before the postponement announcement" | Any generated number next to the name of a real developer |

---

## 5. The simulator (Track B): 8 tables

> **(updated 25 Oct 2026)** Detailed generator design, noise models, realistic defects and final schemas: `synthetic-data-plan.md`. Where the two differ, `synthetic-data-plan.md` is the reference.

**Principle:** each table (1) has a real version at ACUD, and (2) feeds a signal. Every parameter is in `cfg_assumptions.yaml` with its source, or marked "assumption". Fixed seed. January 2023 → September 2026, monthly. **One script:** `simulate.py`. Every file is labelled "Synthetic - for training only" and has a data dictionary.

| # | Table | Feeds | Real version held by |
| --- | --- | --- | --- |
| 1 | `g_twins` | All | - |
| 2 | `g_plan_monthly` | B5 | Planning sector |
| 3 | `g_progress_monthly` (progress + facades + `dw_built_obs` + `sar_obs`) | B5, K1/K1b for the twins | Supervising engineer reports (art. 54) |
| 4 | `g_escrow_monthly` (sales, collection, deposit, withdrawal, balance, remaining cost) | B1 | Finance and banks |
| 5 | `g_land_installments` | B2 | Finance |
| 6 | `g_utilities_monthly` (electricity + water) | B4 | Utility company |
| 7 | `g_complaints` | B3 + complaints classifier | Customer service |
| 8 | `g_status_events` (warning, deadline, termination, monthly level) | Comparison target | Warning and termination records |

### Stories (`cfg_scenarios.yaml` = the answer key)
| Story | Share | What happens |
| --- | --- | --- |
| Healthy | ~55% | Built to plan, handover on time, rising occupancy |
| Slow but financially healthy | ~15% | 6–12 months late, good escrow, no distress |
| Gradual stall | ~10% | Weak collection → cash shortage → slowdown → stall |
| Stall after the March 2024 shock | ~8% | Cost jump + drop in collection after 6 March 2024 |
| Stall then recovery | ~7% | 6–9 month stall, then work resumes (tests false alarms) |
| Complete structure with weak occupancy | ~5% | Looks finished from space, no residents |

Result: about 8% reach "distressed", which is consistent with the ACUD statement.

### Generation logic (monthly, for each twin)
1. **Plan:** an S-curve over 36 months from land handover.
2. **Cost:** built-up area (land × min(coverage 18–22.5% × floors, 1.6), the ACUD occupancy factor) × cost per m² (720–1,270 USD × actual exchange rate) × steel and cement index.
3. **Sales and collection:** sales curve; down payment 8.5% + installments over 7.7 years; the story reduces collection after the shock.
4. **Escrow:** deposit = collection; minimum = Decree 2184 percentage by area category × phase cost; withdrawal = spending.
5. **Spending and progress (the linking loop):** actual spending = the lower of planned spending and available cash → progress follows spending.
6. **Land installments:** quarterly and equal; paid if cash is enough, otherwise late.
7. **Utilities:** during construction ∝ activity (🟡); after handover: occupied units × 153 kWh × a seasonal factor from real temperature; water = 3.8 persons/unit × 290 litres/day.
8. **Complaints:** ∝ units sold × base rate (🟡) × a multiplier on delay/stall; Arabic text for a sample of 200 only.
9. **Status:** ≥ 6 months with no progress → warning; date passed → delayed; > 24 months, or land arrears + escrow below the minimum → distressed; termination is rare (🟡).
10. **Generated observations:** `dw_built_obs` and `sar_obs` from progress + seasonality + noise, with the same statistics as the real series (radar saturates when the structure is complete).

**Consistency checks (failure = the output is not used):** the balance never goes negative · collection ≤ sales value · progress never decreases · occupied ≤ handed over · story shares close to target · same seed = same numbers.

---

## 6. 🧪 Under testing, and how we decide

| Experiment | Question | If it succeeds | If it does not succeed |
| --- | --- | --- | --- |
| ~~Observed stage from Dynamic World classes~~ **❌ vegetation/water: does not work** | The probabilities of grass, trees and water are ≈ 0.03 in all plots, even complete green ones (noise floor at 10 m) | - | **Replaced with the NDVI share from Sentinel-2 (✅ 95%)**: see the row "Vegetation, roads and finishing" below |
| **Paint/external plaster** from Sentinel-2 colour | Does a colour change appear after the structure, in painted ones only? | An extra sign of external works | By eye only, in Wayback images (expected) |
| ~~Height 2024–2026 with laser (GEDI / ICESat-2)~~ **❌ finished: not enough** | GEDI: no measurements after 2024 (532 in 2024, zero in 2025–2026); 0–14 measurements per compound per year, and Atika has zero in all years; in partly built plots the measurement reads the ground (~3 m). ICESat-2: few tracks, they do not pass over most compounds. Overture: only 5 buildings have a height | - | **Adopted:** height up to 2023 from Open Buildings (labelled "not updated after 2023") + radar for "is it still growing?" + planned floor count from developers + manual check with Wayback images for the top of the list + "permitted floor count" as a data request |
| **Height model 2024–2026** (Sentinel-1/2 → Google heights 2016–2023) **❌ did not pass the acceptance condition** | Tested on 2022–2023: compound error 3.0 m ✅, correlation 0.82 ✅, satellite bias ≤ 0.7 m ✅, **class classification 72% ❌ (condition 80%)**: it raises low compounds by ~+2.7 m. One pre-registered improvement attempt did not change the result | - | **We do not use its predictions.** It is shown in the presentation as an honest experiment that did not pass the condition (`22_height_model/validation_report.md`). **Adopted: height of each building up to 2023** (section 3) |
| **Height 2024–2025 from shadow length** (Wayback 30 cm images, 27 compounds) **❌ did not pass the acceptance condition** | Pre-registered test on 13 compounds the model had not seen: compound error **5.8 m ❌**, correlation **0.45 ❌**, classification 82% ✅; building level: error 4.7 m, classification 46% ❌; stability 2024–2025: 3.3 m ✅. **Exploratory (not pre-registered):** compound change 2021→2023 correlates 0.69 with the real change, and the 4 fastest-growing compounds appeared at the top | - | **We do not use its numbers.** A "still growing" signal at compound level needs its own pre-registered test before it can be stated (`23_shadow_height/results.md`) |
| **Vegetation, roads and finishing from images** | 50 cases with visual labelling before the computation, and the test on the held-out half | - | ✅ **Vegetation from Sentinel-2 (NDVI) 95%** → an automatic "external works" sign up to 2026 · 🟡 paved roads 81% (supporting only) · ❌ external finishing 60% (by eye only), `24_surface_signals/results.md` |
| **Independent radar review** | Does the computation repeat with independent code? And is the 0.5 dB threshold suitable? | K1b adopted | K2 on Dynamic World alone, and the limitation is stated |

The decision for each experiment is written in one line in `decisions_log.md`, with the date and the reason.

---

## 7. The AI component

### A) Inspection file agent (Track A, the core one)
- **Request:** "Prepare an inspection file for compound X at date T".
- **Tools (simple Python functions):** `get_facts` (the register + record_id + link) · `get_kpis` (K1–K4, level, observed stage, series) · `get_images` (the two Wayback images with capture date) · `get_rules` (articles of Decree 2184).
- **Flow:** code fills the template with the numbers, then the language model writes one paragraph from the attached facts only + **3 questions for the visit** (for example: "Is the work stalled or in interior finishing? Are the facades plastered/painted? Are the internal roads paved?").
- **File structure (program report format):** what happened · why (evidence + a competing explanation rejected with a number) · what it means · what we do (action + owner + date + **escalation trigger**).
- **Verification:** match every number, date and name against the source JSON; **flag causal words** ("because of", "because") for manual review.
- **`ai_verification_log`:** number · claim · its type · how we verified · what the data says · verdict (correct / wrong number / unsupported claim / missing context) · correction.
- **Output:** an Arabic HTML/PDF file, with the footer "Drafted by AI, reviewed by [name]" + the model and the request time. In the presentation: 5 stored files.

### B) Complaints classifier (Track B, capability demo)
- Mask numbers and names with regex **before** any model (Law 151/2020); the regex decides whether the file is valid.
- 5 classes (delay, work stoppage, payment and installments, quality, other) against a keyword baseline; an extra test on `complaints_30.csv` from the program pack.
- **Stated openly:** accuracy on texts we wrote does not prove accuracy on real complaints.

**Language model:** Gemini (the program tool) or whatever is available; outputs are stored for the presentation.

---

## 8. Operating loop

| Element | What it is | Why |
| --- | --- | --- |
| **Cycle list** | CSV/PDF with the top N compounds, with level, stage, reason sentence and a link to the inspection file | What the committee actually receives |
| **`ops_visits`** | A short form in the dashboard: compound, date, result (progressing / stalled / complete / not done), note | Builds ground truth with each cycle; recalibrates the thresholds |
| **Quarterly recomputation** | `run_all.py` when a new quarter is released | The monitoring plan |

**Short inspection procedure (proposed; the actual matrix is set by ACUD):**
1. Confirm the signal with a second source (radar/Open Buildings/Wayback image/last statement).
2. Open a line in `ops_visits`.
3. Level 1 → inform the pillar lead and visit within two weeks; 2 → within the cycle; 3 → request the supervisor report.
4. (Track B) Review complaints and escrow.
5. Record the result with the time, and close the line or escalate it.

---

## 9. Data pipeline and quality

**Tools:** Python + DuckDB + Streamlit only.

```
Project/app/
  data/raw/          ← copies of the files used from real_data (as they are)
  data/sim/          ← simulator outputs (Synthetic - for training only)
  config/            ← cfg_assumptions.yaml · cfg_scenarios.yaml
  src/
    ingest.py        ← load raw into DuckDB as it is
    gates.py         ← quality gates
    kpis.py          ← K1–K4, levels, stage and B1–B5 in SQL parameterized with $asof
    simulate.py      ← simulator (8 tables)
    backtest.py      ← backtest + sensitivity
    agent_file.py    ← inspection file + verification
    complaints.py    ← masking + classifier
  dashboard/app.py   ← Streamlit
  run_all.py         ← one command that builds everything
```
(The Dynamic World and radar download is done once with the ready `real_data/17_*` scripts, and the results are saved as CSV in `data/raw`.)

### Quality gates (9): rule + threshold + dimension + owner + decision (fix / flag / stop)
| Gate | Dimension | Rule and threshold | Owner | On failure |
| --- | --- | --- | --- | --- |
| Source | Accuracy | Every fact has a record_id and an accepted review verdict (100%) | R2 | **Fix**: excluded |
| Completeness | Completeness | ≥ 6 Dynamic World images in the quarter | R3 | **Flag**: "not assessable" |
| Validity | Validity | Probabilities 0–1; radar within a sensible range; dates valid | R1 | **Stop** |
| Uniqueness | Uniqueness | (compound, quarter) is unique | R1 | **Stop** |
| Consistency | Consistency | Every compound_id is in the register; row counts before/after each join are equal | R1 | **Stop** |
| Freshness | Freshness | Last quarter ≤ one quarter from the computation date | R3 | **Flag**: "stale" |
| Separation | Consistency | No g_* table is joined to a real compound; every displayed number carries its origin type | R1 | **Stop** |
| "Data or city?" | Accuracy | If > 30% of compounds move to "no change" in the same quarter → an event in the source | R4 | **Flag** the quarter and review |
| Stuck series | Accuracy | A value exactly identical for 4 consecutive quarters | R3 | **Flag** and review |

**Outputs:** `quality_checks_log.csv` (program template columns) + a quality report with an "impact on the indicator" column.
**Lineage:** `kpi_values` carries `source`, `run_id`, `computed_at`; storage is "delete then insert". `run_log`: when, what, rows, failed gates, duration. **The agent, the dashboard and the memo read from the same `kpi_values`.** Two runs = the same numbers.

---

## 10. The dashboard (Streamlit, 4 screens)

| Screen | Answers | Content |
| --- | --- | --- |
| 1 Priority map | Whom do we inspect first? | R7/R8 plots coloured by level, the **cycle list** with level, stage and reason sentence, a download button; grey = not assessable |
| 2 Compound file | Why this one? | Dynamic World curve (yearly) + radar curve + Open Buildings points (area and height) + "developer announced" markers + announced date line + **observed stage** + the two Wayback images + K1–K4 + "inspection file" button + visit recording form + lineage line |
| 3 Would it have warned early? | Backtest | "If we were in 2024-Q2 / 2025-Q2", by name; sensitivity table (with and without radar); district lighting |
| 4 Data trust | How much do we trust it? | Gates, coverage, dust days, not assessable, 846/863, colour key 🟢🔵🟠🟡 |

**Mode switch:** "Real: R7/R8" / "Demo with virtual data" (screens 1 and 2 on the twins + B1–B5 panel + a fixed orange banner). No shared map and no real names on the twins.

**Display rules (from the program):** 4 main tiles at most; each tile: value + unit + denominator + "as of" + origin type · **no card = no colour**, with a colour key, **and never colour alone** (the level is written as a word) · differences in grey · the five forbidden mistakes: a percentage without a denominator, a truncated axis, a comparison with a different season, an average that hides the spread, a coverage change without announcement · **the ten-second test** on screen 1.

---

## 11. Timeline

**Roles:** R1 data pipeline and quality *(Analytics Engineer)* · R2 real data and simulator *(Analytics Engineer)* · R3 GIS and space signals, then the complaints classifier *(Data Science Engineer)* · R4 analysis and agent *(Data Science Engineer)* · R5 dashboard and presentation *(Analytics Engineer)*.
**Calendar:** D1 = day 6 · D2 = day 7 · D3 = day 8 · *day 9 shift simulation: no project work* · D4 = day 10 (mid-term review) · D5 = day 11 (submission and knowledge transfer) · D6 = day 12 (presentation).

### D1 (day 6): foundation and sign-off
**Compass sign-off:** use-case canvas with the eight checks (cell, goal and why, decision and its owner, a complete KPI card [K2], success criterion, data plan, risks and responsible AI, feasibility) + mention of **the instructor's permission for real data** in the data plan + ask the instructor about **the assessment criteria and the presentation length**.

| Who | Task | Output |
| --- | --- | --- |
| **Everyone (2 hours)** | Locate 23 named compounds (≈ 5 per person) on Google Maps or the developer's official map; priority to those with known outcomes (Venia, La Verde, Residence Eight, Park Lane, Anakaji, Scenario, Kardia, Moraya, Armonia, The Loft). Broker sites are forbidden | `locations_team.csv`: `project_id, lat, lon, method, url, confidence` |
| R1 | `app/` structure, `ingest.py`, first 4 gates, `run_all.py` skeleton | DuckDB with the real tables |
| R2 | `r_compounds`, `r_progress_announced`, `r_project_events` from the confirmed records; `eval_outcomes`; `cfg_assumptions.yaml` and `cfg_scenarios.yaml` | Tables + the two config files |
| R3 | Snap the points to OSM plots; draw a polygon where there is no plot; area check (0.6–1.5) | Initial GeoJSON |
| R4 | Fix the K1 (0.03) and K1b (0.5 dB) thresholds; independent radar review; decisions on the section 6 experiments in `decisions_log.md` | Half-page memo |
| R5 | Skeleton of the four screens | Skeleton dashboard |

**Done if:** the Compass is signed · ≥ 20 compounds located · ingest works · the two config files are written · the decisions (section 14) are signed.

### D2 (day 7): first real list + start of the simulator
| Who | Task | Output |
| --- | --- | --- |
| R1 | K1–K4 and the levels in SQL with `$asof`; `kpi_values`, `run_log` | KPI table |
| R2 | `simulate.py` tables 1–5 + consistency checks | Half of the simulator |
| R3 | Dynamic World (all classes) **and radar** for the new polygons (the scripts are ready); observed stage; Wayback images | Series + stages + images |
| R4 | Cycle list at 2026-Q3 + reason sentence + the test "every number in the sentence = its value" | First real list |
| R5 | Screens 1 and 2 with real data | Map + compound file |

**Done if:** the first real cycle list, with reason sentences.

### D3 (day 8): evaluation
| Who | Task | Output |
| --- | --- | --- |
| R4 | Backtest (2024-Q2, 2025-Q2) + sensitivity (with and without radar) | Table by name |
| R2 | `simulate.py` tables 6–8 + all consistency checks | The full simulator |
| R1 | The nine gates; `run_all.py` from raw to dashboard; two identical runs | One command that works |
| R3 | Polygon review with a second signature; final "not assessable" list; start the masking in `complaints.py` | Final GeoJSON |
| R5 | Screens 3 and 4 + mode switch + `ops_visits` form | Dashboard with the full structure |

**Done if:** backtest table by name · `run_all.py` builds everything.

### D4 (day 10): mid-term review + Track B, the agent and the freeze
**Morning: mid-term review (10 minutes):** first cycle list + backtest + early dashboard + risks.

| Who | Task | Output |
| --- | --- | --- |
| R4 | B1–B5 + comparison of the two rules (+ the model if time allows); inspection file agent + verification; 5 stored files; method card and monitoring plan | Comparison + 5 files + verification log |
| R3 | Complaints classifier against keywords; governance cards for 3 datasets | Result + 3 cards |
| R5 | Final dashboard; decision memo (Arabic/English); value-in-EGP slide | Dashboard + memo |
| R2 | Data dictionary for each generated table; ACUD request list; risks and responsible AI note; wording audit | Dictionary + list + note |
| R1 | **Code freeze**; technical documentation; operating guide; draft knowledge transfer pack | README + draft |

**Done if:** one command builds everything · dashboard + cycle list + 5 inspection files + decision memo.

### D5 (day 11): submission and knowledge transfer + rehearsal
Submit all files · **knowledge transfer pack** (how to rerun every quarter, the owners, what may break, the `cfg` files, the `ops_visits` loop) · two timed rehearsals · backup video · **the ten-second test** · cross-review (a source for every number, origin type visible, no "distressed" on a real compound) · **fixes only.**

### D6 (day 12): presentation to the ACUD committee
The live demo follows the dashboard routine: **status scan → freshness check → comparison → deep dive → decision.**

---

## 12. Deliverables and presentation

### Deliverables (13)
| # | Deliverable | Owner |
| --- | --- | --- |
| 1 | KPI cards (10 fields + 2 tags) and their tree + the levels table | R5 |
| 2 | Data pipeline with gates (`run_all.py`) + `quality_checks_log.csv` + quality report | R1 |
| 3 | Analytical core: the rule, backtest, sensitivity, Track B comparison | R4 |
| 4 | Operational dashboard + cycle list + `ops_visits` | R5 |
| 5 | **Method card** (purpose, rule, data, thresholds, limits, known failure modes, what it was tested on) + **monitoring plan** (coverage, share of not assessable, drift in the level distribution, visit hit rate, frequency, owner) | R4 |
| 6 | Risks and responsible AI note (principles of Law 151/2020; who sees what: raw/masked/aggregated; fairness limits: observation bias by plot size and building type; misuse: reading the list as a verdict) + `ai_verification_log` | R2 + R4 |
| 7 | Technical documentation and user guide + governance cards + data dictionary for the generated tables | R1 + R2 + R3 |
| 8 | **Decision memo**, one page per language: the decision yes/no first → recommendation → 3 facts, each with its denominator → 2–3 options, including "no change" → risks and mitigation → owner, date and review date. The same facts and order in both languages | R5 |
| 9 | **Knowledge transfer pack** (one page) | R1 |
| 10 | One run command that works during the presentation | R1 |
| 11 | Inspection files for five compounds | R4 |
| 12 | List of data requests to ACUD | R2 |
| 13 | The final presentation | R5 |

### Presentation (11 slides, 12–15 minutes; length to be confirmed with the instructor)
1. **The problem in numbers:** > 400 developers and > 500 projects; field review every 3 months (according to the statement of the ACUD chairman); 7–8% are seriously delayed; 6 terminations by mutual consent.
2. **The question and the decision:** whom do we inspect first? The observatory ranks, and the committee decides.
3. **Data:** 846 documented facts out of 863, and no invented number; origin key; nothing generated in the real list.
4. **How we see construction from space:** on one plot: Dynamic World (from above) + radar (height) + Open Buildings (24 m ≈ 7–8 floors) + Wayback before/after image.
5. **Two signals → 4 levels + observed stage:** the levels table and its legal reference; "stalled" against "complete".
6. **Live demo:** R7/R8 map, cycle list, open a compound, reason sentence, inspection file, record a visit.
7. **Backtest:** if we had applied the rule in mid-2024, where would it have put Venia / La Verde / Residence Eight against Serrano / Catalan?
8. **"With your data":** switch the dashboard: escrow eroding after the shock, land arrears, rising complaints, and the warning appears before the observed change stops; the complaints classifier.
9. **Value in EGP** (a scenario with three settings).
10. **Risks and responsible use.**
11. **What we ask from ACUD** + the next step.

**Data request list (in order of impact):**
1. Plot boundaries and the developer allocated to each plot in R7/R8
2. The approved schedule and the contractual handover dates
3. Quarterly supervising engineer reports (art. 54 of Law 119/2008): **the only source that states the completion percentage and interior finishing**
4. Field review records and their results
5. Record of warnings, deadlines and terminations
6. **Building permits and the permitted number of floors for each plot** (Law 119 requires the permit number and the number of licensed floors to be stated in sales contracts, art. 67; and ACUD launched an electronic permit system in December 2025, so the data exists in digital form)
7. Land installments and arrears
8. Escrow account balances and collection
9. Meter requests, occupancy certificates (art. 62) and consumption readings
10. Anonymized complaints from unit buyers

### Value in EGP (no double counting)
```
Annual value    = cost of the current policy − cost of the proposed policy
Current policy  = (number of projects × 4 visits) × cost per visit
Proposed policy = (cycle-list visits × 4) × cost per visit + system operating cost + (cases we missed × cost of late detection)
```
Three settings in `cfg_assumptions.yaml`. Wording: "Under these assumptions, from X to Y million EGP per year".

### Expected questions
| Question | Answer |
| --- | --- |
| Are the numbers real? | The whole list comes from real data, with its sources; the financial part is a demo on virtual twins, and it is labelled as such. |
| Are you saying a developer is distressed? | No. We say "no observed change since X" and "passed its announced date by Y". The decision belongs to the committee. |
| How do you trust space images? | Three independent sources agree: Dynamic World and Open Buildings (correlation ~0.95) and radar (a physical measurement), and we recomputed independently. We say "observed change", not "measured area". |
| A developer built one floor and stopped? | From above it stays flat, radar stays flat, and there is no vegetation and no roads → "stalled structure" rises in the list. And if the developer keeps building upward, radar rises, so it is not treated unfairly. |
| What if the compound is complete? | Vegetation, water, paved roads and the handover announcement lower its level and ask for confirmation, and the inspection file asks the question openly. |
| Why no completion or finishing percentage? | Images see from above, not interior plaster and ceramics. These are in the supervisor reports, and we request them. |
| Weather? | A "review the image" flag on dust days; and radar is not affected by dust at all. |
| What do you need from us? | The list on the last slide; each item turns part of the demo into real operation. |

---

## 13. Risks and fallback

| Risk | Fallback |
| --- | --- |
| A problem in Dynamic World | Open Buildings for history + radar + Sentinel-2 v2 (reference REF_A) for 2024–2026; the claims become narrower |
| Radar does not pass the review | K2 on Dynamic World alone; the completion rule partly compensates; the limitation is stated |
| The section 6 experiments do not succeed | The alternatives are written in section 6; nothing in the core plan depends on them |
| Boundaries for fewer than 20 compounds | The product works on the located ones; the rest are "not assessable" and become a data request. No guessing |
| Earth Engine / slow radar download | All results are stored as CSV; the download is done once on D2; no live computation in the presentation |
| Little ground truth | Present by name, with no accuracy claim |
| Wayback images (Esri terms) | Display only, with source attribution, and the capture date, not the release date; not used in any computation |
| Mixing generated data with real data | Mode switch + orange banner + no shared map + no real names on the twins |
| Objection from a developer | Neutral wording; "drawn by the team, not legal boundaries"; the list is a recommendation |
| Lack of time | **Cut order:** event study → statistical model → complaint texts and their classifier (the rate stays as a count) → language model paragraph (the template stays) → utilities table → observed stage (the completion rule based on statements stays) → Wayback images → screen 3 as a slide. **Track A and the cycle list are not cut.** |

---

## 14. Decisions to be signed on D1

| # | Decision | Proposal |
| --- | --- | --- |
| 1 | Tracks A (core) + B (demo, 8 tables) | Approve |
| 2 | Dynamic World as the main metric + radar as a second signal | ✅ DW adopted; radar after the D1 review |
| 3 | Thresholds K1 = 0.03 and K1b = 0.5 dB + the levels table | Fixed on D1 and not changed after D3 |
| 4 | Boundary acceptance | Confidence ≥ medium + area ratio 0.6–1.5 + two signatures |
| 5 | Developer names in the real list | Only with the binding wording, and only for compounds with accepted boundaries (✅ the instructor permitted real data) |
| 6 | Label for generated files | "Synthetic - for training only / مولّد - للتدريب والعرض فقط" (the Arabic part means "generated - for training and demo only") |
| 7 | Questions for the instructor on day 6 | Assessment criteria (rubric) · presentation length |

---

## 15. Definition of project completion

- The success criterion in section 0 is met and shown honestly (or its failure and the reason are shown).
- `python run_all.py` builds everything from the raw files to the dashboard and the cycle list, and two runs = the same numbers.
- Every gate has a dimension, an owner and a decision in `quality_checks_log.csv`.
- Every number in the dashboard and the presentation has a source or a visible origin type (🟢🔵🟠🟡).
- No generated number touches a real compound; no "distressed" and no "finishing percentage" on a real compound.
- The backtest is shown honestly, even if the rule was wrong.
- Every number written by a language model is matched in `ai_verification_log`.
- Every experiment in section 6 has a written decision in `decisions_log.md`.
- The 13 deliverables are ready, and the presentation is rehearsed twice, with a backup video.

---

## 16. Why this plan (decision log)

### A) What we changed from `01-specs.md`
| In the specs | The problem | What we did |
| --- | --- | --- |
| Decree 2184: deposit 10–30% | **Factual error:** the deposit is 20/15/10/5/3%; the 30% figures are completion percentages | Corrected from the Cabinet portal |
| Progress = NDBI from Sentinel-2 | NDBI does not measure construction in the desert (proven with data) | Dynamic World + radar, confirmed with Open Buildings |
| Automatic exclusion of dust and heat days | No decision stops construction in the heat; one dust day does not change a month's progress | "Review the scene" flag only |
| Value-in-EGP equation | **Double counting** + an annual period against a 16-month test | One equation: current − proposed |
| "Stall within 8–12 weeks" | A number with no reference | 6 months = regularization deadline |
| "NDBI flat 6 times" = data error | It may be a real stall | Removed |
| Horus city and 33 generated compounds | They do not serve to show anything real | 29 real + virtual twins for the demo |
| Success = 80% recall, 60% precision (دقة) and 50% reduction | Measured on an answer key we wrote ourselves | Backtest on real outcomes, by name |
| Electricity and water from the training pack | Aggregated over the area, and for 2026 only | A generated table based on real references + real district lighting |
| Fairness check by developer size | No size data | Mentioned as a limitation |
| Presentation: "red compound, then a storm" | Contradicts the specs' own rule | Removed |
| Daylight saving time gate and the unrelated pack tables | Our data is monthly/quarterly | Removed |

### B) Plan review decisions
| Change | Reason |
| --- | --- |
| Weighted 0–100 score → 4 levels = the worse of two signals | The score suggests precision that does not exist, and its weights are hard to defend; the levels are tied to the deadlines of Decree 2184 and are explained in one sentence |
| **Adding radar (K1b)** | Dynamic World sees from above only, so it is unfair to those who build upward; radar sees height and volume and is not affected by dust; proven in the initial test |
| **Adding the observed stage (vegetation, water, roads)** | The image alone cannot tell "complete" from "stalled"; external works are evidence independent of the developer's word |
| **Height as context, not an indicator** | Open Buildings gives height up to 2023 only; laser for some compounds; we do not promise a floor count |
| **No "finishing percentage"** | Interior finishing cannot be seen from space; external paint is seen by eye only, in high-resolution images |
| Cycle list + `ops_visits` | A real work tool and ground truth built over time; instead of the ticketing system |
| Threshold 0.03 instead of 0.02 | The review measured the noise at 0.01–0.03 |
| March 2024 event study optional | It does not feed the decision and may be misunderstood |
| Spreading the simulator over D2–D3 | 8 tables in one day for one person is a risk |

### C) What we took from the program lectures
KPI card with ten fields and two tags · three-level tree · gates (dimension + owner + fix/flag/stop) + the "Data or city?" and stuck series gates · lineage (`kpi_values` with source/run_id) · dashboard rules (4 tiles, no card = no colour, ten-second test) · report format (what/why/what it means/what we do + rejected competing explanation) · verification log with four verdicts · decision memo in the program format · knowledge transfer pack and governance cards · the actual calendar (day 9, review on day 10, submission on day 11) · Compass §6 alert (resolved: the instructor permitted real data).

**What we left out:** the weighted composite indicator · Oasis data cleaning · scheduling tools and Pandera · the full shift simulation · prediction models and anomaly detection · ISO clause numbers.

### D) Program templates we reuse
| Template | Use |
| --- | --- |
| `templates/D03_quality_checks_log.xlsx` | Columns of `quality_checks_log.csv` |
| `templates/D02_data_quality_report.xlsx` | Quality report with an "impact on the indicator" column |
| `handouts/D03_governance_card.pdf` | Governance cards |
| `docs/kpi_reference.csv` | Schema of `kpi_cards.csv` |
| `snippets/helpers.py` → `ar()` | Arabic text in charts and PDF |
| `store()`/`run()`/`run_log` code (day 4 lecture) | Basis of `run_all.py` |
| `generator/` and `answer_key.md` (day 1–2 pack) | Simulator pattern and answer key |
| `labs/D03/complaints_30.csv` + the key | Extra test for the complaints classifier |

*(The paths are inside the `oasis_datakit` pack, in the day folders.)*
