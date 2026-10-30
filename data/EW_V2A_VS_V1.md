# v2a against v1: side by side (EW_PROTOCOL_V2 Stage 1)

Synthetic - for training only. Run on 30 October 2026, at commit 75a581a plus the v6 rebuild.

Setup: protocol hash 0d3348d7… (matches `EW_PROTOCOL_V2.sha256`), `candidates.variant: v2`, `no_height_ablation: true`, then the config was restored to v1. The split is the same as v1: train through 2024Q4 (96 rows), test 2025Q2–2026Q1 (48 rows, 4 distressed). The only change is that `height_mean_m` is dropped from both feature lists.

| Method | v1 recall@4 | v2a recall@4 | v1 macro-F1 | v2a macro-F1 |
| --- | --- | --- | --- | --- |
| public_rule | 3 of 4 | 3 of 4 | — | — |
| combined_rule | 3 of 4 | 3 of 4 | — | — |
| logistic_satellite | 1 of 4 | 1 of 4 | 0.553 | 0.538 |
| logistic_combined | 2 of 4 | 2 of 4 | 0.615 | 0.591 |
| boosting_satellite | 4 of 4 | 1 of 4 | 0.478 | 0.429 |
| boosting_combined | 1 of 4 | 1 of 4 | 0.473 | 0.455 |

Random baseline at capacity 4: mean 0.335, 95 % interval [0.000, 0.750].

**Reading (per the protocol):** a Stage 1 result on one fixed split with 4 distressed rows **cannot change the primary variant**, so v1 stays primary and this is reported as an ablation.
- Dropping height lowers every macro-F1 slightly.
- It removes the only above-random hit count (boosting_satellite 4 of 4 → 1 of 4). That earlier 4 of 4 rested partly on the height column, and on 4 rows it is noise either way.
- The rules do not use height and are unchanged.

Stage 2 (v2b, v2c, rolling origin) is not implemented.

Files: `EW_REPORT_V2.md`, `V2_MODEL_METRICS.csv`, `V2_MODEL_METADATA.json`, and v1 in `EW_REPORT_CURRENT.md` / `CURRENT_MODEL_METRICS.csv`.
