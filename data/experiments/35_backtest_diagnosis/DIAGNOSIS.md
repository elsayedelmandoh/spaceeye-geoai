# Why the real-case backtest alerted in 1 of 6 cases (diagnosis only)

Scope: R7, codes only. Nothing was refit, retuned or committed. No "would pass with threshold X" number is given anywhere in this file.
Criterion (fixed 2026-10-26): level 1-2 in a quarter ending at least 6 months before the first delivery date, after construction had started; 5 of 6 needed, 1 of 6 observed.

## Files and how they were produced

| File | Content |
| --- | --- |
| `diagnose_backtest.py` | The script (run with the repo `.venv`, `python -I`). Re-runnable, read-only on repo and app_data. |
| `timelines/E{1,4,5,6,7,8}_C##.csv` | Quarter-by-quarter rows 2019Q1 to the quarter of the first date: images, K4, DW built share, K1, A (`activity_prob`, `active`), started, K2, K3, K6, level, level each K rule alone would give, "what was missing", OBT yearly structure, published progress. |
| `timelines/compact_tables.md` | Condensed view of the same CSVs. |
| `summary_by_case.csv` | One row per case with the counts quoted below. |
| `k2_firing_all_compounds.csv` | Whether K2 can fire at all, for all 12 compounds. |

Inputs: `Project/app_data/backtest/kpi_values_backtest.parquet` (asserted identical in level, K2 and started to `releases/ready-data/backtest/kpi_inputs.csv`, 372 rows), `Project/app_data/real/{sat_quarterly,sat_yearly,statements,compounds,eval_outcomes}.parquet`, `configs/data.yaml`. The backtest activity variant is `q2hold`: A is read once a year from the Q2-ending window and held for four quarters.
The `app_data/real` and `repo app_data` folders do not exist inside the repo worktree; the Project-level copies were used.

## Structural facts (apply to every case)

1. Imaging is never the problem. Every pre-cutoff quarter of every case has K4 true; minimum 10 images, median 14-15 per quarter (`summary_by_case.csv`). Reason (a) is excluded as a cause of misses.
2. Before the first date only two rules can ever give level 1-2 on an already-started site: K2 (at least 2 consecutive quarters with A inactive after the start) and K6 (13+ months since launch/promise with no confirmed start). K3 is 0 until the first date passes; its level 2 needs K3 of 13 or more, so it can only fire after the date. K3-driven level 1-2 appeared 15 months after the date in C14 (2026Q1), C12 (2024Q1), C10 (2025Q1), C02 (2024Q2); never in C19, because its handover was published (2025-02-11) before K3 reached 13.
3. K2 needs a stall seen by A. In the five missed cases A was active in 100% of started, assessable pre-cutoff quarters and max K2 before the cutoff was 0. K2 does work when a stall is seen: C03 has 18 inactive quarters, max K2 14 (`k2_firing_all_compounds.csv`), so the machinery is not broken; the cases simply contain no stall.
4. Start-confirmation lag of about 3 quarters in all cases: with `q2hold`, A first turns active at a Q2 window and "started" needs 4 consecutive active quarters. Examples: C14 first active 2021Q2, started flag 2022Q1; C10 and C02 the same; C19 2020Q2 to 2021Q1; C12 2020Q2 to 2021Q1. Quarters in the lag have no level (except via K6). This explains why "assessable" quarters are few (C02: 3, C10: 6), but because the sites were active, K2 would have been 0 anyway.
5. The five missed cases are delays during continuous construction or in finishing. They are not stalls. The criterion tests a stall detector against delivery-delay cases; that mismatch is the main finding.

## Per-case diagnosis

DW = Dynamic World built share; OBT = Open Buildings Temporal yearly structure (2024 values are an estimate, not a measurement; they are context only, not used by any rule). Floors allowed = 8 (about 24-26 m) for all six.

### E1 / C14 (first date 2024-12-31, cutoff 2024-06-30)
- Timeline: 22 quarters before cutoff, all with 10+ images; 10 assessable (2022Q1-2024Q2); started 2021Q2; levels `4444444444`.
- A active 10/10 (activity_prob 0.68-0.89); K1 above 0.02 in 9/10 (only 2023Q4 at 0.0137); K2 = 0; K3 = 0; K6 null. First level 1-2 only 2026Q1 via K3 = 15.
- Reality check: DW built share 0.059 at start to 0.152 at cutoff; OBT mean height 10.0 m (2022), 15.5 m (2023), 18.7 m (2024, estimate); share of cells at least 20 m: 0, 0.18, 0.49. Published progress 35% (2024-09-24) with a 2024 delivery promise. The site was building all along, just too slowly for the promise.
- Reason: (e) continuously active but behind plan. No K measures pace against the promised date. (Side note: A turned active in 2021Q2 while K1 was still below 0.01 and OBT had no built cells, so A was early, not late.)
- What would catch it: a pace-versus-plan indicator (structure progress relative to elapsed share of the promised period).
- Legitimate fix: yes, conditionally. The principle can be fixed before testing only if the expected-progress curve comes from data independent of these six cases (plan durations in the decree/specs, other districts such as R8, literature) and is hashed before R7 is scored. Calibrating it on these six would be fitting. Caveat: the postponement was only announced after the cutoff (2024-09-24).

