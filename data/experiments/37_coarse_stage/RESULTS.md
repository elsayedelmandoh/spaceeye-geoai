# Coarse construction stage (S0 / S1 / S2): Step 2-3 results

**Verdict: PASS. Arms passing all gates: B, H. Rule outcome: arm H** (B passes, but H beats B on development macro recall by 0.132 >= 0.03; M fails the 2025 regime check by 0.001). Not applied to R7 yet. Arm H2 is pending: server inference not yet available.

Test = 66 held-out blocks (seed 2038), evaluated once (`test.flag`). Intervals are 90 % block bootstrap. Gates: macro recall >= 0.75, each class recall >= 0.60, S2 precision >= 0.60, 2025-rows macro recall >= 0.70.

## Results per arm

| arm | model | dev macro recall | test macro recall [90 % CI] | recall S0 | recall S1 | recall S2 | S2 precision | 2025 rows macro recall [90 % CI] | Step 3 gates | 2025 check | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B (two DW thresholds) | threshold | 0.700 | 0.759 [0.695, 0.821] | 0.782 [0.682, 0.873] | 0.815 [0.717, 0.907] | 0.680 [0.537, 0.808] | 0.836 [0.733, 0.917] | 0.705 [0.586, 0.817] | pass | pass | **PASS** |
| M (satellite features) | lgbm | 0.840 | 0.818 [0.768, 0.865] | 0.908 [0.844, 0.958] | 0.667 [0.562, 0.771] | 0.880 [0.814, 0.941] | 0.857 [0.765, 0.931] | 0.699 [0.607, 0.795] | pass | fail | **FAIL** |
| H (M + OBT heights) | logit | 0.832 | 0.818 [0.765, 0.867] | 0.916 [0.842, 0.981] | 0.685 [0.571, 0.792] | 0.853 [0.769, 0.924] | 0.901 [0.794, 0.983] | 0.767 [0.667, 0.873] | pass | pass | **PASS** |
| H2 (server model heights) | pending: server inference not yet available | | | | | | | | | | not run |

Notes:
- Several interval lower bounds sit below their thresholds (B macro recall, B S2 recall, S1 recall of M and H, the 2025 macro recall of every arm). With 66 test blocks the gates are not decided with margin by these intervals.
- 2025 test rows: 62 (S0 26, S1 8, S2 28); only 8 are S1, so the 2025 S1 recall is very noisy.
- H uses OBT 2023 carried forward for 2025 rows (`height_age_years` = 2).
- Dev macro recall, LightGBM minus logistic: M +0.024 (kept LightGBM, rule +0.02), H +0.002 (kept logistic).
- B thresholds (fitted on development): built < 0.0829 -> S0; else grass+trees >= 0.0537 -> S2; else S1.

## Choice rule

- Passing arms in order of simplicity: B, H. M does not pass (2025 macro recall 0.699 < 0.7).
- Dev macro recall: B 0.700, M 0.840, H 0.832.
- H beats B by 0.132 (>= 0.03), so **H** is chosen.

## Confusion matrices (test, rows = true)

**B (two DW thresholds)**

| true / predicted | S0 | S1 | S2 |
| --- | --- | --- | --- |
| S0 | 93 | 21 | 5 |
| S1 | 5 | 44 | 5 |
| S2 | 1 | 23 | 51 |

**M (satellite features)**

| true / predicted | S0 | S1 | S2 |
| --- | --- | --- | --- |
| S0 | 108 | 5 | 6 |
| S1 | 13 | 36 | 5 |
| S2 | 2 | 7 | 66 |

**H (M + OBT heights)**

| true / predicted | S0 | S1 | S2 |
| --- | --- | --- | --- |
| S0 | 109 | 6 | 4 |
| S1 | 14 | 37 | 3 |
| S2 | 5 | 6 | 64 |

## Confusion matrices (development, 5-fold GroupKFold out-of-fold)

**B (two DW thresholds)**

| true / predicted | S0 | S1 | S2 |
| --- | --- | --- | --- |
| S0 | 170 | 52 | 19 |
| S1 | 15 | 125 | 30 |
| S2 | 0 | 62 | 120 |

**M (satellite features)**

| true / predicted | S0 | S1 | S2 |
| --- | --- | --- | --- |
| S0 | 206 | 19 | 16 |
| S1 | 18 | 141 | 11 |
| S2 | 11 | 19 | 152 |

**H (M + OBT heights)**

| true / predicted | S0 | S1 | S2 |
| --- | --- | --- | --- |
| S0 | 202 | 22 | 17 |
| S1 | 16 | 139 | 15 |
| S2 | 13 | 16 | 153 |

## Counts

- Pass-1 labels: S0 360, S1 224, S2 257, mixed 22, unusable 3 (866 usable image rows; 14 more block-years were unusable at sampling, 880 in total).
- Used for fitting and gates (S0/S1/S2): 841 rows in 220 blocks.
- Development: 154 blocks, 593 rows {'S0': 241, 'S2': 182, 'S1': 170}.
- Test: 66 blocks, 248 rows {'S0': 119, 'S2': 75, 'S1': 54}.
- Step 1 kappa: 0.784 (pass), see `AGREEMENT.md`.

## Deviations and interpretations

