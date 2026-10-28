# 01-specs.md

> Implementation update,28October2026: this full product design is retained from the team's latest main branch. The current R1/R2 data implementation is specified in [IMPLEMENTED_DATA_SPEC.md](../data/IMPLEMENTED_DATA_SPEC.md), [DATASET_CONTRACT.md](../data/DATASET_CONTRACT.md) and [HANDOFF.md](../data/HANDOFF.md). Current scope12R7 compounds,capacity4,K5policy proxy/assumed EGP,K6priority,180rows/40features. Three-class labels exist; no new classifier or dashboard was trained/built. Older percentages/counts and pending statuses in this design are historical or planned, not current validation.

# SpaceEye: R7 Digital Twin and Inspection Priority Observatory (New Administrative Capital)

Last updated: 27 Oct 2026 · Team of 5 · Data and column details: [`03-dataset.md`](../project-definition/03-dataset.md)

> **Synthetic data - for training only** applies to every generated table, chart and slide. Real public data is used as published, with its source.

This file and `03-dataset.md` retain the full product design. Current implemented-data behavior is documented in `docs/data/`. Superseded drafts are retired from the repository and retained in local backups/Git history;they are not active plans. Section15records earlier design changes,not new implementation evidence.

`docs/.internal/archive/SpaceEye.md` (27 Oct 2026, Arabic) is the plain-language team explainer. It is secondary: **when it disagrees with these two files, these two files win.** Its new results are merged here (section 15 B).

---

## 0. The plan on one page

| | |
| --- | --- |
| **Decision we serve** | Which compounds in **R7** should the inspection committee visit first in the next cycle, and why? |
| **Decision owner** | Buildings & Facilities pillar lead, through the inspection committee. The system **recommends**; the committee **decides**. |
| **Compass cell** | Type: preventive · Pillar: Buildings & Facilities · Condition: normal · Goal: stability (early detection of delay protects handover and investor trust) |
| **Product** | Dashboard + **cycle list** sized to inspection capacity + an **inspection file** per compound + a form to record each visit result |
| **Unit** | **R7 compounds only.** Of the 22 compounds confirmed in R7/R8 (boundary confidence ≥ 80%), only those in R7 stay; **R8 is removed to reduce scope**. Count: open item 4. Codes only (`C..`), developers `D..`. |
| **One idea** | **Inspection priority:** whom should the committee visit first this quarter, and why. Early warning is part of it, not a separate product. |
| **Digital twin (light, compound level)** | The twin of R7 = for each compound: **observed state** (Track A, synced quarterly from satellites and statements) + **simulated hidden state** (generator: sales → cash → spending → progress → handover, Track B) + **what-if scenarios** (change an input, see which compounds move up in priority; section 9 screen 5). Not a 3D / building-level / live twin (section 1). |
| **Track A: images** | Everything read from images (Dynamic World, Sentinel-2, Open Buildings, Wayback) → per compound-quarter: activity score A, K2, K4, vegetation, height (to 2024), finishing flag (if its test passes). With K3, K5, K6 from statements it drives the **priority level** (worst of the signals, no weights, section 2), the **map** and the **cycle list**. All real data. |
| **Track B: numbers** | One tabular dataset `ml_dataset` (1 row = compound × quarter): **features X** = Track A outputs + K3, K5, K6 + ACUD-data inputs (B1-B5, generated today) → **label y** = outcome in the next 6 months: `distressed` / `completed` / `ongoing`. A **classification model** (logistic vs gradient boosting) learns y. It consumes Track A's outputs, so image work is never duplicated. Generated data → "Synthetic - for training only"; its probabilities show next to the rule in the compound file, never on the map. |
| **Success criterion** | Fixed on 26 Oct 2026, before any computation: with the clock frozen, the satellite rule puts **≥ 5 of the 8** real delay cases in level 1-2 at least **6 months** before the delay became public. Plus: two runs give identical numbers; 100% of AI-written numbers match the log. **Track B (generated):** the pass condition written in `EW_PROTOCOL.md` before the early-warning run (recall@8 threshold, above random); its exact wording goes here (open item 1, section 16). |
| **What we do not promise** | No "distress prediction" for a real compound, no "completion %" or "finishing %" from images. |
| **Closing message** | "This is what public data alone can do. Give us your data, and the demo parts become real operation." |

### The key result so far (everyone must understand it)

> **Scope note:** the results below are from the **first build on R7 + R8 (22 compounds)**. They are re-run on R7 only (open item 4); until then they are quoted as "first build, R7+R8".

- **Backtest: the satellite rule alone warned early on only 1 of 8 late cases** (target was 5). The criterion failed and is shown honestly.
- **Why:** all 8 were still building until close to their deadline. Their delay happened in **finishing and handover**, which satellites cannot see.
- **Meaning:** satellites tell "building or not" well. **Early warning of delay needs ACUD's data** (supervisor reports, contractual dates, meters, escrow).
- **So Track B adds ACUD's data as features.** The presentation shows the difference in numbers: images alone (Track A) vs images + ACUD data (Track B, generated today).
- **Early-warning result (generated data, first build at commit `a0f03fd`):** recall@8, the share of truly distressed compounds that were in the top 8 of the quarter's list: **satellites + company data 92% · satellites alone 62% · random 37%**. Method and split behind the 92%, and the recall@8 of the product rule itself (public + ACUD signals): *open item 1 (from `app_data/EW_REPORT.md`)*.
- **Caveat:** these numbers are on generated data. They show the idea works; they are not accuracy on reality.

**Presentation message:** "Satellites see that buildings exist, but not the delay, because the delay happens in finishing. ACUD's data completes the picture: with it the warning catches 92% instead of 62% (generated data)."

---

## 1. Scope

### In scope