### E4 / C12 (first date 2022-12-31 = K3 clock; original phase-1 date 2021-12-31; cutoff 2022-06-30)
- Timeline: 14 pre-cutoff quarters, 10+ images each; 9 assessable (2020Q2-2022Q2); levels `222444444`. The three level-2 quarters (2020Q2-Q4) come from K6 = 13, 16, 19 before the start was confirmed (started false), so they are excluded by the after-start reading, and they are a confirmation-lag artifact: the site was already being built (DW built 0.059 in 2019Q1 to 0.123 in 2019Q4; OBT 37 cells and 17.8 m in 2020). This is why the "literal" reading is true for this case.
- From 2021Q1: A 0.94-0.99 active 6/6, K1 above 0.02 6/6, K2 = 0.
- Reality check: OBT mean height 24.1 m and 68.5% of cells at least 20 m (2021), 23.0 m and 55.5% (2022, new cells added), 30.4 m and 99% (2023). Published progress 70% (2021-09). Handover 2024-04-18, complete 2026-09. So the structure finished roughly 6-12 months after the first date and handover followed later.
- Reason: (e) behind plan while active, with a (d) finishing/handover tail. No stall to detect.
- What would catch it: a pace-versus-plan indicator, but evidence 6 months before the first date is weak (structure about 69% at the 2021 survey). Re-defining the K3 clock to a later phase promise would be case-fitting.
- Legitimate fix: no (not supported by the pre-cutoff evidence; the only clean fix would be a different date definition, which is fitting).

### E5 / C21 (first date 2023-12-31, cutoff 2023-06-30): the one case caught
- Alert: level 1 in 2020Q3, 2020Q4, 2021Q1 (K2 = 6, 7, 8) and again 2021Q2-Q4 (K6 = 27, 30, 33 with K2 = 0); 39 months before the date. Levels `111111444444`.
- Why it fired: a launch statement published 2020-08-23 (event period 2019-04) set `started` to 2019Q2 retroactively. A was inactive from 2019Q2 to 2021Q1 (activity_prob 0.075 then 0.299, below the 0.4146 threshold), so K2 counted the pre-construction and ramp-up quarters as "inactive since start". K6 (months since launch without confirmed observed start) fired in parallel at 18+ months.
- Reality check: DW built growth only began 2020Q4 (K1 = 0.038, then 0.071, above 0.02), so A (annual Q2 reading) was inactive 2-3 quarters after growth was visible. From 2021Q2 A was active and no alert fired from K2 again (2022Q1 onwards level 4). The alerts in 2021Q2-Q4 are K6 running on while the start flag was still unconfirmed.
- Reading: the hit is a "launch announced, construction not yet started" alert (arguably true: about 20 months passed between the April 2019 launch and visible construction), produced mainly through publication-backdated start timing and A lag. It is not a stall detected during construction, and it does not generalize to the other five. Afterwards the site was active (OBT mean 11.4, 15.2, 16.3, 20.6 m for 2020-2023; share at least 20 m 0.11, 0.30, 0.51, 0.64) and no alert fired in the last 6 quarters before the cutoff.

### E6 / C10 (first date 2023-12-31, cutoff 2023-06-30)
- Timeline: 18 pre-cutoff quarters, 10+ images; 6 assessable (2022Q1-2023Q2); levels `444444`; started 2021Q2 (flag 2022Q1).
- A active 6/6 (0.94, 0.99, 0.67); K1 above 0.02 in 4/6; K1 = -0.007 and -0.010 in 2023Q1-Q2, with A still active. K2 = 0. First level 1-2: 2025Q1 via K3.
- Reality check: DW built 0.069 to 0.274 at cutoff (still rising, 0.316 at the date); OBT mean height 12.1 m (2021), 15.8 m (2022), 24.5 m (2023) with 81.5% of cells at least 20 m; 269 cells in 2024 versus 151 (new buildings, a later phase). The shell of the first phase was essentially complete by the date; the flat K1 in 2023 looks like completion rather than a stall (DW cannot tell the two apart). Phase 1 delivered late (planned 2025-04), whole project completed 2026-09 (33 months).
- Reason: (d), finishing and later phases are invisible to the activity signal; (b) is not supported (A active while K1 flat is consistent with a finished shell).
- What would catch it: nothing in the current satellite inputs; any "flat DW means alert" rule would also flag every finished building (false alarms).
- Legitimate fix: no.

