# Current binary distress evaluation protocol

Scope revised by the team lead on 28 October 2026 and frozen before binary refitting. Previous distributions and v4 diagnostics were already inspected; this is not a blind independent experiment. Synthetic - for training only.

## Target and data

Predict distressed / not_distressed during the next six calendar months, excluding the cutoff month. Use the existing boolean future-distress target and its equivalent categorical y_outcome_6m. No completed class, completion probability or three-class acceptance requirement remains. Handover without future distress maps to not_distressed; that label does not assert continuing construction or physical completion.

Retain 180 compound-quarter rows and exactly 40 declared features. Exclude keys, targets, censoring and already-handed-over status from X. Censored targets stay null; exclude censored/already-handed-over cutoffs from fitting/evaluation. Preserve public handover facts and rule caps independently of the model target.

## Split and methods

Train through 2024Q4; embargo 2025Q1; time test 2025Q2 through 2026Q1. Fit preprocessing on training data only. Predict all rows with split/exclusion flags. No oversampling, extra fictional compounds, shifted test rows or altered source observations.

Fit logistic and histogram boosting on all 40 features and on the metadata-declared public/derived subset. Logistic: median imputer preserving empty features, standard scaler, C=0.3, balanced weights, max_iter=2000, seed 2026. Boosting: median imputer, depth 2, 60 iterations, learning rate 0.05, min_samples_leaf 6, l2=1, balanced weights, seed 2026. No search or test-driven noise changes.

Primary validation is fixed-time. Secondary developer holdout: three developers selected by seed 2026 without reading outcomes; same chronology; fit only when three test developers and both training classes remain. Otherwise record the reason, without reshuffling based on outcomes.

Compare public rule, combined rule and 2,000 random draws at capacity 4. Evaluation candidates are K4-assessable compounds; this differs from the operational levels-1-to-3 list. Model ties use code; rule ties use level, descending K2/K3, code. Preserve rule completion cap and unassessable state.

## Metrics and acceptance

Class order: distressed, not_distressed. Publish finite p_distressed and p_not_distressed in [0,1], summing to 1. Report supports, per-class recall, two-class macro-F1, confusion counts and distressed recall@4 as n of m. Include random mean and percentile interval; identify secondary-view metrics separately.

Implementation acceptance: both binary classes represented in primary train/test, correct censoring/time split, training-only preprocessing, feature/target separation, normalized probabilities, row keys, protocol/source hashes and repeat-fit equality. Performance limitations do not justify changing data to obtain a desired score. No operational accuracy or superiority threshold is promised by implementation completion.

Real cases remain a separate rule check, never model training/tuning labels. Repeated synthetic quarters are not independent real events. Independent real validation/calibration is required before predictive deployment claims.