| Item | Why |
| --- | --- |
| Coded compounds in R7 (boundary confidence ≥ 80%) | The unit management knows; smaller scope |
| Light compound-level digital twin of R7 + what-if screen | Observed state + simulated hidden state + scenarios |
| Google Dynamic World quarterly, 2016Q1 → 2026Q3 | "Is it building?" from above, up to 2026 |
| Activity score A (DW trend + DW class shares + Sentinel-2 indices) | Passed 5 tests; the base indicator (section 4) |
| Sentinel-2 vegetation share (NDVI) | "May be complete" sign (95% on the test sample) |
| Google Open Buildings heights 2016-2023 (+ 2024 v4 estimate ±2 m) | Context in the compound file, not part of the level |
| Published statements and events (promises, announced %, handover) | Second signal (K3) + backtest ground truth |
| Decree 2184/2022 and Building Law 119/2008 | Legal thresholds for levels and cover |
| Esri Wayback before/after images, 2 per compound | Display, judged by eye. Also the input of the finishing experiment (section 4), which stays out of the level |
| Monthly drivers: USD/EGP, policy rate, rebar, cement, temperature, Ramadan/Eid | Anchors for the generator |
| Generated ACUD data (stand-in until ACUD provides the real tables) | Feeds B1-B5 and Track B features |
| Track B classifier (logistic vs gradient boosting) on `ml_dataset` | Learns distressed / completed / ongoing from images + numbers |
| K5 fine exposure and K6 never-started clock | Catch compounds that never build or sit past their grace period |
| Inspection file agent + complaints classifier | The AI component |
| Value in EGP as a 3-setting scenario | Required by the program |

### Out of scope (even if we have the data)

| Item | Why |
| --- | --- |
| Compound or developer **names** in any table, chart, file or dashboard | Rule since 26 Oct; an automatic gate stops the run (one exception: the backtest slide, section 12) |
| Sentinel-1 radar | Detected construction in only 63% of cases; dropped |
| "Completion %" or "finishing %" as numbers | Interior work cannot be seen from space |
| Monthly monitoring | Noise is larger than the signal; quarterly only |
| Finishing from Sentinel-2 (colour, brightness, NDVI, water index, bare soil, texture) | 67%, target 75%: a signal, not enough. By eye in Wayback until the vision-model test passes |
| Our height model for 2024-2026 | Failed its independent test (69-74%, target 80%); not shown in the product (section 4) |
| Paved roads as a real indicator | 81%, too weak; it lives in the generated tables (`roads_paved_share`) |
| A weighted 0-100 priority score | Suggests precision that does not exist; replaced by levels |
| Night lights per compound | 6-9 pixels; district context only |
| Heat days as an indicator, dust exclusion | No rule stops construction; at most a "review the scene" flag |
| Live online computation in the presentation | Everything comes from stored files |
| District R8 (and any other district) | Removed to reduce scope; R7 only |
| A full 3D / building-level / live digital twin | Our 2024-2026 heights failed their test, no BIM models, quarterly data only, no real ACUD data, ~6 days left |
| A separate schedule-tracking product | One idea: schedule tracking lives inside the rule as B5 |
| A fine amount in EGP on a real compound | No published fine rate; the rate is in each allocation contract (data request). EGP only on generated data |
| Readings every 5 days | Noise above signal (monthly already failed); quarterly only |

---

## 2. Indicators and levels (Track A rule; the same signals are Track B features)

**Method rules:** every comparison is year over year (Dynamic World is seasonal). We say "observed built probability", never "area". All thresholds live in `configs/data.yaml` and are not changed after seeing results.

| # | Indicator | Definition | Origin |
| --- | --- | --- | --- |
| K1 | 12-month DW change | Mean `built_prob_mean` of the last 4 quarters minus the 4 before; growth if > **0.02**. Kept as an input to A and as the baseline A must beat | 🔵 |
| **A** | **Activity score** | Gradient-boosting probability that the compound is building this quarter, from DW trend, persistence, DW class shares and Sentinel-2 window means. Trained on plot windows ending 2019Q1-2023Q4, labels from Open Buildings | 🔵 |
| K2 | Quarters with no activity | Consecutive latest quarters where A is below its threshold, **counted only after construction started** (4 consecutive active quarters, or a published launch/delivery event). Before that: "not started" | 🔵 |
| K3 | Handover clock | Months since the **first** announced handover date with no handover announcement. Later promises **never reset** it. Only statements published before the as-of date count | 🟢 |
| K4 | Assessability | ≥ 6 Dynamic World images in the quarter + boundary confidence ≥ 80%; otherwise "not assessable" | 🟢 |
| **K5** | **Fine exposure** (غرامات) | Two parts. **(1) Months in a fine-eligible state** (real): months past the first deadline with construction never started, plus months past the 12-month grace (K3 > 12). **(2) Fine amount in EGP** (Track B, generated only): eligible months × assumed monthly rate × land value; the rate is 🟡 `assumption: true` until ACUD gives the contract rate | 🔵 / 🟠 |
| **K6** | **Never-started clock** (مش بيبني أصلاً) | Months since the first published launch or promise with **no construction start** (no 4-quarter run of activity). The land allocation date would be better (data request) | 🔵 |

### Priority level = the worst of K2, K3 and K6 (no weights)

The term is **priority level** (Arabic: مستوى أولوية التفتيش), never "risk level". It says whom to visit first, not that a developer is in trouble. Example: C05 is level 1 because its first date passed 25 months ago, yet it may be finishing interiors; the visit decides.

| Level | Condition | Action | Legal reference |
| --- | --- | --- | --- |
| 1 🔴 Inspect now | K2 ≥ 4, or K3 > 24, or (K2 ≥ 2 and K3 > 12), or **K6 > 24** | Visit within two weeks + inform the pillar lead | 24 months = right to refund (2184) |
| 2 🟠 Inspect this cycle | K2 = 2-3, or K3 = 13-24, or **K6 = 13-24** | Within the cycle's visits | 12 months = handover grace |
| 3 🟡 Document review | K2 = 1, or K3 = 1-12 | Request the supervisor report | Within the grace period |
| 4 🟢 Routine | Otherwise (started) | Next cycle | - |
| Not started | No construction start, K6 ≤ 12 and no K3 date passed | Watch | - |
| ⚪ Not assessable | K4 failed | Fix location/images first | - |

