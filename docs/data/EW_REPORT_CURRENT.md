# Current early-warning evaluation

Synthetic - for training only. See [frozen protocol](EW_PROTOCOL_CURRENT.md).

Training: 96 rows. Time test: 48 rows. Capacity: 4. Unsupported training classes: completed.

**Three-class acceptance: NOT MET.** Missing-class probabilities remain null; fitted probabilities are conditional on the observed classes.

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

This updates the schema/capacity experiment; historical N=8 results remain separate. A completed test case can count as a miss even though its training class is absent. Scores do not establish real-world predictive accuracy or fairness.
