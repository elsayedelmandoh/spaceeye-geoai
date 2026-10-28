# Current early-warning evaluation

Synthetic - for training only. See [frozen protocol](EW_PROTOCOL_CURRENT.md).

Training: 96 rows. Time test: 48 rows. Capacity: 4. Target: distressed / not_distressed.

**Binary implementation acceptance: PASS.** Both classes are represented; the two probabilities sum to one. Completion prediction is outside the approved scope.

| Method | Distressed cases selected | Recall@4 |
| --- | --- | --- |
| public_rule | 3 of 4 | 0.750 |
| combined_rule | 3 of 4 | 0.750 |
| logistic_satellite | 1 of 4 | 0.250 |
| logistic_combined | 2 of 4 | 0.500 |
| boosting_satellite | 4 of 4 | 1.000 |
| boosting_combined | 1 of 4 | 0.250 |

Random: 2,000 draws, mean 0.335, 95% interval [0.000, 0.750].

Class support, per-class recall and macro-F1: [metrics](CURRENT_MODEL_METRICS.csv). Exact split, feature sets and confusion counts: [metadata](CURRENT_MODEL_METADATA.json).

Secondary developer holdout: FITTED; see metadata and the metrics view column.

This is the current binary scope; historical N=8 and v4 three-class-scope results remain separate. Scores do not establish real-world predictive accuracy or fairness.