K5 does not set the level on its own (its eligible months already come from K3 and K6); it is shown in the compound file and is a Track B feature.

**With ACUD data** (same rule, more signals; from `add_rule_columns` at `a0f03fd`):
- any of B1, B2, B3, B5 triggered → level at least **2**;
- B1 (cover below the decree minimum) **and** K2 ≥ 2 → level **1**;
- B4 (occupancy gap) is context in the compound file, not a trigger.

- **"May be complete" rule:** handover announced, or vegetation share ≥ 0.10 → level capped at 3, flag "may be complete: confirm on site".
- **Order inside a level:** K2 descending, then K3 descending.
- **Cycle list:** the top N compounds with level 1-3; N = inspection capacity (`cycle_capacity`) ≈ **a third of the R7 compounds** (was 8 for 22 compounds; with R7 only, 8 would be almost every compound). Exact N: open item 4.

**Reason sentence** (one fixed template, filled by code, codes only). **Arabic** in everything the committee sees (dashboard, cycle list, inspection file); English in code and logs. English form of the template:
"Level 1: no building activity for 4 quarter(s) (activity score 0.12); first announced handover date (Jun 2024) passed by 27 months; observation complete (14 images in the quarter)."
Arabic example: "مفيش نشاط بقاله 3 أرباع، والميعاد المعلن فات بـ 8 شهور".

### KPI cards (10 fields + 2 tags, program format)

| Field | A activity | K2 no activity | K3 handover clock | K4 assessability | K5 fine exposure | K6 never started |
| --- | --- | --- | --- | --- | --- | --- |
| Purpose | Is it building? | For how long has it not been? | Has it passed its first commitment? | Can we trust the signal? | How long has it been fine-eligible? | Is land held without building? |
| Unit | Probability 0-1 | Quarters | Months | Yes/No | Months (real); EGP (generated only) | Months |
| Source | Dynamic World + Sentinel-2 | A | Statements + Decree 2184 | DW + boundaries | K3, K6 + contract fine rate (assumed) | A + statements |
| Frequency | Quarterly | Quarterly | Per statement / quarter | Quarterly | Quarterly | Quarterly |
| Owner (role) | Spatial data analyst | Spatial data analyst | Developer follow-up officer | Data engineer | Developer follow-up officer | Spatial data analyst |
| Baseline | K1 (DW change alone) | 0 | First announced date | - | 0 | First launch / promise date |
| Target | Set by owner | 0-1 | ≤ 0 | 100% | 0 | 0 (started) |
| Thresholds | Model threshold (out-of-fold) | 2 / 4 | 12 / 24 | ≥ 6 images | Context, no level | 12 / 24 |
| Leading/lagging | Leading | Leading | Lagging | Guard | Lagging | Leading |
| International axis | Urban planning | Urban planning | Housing | Governance/data | Governance/data | Urban planning |

Axis names only, no ISO clause numbers. Schema follows `kpi_reference.csv` from the program pack.

### KPI tree

```
Strategic:    reliable handover in R7                            (owner: Buildings & Facilities pillar lead)
Tactical:     share of compounds in level 1-2 · K3 overruns · K5 eligible months   (owner: head of the inspection committee)
Operational:  A · K2 · K6 · K4 (guard) · share of cycle-list visits done          (owner: observatory team)
```

### ACUD-data signals (generated today, real when ACUD provides them)

| # | Signal | From `fin_monthly` | Trigger |
| --- | --- | --- | --- |
| B1 | Escrow cover | `cover_balance_egp` vs `cover_required_egp` | Balance below the required cover while cover is still required |
| B2 | Land arrears | `land_months_late` | ≥ 2 |
| B3 | Complaint rate | `complaints` per 1,000 units sold, vs own history | ≥ own 95th percentile, with ≥ 12 months of history |
| B4 | Occupancy gap | `kwh` vs `meters_active` | Context only (built but empty) |
| B5 | Plan gap (schedule variance) | `planned_pct` − `reported_pct` | > 20 points |

**B5 is the schedule-tracking idea.** The plan is an S-curve: slow start (excavation, utilities, foundations), fast middle (repeated floors), slow finish (facades, finishing, landscaping). The curve comes from the **contractual plan ACUD holds** (generated today as a Weibull S-curve), never from Decree 2184, which sets no yearly progress milestones.

---

## 3. Analytical core

1. **Track A rule** = the levels in section 2. It ranks the cycle list.
2. **Activity score A** replaced the old DW-only change rule after 5 pre-registered tests: +3 to +5 balanced-accuracy points over K1, half the false alarms, seasonal spread ≤ 10 points.
3. **Ground truth `eval_outcomes`:** 8 real cases with a published outcome (handover, postponement, no handover after the promise).
4. **Backtest (frozen clock):** apply the levels with data published before each quarter only. A frozen-clock check recomputes from data cut at the quarter and compares. Result: **1 of 8** warned ≥ 6 months early (target 5). Per case: what happened / why / what next, and a competing explanation rejected with a number. Small sample: counts, no percentages.
5. **Track B classifier.** Dataset `ml_dataset` (columns in `03-dataset.md` section 8.4): 1 row = compound × quarter, X = Track A outputs + K3, K5, K6 + ACUD-data inputs, **y = outcome in the next 6 months, 3 classes: `distressed` / `completed` (handover reached) / `ongoing`**. Labels come from the generated hidden truth (`answer_key`); the 8 real `eval_outcomes` are a check set only (too few to train). Models: logistic regression vs gradient boosting. Metrics: per-class recall, macro-F1, **recall@N for `distressed`** (N = cycle capacity) against a random top-N list. **Small data (R7 only, ~150 rows):** time split; developer holdout only if ≥ 3 developers stay in the test set; counts reported (n of m), stated as a limitation. No R8 rows and no extra virtual compounds are added for training. Its probabilities show next to the rule in the compound file; the cycle list still uses the rule. The first build (`a0f03fd`) ran the binary version (`label_distress_next_6m`) for each compound-month: Compared methods: satellite rule, K2 alone, B triggers alone, simple rule (satellite + B), logistic regression, gradient boosting; each model on satellite features, internal features, and both. Views: time split (train to 2024Q4, test labels 2025Q2-2026Q1), held-out developers, cross-validation by developer, so no developer is in both train and test. **Metric: recall@8** (of the truly distressed compounds, how many were in the top 8 of the quarter) + precision, against a random top-8 list (2,000 draws). Result: 92% / 62% / 37% (section 0).
6. **No leakage:** statements filtered by `published_date`; quarters ≤ as-of; the model never reads `answer_key` features; training plots that cover ≥ 50% of a compound are excluded in a backtest variant.
7. **Still to test on generated data:** FPMI and SAF (team ideas).

