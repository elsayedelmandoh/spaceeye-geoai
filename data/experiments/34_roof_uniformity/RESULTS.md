# T-AH-18 results: roof uniformity (OBT) and radar (Sentinel-1) for "structure topped out"

Run exactly per PROTOCOL.md (pre-registered 2026-10-30). Codes only, no compound names.

## Counts
- Buildings (OB V3, conf >= 0.75, area >= 200 m2, centroid in union of 12 R7 polygons + 1 km): 1457 (1771 in the bounding box before the centroid test); 500 m blocks (UTM 36N, origin at multiples of 500 m): 64; test blocks: 19 (seed 2035, 30 %, drawn before fitting).
- Unit-years t = 2017-2021: 7285; labelled: 1098.

| t | labelled | topped_out=1 | topped_out=0 |
|---|---|---|---|
| 2017 | 0 | 0 | 0 |
| 2018 | 0 | 0 | 0 |
| 2019 | 100 | 52 | 48 |
| 2020 | 340 | 125 | 215 |
| 2021 | 658 | 236 | 422 |

All 1457 buildings have OBT height 0 / presence 0 in 2016-2018 (median over buildings), so no unit-year in t=2017 or 2018 satisfies either label. Development therefore has only t=2019 rows (the protocol was not changed).
- Development rows (t=2017-2019, non-test blocks): 43 (positives 56 %). Test rows (t=2020-2021, test blocks): 326 (2020: 128, 2021: 198).

## Development (5-fold CV grouped by block, pooled out-of-fold balanced accuracy)
| arm | features | logistic | LightGBM (depth<=3) | chosen |
|---|---|---|---|---|
| U | 3 | 0.497 | 0.509 | logistic |
| R | 18 | 0.811 | 0.509 | logistic |
| U+R | 21 | 0.811 | 0.509 | logistic |

LightGBM would be chosen only if it beat logistic by >= 0.02; it never did. With only 43 development rows these scores are very noisy.

## Test (once, t=2020-2021, test blocks, 90 % bootstrap interval by block, 2000 resamples, seed 2035)

Gates: balanced accuracy >= 0.75 and recall >= 0.70. Pass is judged on the point estimates; the lower bounds are shown for strictness.

| arm | model | balanced acc. | 90 % CI | recall | 90 % CI | pass (point) | pass (lower bounds) |
|---|---|---|---|---|---|---|---|
| U | logistic | 0.495 | 0.460-0.539 | 0.770 | 0.717-0.846 | FAIL | FAIL |
| R | logistic | 0.551 | 0.494-0.587 | 0.973 | 0.867-1.000 | FAIL | FAIL |
| U+R | logistic | 0.543 | 0.495-0.577 | 0.980 | 0.887-1.000 | FAIL | FAIL |
| trivial rule h_t >= 20 m | none | 0.355 | 0.314-0.440 | 0.047 | 0.000-0.269 | FAIL | FAIL |
| base rate (share topped_out=1) | | test 0.454 | | dev 0.558 | | | |

Share of test rows predicted positive: U 0.78, R 0.92, U+R 0.93.

## Decision per PROTOCOL.md
Arm R: FAIL. Arm U: FAIL. Arm U+R: FAIL. If all fail, T-AH-18 is recorded as tested and failed.

## Exact data reductions
- OBT (GOOGLE/Research/open-buildings-temporal/v1): one image per year, filterDate per calendar year, mosaic; bands building_height, building_presence; reduceRegions with Reducer.toList, scale 4 m, crs EPSG:32636 (nearest sampling of the 0.5 m grid at 4 m), footprint polygons from OB V3. Pixel lists reduced locally.
- h_t = mean height over footprint pixels with presence >= 0.5; h_final = h_2023. "Presence share" (label 0 rule, >= 0.3) is read as the share of footprint pixels with presence >= 0.5 (the protocol does not define it further). Label 1 also requires h_t defined and every later-year height defined (a later year with no presence pixel fails the 2 m stay rule). Label 0: presence share_t >= 0.3 and h_2023 - h_t >= 3 m.
- Arm U: population std / mean, IQR / median (np.percentile 25, 75) and share within 2 m of the median, over footprint pixels with presence >= 0.5 in year t.
- Sentinel-1 (COPERNICUS/S1_GRD, IW, VV and VH present, ascending and descending pooled, already in dB in GEE; no extra calibration or speckle filter): per calendar year, per pixel median and temporal std (ee stdDev) of all scenes in dB, then mean over the region at 10 m (EPSG:32636, tileScale 4). Regions: footprint, and a 20 m ring = buffer(20) minus footprint (ring may contain neighbouring buildings). Scenes per year over the study box: 2015 29, 2016 43, 2017 128, 2018 124, 2019 120, 2020 104, 2021 89.
- Arm R features (18): per region (footprint, ring) VV and VH median, VV and VH temporal std, VV-VH (of the medians), change of VV and VH medians t-1 -> t and t-2 -> t-1.
- Models: median imputation (no NaNs occurred), StandardScaler + LogisticRegression(class_weight balanced, C=1) ; LightGBM max_depth 3, 7 leaves, 150 trees, lr 0.05, class_weight balanced, seed 2035. Final model fitted on all development rows, predicted at the default 0.5 threshold; no tuning on test. Dev score = balanced accuracy of pooled out-of-fold predictions with sklearn GroupKFold(5).
- Bootstrap: 2000 resamples of the 19 test blocks with replacement (same resamples for all arms and the trivial rule), 5th-95th percentile.

## Limits
- Development has only 43 labelled rows (t=2019 only) because OBT shows no buildings in 2016-2018 at these sites; CV scores (R up to 0.81) did not hold on test, consistent with noise and overfitting of 18-39 features to ~43 rows.
- Positives (topped_out=1) cluster at h_t about 9 m (median 9.2 m, 2019-2021) and negatives are mostly taller later; the trivial rule h_t >= 20 m therefore scores below chance (balanced accuracy 0.36). Likely OBT height of newly detected buildings is a near-constant default, so the truth itself is weakly informative at these sites.
- S1 footprints are small (>= 200 m2, a few 10 m pixels) and rings contain neighbouring buildings. 2015-2016 S1 coverage is sparse (29 and 43 scenes) but only enters t=2017 features, which have no labels.
- The truth is built from the same OBT product as arm U (arm U is history only, not independent of the label source).
