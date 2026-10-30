# K7 "pace vs plan": results (run 2026-10-30)

Protocol: `PROTOCOL.md` (sha256 `d48ac669...fec`, verified OK before each script; not edited). Codes only. Scripts: `scripts/01_calibrate.py`, `scripts/02_k7_eval.py` (repo `.venv`, `python -I`). Data tables: `calibration.json`, `calibration_shape.csv`, `k7_values.csv`, `eval1_cases.csv`, `eval2_alert_quarters.csv`, `sensitivities.csv`.

## Verdict

**K7 does NOT enter the warning levels. It stays a displayed context indicator with its numbers.**

Decision rule, applied literally:

| Condition | Result | Met |
| --- | --- | --- |
| Adds at least 2 caught cases on the R7 check (primary after-start reading) | 1 of 6 (existing) -> 6 of 6 (worst-of with K7): +5 | yes |
| No level 2 false alarm on a compound-period without a known delay | C18: 12 compound-quarters at K7 level 2 (2021Q1-2023Q4), no published delay | **no** |
| Agrees with every R8 test case | R8 evaluation pending approval, not run | not evaluated |

The second condition fails, so the rule fails. The first condition is met but is **motivated by these cases** (not an independent test): the idea came from looking at the 6 R7 cases. Even a pass would have carried the label "motivated by the evaluation cases; independent confirmation pending".

Caveat on the failing condition: C18 is the only plan compound without a published delay outcome, and its observed structure was also far behind its plan (O 0.08 in 2021, 0.41 in 2022, 0.86 in 2023 against a first deadline of 2021-12-31, which is a phase-1 date). "No published delay" is lack of an outcome record, not evidence of on-time delivery, so these 12 alerts may be correct alerts. The protocol counts them as false alarms; so do I.

## 1. Calibration (non-R7 plots only; written before any R7 value)

`calibration.json` (sha256 `a6c06cc3562a652f91be2151682dcd1e0622b8eb2cd33fb669973c46c4cd769f`, written 15:14:36, before `k7_values.csv` 15:16:14).

- **c = 0.1828** from n = 21 qualifying plots (>= 10, so the 0.225 fallback is not used). Quartiles of the plot values: 0.1315 to 0.2607.
- 225 plots in `30_district_retrospective`; 45 excluded as touching R7 (see deviation 1); 128 of the rest have a model start.
- Qualifying: status "completed" or share >= 20 m of at least 0.8 in 2023. Value: 2023 built footprint / plot area (`built_fraction_thr`, OBT).
- Sensitivity (reported, not used): compound-only exclusion (37 plots excluded) gives c = 0.1915 (n = 24); c = 0.225 is the district rule.

Shape check (descriptive; non-R7 plots with a model start; median share >= 20 m, count-based, by years since start):

| Years since start | -2 | -1 | 0 | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Plot-years | 18 | 36 | 69 | 104 | 98 | 76 | 64 | 43 |
| Median share >= 20 m | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.002 | 0.000 |
| Excluding left-censored starts (n) | 17 | 24 | 41 | 61 | 55 | 33 | 21 | 0 |
| Median share >= 20 m, excl. left-censored | 0.000 | 0.000 | 0.000 | 0.000 | 0.052 | 0.143 | 0.178 | n/a |

Reading: the typical non-R7 plot shows no 20 m share for the first 1-2 years after the model start and only 0.05 to 0.18 by years 2-4 (heterogeneous plots, model starts). That is a slow, back-loaded rise, so a linear expected path (E) front-loads the plan relative to this curve. The shape check does not change the rule.

## 2. K7 path per compound (O observed share, E expected share, K7 = E - O)

Plan compounds only (7 with a published deadline; C01 C03 C04 C07 C17 show "no plan"). K7(y) is used from (y+1)Q1. Years 2025-2026 are v9 C7 candidates, display only, never used. Level: 2 if K7 >= 0.30, 1 if 0.15 to 0.30 (as written in the protocol).

K7 by year (level in brackets: 2, 1, `.` none):

| Year | C02 | C10 | C12 | C14 | C18 | C19 | C21 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.066 |
| 2020 | 0.000 | 0.000 | 0.098 | 0.000 | 0.329 (2) | 0.090 | 0.317 (2) |
| 2021 | 0.247 (1) | 0.123 | 0.369 (2) | 0.000 | 0.923 (2) | 0.442 (2) | 0.372 (2) |
| 2022 | 0.809 (2) | 0.574 (2) | 0.416 (2) | 0.161 (1) | 0.589 (2) | 0.675 (2) | 0.272 (1) |
| 2023 | 0.820 (2) | 0.493 (2) | 0.000 | 0.608 (2) | 0.137 | 0.575 (2) | 0.115 |
| 2024 (v4 estimate) | 0.741 (2) | 0.269 (1) | 0.000 | 0.714 (2) | 0.000 | 0.466 (2) | 0.000 |
| 2025 (candidate) | 0.646 | 0.204 | 0.000 | 0.400 | 0.000 | 0.201 | 0.000 |
| 2026 (candidate) | 0.472 | 0.080 | 0.000 | 0.000 | 0.000 | 0.170 | 0.000 |