| Allowed to say | Not allowed to say |
| --- | --- |
| "No building activity for X quarters" | "Distressed" about a real compound |
| "Passed its first announced date by Y months" | "Completion 60%" or "finishing %" from images |
| "Observed height 2023 ≈ 24 m (estimated)" | "8 floors built" as a fact |
| "recall@8 on generated data, first build R7+R8: 92% vs satellites alone 62% vs random 37%" (always with the denominator, the baseline, the scope and "generated data") |
| "A compound-level digital twin of R7: quarterly sync from satellites, simulated finance until ACUD's data arrives" | "A 3D / real-time digital twin" | "The model predicts distress with 92% accuracy" |
| "Priority level 1: visit first" | "Risk level" / "high-risk developer" |
| "Eligible for review under contract terms for N months" | "Fined" / "owes X EGP" about a real compound |
| "No construction start N months after the first launch" | "Land speculator" |
| "Height 2024-2026: estimate, not approved" (slide only) | A height number for 2024-2026 in the dashboard |

---

## 4. Tests already decided

**Rule:** every idea is tried on real data first and must pass a condition written before the test. No threshold changes after seeing the result. Ideas are logged in `Project/team_ideas.md`.

| Idea | Result |
| --- | --- |
| Activity score A (DW trend + class shares + Sentinel-2) | ✅ Accepted after 5 tests; the base of the project |
| Vegetation from Sentinel-2 | ✅ 95% |
| Project-level (not building-level) monitoring, historical study, assumed developer and plan | ✅ In the design |
| InSAR coherence | ❌ Added no detection |
| Monthly monitoring | ❌ Noise above signal |
| Esri land cover + COLD | ❌ No accuracy gain |
| COVID effect, villas vs apartments, ADF, FPMI, SAF | ❌ All are apartments; COVID did not slow building; ADF would drop 36 of 40 levels. FPMI and SAF move to the generated data |
| Paved roads from images | 81% (now generated) |
| Finishing from Sentinel-2 (10 m): colour and brightness change, NDVI, water index (pools, lakes), bare soil, texture | ❌ 67%, target 75% |
| Finishing from Wayback (0.3 m) with a vision model (Qwen-VL on the server): facades, windows, planting, paving, pools | ⏳ Testing (R3). Pass condition, written before the run: ≥ 75% agreement on ~50 held-out compound-images, labelled blind to the model by a member other than R3. If it passes: a flag in the inspection file only, never in the level. Check the Esri terms before any use. **Cut at D4 (code freeze) if it has not passed** |
| Sentinel-1 radar | ❌ Detects building in only 63%; dropped |
| Roof slab uniformity (mean ÷ max building height; low = open frame with columns, near 1 = roof slab cast) and structural volume | 🆕 Candidate (from the TerraPulse draft). Test on Google heights 2016-2023 (yearly) against a condition written before the test; owner R3; logged in `team_ideas.md`; cut at D4 if not passed. Context in the compound file only, never in the level |

**Building height (7+ attempts):**

| Attempt | Result |
| --- | --- |
| Shadow length in 30 cm images | ❌ |
| GEDI / ICESat-2 laser | ❌ Too sparse; review only |
| Sentinel-1/2 models on Google footprints (v1-v3) | Close, but biased |
| **v4: computed on built cells only** | ✅ Bias from +2 m to 0.06 m. **Adopted up to 2024** |
| v5-v7: stronger models | Good on existing height (error 1.7 m, r 0.90), but miss buildings rising after 2023 |
| v8: Google-like model. Input: 32 Sentinel-2 images per year (Apr-Sep). Output: where buildings are and their height at 4 m. Trained on Google maps 2016-2021, tuned on 2022, tested on 2023. 12 models (pretrained NASA and Allen AI models + models from scratch) and a small model that combines them (+17%). Each year comes from that year's own images, not a forecast | 2023 (known answer): ~1.8 m mean error at district level ✅ · **2024-2026: ❌ not approved.** Independent test on 50 new areas, a reviewer judged images blind to the model: 69-74% agreement, target 80%. Main error: it calls finishing work "new building" |

Checked independently with GEDI / ICESat-2 laser, high-resolution images, and "stable buildings must stay stable".

**Adopted now:** 2016-2023 real from Google; 2024 the v4 estimate (±2 m). Our 2024-2026 model is not used in the product (not in the dashboard, not in the level); it appears only as an honest experiment on a slide. Height is **context in the compound file, not part of the level**.

---

## 5. The generator (stand-in for ACUD data)

Design and columns: `03-dataset.md` section 7. Summary:

- **Stories come from each compound's real signals.** If the satellite sees a stall, money and complaints reflect it. Stories: healthy, slow_late, partly_delivered, gradual_stall, stall_recovery, new_start.
- **Generated supervisor reports equal the developer's real announced % exactly** in every statement month.
- **Real noise and patterns:** Ramadan and summer slow work; sales rise after the March 2024 float; cost follows the real dollar and steel; reports are late and rounded; some developers are optimistic; electricity follows real temperature; a viral complaint spike.
- **No water meters.** Generated meters are electricity only (a sign that people received units and moved in). Water appears only in complaints (e.g. weak water on the top floor) and, on the real side, in the satellite water index (pools, lakes) used by the finishing experiment.
- **6 planted defects** for the gates to catch, and **hard + calibration realism checks**. Both pass.
- Hidden truth (`answer_key`) is private. **The model never reads it** except the label at training time.

