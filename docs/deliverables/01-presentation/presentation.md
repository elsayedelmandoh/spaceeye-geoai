# Presentation: 13 slides (title slide 0, then 1-11 with 8b after 8)

Tasks T-SA-06 and T-EL-25. Draft text for review. This file holds the on-slide content and speaker notes of `presentation.pptx`, slide for slide in the same order. Length: 12 min, the limit set by criterion 10 of the instructor rubric (`docs/requirements/ACUD-Rubric.md`); the time budget and the criteria each slide answers follow `docs/deliverables/01-presentation/rubric-map.md` (presentation plan) and are stated in each speaker note (total 12:00). Numbers come only from repo files and carry an origin mark: 🟢 real · 🔵 derived · 🟠 generated ("Synthetic - for training only"). Compounds and developers appear as codes only; the only names are the supervisor and team on the title slide. The words "risk level", "distressed" (for a real compound) and any completion % are not used. Some caveats are in the speaker notes.

## Slide 0. SpaceEye GeoAI

- SpaceEye GeoAI
- New Capital Radar: a company that owns a city.
- Supervisor: Dr. Nadim Abdin - Partner & VP Business Development
- Team: Elsayed Elmandoh, Verina Fouad, Ahmed Abdelhameed, Nada Shady, Salma Magdy

Speaker note: 0:15 · opening. Name the project and the slogan, thank the supervisor, introduce the team in one line.

## Slide 1. Problem in numbers

- 🟢 Real statement: More than 400 developers and more than 500 projects.
- 🟢 Real statement: Field review every 3 months.
- 🟢 Real statement: About 7-8% of developers seriously late; 6 mutual terminations.
- A committee cannot visit everything every cycle: whom to visit first?
- These are the chairman's statements, not our measurement. 🔵 R7, our count: 5 of 6 public late cases ran 18-33 months past the promise (median 25); their 6,474 homes waited up to 153,816 home-months; 3 passed the 24-month refund line of Decree 2184/2022 art. 5. Chain and why now: `docs/deliverables/decision-memo.md`.
- Visual: five stat callouts (more than 400 developers · more than 500 projects · field review every 3 months · about 7-8% seriously late · 6 mutual terminations).
- Source: statements by the ACUD chairman, as recorded in `docs/requirements/01-specs.md` (section 12, slide 1).

Speaker note: 0:45 · criterion 1. A committee cannot visit everything every cycle, so the question is whom to visit first. Why now: Decree 2184/2022 art. 5 applies to projects under way, and two R7 clocks run today (C18 57 months past its first date, C14 moved its date twice).

## Slide 2. The question and the decision

- Question: which R7 compounds should the committee visit first next cycle, and why?
- The observatory ranks; the committee decides.
- Scope: R7 only, 12 coded compounds, reporting quarter 2026Q3, cycle capacity 4.
- As-is → to-be: today every one of the 12 compounds gets a field review every 3 months (4 visits a year each); tomorrow a cycle list of at most 4 compounds from levels 1-3, each with a reason sentence, and the committee decides.
- ACUD has not given us visit times or missed cases, so the as-is pain is not measured.
- Visual: as-is → to-be flow of two boxes.
- Source: `configs/cost_assumptions.yaml` (`projects: 12`, `visits_per_year: 4`), `docs/requirements/01-specs.md` (sections 2, 7 and 12).

Speaker note: 0:45 · criteria 1, 2, 3. One sentence from today's practice to the new list; the decision itself comes on slide 11.

## Slide 3. Data

- 1,009 of 1,026 documented facts passed independent review. This is the figure stated in the spec, not a recount.
- Origin key on every number: 🟢 real, 🔵 derived, 🟠 generated.
- Real: satellite series, statements, laws. Generated: finance, supervisor reports, meters, complaints (only ACUD holds the real ones).
- Visual: stat callout (1,009 of 1,026) and origin-key table.
- Source: `docs/requirements/01-specs.md` (section 12); `data/DATASET_CONTRACT.md` (tables).

Speaker note: 0:45 · criteria 2, 8. Point to the origin key; it is used on every later slide. The installed data has no facts register, so 1,009 of 1,026 is the figure stated in the spec (section 12), not a recount; the dashboard's data-trust screen shows the same documented figure.

## Slide 4. Seeing construction from space

- Dynamic World gives a quarterly built probability per compound; the activity score A is the probability that the compound is building this quarter.
- Open Buildings gives yearly heights to 2023; approved height context extends through 2024 and is shown only as context, never part of a priority level.
- Wayback before/after images (with capture date and attribution) are for display; Esri terms to be confirmed before use.
- A quarter is assessable only with at least 6 Dynamic World images and a boundary with a reviewed confidence label (K4).
- Limit: satellites show whether building is happening, not interior finishing. No completion % or finishing % is given.
- Visual: three-row source table (source · gives · role).
- Source: `docs/requirements/01-specs.md` and `data/DATASET_CONTRACT.md`.

Speaker note: 0:30 · criteria 2, 6. Say what the satellite sees and what it cannot.

## Slide 5. The Track A rule

