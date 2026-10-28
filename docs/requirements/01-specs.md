# 01-specs.md

# SpaceEye-GeoAI: Horus City Construction & Default Risk Radar

ACUD AI & Data Readiness Program · Graduation project (Days 6-12) · Team of 5
Synthetic data only - for training only.

---

## 0. One-paragraph summary

Horus City is a fictional district modelled on the New Administrative Capital. About 33 compounds in districts H7 and H8 are being built by fictional developers. Today, progress is checked by blanket engineering inspections every 3 months: slow, costly, and late. SpaceEye-GeoAI turns satellite-style observations (NDBI/NDVI per compound, every 5 days), escrow flows, utility connections and buyer complaints into a **default risk score** per compound. The score **recommends which compounds to inspect first**; a human committee decides. Success is measured on planted stories with a known answer key.

---

## 1. The frame (project compass, section 1)

| Axis | Choice |
|---|---|
| Analytics type | **Preventive**, driven by a **predictive** risk score (a forecast triggers an early action) |
| Pillars | **Buildings & Facilities** + **Government & Citizen Services** |
| Condition | **Normal**, plus one **liquidity-shock what-if simulation** (extreme) |
| Goal | **Stability** |

Key question: *which compounds are drifting toward default, and whom should the inspection committee visit first?*

---

## 2. Use-case canvas (Day 6 sign-off, the 8 checks)

1. **The cell:** preventive (with predictive score) × Buildings & Facilities + Citizen Services × normal × stability.
2. **The goal:** stability, because late detection of stalled compounds damages investor trust and delays handover to residents.
3. **The decision and owner:** which compounds are inspected first, and which escrow accounts are reviewed. Owner role: **Buildings & Facilities pillar owner**; execution by the inspection committee.
4. **One KPI card:** TP-05 Default risk score (section 7).
5. **Measurable success criterion (hypothesis, to be confirmed by backtest):** on the held-out period, catch **≥ 80%** of planted defaulters **≥ 8 weeks ahead** with **precision ≥ 60%**, and cut inspection visits by **≥ 50%** against the blanket quarterly round, with the net value in EGP shown as a range under stated assumptions (section 8.6).
6. **Data plan:** kit tables + our own synthetic tables (section 5).
7. **Risk and responsible-AI note:** section 13.
8. **Feasibility:** Must items are achievable in Days 6-11 with 5 people (section 4 and section 14).

---

## 3. Settled decisions and open assumptions

| Item | Status |
|---|---|
| City name Horus City; H7/H8 replace R7/R8; landmark names changed (Horus Tower, Horus Bank) | Settled |
| Developers and compounds fully fictional (D01-D14, C01-C33). No real company names | Settled |
| Satellite series are **synthetic** (generated in code, fixed seed). Real Sentinel-2 is a method reference only | Settled |
| "6 months ahead" is an operational **target**, not a proven result. Measured lead time is reported from the backtest | Settled |
| Milestone schedule (`milestone_plan`) is an **editable assumption**, not a legal citation | Settled |
| Decision 2184/2022 is cited **only** for escrow deposit rules (10-30%) and the 12-month delivery grace; **not** for yearly build milestones | Settled |
| Weights 40/35/25 for the compliance index are a hypothesis tested with sensitivity (equal vs 40/35/25) | Settled |
| The score **recommends** inspection; it never "condemns" a developer | Settled |
| Official rubric not yet available; best-guess rubric in section 15; discuss expected results with the doctor on Day 7 | Open |
| Eid and Ramadan 2026 dates are expected, not announced; kept in a config file | Open |
| Egyptian DST statute number is disputed across sources; do not cite a law number | Open |

---

## 4. Scope (Must / Should / Could)

| Tier | Content |
|---|---|
| **Must** | Synthetic tables + planted stories + answer key; quality gates; KPIs TP-01..06; baseline rule; one measured model; risk map; model card; monitoring plan; bilingual decision brief; AI verification log; **value estimate in EGP (assumption-based, section 8.6)**; **one-sentence reason for every red/amber alert (section 8.7)**; **one-page executive brief (section 12)** |
| **Should** | Gemini complaint classification; compound drill-down screen; liquidity-shock simulation; fairness check |
| **Could** | Per-compound lead-time estimate; detailed user guide; animations |

Cut order if behind at Day 10: Could first, then Should from the bottom.

---

## 5. Data plan

All files carry the label "synthetic - for training only". Everything is generated in code with a fixed random seed. Each table has a data dictionary (column, type, unit, valid range, meaning).

