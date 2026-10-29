# Current Track A real-case check

Six R7 public check cases; no generated financial labels are used here. The saved activity backtest excludes overlapping training plots.

Download [cases.csv](../releases/ready-data/backtest/cases.csv) and [saved summary.json](../releases/ready-data/backtest/summary.json). The [prepared inputs and replay instructions](../releases/ready-data/backtest/README.md) let a fresh checkout reproduce the six-case counts with `python -m src.pipeline.rerun_backtest`, without the producer's external data drive. This replays prepared inputs; it does not refit activity or repeat raw-source clock checks.

After-start reading: 1 of 6. Point-in-time reading: 0 of 6. Original criterion remains 5 cases; it is not reduced to obtain a pass.

| Case / code | Assessable pre-cutoff quarters | After-start alert quarters | Numeric alternative check |
| --- | ---: | ---: | --- |
| E1 / C14 | 22 | 0 | Rejected: 22 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E4 / C12 | 14 | 0 | Rejected: 14 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E5 / C21 | 18 | 6 | Rejected: 18 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E6 / C10 | 18 | 0 | Rejected: 18 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E7 / C19 | 18 | 0 | Rejected: 18 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E8 / C02 | 15 | 0 | Rejected: 15 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |

The full CSV contains what happened, the rule explanation, the competing explanation and next action. Warning detection is not causal proof. No percentages or retuned thresholds are used.