- Priority level = the worst of K2 (quarters with no activity after construction started), K3 (months since the first announced handover date) and K6 (months since the first launch or promise with no confirmed start). No weights.
- Cap: if a handover is announced or vegetation share is 0.10 or more, the level is at most 3 (in 2026Q3 this sets 3 of 12 levels: C03, C12 and C21).
- Level 1 inspect now; level 2 inspect this cycle; level 3 document review; level 4 routine. Follow-up states without a level: not started, start unknown, not assessable.
- Legal references: 12 months handover grace and 24 months right to refund (Decree 2184/2022).
- K5 (fine-eligible months) is illustrative and never sets a level.
- Plan gap B5 (planned minus reported progress) is generated data (🟠) and appears only in Track B.
- Visual: rule flow (K2, K3, K6 → worst signal → cap) and level-action table.
- Source: `docs/deliverables/kpi-cards.md` (cap count), `configs/data.yaml`, `docs/requirements/01-specs.md` (level table: 24 months right to refund).

Speaker note: 1:00 · criteria 3, 4. The worst signal sets the level, without weights, and each level maps to an action.

## Slide 6. Live demo (Track A)

- Priority map, cycle list (capacity 4, levels 1-3), open one compound, read its reason sentence, open the inspection file, record a visit result.
- Everything on screen in Track A is real or derived. No generated number appears on the map.
- Dependency: the demo needs the dashboard to run from stored files. Run command: `make run (team_run --full, which calls run_all)`, the one run command per board task T-AH-19.
- Visual: five-step flow (priority map → cycle list → reason sentence → inspection file → visit result).
- Source: `docs/deliverables/user-guide.md`; board task T-AH-19 in `docs/requirements/02-team-roles-and-tasks.md`.

Speaker note: 1:30 · criterion 4. Follow the alert to the action: level, cycle list, inspection file, visit form.

## Slide 7. Backtest: 1 of 6 and why

- Six public R7 cases, checked with the clock frozen. Codes only, even on this slide.
- Early alert in 1 of 6 cases (after-start reading, case C21) and 0 of 6 (point-in-time reading).
- The target of 5 cases was fixed before computing, was not lowered and was not met.
- Imaging was sufficient in every case (at least 10 images per quarter). In the five missed cases the sites were seen as active, so the rule had no stall to detect. The rule measures stalls and passed dates, not pace against plan.
- The one hit (C21) came from a start date set by publication timing and a lag in the activity score, not from a real stall during construction, so it does not carry over to the other five.
- These counts do not prove why each delay happened.
- Visual: three stat callouts (1 of 6 · 0 of 6 · 5 required, not achieved).
- Source: `data/BACKTEST_CURRENT.md`, `data/experiments/35_backtest_diagnosis/DIAGNOSIS.md`.

Speaker note: 1:45 · criterion 6. Lead with the miss, and say the target was fixed before computing.

## Slide 8. Track B: generated data

- 🟠 Synthetic - for training only.
- Scope: R7, 12 coded compounds. Target: distressed / not_distressed in the next six months. Completion prediction is outside the approved scope.
- Data: 96 training rows and 48 test rows. The test holds only 4 distressed rows, so statistical power is very low.
- Recall@4 (distressed cases among the top 4 of the list; denominator 4), on generated data: public rule 3 of 4; combined rule 3 of 4; logistic, satellite 1 of 4; logistic, combined 2 of 4; boosting, satellite 4 of 4; boosting, combined 1 of 4.
- Caveat: the boosting 4 of 4 rests partly on the height column; the v2a run without height gives 1 of 4 (`data/EW_V2A_VS_V1.md`).
- Baseline: random top-4 list, 2,000 draws, mean 0.335, 95% interval 0.000 to 0.750.
- Reading: with 4 cases the methods cannot be separated, and combining ACUD-style data did not clearly help. Scores are diagnostic and do not show real-world accuracy.
- Visual: native bar chart of recall@4 for the six methods.
- Source: `docs/deliverables/complaints_eval.csv`, `data/EW_V2A_VS_V1.md`.

Speaker note: 1:00 · criterion 6. Generated data only; with 4 test cases the methods cannot be separated. For questions, complaints classifier: the keyword baseline scored 0.27 accuracy on the 104-row benchmark and 0.37 on the 30-item check set; TF-IDF plus logistic scored 0.22 and 0.30, respectively. Accuracy on texts written by the team does not prove accuracy on real complaints.

## Slide 8b. The observatory: one what-if scenario

- 🟠 Synthetic - for training only.
- Light compound-level observatory: observed state from satellites and statements, simulated hidden state from the generator, what-if scenarios.
- Scenarios: S1 dollar shock, S2 collections drop, S3 inspection capacity change. Demo S3 live: who enters or leaves the cycle list at 2 or 6 visits instead of 4 (45 of 744 rows change list membership: 28 at capacity 2, 17 at capacity 6; levels never change).
- S1 and S2 change nothing in the list or the levels (0 of 216 rows each).
- Generated (🟠), orange banner on screen, no map. Not a 3D or real-time observatory.
- Visual: scenario table (S1 · S2 · S3 and rows changed).
- Source: `logs/review-05.md` (scenario row counts).

