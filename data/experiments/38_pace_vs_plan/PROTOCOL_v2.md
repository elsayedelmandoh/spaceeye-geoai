# K7 v2 "pace vs plan": independent test. Pre-registered 2026-10-30, before the delivery truth is read and before any R8 or new K7 value exists.

This version folds in an independent critique of the first draft (must-fix items 1-8).

## Why v2
v1 (`PROTOCOL.md`, `RESULTS.md`) alerted on all 7 R7 compounds with a published plan, so it could not be judged. It was also motivated by the 6 cases it was tested on, and it had two known defects:
- a straight expected path, while real plots stay near zero height share for years after start;
- a land-area denominator that penalises compounds with little built-up area (C02).

The team lead approved using R8 compounds as a **test-only** set (decision delegated, 30 October 2026).

## Truth (`real_data/39_delivery_truth/DELIVERY_TRUTH.md`, collected independently)
- **on_time:** first handover ≤ original promise + 3 months.
- **delayed:** first handover > promise + 3 months; or no handover, together with a published postponement or a dated source after promise + 3 months saying units are not delivered.
- **unknown:** everything else, including "no handover news". These are excluded and listed.
- The promise D and the handover are compared at the same scope: the earliest published promise and its phase.
- **Independent set:** the R8 compounds plus the R7 compounds outside the 6 backtest cases (C01 C03 C04 C07 C17 C18) that have a known class.
- **C18 caveat:** C18's v1 values were seen while v2 was being designed. The gate must therefore also hold with C18 excluded, and both results are reported.

## K7 v2 (annual heights; point in time: the value for year y is used from (y+1)Q1)
- **Applicability:** K7 is computed only where the district rule or published floors allow at least 7 floors (R7: ground + 7). Otherwise the compound is listed as "not applicable", because low-rise buildings never reach 20 m and K7 would equal E.
- **Start S:** the first OBT year in which the present footprint reaches the threshold below. This is the same definition for calibration plots and compounds. A published launch is not used.
- **Observed R(y):** footprint area at ≥ 20 m divided by footprint area present in year y.
  - Undefined if fewer than 3 buildings or less than 5,000 m² are present. Once E ≥ 0.3, an undefined R counts as R = 0.
  - Heights: OBT 2016-2023, then for 2024 the published v4 estimate for R7. For R8 the 2024 value is the v9 C7 model value. Results are also reported using OBT years only, as a separate column.
  - Planned coverage is shown next to R, because R cannot see phases that have not started.
- **Expected E(y), from an empirical curve:**
  - **Curve plots:** non-R7 plots in `30_district_retrospective` (excluding R7 and its 500 m buffer) that are not left-censored and reach R ≥ 0.8 by 2023. Their n is reported.
  - For each plot, `T80_plot` = the years from S to R ≥ 0.8, and `τ = (t − S) / T80_plot`.
  - E(τ) = the median R across curve plots at τ, binned in steps of 0.25. E = 1 for τ ≥ 1.
  - Plot shares are computed with the same area-based R as compounds where footprints allow. If they are count-based, this is stated as a limitation.
  - **Compound time:** `τ = (mid-year(y) − S) / (D − F − S)`, with F = 12 months, D = the original promise (used only from its publication date on) and S from OBT.
  - If fewer than 10 curve plots qualify, use the stepwise fallback: E = 0 for τ < 0.4, then linear to 1 at τ = 1.
- **Gap and alerts:** `K7 = E − R`.
  - **Strong** if K7 ≥ 0.30 (pipeline level 1, the most severe).
  - **Weak** if 0.15 ≤ K7 < 0.30 (pipeline level 2).
  - The thresholds come from v1. They are untuned, not validated.

## Baselines (computed the same way)
- **B0, time only:** R = 0, so E alone triggers alerts. This shows what a high delay base rate gives for free.
- **B1, existing levels:** the current pipeline levels, using the R7 levels where they exist. For R8, B1 is not available and is reported as such.
- **v1:** frozen as published.

## Evaluation (once, on the independent set)
- **Delayed compound:** caught if any alert (strong or weak) appears in a quarter ending at least 6 months before D. The lead time is reported.
- **On-time compound:** a false alarm if any alert (strong or weak) appears between S and its first handover. Strong and weak alerts are reported separately.
- A compound with no eligible quarter in the catch window is listed and excluded.
- Reported per compound, for v2, B0, v1 and B1: the K7 path, the catches and the false alarms, with Clopper-Pearson 95 % intervals.

## Gate (v2 enters the warning levels only if all hold, both with and without C18)
- the independent set contains at least 2 on-time and at least 3 delayed compounds; otherwise the result is **"not testable"**, and that is final for this version;
- v2 catches at least 2/3 of the delayed compounds, and at least as many as B1 where B1 exists;
- v2 raises no alert on any on-time compound, and raises fewer on-time alerts than B0.

## Decision
- **Pass:** K7 v2 joins the levels as "worst of". Its label says the result is consistent with, not proof of, a working indicator, and gives n per class and the intervals.
- **Fail or not testable:** K7 stays a displayed context indicator, and the reason is stated.
- No change to definitions, F, thresholds, the curve or the truth rule after the truth table or any K7 v2 value has been read. The gate is not loosened afterwards.