---

## 6. The AI component

### A) Inspection file agent (core)
- **Request:** "Prepare an inspection file for compound C07 at quarter T".
- **Tools (plain Python):** `get_facts` (register + record_id + link) · `get_kpis` (A, K2-K4, level, series) · `get_images` (two Wayback images with capture date) · `get_rules` (Decree 2184 articles).
- **Flow:** code fills the template with numbers; the LLM writes one paragraph from attached facts only + 3 questions for the visit.
- **Structure (program format):** what happened · why (evidence + rejected competing explanation) · what it means · what we do (action + owner + date + escalation trigger).
- **Verification:** every number, date and code matched against the source JSON; causal words ("because") flagged for manual review. Logged in `ai_verification_log` (verdict: correct / wrong number / unsupported claim / missing context).
- **Output:** Arabic HTML/PDF with footer "Drafted by AI, reviewed by [name]" + model + time. 5 stored files for the presentation.

### B) Complaints classifier (Track B, capability demo)
- Regex masking of numbers and names **before** any model (Law 151/2020); `assert_zero_phones` must pass.
- 5 classes (delay, stoppage, payment, quality, other) vs a keyword baseline; extra test on `complaints_30.csv` from the program pack.
- Stated openly: accuracy on texts we wrote does not prove accuracy on real complaints.

**LLM:** Gemini (program tool, `GEMINI_MODEL` in `.env`); outputs are stored for the presentation.

---

## 7. Operating loop

| Element | What | Why |
| --- | --- | --- |
| Cycle list | CSV/PDF: top N with level, reason sentence, link to the file | What the committee receives |
| `ops_visits` | Form: code, date, result (progressing / stalled / complete / not done), note | Builds real ground truth each cycle |
| Quarterly recompute | `run_all` when a new quarter is out | The monitoring plan |

Inspection procedure (proposed; ACUD sets the real one): confirm with a second source → open a line in `ops_visits` → level 1 inform lead + visit in 2 weeks, level 2 within the cycle, level 3 request report → (Track B) review complaints, cover and classifier probabilities → record the result, close or escalate.

---

## 8. Pipeline and quality gates

**Status:** the first build (real data, generator, database, indicators and levels, early warning) is done and merged in `main` at commit `a0f03fd`; its results are the current numbers in this file. The code is being rebuilt after this plan is final. The dashboard is the next step.

**Tools:** Python + DuckDB + Streamlit. Entry points: `src.pipeline.run_all` (R1: real tables + indicators + gates), `src.generator.simulate` (R2: generator + realism checks), `uv run pytest tests/ -v`.

**10 gates** (rule + threshold + dimension + owner + fix / flag / stop):

| Gate | Dimension | Rule | Owner | On failure |
| --- | --- | --- | --- | --- |
| source | Accuracy | Every fact has a record_id and an accepted verdict (100%) | R2 | Fix: excluded |
| completeness | Completeness | ≥ 6 DW images in the quarter | R3 | Flag: not assessable |
| validity | Validity | Probabilities 0-1, counts ≥ 0, levels 1-4, valid dates | R1 | Stop |
| uniqueness | Uniqueness | (compound, quarter) and (compound, year) unique | R1 | Stop |
| consistency | Consistency | Every code is in the register; row counts equal after joins | R1 | Stop |
| freshness | Freshness | Last quarter ≤ 1 quarter before computation | R3 | Flag: stale |
| separation | Consistency | No generated column joined into a real table; every column has an origin type | R1 | Stop |
| data_or_city | Accuracy | > 30% of compounds switch to "no activity" in one quarter → source event | R4 | Flag and review |
| stuck_series | Accuracy | Same value 4 quarters in a row | R3 | Flag and review |
| **no_names** | Privacy | No compound or developer name in any output file (reports paths and counts only, never the name) | R1 | **Stop** |

**Outputs:** `quality_checks_log.csv` (program template) + quality report with an "impact on the indicator" column. **Lineage:** `kpi_values` carries `origin`, `run_id`, `computed_at`; storage is delete-then-insert; `computed_on` is fixed so two runs are identical. The agent, dashboard and memo all read the same `kpi_values`.

---

## 9. Dashboard (Streamlit, 5 screens, two tracks)

**Track switch** at the top of every screen: **"Track A: images"** (default, all real) / **"Track B: images + numbers (generated)"**. Track B adds the B signals and the classifier's probabilities (distressed / completed / ongoing). In Track B a fixed orange banner "Synthetic - for training only" stays on, every generated number carries 🟠, and **the map is hidden** (no generated number on a map of real places).

| Screen | Answers | Content |
| --- | --- | --- |
| 1 Priority map | Whom first? | R7 boundaries by level, cycle list with reason sentence, download; grey = not assessable. Map in Track A only; list only in Track B |
| 2 Compound file | Why this one? | DW and A curves, Open Buildings height, "developer announced" markers, first announced date, vegetation, two Wayback images, K2-K6, inspection file button, visit form, lineage line. Track B: classifier probabilities + K5 in EGP (🟠) |
| 3 Would it have warned? | Backtest + evidence | Track A: frozen-clock table, 1 of 8, and why. Track B: per-class recall, macro-F1, recall@N (images vs images + numbers vs random); B1-B5 per compound |
| 4 Data trust | How far to trust? | Gates, coverage, not assessable, 1,009/1,026, colour key 🟢🔵🟠 |
| 5 What if? (twin) | Who moves up if conditions change? | Pick a scenario, re-run the generator from the as-of quarter, show which R7 compounds change priority level and why. Generated (🟠, orange banner, no map) |

**What-if scenarios** (one input changes from the as-of quarter onward; base run never overwritten):

| # | Scenario | Change | Status |
| --- | --- | --- | --- |
| S1 | Dollar shock | USD/EGP +30% (like March 2024) | Ship |
| S2 | Collections drop | Buyer payments −25% for 6 months | Ship |
| S3 | Inspection capacity | N ± 2 (re-rank only, no generator re-run) | Ship (cheap) |
| S4 | Material cost jump | Rebar + cement +40% | Next |
| S5 | Grace change | Handover grace 12 → 6 months (policy test) | Next |

