# Fine rate change protocol (frozen before the 0.5% fit)

Synthetic - for training only.

**Change.** The illustrative monthly fine rate `fines.fine_rate_month` goes from 0.01 (1%) to 0.005 (0.5%) of the assumed land value, by owner decision on 2026-11-03. Nothing else changes: same seed, features, hyperparameters, noise, splits and frozen model protocol `EW_PROTOCOL_CURRENT.md`.

**What the rate reaches.** `K5_egp` and its two relief scenarios in `sim_clean/fin_quarterly` and the training tables, and `fine_rate_month` in `sim_clean/fine_assumptions`. `K5_egp` is one of the Track B classifier features.

**Expectation, written before fitting.** Halving one feature for every row is a monotone rescale. The logistic model standardises it and the boosting model bins it by quantiles, so predictions and metrics should not change.

**Check.**
1. Rerun `src.pipeline.team_run` at 1% on a copy of the data root. It must reproduce the stored v7 outputs.
2. Rerun at 0.5%.
3. Compare `ml_current` predictions row by row (largest absolute difference in `p_distressed`) and every value in the metrics file.

**Decision rule.**
- **Identical:** if the largest difference is at most 1e-9 and every metric is equal, rebuild the v7 ZIP in place with the 0.5% data and update the docs that state the rate.
- **Anything else:** stop, report the difference, and keep v7 at 1%.

Track A is not touched.
