# Presentation: slides 1-11

Task T-SA-06. Draft text for review (the deck is built from this file). Length is still to be confirmed (spec says 12-15 min). Numbers come only from repo files and carry an origin mark: 🟢 real · 🔵 derived · 🟠 generated ("Synthetic - for training only"). Codes only, no names. The words "risk level", "distressed" (for a real compound) and any completion % are not used.

## Slide 1. Problem in numbers

- More than 400 developers and more than 500 projects.
- Field review every 3 months.
- About 7-8% of developers seriously late; 6 mutual terminations.
- Source: statements by the ACUD chairman (Sep-Oct 2026). These are the chairman's statements, not our measurement.

Speaker note: a committee cannot visit everything every cycle, so the question is whom to visit first.

## Slide 2. The question and the decision

- Question: which R7 compounds should the committee visit first next cycle, and why?
- The observatory ranks; the committee decides.
- Scope: R7 only, 12 coded compounds, reporting quarter 2026Q3, cycle capacity 4.

## Slide 3. Data

- 1,009 of 1,026 documented facts passed independent review; 17 removed; 0 invented. [verify in T-SA-08 against the current dataset contract]
- Origin key on every number: 🟢 real, 🔵 derived, 🟠 generated.
- Real: satellite series, statements, laws. Generated: finance, supervisor reports, meters, complaints (only ACUD holds the real ones).
- Source: `data/DATASET_CONTRACT.md`.

## Slide 4. Seeing construction from space

- Dynamic World gives a quarterly built probability per compound; the activity score A is the probability that the compound is building this quarter.
- Open Buildings gives yearly heights to 2023; the 2024 value is an estimate, shown as context only, never part of a priority level.
- Wayback before/after images (with capture date and attribution) are for display; Esri terms to be confirmed before use.
- A quarter is assessable only with at least 6 Dynamic World images and a boundary with a reviewed confidence label (K4).
- Limit: satellites show whether building is happening, not interior finishing. No completion % or finishing % is given.

## Slide 5. The Track A rule

- Priority level = the worst of K2 (quarters with no activity after construction started), K3 (months since the first announced handover date) and K6 (months since the first launch or promise with no confirmed start). No weights.
- Level 1 inspect now; level 2 inspect this cycle; level 3 document review; level 4 routine. Follow-up states without a level: not started, start unknown, not assessable.
- Legal references: 12 months handover grace and 24 months right to refund (Decree 2184/2022).
- K5 (fine-eligible months) is illustrative and never sets a level.
- Plan gap B5 (planned minus reported progress) is generated data (🟠) and appears only in Track B.
- Source: `docs/deliverables/kpi-cards.md`, `configs/data.yaml`.

## Slide 6. Live demo (Track A)

- Priority map, cycle list (capacity 4, levels 1-3), open one compound, read its reason sentence, open the inspection file, record a visit result.
- Everything on screen in Track A is real or derived. No generated number appears on the map.
- Dependency: the demo needs the dashboard to run from stored files. [confirm the run command with the pipeline owner before rehearsal]

## Slide 7. Backtest: 1 of 6 and why

- Six public R7 cases, checked with the clock frozen. Codes only, even on this slide.
- Early alert in 1 of 6 cases (after-start reading, case C21) and 0 of 6 (point-in-time reading).
- The criterion of 5 cases was fixed before computing and was not lowered. It was not achieved.
- The diagnosis shows imaging was sufficient in every case (at least 10 images per quarter). In the five missed cases the sites were seen as active, so the rule had no stall to detect. The rule measures stalls and passed dates, not pace against plan.
- These counts do not prove why each delay happened.
- Source: `data/BACKTEST_CURRENT.md`, `data/experiments/35_backtest_diagnosis/DIAGNOSIS.md`.

## Slide 8. Track B: generated data (🟠 Synthetic - for training only)

- Scope: R7, 12 coded compounds. Target: distressed / not_distressed in the next six months. Completion prediction is outside the approved scope.
- Data: 96 training rows and 48 test rows. The test holds only 4 distressed rows, so statistical power is very low.
- Recall@4 (distressed cases among the top 4 of the list; denominator 4), on generated data:
  - public rule 3 of 4; combined rule 3 of 4
  - logistic, satellite features 1 of 4; logistic, combined features 2 of 4
  - boosting, satellite features 4 of 4; boosting, combined features 1 of 4
- Baseline: random top-4 list, 2,000 draws, mean 0.335, 95% interval 0.000 to 0.750.
- Reading: with 4 cases the methods cannot be separated, and combining ACUD-style data did not clearly help. Scores are diagnostic and do not show real-world accuracy.
- Complaints classifier: capability demo on generated texts. [take numbers from `docs/deliverables/complaints_metrics.csv` before quoting any]
- Source: `data/EW_REPORT_CURRENT.md`.

## Slide 8b. The twin: one what-if scenario

- Light compound-level twin: observed state from satellites and statements, simulated hidden state from the generator, what-if scenarios.
- Scenarios in the plan: S1 dollar shock, S2 collections drop, S3 inspection capacity change. Pick one live and show which compounds move up in priority.
- Generated (🟠), orange banner on screen, no map.
- Not a 3D or real-time twin. [confirm the what-if screen is ready; if not, drop the word "twin" and say "observatory", as the spec's fallback says]

## Slide 9. Value in EGP (3 settings)

- Visiting 4 compounds per cycle instead of all 12: 16 visits a year instead of 48.
- Under these assumptions, from -0.006 to 0.098 million EGP per year.
- Every cost input is an assumption. The conservative setting is negative.
- Cost per visit (2,000 / 3,000 / 4,000 EGP) comes from a team of 3 at published engineer pay plus assumed transport. Operating cost, missed cases and cost of a late case are placeholders.
- Source: `configs/cost_assumptions.yaml`. Not a measured saving.

## Slide 10. Risks and responsible use

- A priority level says whom to visit first. It is not a verdict on a developer, and no compound is called distressed.
- K3 relies on developer statements, which are real but not independent measurements.
- Generated data is never mixed with real data; Track B is marked and hidden from the map.
- Small samples (6 real cases, 4 test cases): counts only, no percentages.
- The committee decides; every visit result is recorded to build real ground truth.
- [align with `docs/deliverables/responsible-ai.md` before the final version]

## Slide 11. What we ask from ACUD and next step

- Message: this is what public data alone can do. Give us your data and the demo parts become real operation.
- Data request, by impact: plot boundaries, allocated developer and land allocation date · contract fine rates and fines issued · approved schedule and contractual handover dates · quarterly supervisor reports (Law 119 art. 54) · field review records · warnings, deadlines, terminations · building permits and permitted floors · land installments and arrears · escrow balances and collections · meter requests and occupancy certificates · anonymised buyer complaints.
- Next step: run one cycle with the list and record visit results.
- Source: `docs/deliverables/data-request.md`.