Speaker note: 0:30 · criterion 6. Show S3 only; say S1 and S2 change nothing.

## Slide 9. Value in EGP (3 settings)

- Visiting 4 compounds per cycle instead of all 12: 16 visits a year instead of visiting every compound each cycle.
- Under these assumptions, from 0.007 to 0.102 million EGP per year.
- Cost inputs are public proxies or assumptions. Even the conservative setting is positive, but small.
- Cost per visit (2,000 / 3,000 / 4,000 EGP) is an assumption based on a team of 3 at published engineer pay plus assumed transport. Operating cost and missed cases are public proxies (CBE, Hetzner, WageIndicator, chairman's 7-8% statement); the cost of a late case is a placeholder.
- The cost of a false alarm against the cost of a missed case has not been measured.
- Not a measured saving.
- Visual: two stat callouts (0.007 and 0.102 million EGP per year) and a three-setting table (cost per visit, operating cost, missed cases per year).
- Source: `configs/cost_assumptions.yaml` (the same file holds the three settings, the proxy values and the placeholder); `docs/deliverables/01-presentation/rubric-map.md` (criterion 6 gap).

Speaker note: 1:30 · criterion 7. Compare with the current policy of visiting all 12; say the conservative setting is positive but small. The cost of a late case is a placeholder of 20,000 EGP per missed case in all three settings.

## Slide 10. Risks and responsible use

- A level is not a finding: It says whom to visit first; it is not misconduct, legal distress, breach or a verified fine. No automatic sanction.
- Unknown stays unknown: Missing evidence is never read as negative. K3 relies on developer statements, not independent measurement.
- Generated data: Never mixed with real data; Track B is marked and hidden from the map. It shows nothing about real accuracy or fairness.
- Small samples: 6 real cases and 4 test cases: counts only, no percentages.
- Complaint text: Masking does not prove every real name is removed; real text needs further review. No external AI call is enabled.
- Law 151/2020: Interpretation needs the data custodian's review. Not legal advice.
- Handover: Guides, method card and checklist are in the repo; no one outside the team has rebuilt the system from them yet.
- The committee decides; every visit result is recorded to build real ground truth.
- Knowledge transfer: technical operations guide, committee user guide, handover pack, method card and final checklist are in the repo; the user guide was checked against the code, not in a browser.
- Visual: risk and control table.
- Source: `docs/deliverables/responsible-ai.md`, `docs/requirements/01-specs.md` (Law 151/2020).
- Source (knowledge transfer): `docs/deliverables/technical-track-a.md`, `docs/deliverables/user-guide.md`, `docs/deliverables/knowledge-transfer.md`, `docs/deliverables/method-card.md`, `docs/deliverables/final-checklist.md`.

Speaker note: 1:00 · criteria 8, 9. A level sets the visit order and finds nothing against anyone. Then give one line on the handover documents. The committee decides, and every visit result is recorded to build real ground truth. The user guide was checked against the code, not in a browser.

## Slide 11. Decision, transition and next step

- **Decision requested:** use the inspection priority list to choose which R7 compounds the committee visits first next cycle. The system recommends; the committee decides.
- Message: this is what public data alone can do. Give us your data and the demo parts become real operation.
- Transition roadmap (phase · what · owner role · risk · rollback):
  - Phase 1 · Pilot cycle: Run one cycle with the list; record every visit result. Owner: Committee decides; Track A owner prepares the list. Risk: Little ground truth; no accuracy claim. Rollback: The current 3-month review continues.
  - Phase 2 · ACUD data: Coded export ordered by impact; small verified sample first. Owner: ACUD data custodian keeps the identity mapping. Risk: Access and approval not yet given. Rollback: Stay on public data; missing stays unknown.
  - Phase 3 · Quarterly operation: Quarterly monitoring; thresholds and capacity change only by reviewed decision. Owner: Proposed: Track A owner operates, another team member reviews. Risk: Activity score A fails on new quarters. Rollback: Fall back to K1; prior releases stay available.
- Gates between phases, progress indicators, rollback triggers and training: `docs/deliverables/transition-plan.md` (proposed). The fixed 3-month review keeps running through phases 1 and 2, so rollback costs at most one rerun. People and dates: to be agreed with ACUD.
- Transfer: thresholds and capacity are configuration; another region needs its boundaries and statements. Only R7 has been run; no transfer is proven.
- Next step: run one cycle with the list and record visit results.
- Visual: decision box and three-phase roadmap.
- Source: `docs/deliverables/decision-memo.md` (decision requested), `docs/deliverables/data-request.md`, `docs/requirements/01-specs.md` (data request list, art. 54; section 13 risks and fallbacks), `docs/deliverables/technical-track-a.md` (quarterly monitoring procedure), `docs/deliverables/transition-plan.md` (gates, indicators, rollback).

Speaker note: 0:45 · criteria 5, 10, bonus. Open with the decision, name the first phase and close on the next step. Total 12:00. For questions: the ACUD export is ordered by impact (dated inspection and handover outcomes, contract register, parcel geometry first); any STOP in the monitoring procedure writes no manifest.
