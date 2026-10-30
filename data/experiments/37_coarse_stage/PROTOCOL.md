# Coarse construction stage (S0 / S1 / S2). Pre-registered 2026-10-30, before any label or number.

Team lead's request: add the stage of the building. Fine stages failed four times (finishing vs structure: Sentinel-2 0.674, VLM 0.559; topped-out: roof 0.495, radar 0.551). This test uses three coarse stages that look different from above. Structure and finishing are merged on purpose, because they could not be separated.

Inputs are described in `INVENTORY.md`. No existing S0/S2 labels exist, so new labels are made first.

## Stages (unit = 500 m block × year)
- **S0 land / ground works:** mostly bare ground, excavation or foundations; no building mass above ground.
- **S1 under construction:** building frames, unfinished blocks, cranes, construction yards; finishing work counts here.
- **S2 complete and operating:** finished buildings with landscaping (lawns, trees), paved internal roads, and signs of use (parked cars, pools with water).
- **Majority rule:** a block takes the stage of most of its built or plotted area. If no stage covers at least 50 % of it, the label is `mixed`, which is excluded from the gates and counted in the report.
- **Unusable:** cloud, missing tile, or a capture more than 9 months from the target date. These rows are excluded.

## Step 1: labels, made before any feature is computed
- **Sample:** 220 blocks on the UTM 500 m grid inside the New Capital study box used by `29_height_final/finishing`.
  - Exclude the 12 R7 compound polygons and a 500 m buffer around them, so R7 is never used to fit.
  - Exclude blocks that are more than 80 % outside urban plans (pure desert or the ring road).
  - Strata: tertiles of the 2025 Dynamic World grass+trees share, with an equal number per tertile. This is a sampling device to obtain enough S2. It is declared here, and per-class recall does not depend on prevalence.
  - Seed 2036.
- **Dates:** for each block, the Wayback capture nearest to mid-2019, mid-2021, mid-2023 and mid-2025, using capture dates from the metadata, not release dates. A date is used only if it is within 9 months of the target.
- **Rater:** one blind visual pass on Wayback zoom-18/19 crops of the block. The rater sees the image and its capture date only; no feature, height or Dynamic World value is shown.
- **Agreement check:** a second independent pass on a random 25 % of the labelled rows (seed 2037, shuffled order, previous labels hidden).
  - Cohen's kappa must be **≥ 0.70**.
  - If kappa is lower, the experiment **stops** with "labels unreliable" and no model is fitted.

## Step 2: features (fixed list; 12 months centred on the capture date)
- **Dynamic World:** mean probability of built, bare, grass, trees and water over the block, and the change from the previous 12 months.
- **Sentinel-2 median:** NDVI, NDBI, brightness (mean of B2-B4) and SWIR1/NIR ratio; the 90th percentile of NDVI.
- **Sentinel-1 median:** VV, VH and VV−VH (dB), and their temporal standard deviation.
- **Night lights:** VIIRS Black Marble (VNP46A2 or the monthly composite in Earth Engine), mean radiance over the block, and the change from 12 months earlier.
- Heights are not used. OBT ends in 2023, and these features must work for 2024-2026.

## Step 3: models and split
- **Split:**
  - Test = 30 % of the labelled blocks, drawn with seed 2038 and held out in every year.
  - Development = the rest, with 5-fold cross-validation grouped by block.
- **Baseline B (simplest):** ordered thresholds on two Dynamic World values (built, and grass+trees), fitted on development.
- **Model M:** multinomial logistic regression (standardised, class-balanced). LightGBM with depth ≤ 3 is allowed only if it beats the logistic by ≥ 0.02 macro recall on development.
- All choices are frozen on development. The test is run **once**.

## Gates (test, labelled S0/S1/S2 rows; 90 % bootstrap interval by block)
- macro recall (balanced accuracy) **≥ 0.75**;
- recall of each class **≥ 0.60**;
- S2 precision **≥ 0.60**.
- If both B and M pass, B is used, as the simpler method.
- Also reported: the confusion matrix, the class counts, the `mixed` and unusable counts, and kappa.

## Decision
- **Pass:**
  - The stage becomes a **candidate layer** for R7, applied to the 12 compound polygons for 2019-2026 as a stage share per compound-year.
  - It is shown as context with its test accuracy. It does not enter the warning level without a new pre-registered check.
  - Descriptive sanity check only (n = 12, not a gate): agreement with the developer delivery status table.
- **Fail:** recorded as tested and failed, with the numbers. The stage then comes from the human imagery comparison (T-AH-15) or from higher-resolution imagery (`36_vhr_access`).
- No gate, class definition or feature is changed after seeing a test number.

## Amendment 1 (2026-10-30, team lead's request, before any label, feature or model): add heights
Made while Step 1a (sampling and image download) was running. No label, feature (other than the declared stratum value) or model existed yet.

- **Arm H** = all Step 2 features plus height features from Google Open Buildings Temporal (Earth Engine, 4 m) over the block:
  - presence share;
  - mean height and 90th-percentile height of present pixels;
  - share of present area at least 20 m;
  - change of mean height from 2 years earlier.
- **The missing part (OBT stops in 2023).**
  - Label years 2019, 2021 and 2023 use OBT of the same year.
  - The 2025 rows use OBT 2023 carried forward, plus a feature `height_age_years` (0 or 2). This is exactly how the layer would run for 2024-2026, so the 2025 test rows are the honest test of that regime.
  - Satellite change features (Dynamic World, Sentinel-1, Sentinel-2, night lights) are current for every year, so a block that changed after 2023 can still be seen.
- **Arm M** = Step 2 features only, unchanged.
- **Gates for each arm:**
  - the Step 3 gates;
  - and, separately on the 2025 test rows, macro recall **≥ 0.70** with its 90 % block interval reported (this is the 2024-2026 regime check).
- **Choice:**
  - If both arms pass, H is used only if it beats M by ≥ 0.03 macro recall on development; otherwise M, as the simpler arm.
  - Baseline B keeps priority if it passes.
- **R7 application sensitivity, not a gate:** for 2024-2026, also show the stage computed with the v9 C7 candidate heights (`29_height_final/v9/out_v9b`), labelled "candidate heights".
- **Future fix:** current heights for 2024-2026 from higher-resolution imagery (see `36_vhr_access`), tested under a new protocol.

## Amendment 2 (2026-10-30, before any label, feature or model): model heights from the server
The team lead confirmed the GPU server is still available.

- **Arm H2** = Step 2 features plus the same height features as arm H. The heights come from the v9 C7 height model run on the server for the sampled blocks, for every label year (2019, 2021, 2023, 2025). This uses one source for all years, with no carry-forward.
- It runs only if C7 predictions for these blocks can be produced **without retraining** (existing checkpoints and stacker). If that is not possible, H2 is reported as "not run", with the reason.
- **Known caveat:** C7 was trained on OBT 2016-2023 over the same study box. Its 2019-2023 values are therefore close to fitted values, while its 2025 values are true predictions. The 2025 regime check (macro recall ≥ 0.70 on the 2025 test rows) is what decides whether H2 holds up.
- **Gates and choice:**
  - Same gates as the other arms.
  - Among arms that pass, choose in order of simplicity (B, then M, then H, then H2). A more complex arm is used only if it beats the next simpler passing arm by ≥ 0.03 macro recall on development.
