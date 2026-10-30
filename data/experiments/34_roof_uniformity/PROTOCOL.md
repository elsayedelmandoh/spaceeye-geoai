# T-AH-18: is the structure finished? Roof uniformity (Google heights) and radar (Sentinel-1). Pre-registered 2026-10-30, before any number.

Team lead: run the task and add radar. The useful product is a signal for **2024-2026**, after Google heights stop. So radar is the arm that matters; roof uniformity on Google heights only tells the past.

## Question
For a building in year t, has its concrete structure reached its final height ("topped out"), or is it still rising?

## Units
Google Open Buildings V3 polygons (confidence ≥ 0.75, area ≥ 200 m²) in the R7 study area: the 12 R7 compound polygons plus a 1 km buffer, with each building's centroid inside. Unit = building × year.

## Truth (from Google Open Buildings Temporal, 2016-2023; only years with a later check)
- `h_t` = mean OBT height over the footprint pixels with presence ≥ 0.5 in year t. `h_final` = mean height in 2023.
- **topped_out(t) = 1** if `h_final ≥ 8 m`, `h_t ≥ 0.9 · h_final`, and every later year up to 2023 stays within 2 m of `h_t`.
- **topped_out(t) = 0** if the building is present in t (presence share ≥ 0.3) and later rises by ≥ 3 m by 2023.
- Anything else is excluded (ambiguous, absent, or low buildings).
- Years t = 2017-2021, so every unit has at least two later years.

## Features (fixed list)
- **Arm U (roof uniformity, OBT year t only):**
  - coefficient of variation of pixel heights inside the footprint;
  - IQR / median;
  - share of pixels within 2 m of the footprint median.
- **Arm R (radar, Sentinel-1 GRD IW, ascending + descending, 10 m; calendar year t):** over the footprint, then the same over a 20 m ring around it:
  - annual median and temporal standard deviation of VV and VH (dB);
  - the VV-VH difference;
  - the change of the annual medians from year t-1 to t, and from t-2 to t-1.
- **Arm U+R:** both lists.

## Models and split
- **Model:** logistic regression (standardised, class-balanced). A small LightGBM (depth ≤ 3) is allowed only if it beats the logistic by ≥ 0.02 balanced accuracy on development.
- **Development:**
  - years t = 2017-2019;
  - 5-fold cross-validation grouped by 500 m block.
- **Test (once):**
  - years t = 2020-2021;
  - blocks drawn with seed 2035: 30 % of the blocks, held out of development in every year.

## Gates (test, per arm)
- balanced accuracy ≥ 0.75, and recall of `topped_out` ≥ 0.70, with a 90 % bootstrap interval by block;
- the base rate is reported, plus a trivial rule (`h_t ≥ 20 m`) for comparison.

## Decision
- If **arm R passes**, radar becomes a candidate "structure complete" signal for 2024-2026. Its use there is shown as context only, with the test accuracy, and never enters the level without a new pre-registered check.
- If only arm U passes, it describes 2016-2023 only (history), so there is no early-warning value.
- If neither passes, T-AH-18 is recorded as tested and failed.
