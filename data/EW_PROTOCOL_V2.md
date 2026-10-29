# Binary distress evaluation protocol, v2 (frozen before any v2 fit)

Written on 29 October 2026 and frozen (hash recorded in `EW_PROTOCOL_V2.sha256`) before any v2 model is fitted. Synthetic - for training only.

**Status of the evidence.** The v1 results (`EW_PROTOCOL_CURRENT.md`, `CURRENT_MODEL_METADATA.json`, `CURRENT_MODEL_METRICS.csv`, `EW_REPORT_CURRENT.md`) have already been inspected, and several v2 choices respond to them. v2 is therefore **not a blind test**: it is a documented second round. v1 results stay in the repository labelled v1 and are never overwritten; v2 writes only to `data/V2_MODEL_METADATA.json`, `data/V2_MODEL_METRICS.csv`, `data/EW_REPORT_V2.md` and `app_data/ml_v2/`. No v2 number may be presented as untouched holdout performance. Repeated synthetic quarters are not independent real events, and no operational accuracy or superiority threshold is promised.

## What stays identical to v1

Target (distressed / not_distressed in the next six calendar months, censoring and already-handed-over rows excluded), the 180-row dataset `ml_dataset_extended`, key/target/censoring exclusions, training-only preprocessing (median imputer keeping empty features, standard scaler for logistic), estimators and parameters (logistic C=0.3 balanced, max_iter 2000; histogram boosting depth 2, 60 iterations, learning rate 0.05, min_samples_leaf 6, l2 1, balanced), seed 2026, capacity 4, model tie-break by code, 2,000 random draws, the public rule and the combined rule, and the metric set (class supports, per-class recall, two-class macro-F1, confusion counts, distressed recall@4 as n of m, random mean and 95% interval). No hyperparameter search. No oversampling, added compounds, shifted test rows or altered source observations.

## Variants

| Variant | Feature change against v1 | Stage | Features (combined / satellite-only) |
| --- | --- | --- | --- |
| v1 | none (frozen reference) | done | 40 / 18 |
| v2a | drop `height_mean_m` (`candidates.no_height_ablation: true`) | 1, code ready | 39 / 17 |
| v2b | v1 plus `A_accel` | 2, code not written | 41 / 19 |
| v2c | v2a plus `A_accel` | 2, code not written | 40 / 18 |

Each variant is fitted with logistic and histogram boosting on its combined and its satellite-only feature set, exactly as in v1.

**`A_accel` definition (frozen).** For each compound and quarter q: first smooth the activity score with a **causal trailing median** `A_s(q) = median(A(q), A(q-1), A(q-2))` (needs all three quarters, otherwise missing; a centered window is not allowed because it uses future values). Then `A_accel(q) = (A_s(q) - A_s(q-4)) - (A_s(q-4) - A_s(q-8))`, the year-over-year second difference, which removes the Dynamic World seasonal pattern. It uses only quarters up to q, is computed from the full published A history in `kpi_values` (so it is defined for dataset rows from 2023Q1, because A exists from 2019Q1), and a missing quarter gives a missing value, never zero. Origin mark: derived from real observations (blue); the labels stay generated (orange). The helper `a_acceleration` in `src/analysis/ew_features.py` implements the second difference; the trailing median and the dataset build are Stage 2 work.

## Stages and what must exist before each fit

- **Stage 1 (v2a), runnable with the committed code.** Set `candidates.variant: v2` and `candidates.no_height_ablation: true` in `configs/data.yaml`, then run the evaluation. The run refuses to start unless `EW_PROTOCOL_V2.md` still matches `EW_PROTOCOL_V2.sha256`.
- **Stage 2 (v2b, v2c) is not implemented.** Before any Stage 2 fit, a separate commit must (1) add the trailing median and `A_accel` to the dataset build with fabricated-frame tests, (2) make the feature-count check per variant (40, 39, 41, 40), and (3) add the rolling-origin evaluation below. If implementing it shows that a definition in this file must change, freeze a new version (`EW_PROTOCOL_V2_1`) with its own hash instead of editing this file.

## Evaluation plan

1. **Fixed split (as v1).** Train through 2024Q4; embargo 2025Q1; time test 2025Q2 through 2026Q1; secondary developer holdout with the same rules as v1. Report every variant side by side with the v1 rows, with the same denominators.
2. **Rolling origin (Stage 2).** Expanding training window, one embargo quarter, a two-quarter test block. Origins (last training quarter): 2024Q2, 2024Q3, 2024Q4, 2025Q1, 2025Q2, giving test blocks 2024Q4-2025Q1, 2025Q1-Q2, 2025Q2-Q3, 2025Q3-Q4 and 2025Q4-2026Q1. A fold is **skipped and recorded with its reason** when its training part lacks one of the two classes or its test block has no distressed row; folds are never reshuffled or redefined after seeing outcomes. Report per fold and pooled: pooled recall@4 is total hits over total distressed rows in valid folds; pooled macro-F1 is computed on the concatenated predictions of valid folds. Fold test blocks overlap, so they are not independent; the pooled number is a diagnostic, not a confidence interval.
3. **Reading rule.** At the fixed test, one distressed row moves recall@4 by 0.25 (4 rows). Differences of one row are noise and are reported as such.

## Decision rule (written before any v2 fit)

v1 stays the primary Track B variant. A v2 variant replaces it as primary only if **both** hold on the pooled rolling-origin evaluation (Stage 2) with at least three valid folds and at least 8 distressed test rows pooled: (a) pooled macro-F1 is at least 0.05 higher than v1's for the same model family and feature set, and (b) pooled distressed recall@4 hits are not lower than v1's. A v2a-only result (Stage 1, single fixed split of 4 distressed rows) can never change the primary variant; it is reported as an ablation. If the conditions are not met, v2 results are published as a secondary analysis and v1 remains primary. Whatever the outcome, both are reported with denominators, and the wording stays "diagnostic on generated data".

## Implementation acceptance for a v2 run

Both binary classes in the primary train and test; correct censoring and time split; training-only preprocessing; feature/target separation; normalized probabilities; row keys; protocol hash equal to the recorded hash; source hashes; repeat-fit equality; output files only under the v2 names above. Real cases stay a separate rule check and are never model training or tuning labels.

## Not promised

No recall, F1 or accuracy figure is promised or implied. Independent real validation and calibration are still required before any deployment claim.
