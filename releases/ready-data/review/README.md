# Saved review evidence

These seven small files supplement the unchanged v5 data package:

| File | Purpose |
| --- | --- |
| `real/quality_checks_log.parquet` | 11 gate records with values, actions and run lineage |
| `real/run_log.parquet` | 14 saved Track A execution steps |
| `data_completion/audit.json` | Current 180-row, 40-feature dataset checks and split counts |
| `sim_clean/quality_report.json` | Cleaning counts, quarantines and validation limits |
| `model/activity_meta.json` | Operational activity recipe and diagnostics; no fitted weights |
| `model/activity_meta_backtest.json` | Backtest recipe with eight overlapping plots excluded; no fitted weights |
| `ml_current/random_draws.csv` | All 2,000 saved random-baseline draws |

`manifest.json` verifies the distributed bytes; original source hashes are recorded separately and text files use portable LF newlines. These are saved outputs from the documented runs, not checks executed on the reviewer's device. Their historical computation dates and source implementation tag remain visible. Current path/configuration changes do not retroactively certify these snapshots.

Run `python -m src.pipeline.setup_review` from a checkout to verify v5 and these files, and install prepared review data. Existing different local files are preserved: choose a fresh `SPACEEYE_DATA_ROOT` if needed. Full instructions: [review setup](../../../docs/REVIEW_SETUP.md).

Original source data, name maps, hidden synthetic truth, quarantines and fitted checkpoints are excluded. `quality_checks.csv` repeats the same gate records without lineage, so the richer gate log is supplied once. The old mixed-scope `release_audit.json` is not presented as current model validation.