### 5.1 New synthetic tables

| Table | Grain | Rows (approx.) | Purpose |
|---|---|---|---|
| `developers` | one per developer | 12-15 | fictional owners, size class, region of registration |
| `compounds` | one per compound | 33 (H7: 20, H8: 13) | polygon, area (feddan), allotment date, developer |
| `sentinel_passes` | compound × 5-day pass | ≈ 9,000-9,500 | `ndbi`, `ndvi`, `cloud_pct`, `quality_flag` |
| `milestone_plan` | compound × milestone | config-driven | expected completion percentage over time |
| `escrow_flows` | compound × month | ≈ 1,500 | deposits, withdrawals, `coverage_ratio` |
| `buyer_complaints` | complaint | a few thousand | Arabic / Franco text, category, compound, source system |
| `shock_scenarios` | scenario | few | parameters for the liquidity-shock simulation |

Horizon: **Jan 2023 → Oct 2026** for these tables. Kit operational tables stay at 2026.

### 5.2 Kit tables reused

| Kit table | Use |
|---|---|
| `electricity_meters`, `water_meters` (aggregated per H-zone) | proxy for finishing and occupancy stage (the satellite sees the shell, not the fit-out) |
| `service_requests` | citizen channel for complaints (masked before any AI tool) |
| `calendar`, `zones`, `buildings`, `sensors`, `assets` | reference and joins |

Waste, environment and traffic tables are out of scope.

### 5.3 Calendar and clock (2026)

The kit calendar covers 2025 only, so 2026 transitions come from the statutory rule: DST runs from the last Friday of April to the last Thursday of October.

| Item | Value |
|---|---|
| Spring 2026 | Fri 24 Apr 2026, clocks 00:00 → 01:00. Hour 00:xx does not exist. 23-hour day |
| Autumn 2026 | Clocks go back at 00:00 on Fri 30 Oct, to 23:00 on **Thu 29 Oct**. Hour 23:xx occurs twice. 25-hour day |
| Ramadan 2026 | 19 Feb → 20 Mar (expected) |
| Eid al-Fitr | 21-22 Mar (expected, subject to moon sighting) |
| Arafat Day / Eid al-Adha | 26 May / 27-28 May (calendar listing, tentative) |
| Islamic New Year | 17 Jun (calendar listing) |

De-duplication must be timezone-aware (`ambiguous` handling) or real readings in the repeated 23:xx hour are deleted.

### 5.4 Planted stories (answer key)

| # | Story | What the method must do |
|---|---|---|
| S1 | Gradual stall: build velocity decays over months | raise amber then red with ≥ 8 weeks lead |
| S2 | Sudden stall after a liquidity shock | raise red; show lag between shock and stall |
| S3 | Dust storm: NDBI spikes and work halts for days | **do not** flag as default; flag as weather |
| S4 | Slow but financially healthy compound | stay green or amber |
| S5 | Fully healthy compound | stay green |
| S6 | Escrow withdrawals outpace progress | raise a financial warning |
| S7 | Missed satellite pass / long cloud cover | keep last value flagged stale; report coverage; never fill silently |
| S8 | Satellite says built, utilities show none | flag inconsistency for human review |

### 5.5 Planted data defects (kit-style DQ1-DQ12 equivalents)

Clouds (S7), dust-induced false NDBI (S3), duplicate passes, unit mismatch in one developer's escrow report (EGP vs thousand EGP), hidden phone numbers in complaint text, repeated hour at 23:xx on 29 Oct 2026, and one unregistered compound id in a complaints feed.

---

## 6. Pipeline and quality gates

ELT in Python + DuckDB: load raw as it arrived, transform in SQL views, store with lineage.

| Stage | Description |
|---|---|
| 1 Ingest | raw CSV/Parquet into DuckDB, no changes |
| 2 Gate | automatic quality checks (below) |
| 3 Compute | KPI SQL per card, parameterised (`$start`, `$end`, optional `$zone`) |
| 4 Store | `kpi_values` with `source`, `run_id`, `computed_at`; replace, never duplicate |
| 5 Log | `run_log`: when, what, rows, gates failed, seconds |

### 6.1 Gates (rule + threshold + owner + action)

