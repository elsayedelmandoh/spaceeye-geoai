# Update 01: what was done with the teammate's observations

Sources: `logs/debate-01.md`, `logs/debate-02.md`. Everything below was checked against the repo files before it was applied.

| Teammate observation | Checked result | What was done |
|---|---|---|
| Only 96 train / 48 test rows | True (7 and 4 distressed). Already stated in spec section 3. | Added an "Only 96 training rows?" expected question (section 12) and a small-sample risk row (section 13). Real independent events need ACUD data. |
| Boosting recall 0.0 vs rule 75% | Mixes class recall with recall@4; at recall@4 `boosting_satellite` is 4/4. One row = 0.25 at n=4. | Metric clarification and side-by-side satellite (18) / combined (40) reporting added to section 3 item 5. No hyperparameter was changed. |
| Finance features hurt ranking | Boosting recall@4 falls 4/4 to 1/4, logistic rises 1/4 to 2/4 and macro-F1 0.553 to 0.615: noise at n=4. | Features kept; both variants reported. Switching the primary variant now needs the v2 decision rule. |
| No short-window velocity | Track A has 8- and 12-quarter slopes; K2 reacts in one quarter; Track B has 6-month `d_A`, `d_K2`. Acceleration is missing. | Candidate `A_accel` (causal year-over-year second difference) frozen in `EW_PROTOCOL_V2.md`; helper `a_acceleration` with tests; not wired into the dataset yet. |
| Heights stop at 2023 | True, and `height_mean_m` is a model feature (stale for 2025-26, 2 of 12 missing). | Documented in the spec; `candidates.no_height_ablation` switch (off by default); variant v2a. |
| 5-day / monthly Sentinel-2 series, rolling median | Out of scope; about 25 plots; data not in the repo; centered median would leak. | Kept out of model input. Causal trailing median defined as part of `A_accel`; the series needs source, plot-to-code mapping and labels first. |
| >80% recall | Withdrawn by the teammate. | No recall figure is promised anywhere. |

Rule change (owner's decision): Track A thresholds stay frozen; Track B changes are allowed under a protocol written and hashed before fitting, with v1 results kept. Enforced in code: a v2 run refuses to start if `data/EW_PROTOCOL_V2.md` differs from `EW_PROTOCOL_V2.sha256` (`0d3348d7...203b`).

Not done: no retraining (F: data not mounted here); Stage 2 code (trailing median in the dataset build, `A_accel` column, rolling-origin evaluation, per-variant feature-count check) is not written.

Commands to run on the machine with F: (WSL: `sudo mkdir -p /mnt/f && sudo mount -t drvfs F: /mnt/f`):
1. `git pull` on `feat/ml`, then `sha256sum -c data/EW_PROTOCOL_V2.sha256` (run it inside `data/`).
2. `uv run --locked --offline python -m src.pipeline.team_run` to confirm v1 still reproduces.
3. Stage 1 only: set `candidates.variant: v2` and `candidates.no_height_ablation: true` in `configs/data.yaml`, then `uv run --locked --offline python -c "from src.analysis.current_evaluation import run; run()"`. Outputs: `data/V2_MODEL_METADATA.json`, `data/V2_MODEL_METRICS.csv`, `data/EW_REPORT_V2.md`.
Not verified: that command, the v1 reproduction on your data, and the v2 run itself.
