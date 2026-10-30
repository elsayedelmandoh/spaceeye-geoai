# K7 "pace vs plan". Pre-registered 2026-10-30, before any K7 value is computed.

## Why
`35_backtest_diagnosis/DIAGNOSIS.md` found that 3 of the 5 missed R7 cases (E1, E4, E7) were sites that kept working but fell behind their plan. The current rules look for stalls, so they could not see this. K7 measures how far the structure is behind the compound's own published schedule.

**Honesty note:** the idea came from looking at the 6 R7 cases. Those cases are therefore **not an independent test** of K7, and every result on them is labelled "motivated by these cases". Inputs: `INVENTORY.md`.

## Definition (annual heights, so annual values)
- **Observed structure share** `O(y)`:
  - Numerator: the compound's footprint area with height ≥ 20 m in year y. 20 m is about the height of the district's ground + 7 floors rule (30 m cap); the inventory found no per-project floors.
  - Denominator: planned footprint = compound area × c, where c is calibrated (see below).
  - The ratio is clipped to [0, 1].
  - Heights: OBT for 2016-2023 and the published v4 estimate for 2024. 2025-2026 use the v9 C7 candidates, labelled as candidates and used for display only, never in an evaluation.
- **Expected share** `E(y)`, from the compound's own schedule:
  - `S` = start (published launch, else the pipeline's start quarter).
  - `D` = first published deadline.
  - The structure is assumed due by `D − F`, with F = 12 months for finishing (assumption).
  - Formula: `E(y) = clip((mid-year(y) − S) / (D − F − S), 0, 1)`.
  - Compounds with no published deadline get no K7, shown as "no plan".
- **Value:** `K7(y) = E(y) − O(y)`.
- **Levels:**
  - level 2 if K7 ≥ 0.30;
  - level 1 if 0.15 ≤ K7 < 0.30;
  - none otherwise.
- **Point in time:** the value for year y is used from quarter (y+1)Q1 on, when the annual composite exists. It never enters a quarter of year y itself.
- K7 is an extra indicator. In evaluation it is combined with the current levels as "worst of"; nothing else in the pipeline changes.

## Calibration (data independent of R7, done before any R7 value)
- **Plots:** the New Capital OSM plots in `30_district_retrospective`, excluding any plot that touches an R7 compound polygon or its 500 m buffer.
- **c** = median of the final-year (2023) built footprint / plot area, over plots that the retrospective study classed as completed or whose share ≥ 20 m is at least 0.8 by 2023. If fewer than 10 plots qualify, c = 0.225 (the district coverage rule).
- **Shape check (descriptive only):** for plots with a model start, the median share ≥ 20 m by years since start. It is reported to show whether a linear expected path is reasonable; it does not change the rule.
- **Not tuned:** F, the 20 m cut and the 0.15/0.30 thresholds are fixed here. Sensitivities are reported for F = 6 and 18 months and for thresholds ±0.05, but they are never used to choose.

## Evaluation
1. **6 R7 backtest cases (not independent):** after-start and point-in-time readings exactly as `backtest_check` defines them, using current levels + K7, against the existing criterion (5 of 6). Each case shows its K7 path.
2. **False alarms (R7):** compound-quarters with K7 level 1-2 for compounds and periods with no published delay before their deadline. The count and list are reported.
3. **R8 test (only if the team lead approves using R8 as a test-only set):** the same frozen rule on R8 projects with a published deadline and a dated delay outcome. The inventory found only 2 such cases, so this is reported as cases, not as a rate.

## Decision
- K7 enters the warning levels only if:
  - it adds at least 2 caught cases on the R7 check;
  - it raises no level 2 false alarm on a compound-period without a known delay;
  - and it agrees with every R8 test case (if run).
- **Even then, K7 is labelled "motivated by the evaluation cases; independent confirmation pending"** until new independent cases exist.
- Otherwise it stays a displayed context indicator with its numbers.
