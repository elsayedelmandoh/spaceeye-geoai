# Current Track B model card

Synthetic - for training only. This card describes four fitted diagnostics, not a validated three-class operational model. Exact results: [current report](../data/EW_REPORT_CURRENT.md), [metrics](../data/CURRENT_MODEL_METRICS.csv), [metadata](../data/CURRENT_MODEL_METADATA.json).

Data: 12 coded R7 compounds, 180 compound-quarter rows, 40 declared features. Fit 96 rows through 2024Q4; embargo 2025Q1; evaluate 48 rows from 2025Q2 through 2026Q1. Censored/already-completed rows are excluded. Public/derived and generated fields have metadata origins. Keys, future labels and hidden state are excluded from X; median imputation/scaling is fitted on training data only.

Target: distressed / newly fully completed / ongoing in the next six months; distress takes precedence. Training has 89 ongoing, 7 distressed and **zero completed**. Test has 43 ongoing, 4 distressed and 1 completed. Four diagnostics fit the two observed classes: logistic and histogram boosting, each on satellite context and combined features. Completion probability is null; the other two probabilities are conditional on those observed classes. They are not a complete three-way probability distribution.

Parameters, candidate universe, capacity 4, 2,000 random draws and metrics were fixed in [the current protocol](../data/EW_PROTOCOL_CURRENT.md) before these fits. Historical results and class distributions were already known; this is not a blind study. No test-driven tuning or synthetic completion insertion was performed. Per-class recall and macro-F1 include the declared completed class; a missed completed test example counts as a miss.

Generated labels and repeated quarters are not independent real distress events. Results may reflect generator structure and do not establish real accuracy, causality or fairness. A perfect score does not justify adding noise after viewing the test; investigate and register a new experiment if necessary. The six real public cases are a separate rule check set, never model training rows.

Three-class acceptance is not met. Before deployment, obtain supportable completion examples and independent real validation, register an evaluation with all classes represented, and review calibration, errors and subgroup coverage. The rule remains the operational cycle selector; fitted scores do not silently replace it. Saved models remain outside public Git; only approved predictions, aggregates and metadata are shared.
