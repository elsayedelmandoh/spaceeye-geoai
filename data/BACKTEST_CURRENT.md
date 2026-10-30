# Current Track A real-case check

Six R7 public check cases; no generated financial labels are used here. The saved activity backtest excludes overlapping training plots.

After-start reading: 1 of 6. Point-in-time reading: 0 of 6. Original criterion remains 5 cases; it is not reduced to obtain a pass.

| Case / code | This case | Assessable pre-cutoff quarters | After-start alert quarters | Numeric alternative check |
| --- | --- | ---: | ---: | --- |
| E1 / C14 | assessable 2022Q1-2024Q2; level at freeze 4; first level 1-2 alert none | 10 | 0 | Rejected: 10 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E4 / C12 | assessable 2020Q2-2022Q2; level at freeze 4; first level 1-2 alert none | 9 | 0 | Rejected: 9 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E5 / C21 | assessable 2020Q3-2023Q2; level at freeze 4; first level 1-2 alert 2020Q3 | 12 | 6 | Rejected: 12 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E6 / C10 | assessable 2022Q1-2023Q2; level at freeze 4; first level 1-2 alert none | 6 | 0 | Rejected: 6 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E7 / C19 | assessable 2021Q1-2023Q2; level at freeze 4; first level 1-2 alert none | 10 | 0 | Rejected: 10 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |
| E8 / C02 | assessable 2022Q1-2022Q3; level at freeze 4; first level 1-2 alert none | 3 | 0 | Rejected: 3 assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters. |

The full CSV contains what happened, the rule explanation, the competing explanation and next action. Warning detection is not causal proof. No percentages or retuned thresholds are used.

Published [cases.csv](../releases/ready-data/backtest/cases.csv), [saved summary.json](../releases/ready-data/backtest/summary.json), and [prepared-input replay instructions](../releases/ready-data/backtest/README.md). Run `python -m src.pipeline.rerun_backtest` from a checkout without the external source drive. This replays saved prepared inputs; it does not refit activity or repeat raw-source clock checks.
