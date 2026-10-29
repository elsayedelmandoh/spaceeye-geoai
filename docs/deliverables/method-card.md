# Binary distress model card

Synthetic - for training only. Approved target: distressed / not_distressed in the next six months. Completion prediction has been removed by the team lead. See [scope decision](../../data/BINARY_SCOPE_DECISION.md), [protocol](../../data/EW_PROTOCOL_CURRENT.md), [current report](../../data/EW_REPORT_CURRENT.md), [metrics](../../data/CURRENT_MODEL_METRICS.csv) and [metadata](../../data/CURRENT_MODEL_METADATA.json).

Data: 12 R7 compounds, 180 compound-quarter rows, 40 declared features. Primary training: 96 rows through 2024Q4, with 7 distressed and 89 not_distressed. Embargo: 2025Q1. Test: 48 rows from 2025Q2 through 2026Q1, with 4 distressed and 44 not_distressed. Censored and already-handed-over cutoffs are excluded from fitting/labelled evaluation. The latter is cohort information, not a predicted completion class.

Logistic and histogram boosting are fitted on public/derived context and on combined features. Imputation/scaling is fitted only on training data. Keys, labels and hidden state are excluded from X. Boolean/categorical distress targets are equivalent. Both output probabilities are finite and sum to one. Not_distressed does not mean completed, continuously active or guaranteed financially healthy.

The primary split, fixed model parameters, capacity 4 and 2,000 random draws remain registered before this binary refit. Previous distributions/results were already inspected; this is not a blind experiment. A separate fixed-seed chronological developer holdout selects three developers without outcome-driven reselection; status, supports and secondary-view metrics are recorded in metadata.

Implementation acceptance covers supported binary classes, chronology, preprocessing, probability normalization, keys, metrics and reproducibility. It does not imply operational accuracy. Generated repeated-quarter labels are not independent real events. Real public cases remain a separate rule check set and are not used to fit/tune the models. Preserve unsuccessful performance results; do not change data/noise after seeing the test.

The producing revision is pinned by the binary-scope tag and package provenance. Local checkpoints remain outside public Git. Independent real validation, calibration and appropriate access review are required before predictive deployment claims. Operational cycle selection continues to use the rule.