| Dimension | Rule | Threshold |
|---|---|---|
| Completeness | cloud-free passes ÷ expected passes per compound | ≥ 80% per quarter |
| Validity | `ndbi` and `ndvi` in [-1, 1]; `cloud_pct` in [0, 100] | 100% of rows |
| Uniqueness | (`compound_id`, `pass_date`) unique | 0 duplicates |
| Timeliness | newest pass for a compound ≤ 10 days old | 100% of compounds |
| Consistency | `compound_id` exists in `compounds`; developer exists | 100% of rows |
| Accuracy | escrow unit check (EGP vs thousand EGP); stuck NDBI value ≥ 6 passes | 0 rows |
| Clock | no reading in the non-existent hour (24 Apr 2026, 00:xx); the repeated 23:xx hour kept, not dropped | 0 phantom rows |

Every failing gate has an owner and an action: **fix** (known defect with written rule), **flag** (scattered gaps, report coverage), or **block** (not understood, or most of the data). A data trust score is reported per output.

Rule: count rows before and after every join. Use LEFT JOIN, then check.

---

## 7. KPI framework

### 7.1 Logic model

Inputs: satellite passes, escrow, utilities, complaints. Process: inspections and reviews. Outputs: inspections done, tickets closed. Outcomes: compounds delivered on plan; fewer late discoveries. Impact: residents get homes on time.

### 7.2 KPI cards (10 fields + parent + 2 tags)

| ID | Name | Formula (summary) | Unit | Kind | Parent |
|---|---|---|---|---|---|
| TP-01 | Construction progress vs plan (ΔP) | `P_expected - P_actual` per compound; `P_actual` = built footprint ÷ allowed built area | % points | lagging | TP-05 |
| TP-02 | Build velocity, last 90 days | change in `P_actual` over 90 days | % points / 90 d | leading | TP-05 |
| TP-03 | Escrow coverage ratio | escrow balance ÷ remaining cost of unfinished work | ratio | leading | TP-05 |
| TP-04 | Buyer complaint rate | complaints per 1,000 units, 30 days | per 1,000 | leading | TP-05 |
| TP-05 | Default risk score | model output, 0-100 | score | composite | goal |
| TP-06 | Satellite data completeness | cloud-free passes ÷ expected passes | % | leading | TP-02 |

Each card also carries: **purpose, source, frequency, owner (a role), baseline, target, thresholds (amber/red)**, direction, and theme.

### 7.3 Baselines and thresholds

- Baseline = a normal period (median day or compound). Where the card has no agreed limits, use history: median = baseline, worst 20% = amber, worst 5% = red.
- Choose the baseline period carefully (the Ramadan trap).
- The `P_expected` value comes from `milestone_plan`, an assumption. Sensitivity runs on 3 schedules.

### 7.4 KPI tree

```
Goal: Compounds delivered on plan
  TP-05 Default risk score (composite)
    TP-01 Progress vs plan (ΔP)
    TP-02 Build velocity (90 d)
      TP-06 Satellite data completeness
    TP-03 Escrow coverage
    TP-04 Buyer complaint rate
```

### 7.5 Pairs and guard rails

Guard each KPI with its pair: velocity is read together with data completeness; escrow coverage with progress; complaint rate with units delivered. Log which KPIs are gameable.

### 7.6 International mapping

Map each KPI to a theme in ISO 37120 / 37122 and ITU U4SSC using the same theme names as the program's KPI reference; no clause numbers.

### 7.7 Optional composite index

A compliance index per compound with min-max normalisation and two weight sets: **A** equal, **B** 40% build speed / 35% payment compliance / 25% green-area compliance. Report whether ranks change. Weights are a choice, stated explicitly.

---

## 8. Analytical core

### 8.1 Label

Default event: stall or default in the next 8-12 weeks (from the answer key for planted stories).

### 8.2 Baseline rule

Alert when ΔP exceeds amber/red limits **and** velocity is below its own history, with announced dust/heat days excluded. Evaluate first, as the program does ("can it beat a simple rule?").

### 8.3 Model

A small, interpretable model (logistic regression or small gradient boosting) on: ΔP, velocity (90 d), escrow coverage, complaint rate, satellite completeness, developer size. A larger model is used only if it beats the rule clearly. If it does not, the rule is the product.

### 8.4 Backtest (no leakage)

- Time split: **train Jan 2023 → Jun 2025; test Jul 2025 → Oct 2026**.
- Also hold out about 20% of compounds entirely to test generalisation.
- No feature may use information from after the prediction date.
- Metrics: precision, recall, lead time (weeks), false-alarm rate, calibration, compared with the baseline rule and the blanket inspection round.
- Report error with the sample size; with few events, say so.

### 8.5 Liquidity-shock what-if