**Display rules:** ≤ 4 main tiles; each tile = value + unit + denominator + "as of" + origin; no card = no colour; never colour alone (level written as a word); the 5 forbidden mistakes (% without denominator, truncated axis, different-season comparison, average hiding spread, unannounced coverage change); the ten-second test on screen 1.

---

## 10. Roles and timeline

| Role | Owns | Next |
| --- | --- | --- |
| R1 Data pipeline (Analytics Engineer) | `run_all`, gates, lineage, docs | Review gates and `run_all`; code freeze D4; knowledge transfer pack |
| R2 Data and generator (Analytics Engineer) | Real tables, generator (twin simulation), dictionaries | Filter to R7; regenerate; scenario inputs for the what-if screen; ACUD data request list |
| R3 GIS and satellites (Data Science Engineer) | Boundaries, DW/S2 pulls, height, finishing experiment | Vision-model finishing test on Wayback (≥ 75% condition, Esri terms check); 2 Wayback images per compound |
| R4 Analysis and agent (Data Science Engineer) | Track A rule, backtest, **Track B `ml_dataset` + classifier**, agent | K5/K6 in `kpi_values`; 3-class classifier and its metrics; FPMI and SAF tests; inspection file agent |
| R5 Dashboard and presentation (Analytics Engineer) | Screens, memo, slides | Track switch on every screen; map in Track A only; orange banner in Track B; what-if screen |

All roles review each other; one person owns each deliverable. The docs name **roles only**, never people.

**Calendar:** D1 = day 6 · D2 = day 7 · D3 = day 8 · day 9 no project work · D4 = day 10 (mid-term review) · D5 = day 11 (submission and knowledge transfer) · D6 = day 12 (presentation). Today's program day (27 Oct) and which days are done: open item 2. The D4 code freeze applies to the rebuilt code.

| Day | Done when |
| --- | --- |
| D1 | Compass signed (use-case canvas, 8 checks) · boundaries confirmed · config written · section 14 decisions signed · rubric and presentation length asked |
| D2 | First Track A cycle list with reason sentences (incl. K5, K6) · generator tables built |
| D3 (also) | `ml_dataset` built; first Track B classifier run |
| D3 | Backtest table · `run_all` builds everything · all realism checks pass |
| D4 | Mid-term review (10 min) · early-warning comparison · agent + 5 files + verification log · code freeze |
| D5 | Everything submitted · knowledge transfer pack · two timed rehearsals · backup video · cross-review · fixes only |
| D6 | Presentation: status scan → freshness check → comparison → deep dive → decision |

---

## 11. Deliverables

| # | Deliverable | Owner |
| --- | --- | --- |
| 1 | KPI cards + tree + levels table | R5 |
| 2 | Pipeline with gates + `quality_checks_log.csv` + quality report | R1 |
| 3 | Analytical core: Track A rule (K2-K6), backtest, Track B `ml_dataset` + 3-class classifier | R4 |
| 4 | Dashboard (track switch) + cycle list + `ops_visits` | R5 |
| 5 | Method card + monitoring plan | R4 |
| 6 | Risks and responsible-AI note (Law 151/2020, who sees what, fairness limits, misuse) + `ai_verification_log` | R2 + R4 |
| 7 | Technical docs, user guide, governance cards, data dictionaries | R1 + R2 + R3 |
| 8 | Decision memo, one page per language (Arabic/English), same facts and order | R5 |
| 9 | Knowledge transfer pack (one page) | R1 |
| 10 | One run command that works in the presentation | R1 |
| 11 | Inspection files for 5 compounds | R4 |
| 12 | Data request list to ACUD | R2 |
| 13 | Final presentation | R5 |

---

## 12. Presentation (11 slides, 12-15 min, length to confirm)

1. Problem in numbers: > 400 developers, > 500 projects; field review every 3 months; 7-8% seriously late; 6 mutual terminations (ACUD chairman statements).
2. The question and the decision: whom first? The observatory ranks, the committee decides.
3. Data: 1,009 of 1,026 documented facts, 0 invented; origin key.
4. Seeing construction from space: DW, activity score, Open Buildings height, Wayback before/after.
5. Track A rule: priority level = the worst of K2, K3, K6 → 4 levels, with legal references; K5 fine-eligible months; the S-curve plan gap (B5) explained in one picture.
6. Live demo (Track A): map, cycle list, open a compound, reason sentence, inspection file, record a visit.
7. Backtest: 1 of 8 and why. **The only place real names may appear**, and only next to real signals.
8. Track B: `ml_dataset` (X, y) and the 3-class classifier; recall@N for distressed on generated data, R7 (first build R7+R8: 92% images + numbers vs 62% images alone vs 37% random); complaints classifier.
8b. The twin: one what-if scenario live (screen 5), showing which compounds move up.
9. Value in EGP (3 settings).
10. Risks and responsible use.
11. What we ask from ACUD + next step.

**Data request list (by impact):** plot boundaries, allocated developer and **land allocation date** (better K6) · **contract fine rates and fines issued** (real K5 in EGP) · approved schedule and contractual handover dates · quarterly supervisor reports (Law 119 art. 54, the only source of completion and interior finishing) · field review records · warnings, deadlines, terminations · building permits and permitted floors (art. 67; e-permits since Dec 2025) · land installments and arrears · escrow balances and collections · meter requests, occupancy certificates (art. 62), consumption · anonymised buyer complaints.

**Value in EGP (no double counting):**
```
Annual value    = cost of current policy − cost of proposed policy
Current policy  = (projects × 4 visits) × cost per visit
Proposed policy = (cycle-list visits × 4) × cost per visit + operating cost + (missed cases × cost of late detection)
```
Three settings in `configs/cost_assumptions.yaml`. Wording: "Under these assumptions, from X to Y million EGP per year".

