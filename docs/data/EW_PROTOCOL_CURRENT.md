# Current evaluation protocol

Frozen before the current model run, 28 October 2026. Previous data distributions and historical binary results have already been inspected; this is not a blind independent experiment. Synthetic - for training only.

## Data and split

Use the existing 180-row, 40-feature expanded table and its declared feature list, unchanged. One row is compound x quarter. Exclude keys, both targets, censoring and already-completed status from X. Exclude censored/already-completed rows from fitting and labelled evaluation. Training <=2024Q4; embargo 2025Q1; time test 2025Q2–2026Q1. Predict all 180 rows for inspection, marking split and censoring. Fit imputation/scaling only on training data; no synthetic oversampling or extra completion events.

Target: next six calendar months, distress precedence, new full handover for completed. Class order: distressed, completed, ongoing. Current training lacks completed; publish `p_completed=null`, observed-class probabilities with an explicit conditional-probability flag and unsupported-class metadata. Never present null as zero risk or claim a validated three-class model. A true three-class release requires independently supportable training examples for each class and a newly registered evaluation.

## Methods and parameters

Four fitted diagnostics: logistic and histogram gradient boosting, each with all 40 features and the metadata-declared public/derived satellite-context subset. Include K5/K6 and current level in the combined table; never use generated monetary fine as a satellite feature. Logistic: median imputer (preserve empty features), standard scaler, C=0.3, balanced weights, max_iter=2000, seed 2026. Boosting: median imputer, depth=2, iterations=60, learning_rate=0.05, min_samples_leaf=6, l2=1, balanced weights, seed 2026. No parameter search or added noise based on scores. Perfect synthetic scores trigger a limitation note, not test-driven data changes.

Compare the public priority rule, public+B1/B2/B3/B5 rule (B4 context only), and random ranking. Keep K4 assessability and the may-be-complete cap; financial triggers do not invent a level for unassessable observations. Rule ranking: level, descending K2, descending K3, code. Models rank by distressed score, then code. For the evaluation comparison every K4-assessable compound is a candidate and capacity is 4; this is an evaluation ranking, not the operational list restricted to levels 1–3. Report operational lists separately. Random: 2,000 draws, seed 2026, same candidates and capacity per quarter.

## Metrics and interpretation

Report class support, per-class recall (null with no test support), macro-F1 over the three declared classes, confusion counts and distressed recall@4 as n of m. Also report binary distressed-vs-rest recall@4 for every ranking, seeded random mean and 2.5/97.5-percentile interval. A completed test case missed by a model lacking that training class counts as a miss; the missing probability remains null.

No developer holdout if it would leave fewer than three distinct test developers with nonempty multi-class training support. Record any skipped split and reason rather than choosing developers based on outcomes. Do not reuse real-case check labels to train or tune the synthetic-data models. Real cases get a separate frozen-clock rule check only; public cases do not provide matched real financial features.

## Acceptance

Implementation acceptance: reproducible seeded fits, feature/target separation, correct time split, training-only preprocessing, current-input hashes, explicit missing-class outputs and matching row keys. Scientific three-class acceptance additionally requires every declared class in training and test; it currently fails. Descriptive evidence above random is the observed recall@4 exceeding random's mean; strong evidence would require exceeding its upper interval and independent real validation. Neither condition alone authorizes deployment. Freeze parameters irrespective of the observed result.