- `shock_scenarios` parameters: collection drop (e.g. 30%), material cost rise (e.g. 20%), delay (8-12 weeks).
- Apply to a chosen group of compounds; recompute ΔP and risk; show how many cross amber/red and how late.
- Desert overlay is separate: announced dust/heat days slow work but are **not** counted as default.
- Operational rule: slowdown in announced dust or heat days is excluded from distress signals.

### 8.6 Value estimate in EGP

Turns "50% fewer visits" into money. It is a **scenario, not a measured saving**: every unit cost is an assumption in `config/cost_assumptions.yaml`, and the slide says so.

```
net_value_per_year = visits_avoided × cost_per_visit
                   - false_alarm_visits × cost_per_visit
                   - missed_default_cost
```

- `visits_avoided`: blanket round (33 compounds × 4 rounds) minus targeted visits triggered by the score, taken from the backtest.
- `false_alarm_visits`: alerts on compounds that did not default (from the backtest).
- `missed_default_cost`: defaults the score did not catch × an assumed cost of late discovery. Included so the number is not one-sided.
- Report a range from three cost settings (low / base / high), never one point.
- Wording on slides: "under these assumptions, about X to Y million EGP a year", with the assumptions listed beside it.

### 8.7 Explainable alerts

Every amber or red compound shows one sentence saying why, built from numbers computed on the data, not from a language model:

> "Build velocity down 60% vs its own 90-day history, escrow coverage 0.4 (limit 0.5), 12 new complaints in 30 days."

- Use logistic regression coefficients × feature values to rank the top 2-3 contributing features; fill a fixed sentence template with their real values.
- Shown in the drill-down screen, in the ticket text, and in the one-page brief.
- Weather-excluded days are mentioned when relevant ("3 announced dust days excluded").
- A test checks that every number in the sentence equals the value in the data.

---

## 9. GenAI component

- Gemini classifies buyer complaints (delay, work stopped, payment, quality, other) against a keyword baseline, scored on an answer key.
- Phone numbers are masked **before** any AI tool by regex; the regex check decides whether a file is safe to share, not the AI.
- AI output is a claim; the data is the judge. Every number a model writes is verified in the **AI verification log**.
- Prompts contain column names and masked synthetic text only, never real data.

---

## 10. Operations workflow

| Level | Meaning | Action |
|---|---|---|
| 1 | Escrow anomaly together with red risk | Supervisor + pillar owner, now |
| 2 | Red risk | Inspection within 2 weeks |
| 3 | Amber risk | Document review, same cycle |
| 4 | Green, watch | Next quarterly check |

Ticket life cycle: Open → Triage → Assign → In progress → Resolved → Closed; escalate when severity is high or no owner. One **parent ticket per compound**. Weekly handover report for the committee: what moved, which decisions are open, what data is stale.

This matrix is a training model, not ACUD's real matrix.

---

## 11. Dashboard (Streamlit)

Applies the 5-step routine: scan status, check freshness, compare, drill down, decide.

| Screen | Content |
|---|---|
| 1 Risk map | H7/H8 polygons coloured green/amber/red, freshness of last pass |
| 2 Compound drill-down | ΔP, velocity, escrow, complaints side by side; ticket status; **one-sentence reason for the alert (section 8.7)** |
| 3 Data trust | gate results, cloud coverage, stuck values, trust score |
| 4 Simulation | shock sliders, before/after comparison |

Every tile shows value and unit, period, comparison, target, status colour, freshness. Avoid the five misleading readings: no percentage without its base, no truncated axes, correct comparison period, spread not just the mean, and a note when coverage changed.

---

## 12. Deliverables (Day 12 checklist)

1. KPI cards + KPI tree
2. Pipeline with quality gates (runs end to end)
3. Analytical core: baseline, model, backtest results
4. Operational dashboard
5. Model card + monitoring plan
6. Risk and responsible-AI check + AI verification log
7. Technical documentation, user guide, knowledge-transfer pack
8. Bilingual (English/Arabic) decision brief + final presentation
9. **One-page executive brief** (a one-minute read): problem, result in numbers, value range in EGP with assumptions, recommendation, risks, next step. It is the front page of the decision brief, in both languages.
10. **One command** (`make run` or `python run_all.py`) that rebuilds data, gates, KPIs, model, backtest and dashboard data; it is run live in the demo.

---

## 13. Risk and responsible-AI note