O (observed share of planned footprint at >= 20 m) and E, selected years:

| Code | O 2021 | O 2022 | O 2023 | O 2024 | E 2021 | E 2022 | E 2023 | E 2024 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C02 | 0.000 | 0.191 | 0.180 | 0.259 | 0.247 | 1.000 | 1.000 | 1.000 |
| C10 | 0.018 | 0.138 | 0.507 | 0.731 | 0.141 | 0.712 | 1.000 | 1.000 |
| C12 | 0.343 | 0.584 | 1.000 | 1.000 | 0.712 | 1.000 | 1.000 | 1.000 |
| C14 | 0.000 | 0.001 | 0.111 | 0.286 | 0.000 | 0.162 | 0.719 | 1.000 |
| C18 | 0.077 | 0.411 | 0.863 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| C19 | 0.011 | 0.141 | 0.425 | 0.534 | 0.453 | 0.817 | 1.000 | 1.000 |
| C21 | 0.227 | 0.594 | 0.885 | 1.000 | 0.599 | 0.866 | 1.000 | 1.000 |

Schedule used: S = launch event (C21 2019-04-01), launch publication date (C14 2022-03-16, no event date), else pipeline start quarter (C02 C10 C18 C19 2021-04-01 / 2020-04-01, C12 2020-04-01); D = `first_deadline`; F = 12 months. Full values: `k7_values.csv`.

## 3. Evaluation 1: the 6 R7 cases (not independent; motivated by these cases)

Same eligible quarters as `backtest_check` (level known, quarter ends >= 6 months before the first date), existing levels combined worst-of with K7 level 1-2. The baseline reproduces the frozen replay exactly (asserted against `releases/ready-data/backtest/cases.csv`: after-start 1/6, point-in-time 0/6).

| Case | Code | Existing after-start | Combined after-start (first alert, lead) | Combined point-in-time | K7 at last eligible quarter |
| --- | --- | --- | --- | --- | --- |
| E1 | C14 | no | yes (2023Q1, 21 months) | yes | 0.608 |
| E4 | C12 | no | yes (2022Q1, 9 months) | yes | 0.369 |
| E5 | C21 | yes (2020Q3, 39 months, K2) | yes (2020Q3, 39 months; K7 alone from 2021Q1) | yes | 0.272 |
| E6 | C10 | no | yes (2023Q1, 9 months) | yes | 0.574 |
| E7 | C19 | no | yes (2022Q1, 21 months) | yes | 0.675 |
| E8 | C02 | no | yes (2022Q1, 12 months) | yes | 0.247 |

- Existing: after-start 1/6, point-in-time 0/6. Combined: after-start 6/6, point-in-time 6/6. Criterion (5 of 6) met by the combined reading, **on cases that motivated K7**.
- Alternative (original promise) dates: combined after-start 5/6 (E4 not caught: its earlier date 2021-12-31 leaves only the 2021 values), point-in-time 5/6.
- Cautions: (i) E8/C02 K7 is 0.247 at its last eligible quarter (level 1, only 3 eligible quarters). (ii) K7 stays high for C02 even in 2024-2026 (0.74, 0.65, 0.47) because its measured footprint is about 5 percent of land area against c = 0.183: K7 mixes "behind schedule" with "footprint smaller than the c-based plan" and cannot tell a delay from a smaller build-out (phases not yet started).

## 4. Evaluation 2: false alarms (R7)

Compound-quarters with K7 level 1-2 for quarters 2017Q1 to 2025Q4 (K7 from measured/published years 2016-2024 only; 2026 quarters excluded because K7(2025) is a candidate value). Plan compounds with a known delay outcome (C02 C10 C12 C14 C19 C21, the six cases) are hit periods, not false alarms. Interpretation stated in deviation 4.

| Code | Delay known | Alert quarters | Level-2 quarters | Span |
| --- | --- | --- | --- | --- |
| C18 | **no** | **12** | **12** | 2021Q1-2021Q4 (before D, 4), 2022Q1-2023Q4 (after D, 8) |
| C02 | yes | 16 | 12 | 2022Q1-2025Q4 |
| C10 | yes | 12 | 8 | 2023Q1-2025Q4 |
| C12 | yes | 8 | 8 | 2022Q1-2023Q4 |
| C14 | yes | 12 | 8 | 2023Q1-2025Q4 |
| C19 | yes | 16 | 16 | 2022Q1-2025Q4 |
| C21 | yes | 12 | 8 | 2021Q1-2023Q4 |