| Expected question | Answer |
| --- | --- |
| Are the numbers real? | The list is real data with sources; the financial part is generated and labelled. |
| Are you calling a developer distressed? | No. "No building activity since X" and "passed its first date by Y". The committee decides. |
| Why trust satellites? | DW matches Open Buildings (r ≈ 0.96 on recomputed values); A passed 5 pre-registered tests. |
| Why did the backtest fail? | The 8 late cases kept building; delay was in finishing, which satellites cannot see. That is why we need your data. |
| Why no completion %? | Images see roofs, not plaster and ceramics; supervisor reports do. |

---

## 13. Risks and fallback

| Risk | Fallback |
| --- | --- |
| A fails on new quarters | Fall back to K1 (DW change), state the narrower claim |
| Height model 2024-2026 failed its test | Done: v4 (to 2024) stays as context; height is not in the level |
| Finishing vision model fails or Esri terms forbid it | Finishing stays by eye in the inspection file; nothing in the level depends on it |
| Boundaries for fewer compounds | Product works on the located ones; rest are "not assessable" and a data request |
| Slow Earth Engine download | All results stored as CSV; no live computation |
| Little ground truth | Present by case, no accuracy claim |
| Wayback terms | Display with attribution and capture date; the finishing experiment runs only after the terms are checked, and never feeds the level |
| Mixing generated with real | Track switch, Track A by default; separation gate (generated columns only enter Track B, each marked 🟠); map hidden in Track B; orange banner |
| Classifier only learns the generator's own rules | Labels come from hidden truth, not from the status rule the features mimic; check on the 8 real cases; if a model scores perfectly, add noise (`03-dataset.md` 7.6) |
| K5 in EGP read as a real fine | EGP only in Track B with 🟠 and "assumed rate"; real side shows eligible months only |
| Unlabelled generated data presented as real (e.g. the TerraPulse notebook: NDBI, built area and heights are formulas + random noise) | Never used as data; every number needs a source or an origin mark |
| A name leaks | `no_names` gate stops the run |
| Too few R7 compounds for a meaningful list or metric | Capacity N ≈ a third of R7; report counts (n of m), no percentages if m < 10; random baseline always shown |
| What-if screen not ready | Drop the word "digital twin" (use "observatory") rather than claim a twin without scenarios |
| Lack of time | **Cut order:** finishing vision-model test and roof-uniformity test (cut at D4 anyway) → FPMI/SAF tests → Track B gradient boosting (keep logistic) → complaint texts and classifier → LLM paragraph (template stays) → Wayback images → screen 3 as a slide. **Track A (rule, cycle list) and the Track B logistic baseline are never cut.** |

---

## 14. Rules that never break

- No compound or developer name anywhere (codes only); the gate stops the run. Exception: backtest slide.
- No "distressed" and no "finishing %" on a real compound.
- Every number carries its origin: 🟢 real · 🔵 derived · 🟠 generated.
- No generated number on the map; generated numbers appear only in Track B, marked 🟠, under the orange banner.
- Scope is **R7 only**.
- "Digital twin" means the light compound-level twin with what-if scenarios; never claim 3D or real-time.
- One idea, two tracks: Track A (images → rule → cycle list, real) and Track B (numbers: `ml_dataset` X, y → classifier). Track B reads Track A's outputs; image work is never duplicated.
- Data lives outside the repo (`Project/app_data`, `Project/private`); private files are never committed.
- Every new idea is tested first and logged in `team_ideas.md`.
- No threshold changes after seeing a result; no needless complexity.
- No number that failed its test is used; every estimate is labelled "estimate".
- Broker / real-estate sites: allowed for a compound's **location only**, when images confirm it and the method is logged per compound. Never a source for any number (dates, %, units, prices).
- Work on branches, with clear commits.

**Done when:** the success criterion is shown honestly (it failed: shown with the reason) · one command builds everything, twice identically · every gate has dimension, owner and decision · every number has a source or origin mark · every LLM number is in `ai_verification_log` · the 13 deliverables are ready and rehearsed twice.

**Decisions to sign on D1:** R7 only · light compound-level digital twin with what-if · two tracks (A images, B numbers) · worst-of-signals rule incl. K6 and B triggers · K5 definition and the assumed fine rate · Track B label (3 classes, next 6 months) · activity score A as the base indicator · thresholds and levels table (frozen) · boundary acceptance (confidence ≥ 80%) · codes only, no names · generated label "Synthetic - for training only / مولّد - للتدريب والعرض فقط" · questions for the instructor (rubric, presentation length).

---

## 15. What changed from the older drafts

### A) From the five archived drafts

| Topic | Older drafts | Now | Why |
| --- | --- | --- | --- |
| Compounds | 29 named (24-25 Oct); parcels (TerraPulse) | 22 coded `C01..C22` | Only 22 boundaries reached ≥ 80% confidence; names removed |
| Base indicator | K1 DW change + K1b radar | Activity score A | A passed 5 tests; radar only 63% |
| K3 | Months since the **last** announced date | Months since the **first** announced date | Later promises must not reset the clock |
| K1 threshold | 0.03 | 0.02 (input to A only) | `configs/data.yaml` |
| Success criterion | ≥ 2 of 3 named cases | ≥ 5 of 8 cases, ≥ 6 months early | Fixed before computation; result 1 of 8 |
| Track B unit | ~33 virtual twins, 15 fictional developers, 8 `g_*` tables | The 22 coded compounds, 1 wide `fin_monthly` + `complaints` + private `answer_key` | Stories follow real signals; reports match real announcements |
| Fact count | 863 / 846 | 1,026 / 1,009 (17 removed, 0 invented) | Later audit |
| Brand and area | TerraPulse, R7 only | SpaceEye (area: R7 only since section E) | Repo identity |
| Decree 2184 progress | S-curve 15/45/75/100% by year (TerraPulse) | Art. 4: cover released at 30/25/20/15/10% certified progress | Rechecked against the full decree text |
| Apartment footprint | 20% (TerraPulse) | Ground floor ≤ 22.5%, ground + 7, FAR 1.6-1.8 | ACUD 2018 conditions, audited |
| Developer data source | Property Finder, Nawy (TerraPulse) | Developer pages and official statements only | Broker sites are banned as sources |
| Earlier still (old specs) | Horus city, 33 fictional compounds, NDBI, cover 10-30%, weighted score | All replaced as above | Factual errors and no real signal |