| Risk | Control |
|---|---|
| False alarm harms a healthy developer | score recommends inspection only; human committee decides; false-positive cost stated |
| Unfair to small developers or to H8 | fairness check by size class and district |
| Personal data in complaints (Law 151/2020) | collect less, show less, share less; masking before AI use; raw / masked / aggregated access |
| Over-reliance on satellite | satellite sees shell only; fit-out measured with utilities and escrow |
| Weather mistaken for default | dust/heat overlay and rule |
| Synthetic realism limit | state it; thresholds need calibration on real imagery before any rollout |
| Misuse (e.g. freezing accounts automatically) | no automatic action; every score logged |

Access model: operator (masked), analyst (masked), data and AI engineer (raw on request, logged), pillar owner (aggregated), external contractor (aggregated only).

---

## 14. Team and timeline

### 14.1 Roles

| Role | Responsibility |
|---|---|
| R1 | Pipeline, DuckDB ELT, quality gates, data trust score |
| R2 | Synthetic generator, tables, planted stories, answer key, data dictionaries |
| R3 | GIS: polygons H7/H8, spatial joins, map |
| R4 | ML: baseline rule, model, backtest, model card, monitoring; Gemini complaint classification |
| R5 | Dashboard, KPI cards and tree, decision brief, presentation |

All roles review each other's output; one person owns each deliverable.

### 14.2 Timeline

| Day | Goal |
|---|---|
| 6 | Kickoff; canvas with the 8 checks; sign-off; roles; data dictionary agreed |
| 7 | Generator and first tables; first gates; first KPI (TP-01); discuss expected results with the doctor |
| 8 | Baseline rule, model, first measured result, early map |
| 9 | Shift simulation; no project work (keep lessons for the playbook) |
| 10 | Mid-review, 10 minutes per team: a measured result, early dashboard, risks |
| 11 | Freeze code; model card; docs; user guide; knowledge transfer; rehearsal |
| 12 | Presentation to the idea evaluation panel |

Send the canvas summary to the doctor before or at the start of Day 6, so sign-off precedes the Day 7 discussion.

---

## 15. Best-guess rubric (self-check, 1-5)

The official rubric is not available. Score each line 1-5 on Days 10 and 11. Replace with the official one when received.

| Area | What the panel is likely to look for |
|---|---|
| Problem and cell | clear decision, owner, goal |
| Indicators | cards with purpose, owner, baseline, target, thresholds; a tree |
| Data and quality | tables documented; gates; defects found and logged |
| Analytics | baseline vs model; measured error; no leakage |
| Operations | tickets, severity, handover, simulation |
| Dashboard | routine applied; no misleading displays |
| Governance and responsible AI | masking, access, fairness, verification log |
| Communication | bilingual brief; clear demo; honest limits |

---

## 16. Presentation plan (12-15 minutes)

1. Problem in numbers: blanket inspections cost time and find problems late
2. Data and governance
3. KPIs and tree
4. Measured result against baseline and blanket inspection
5. Live demo: Horus City map; open a red compound; show it is a dust storm and not default (S3)
6. Liquidity-shock simulation
7. Risks and responsible AI
8. Rollout steps and what needs calibration on real imagery

Demo is a deterministic replay with cached Gemini outputs, plus a recorded video as backup. Show the **one command** running live (with the replay as fallback), then the red compound with its one-sentence reason, then the EGP range with its assumptions.

---

## 17. Mock panel Q&A

| Question | Answer |
|---|---|
| Why synthetic data? Will it work on real imagery? | Synthetic data gives a known answer key, so we can measure. The method is portable, but thresholds such as NDBI need calibration on real images before any rollout. This is written in the model card |
| Could the model wrong a small developer? | The score only recommends inspection. A human committee decides. We run a fairness check by size and district, state the false-positive cost, and log every score |
| How do you tell weather slowdown from financial distress? | Announced dust or heat days are excluded from distress signals, and story S3 in the answer key proves the separation |
| How is benefit measured in money? | Visits avoided × cost per visit, minus false-alarm visits, minus the cost of missed defaults, shown as a low/base/high range. Unit costs are assumptions in a config file, so it is a scenario, not a measured saving |
| Are the milestones legal requirements? | No. Decision 2184/2022 covers escrow deposit rules and the delivery grace period. Our schedule is an editable assumption, with sensitivity on three schedules |
| What about personal data? | Complaints are synthetic; phone numbers are masked by regex before any AI tool; the regex, not the AI, decides if a file is safe |

---

## 18. Definition of done

- The pipeline runs from raw files to the dashboard with one command, and a second run gives the same numbers.
- All gates are documented with an owner and action.
- All 8 planted stories have an expected and an observed result.
- Backtest numbers are reported honestly, including when the model does not beat the rule.
- Every number written by an AI assistant is verified in the log.
- Every file says "synthetic - for training only".
