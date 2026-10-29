# Track A backtest: files and replay

These small prepared files supplement the unchanged v5 ZIP. No private drive is needed for the case-count replay.

- `cases.csv`: the original six-case output named in T-AH-10.
- `summary.json`: saved full-run counts, activity-variant metadata and four clock checks.
- `kpi_inputs.csv`: 372 prepared quarter rows for 12 R7 codes, with only the eight columns needed by the case evaluator. These use the backtest activity variant that excluded eight overlapping plots. Do not substitute the operational KPI table from v5; it uses a different fitted activity variant.
- `events.csv`: four required columns from the six already-public, coded Track A evaluation cases. These are separate from private synthetic labels.
- `manifest.json`: input/output hashes, original source hashes and frozen configuration.

From the repository root, with Python 3.12+ and uv installed:

```sh
uv sync --locked
uv run --locked python -m src.pipeline.rerun_backtest
```

With an existing environment, use `python -m src.pipeline.rerun_backtest`.
Recomputed files appear in `artifacts/backtest/`: `cases.csv`, `summary.json` and `replay_audit.json`. Optional: `--output /path/to/results`.

Expected counts: after-start **1 of 6**, point-in-time **0 of 6**, literal **2 of 6**. The fixed minimum is five cases, so the success criterion is **not met**. A successful replay means the saved result was reproduced, not that the predictive criterion passed.

This command re-evaluates cases from saved prepared inputs and verifies every case and summary count. It does not refit activity or repeat the raw-source frozen-clock checks; the new summary deliberately omits those saved checks. For the full source-to-output run, obtain the external source caches, configure `configs/data.yaml`, then run `python -m src.pipeline.run_all`. The v5 ZIP alone does not include those caches. See [full-run evidence](../../../data/FULL_TRACK_A_REPRODUCIBILITY.json).

The expanded explanations already uploaded inside v5 are at `current/backtest/cases_explained.csv`; its summary is at `current/backtest/summary.json`.