False-alarm list (no known delay): C18 2021Q1, 2021Q2, 2021Q3, 2021Q4, 2022Q1, 2022Q2, 2022Q3, 2022Q4, 2023Q1, 2023Q2, 2023Q3, 2023Q4, all level 2 (K7 from 2020, 2021, 2022 = 0.329, 0.923, 0.589). Total 12 quarters, all level 2 under the protocol wording. Full list: `eval2_alert_quarters.csv`.

## 5. Sensitivities (reported, not used to choose)

Columns: existing / combined after-start cases (of 6), combined point-in-time, added after-start cases, false-alarm quarters on C18 (level 1-2; of which K7 >= 0.30 at the base thresholds, labelled "level 2").

| Variant | Combined after-start | Combined point-in-time | Added | C18 alert quarters | of which level 2 |
| --- | --- | --- | --- | --- | --- |
| Base: F=12, 0.15/0.30 | 6 | 6 | +5 | 12 | 12 |
| F=6, 0.15/0.30 | 6 | 6 | +5 | 12 | 8 |
| F=18, 0.15/0.30 | 6 | 6 | +5 | 12 | 12 |
| F=12, 0.10/0.25 | 6 | 6 | +5 | 16 | 12 |
| F=12, 0.20/0.35 | 6 | 6 | +5 | 12 | 8 |
| F=6, 0.10/0.25 | 6 | 6 | +5 | 16 | 8 |
| F=6, 0.20/0.35 | 5 | 4 | +4 | 8 | 8 |
| F=18, 0.10/0.25 | 6 | 6 | +5 | 16 | 12 |
| F=18, 0.20/0.35 | 6 | 6 | +5 | 12 | 12 |
| S = pipeline start for all | 6 | 6 | +5 | 12 | 12 |
| Deadline usable only from its publication quarter | 6 | 6 | +5 | 10 | 10 |
| c = 0.1915 (compound-only exclusion) | 6 | 6 | +5 | 16 | 12 |
| c = 0.225 (district rule) | 6 | 6 | +5 | 16 | 12 |

Every variant keeps at least 4 added cases and a C18 false alarm (8 to 12 level-2 quarters), so the verdict does not depend on F, the thresholds or c within this range. The "of which level 2" column counts the protocol's literal level 2 (K7 >= upper threshold).

## 6. R8 evaluation

**Pending approval** (the team lead has not approved using R8 as a test-only set). Not run; no R8 value computed.

## Deviations and interpretation points (for the team lead)

1. **R7 exclusion for calibration.** 5 of the 12 compounds have no location (R7-P08 to P12 are "not_located") and only 3 accepted boundary polygons exist. A literal "compound polygon + 500 m" would leave plots next to unlocated compounds. I excluded plots touching the union of (accepted compound polygons, plots holding an R7 pin, R7 pins of located compounds, and the whole R7 district outline), buffered 500 m (45 plots). The literal compound-only version (37 plots) gives c = 0.1915, reported above as a sensitivity. Distances use a local equirectangular projection (no `pyproj` in the venv); error is negligible at 500 m.
2. **Share >= 20 m for plots is count-based** (`share_full_of_present`, buildings of class "full" among present buildings), because per-building footprint areas are not available for the 225 plots. Footprint / plot area uses OBT `built_fraction_thr`. R7 compounds use the area-based share (`obt_share_area_ge20m` x `obt_built_area_m2`).
3. **2024 footprint** for K7 comes from `sat_yearly` (v4-style estimate): share >= 20 m x number of built cells x m2 per cell, with m2 per cell taken from the same compound's 2023 OBT area / cells. Cell counts in 2024 equal 2023 except C10 (151 to 269).
4. **"No known delay" reading.** Only C18 is a plan compound without a delay outcome; the other six plan compounds are the delayed cases, so their K7 alerts are hit periods. Also, "level 2" is taken literally as K7 >= 0.30 as the protocol writes it. The pipeline's own numbering is the reverse (level 1 = most severe), so this wording may be a typo. If level 2 meant 0.15 to 0.30, C18 would have 0 level-2 and 12 level-1 alert quarters, which would not pass in spirit either; the strict wording would technically pass. Please confirm the intended numbering. Alerting (level 1-2) is unaffected.
5. **Launch date for C14** is the publication date of the launch statement (2022-03-16; no event date exists), as the rule "published launch" reads; the pipeline observed activity from 2021Q2. Using the pipeline start for all compounds is in the sensitivity table (no change in outcome).
6. **K7 values from 2025-2026** (candidates) are shown but excluded from every evaluation, so false-alarm quarters stop at 2025Q4 and the last K7 year used is 2024.
7. **Deadline publication timing** is not part of the protocol's point-in-time rule; as a sensitivity I required the deadline to be published before use (C18 drops from 12 to 10 alert quarters; verdict unchanged).
8. The shape check (median share 0 for 2 years after start) suggests the linear E path is not a good fit for typical plots; reported, not acted on, per protocol.