### E7 / C19 (first date 2023-12-31; original 2022-12-31; cutoff 2023-06-30)
- Timeline: 18 pre-cutoff quarters; 10 assessable (2021Q1-2023Q2); started 2020Q2; levels `4444444444`; A active 10/10 (0.56-0.95), K1 above 0.02 10/10, K2 = 0. K3 never reached level 1-2 even later because the handover was published 2025-02-11 (K3 reset to 0).
- Reality check: OBT mean 11.5 m (2021), 15.7 m (2022), 21.8 m (2023), 26.0 m (2024 estimate); share at least 20 m 0.08, 0.28, 0.67, 0.80. Published progress 70% (2022-09-21) while OBT showed 28% of cells at least 20 m in 2022: a developer claim well ahead of the structure. A phase-1 promise for 2022Q4 was published 2022-04 and 2022-09. Delivery started 2024-Q4 (19 months late).
- Reason: (e) active but far behind the promise, with the promise already unreachable when published.
- What would catch it: pace-versus-plan, or a published-progress versus satellite-structure consistency check. Both could be stated as principles before testing.
- Legitimate fix: yes, conditionally, same conditions as E1 (independent calibration, pre-registered, hashed). The progress-claim check is a single-case observation here and should not be tuned on it.

### E8 / C02 (first date 2023-03-31; original 2023-06-30; cutoff 2022-09-30)
- Timeline: 15 pre-cutoff quarters, 10+ images; only 3 assessable (2022Q1-Q3; started 2021Q2, flag 2022Q1); levels `444`. A active 3/3 (0.93), K1 above 0.02 3/3, K2 = 0. K6 reached 11 in 2021Q4 (no level because not started) and would have hit 13 one quarter later had the start not been confirmed.
- Reality check: OBT mean height 12.8 m (2021) to 25.3 m (2022) with 97% of cells at least 20 m, so the structure was complete about 9 months before the first date; delivery started only in 2024 (about 18 months late). The delay sits in finishing/handover, which the satellite activity signal does not see.
- Reason: (d) not visible from space; contributing (a)-like effect: very short pre-cutoff window (first date 2023-03 was promised about 24 months after the 2021-01 publication, plus the 3-quarter start-confirmation lag).
- Legitimate fix: no. A finishing-stage detector exists only as an untested protocol (`29_height_final/PROTOCOL_finishing_detector.md`); it was not evaluated here.

## Summary table

| Case | Main reason | Key evidence | Legitimate fix |
| --- | --- | --- | --- |
| E1 / C14 | (e) active but behind plan | A active 10/10, K1 above 0.02 in 9/10, K2 = 0; OBT height 10.0 to 15.5 to 18.7 m; 35% progress at 2024-09; K3 only reaches level 2 at 2026Q1 | Yes, conditionally (pace-versus-plan from independent data, pre-registered) |
| E4 / C12 | (e) behind plan with (d) finishing tail; K6 false alarm in lag | 3 level-2 quarters are K6 before start confirmation; then A active 6/6, K2 = 0; structure 69% at least 20 m (2021), 99% (2023); handover 2024-04 | No |
| E5 / C21 | Caught: backdated start plus A lag plus K6, not a stall | Level 1 from 2020Q3 (K2 = 6-8, K6 18-33); A 0.075/0.299 inactive while K1 was 0.038-0.085 from 2020Q4; later no alert | n/a (not generalizable) |
| E6 / C10 | (d) finishing and later phases invisible | A active 6/6, K2 = 0; OBT 24.5 m, 81.5% at least 20 m in 2023; K1 negative 2023Q1-Q2 consistent with a finished shell | No |
| E7 / C19 | (e) active but far behind promise | A active 10/10, K1 above 0.02 10/10; 70% claimed in 2022-09 vs 28% of cells at least 20 m; K3 never fires (handover published first) | Yes, conditionally (same as E1) |
| E8 / C02 | (d) not visible from space, plus short window | Only 3 assessable quarters; OBT 25.3 m and 97% at least 20 m in 2022, 9 months before the date; delivery start 2024 | No |

Classification totals: (a) 0 as primary (images 10+/quarter always); (b) 0 (A and K1 agree in 4 of 5 missed cases; the C10 disagreement fits a finished shell); (c) structural: before the date only K2 and K6 can fire and the five missed cases give K2 no stall; (d) 2 (E6, E8); (e) 3 (E1, E4, E7).

## Limits and unchecked items

- Not independently checked: OBT height columns are context from `sat_yearly` (2024 estimate); no raw imagery or source drive was available, so Dynamic World growth was compared through the saved K1 and `dw12_built` values only.
- Published progress percentages are sparse (one to three per compound) and are developer statements; they are not ground truth.
- The `app_data/real` activity columns use the operational variant; only the backtest parquet was used for A, K2, K6 and level (verified equal to the release inputs).
- The "start-confirmation lag" and "K3 cannot fire before the date" statements are read from `src/pipeline/kpis.py` and confirmed in the timelines; no counterfactual rerun of the pipeline was done (by instruction).
- Any v2 pace indicator is only a candidate principle here: its form and calibration data must be chosen and hashed before R7 is scored, using data outside these six cases.