### B) From `SpaceEye.md` (27 Oct 2026, now in `docs/.internal/archive/`)

| Topic | `SpaceEye.md` says | Decision here |
| --- | --- | --- |
| Name of the 1-4 level | "Risk level" (مستوى خطر) | **Priority level**; risk reads as a verdict on the developer |
| Early-warning result | recall@8 92% / 62% / 37% | Quoted, always with "generated data", the denominator and the random baseline. Method, split and pre-registered condition: open item 1 |
| Height 2024-2026 | Our model, "estimate, not approved" | Not in the dashboard or the level; slide only |
| Finishing | Sentinel-2 67% ❌; Qwen-VL on Wayback ⏳ | Experiment with a ≥ 75% condition; inspection-file flag only if it passes; Esri terms first |
| Boundary sources | "Maps and real-estate sites, matched with images" | Allowed for location only, image-confirmed, method logged; never for numbers |
| Reason sentence | Arabic | Arabic for the committee, English in code and logs, one template |
| Code status | Done and merged in `main` | True at `a0f03fd`; being rebuilt; its results stay as the current numbers |
| Water | No water meters | Confirmed: electricity meters only |
| `fin_monthly` rows | 993 | = 990 + 3 duplicate reports (defect 2); no conflict |
| Team lead's name, outside files (`DATA_PLAN_FINAL.md`, `team_ideas.md`) | Named | Roles only in the docs; outside files listed in `03-dataset.md` section 2 |

### C) Track structure and the TerraPulse pipeline summary (27 Oct 2026)

| Topic | Before / TerraPulse says | Decision here |
| --- | --- | --- |
| Tracks | Track A (real) + Track B ("with your data") | **One track**: one pipeline, one list, one dashboard with a data switch |
| Approach | Rule for A; models for B | **One rule** (worst of signals) in both modes; models are evidence |
| Idea | Spatial digital twin, schedule variance vs a legal S-curve | **Inspection priority**; schedule variance = B5 from the contractual plan |
| S-curve | Decree 2184 milestones 15/45/75/100% | Not in the decree; the S-curve is the shape of a contractual plan |
| Red alert | Schedule variance > 30% from satellite "progress" | Levels only; no completion % from images |
| Data | 4 tables + `master_r7_chronological_timeseries` (10,950 rows, every 5 days, 2018-2023) | Rejected: the notebook's NDBI, built area and heights are formulas + random noise, not observations |
| Heights | Google heights per snapshot | Google heights are yearly, to 2023 |
| Roof slab uniformity, structural volume | Indicators | Candidate idea, to test (section 4) |
| Models | XGBoost / LightGBM on the master table | Logistic + gradient boosting as evidence only |

### D) Two tracks, fines and never-started (27 Oct 2026, replaces the one-track decision in C)

| Topic | Before | Now |
| --- | --- | --- |
| Tracks | One track with a data switch | **Track A: images** (rule, map, cycle list, real) + **Track B: numbers** (`ml_dataset` X, y → classifier). B reads A's outputs |
| Model role | Evidence only | Track B's product: 3-class probabilities in the compound file; the cycle list still uses the rule |
| Label | Binary `label_distress_next_6m` | `distressed` / `completed` / `ongoing` in the next 6 months |
| Fines (غرامات) | Not covered | **K5**: fine-eligible months (real) + EGP on generated data with an assumed rate |
| Never started (مش بيبني أصلاً) | "Not started → watch", no level | **K6**: months since first launch with no start; 13-24 → level 2, > 24 → level 1 |

### E) R7 only and the digital twin (27 Oct 2026)

| Topic | Before | Now |
| --- | --- | --- |
| Area | R7 + R8, 22 compounds | **R7 only** (R8 removed to reduce scope); count: open item 4 |
| Cycle capacity / metric | N = 8, recall@8 | N ≈ a third of R7 compounds, recall@N; results re-run on R7 |
| Digital twin | Rejected as a separate product (C) | **Light compound-level twin**: observed state (Track A) + simulated hidden state (generator) + what-if screen. 3D / live twin out of scope |
| Activity score A training plots | 225 plots across the capital | Kept (training data, not scope); A is not retrained |
| R8 data already collected | In the tables | Audited R8 files stay untouched in `real_data/`; R8 is filtered out of every built table; R8 "44% average progress" kept only as a generator calibration reference |
| What-if scenarios | Not defined | S1 dollar shock, S2 collections drop, S3 capacity N ± 2 ship; S4 materials, S5 grace next (section 9) |
| Track B data size | 22 compounds | R7 only (~150 rows); time split, developer holdout only if ≥ 3 test developers; no R8 or virtual rows |
| Project name | Inspection Priority Observatory (R7/R8) | R7 Digital Twin and Inspection Priority Observatory |

---

## 16. Open items (facts still needed)

| # | Item | Where to get it | Fills |
| --- | --- | --- | --- |
| 1 | Early warning: which method (logistic / gradient boosting) and view (time / held-out developers / CV) gave 92%; the pass condition pre-registered in `EW_PROTOCOL.md`; **recall@8 of the product rule** (public + ACUD signals, method "(2) simple rule") | `app_data/EW_REPORT.md`, `EW_PROTOCOL.md` | Section 0 (success criterion, key result), section 3 item 5 |
| 2 | Today's program day and which of D1-D6 are done | Team lead | Section 10 timeline |
| 3 | Assumed monthly fine rate for K5 in EGP (until ACUD gives contract rates) | Team decision on D1, written in `configs/data.yaml` with `assumption: true` | Section 2 K5 |
| 4 | How many of the 22 coded compounds are in R7, and how many of the 8 backtest cases; then N (`cycle_capacity`) and the re-run of the backtest and early-warning results on R7 | `Project/private/` code map | Sections 0, 2, 3, 9 |