- **Gates read on point estimates.** The protocol lists 90 % block intervals next to the gates without saying whether the point value or the lower bound must clear them. Pass/fail uses the point estimate; every interval is shown.
- **The 2025 regime check is applied to every arm, including B** (Amendment 1 says "each arm"). B also passes the original Step 3 gates alone; the table shows both.
- **Dynamic World:** mean over all DW scenes in the window (no join to Sentinel-2 L1C cloud < 20 % as in Step 1a). Change = window mean minus the mean of the 12 months before the window start.
- **Sentinel-2:** SR harmonized, scenes with CLOUDY_PIXEL_PERCENTAGE < 60 and SCL masked (cloud, shadow, cirrus, snow, no-data, saturated); median bands give NDVI, NDBI, brightness, SWIR1/NIR. NDVI p90 = per-pixel temporal 90th percentile of scene NDVI, then block mean.
- **Sentinel-1:** GRD IW, ascending pass only (one geometry, all relative orbits), VV and VH in dB as stored in Earth Engine; temporal std per pixel, then block mean.
- **Night lights:** VNP46A2 Gap_Filled_DNB_BRDF_Corrected_NTL, daily mean over the window; change vs the 12 months before the window start. Raw Earth Engine units (not rescaled).
- **Windows** are capture date -6 / +6 months. All block values are means over the 500 m block at 10 m (UTM 36N); block cell = block_id.
- **Open Buildings Temporal:** one image per year (2017, 2019, 2021, 2023), presence >= 0.5, read at 4 m. Height statistics are over present pixels; a block with no present pixel gets height mean / p90 / tall share = 0 (presence share 0). Change of mean height = mean height at the height year minus the year two earlier (2017 for 2019 rows; 2021 for 2025 rows, where the height year is 2023).
- **Model details not fixed by the protocol:** logistic C = 1 (default, not tuned); LightGBM depth 3, 7 leaves, 200 trees, learning rate 0.05, class-balanced; B thresholds from a 49-quantile grid maximising macro recall; GroupKFold(5) without shuffling; bootstrap 2,000 block resamples, seed 2039. LightGBM was compared with the logistic inside each feature arm (M and H) with the +0.02 dev rule.
- **Arm H2:** pending: server inference not yet available. Not run.
- **PROTOCOL.md hash:** sha256 equals the value in PROTOCOL.sha256 (166255658c4f81731c6a3c2d12bba75bdee439ae059effce535fc5c71d8af8b0), including the Amendment 2 text; no mismatch.
- Earth Engine reported "restricted mode" (noncommercial quota) as a warning; all requests still completed.

## Files

- `scripts/s2_features.py`, `scripts/s3_model.py`; `features/ee_window_features.csv`, `features/obt_features.csv`; `dev_results.json` (frozen before the test), `test_results.json`, `test.flag`.

## Owner decision (2026-10-30)
The team lead accepts reading the gates on point estimates, as the protocol does. The 90 % intervals stay reported. The same applies to T-AH-17 (`40_finishing_human_check`). This decision was made after the result was known. It does not change any gate value; it only confirms that intervals are reported, not gated.

## Independent review (2026-10-30): sound with caveats
An independent reviewer re-implemented the pipeline and reproduced every number (split, B thresholds, all arms, 2025 rows, kappa). It found no test-into-dev leakage, and the label files have no integrity defect after the batch A rewrite. The following caveats must accompany any use of this layer.

1. **2025 regime, the "under construction" class:** H recall is 0.375, only 3 of 8 rows (90 % CI 0.11-0.67). The 2025 macro recall of 0.767 comes from S0 and S2. B finds 6 of 8. For 2024-2026, H is reliable for "land" and "complete" but weak for "under construction".
2. **Choice rule:**
   - H was chosen under Amendment 2's chain rule (the latest rule, written before any label).
   - Under the original text plus Amendment 1 ("B keeps priority if it passes"), the layer would be B: test macro 0.759, S2 recall 0.680.
3. **H vs M:** they cannot be told apart on test (difference CI ±0.04). M missed the 2025 check by 0.001, one row.
4. **Point estimates:** gates are read on point estimates, as the owner confirmed. Lower bounds below the thresholds are H S1 recall (0.571) and H 2025 macro recall (0.667).
5. **Labels:** labels come from AI raters of one model family, so kappa measures consistency, not truth. 34 % of test rows are low confidence, and H scores 0.94 on high-confidence rows against 0.64 on low-confidence ones. The 22 `mixed` rows (transitional blocks) are excluded.
6. **Spatial transfer:** 76 % of test blocks touch a dev block. Test blocks without an adjacent dev block score 0.749 (n = 16). R7 is buffered and is used at compound-polygon level, so expect lower accuracy there.
7. **Timing:**
   - Windows are ±6 months, so the stage for date T exists only after T + 6 months.
   - `height_age_years` was validated only at 2. Sensitivity on the 2025 test rows: value 1 (2024 use) 0.767, value 3 (2026 use) 0.731.
8. **H2:** H2 (server model heights) is still pending. Any later H2 result is scored on an already-seen test set and stays provisional.
9. **Provenance:** `s3_model.py` was touched after the test run. The reviewer's independent recompute matches `test_results.json` exactly. The scripts and outputs should be archived now.

Reviewer scripts: `C:\Users\Ahmed\AppData\Local\Temp\rev37\`.
- R7 application: see r7_application/R7_APPLICATION.md (start of construction plausible; completion does not transfer to R7).
