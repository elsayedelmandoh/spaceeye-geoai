# Current Track A real-case check

Six R7 public check cases; no generated financial labels are used here. The saved activity backtest excludes overlapping training plots.

After-start reading: 1 of 6. Point-in-time reading: 0 of 6. Original criterion remains 5 cases; it is not reduced to obtain a pass.

| Case / code | Assessable pre-cutoff quarters | After-start alert quarters | Numeric alternative check |
| --- | ---: | ---: | --- |
| E1 / C14 | 10 | 0 | Rejected: 10 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E4 / C12 | 9 | 0 | Rejected: 9 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E5 / C21 | 12 | 6 | Rejected: 12 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E6 / C10 | 6 | 0 | Rejected: 6 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E7 / C19 | 10 | 0 | Rejected: 10 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E8 / C02 | 3 | 0 | Rejected: 3 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |

The full CSV contains what happened, the rule explanation, the competing explanation and next action. Warning detection is not causal proof. No percentages or retuned thresholds are used.

Published [cases.csv](../releases/ready-data/backtest/cases.csv), [saved summary.json](../releases/ready-data/backtest/summary.json), and [prepared-input replay instructions](../releases/ready-data/backtest/README.md). Run `python -m src.pipeline.rerun_backtest` from a checkout without the external source drive. This replays saved prepared inputs; it does not refit activity or repeat raw-source clock checks.
