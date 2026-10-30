# Current early-warning evaluation

Synthetic - for training only. See [frozen protocol](EW_PROTOCOL_V2.md).

Training: 96 rows. Time test: 48 rows. Capacity: 4. Target: distressed / not_distressed.

**Binary implementation acceptance: PASS** (implementation checks only: both classes are represented and the two probabilities sum to one; it says nothing about predictive power). Completion prediction is outside the approved scope.

Statistical power is very low: the time test holds 4 distressed rows, and rows of a compound that is already distressed count as well (persistence, not only new onsets).

| Method | Distressed cases selected | Recall@4 |
| --- | --- | --- |
| public_rule | 3 of 4 | 0.750 |
| combined_rule | 3 of 4 | 0.750 |
| logistic_satellite | 1 of 4 | 0.250 |
| logistic_combined | 2 of 4 | 0.500 |
| boosting_satellite | 1 of 4 | 0.250 |
| boosting_combined | 1 of 4 | 0.250 |

Random: 2,000 draws, mean 0.335, 95% interval [0.000, 0.750].

Class support, per-class recall and macro-F1: [metrics](V2_MODEL_METRICS.csv). Exact split, feature sets and confusion counts: [metadata](V2_MODEL_METADATA.json).

Secondary developer holdout: FITTED_UNINFORMATIVE (its test rows hold no distressed case, so recall is undefined and the view is uninformative); see metadata and the metrics view column.

This is the current binary scope; historical N=8 and v4 three-class-scope results remain separate. Scores do not establish real-world predictive accuracy or fairness.
