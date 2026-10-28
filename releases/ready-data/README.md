# Ready data: start here

**[Download v5](SpaceEye_R7_READY_DATA_2026-10-28_v5.zip?raw=1)** and [read the data guide](DATA_GUIDE.md).

Current scope: 12 coded R7 compounds, capacity 4, 180 training rows and 40 features. Version 5 adopts the team lead's binary prediction scope: distressed / not_distressed in the next six months. Completion prediction is removed; source handover facts remain context.

1. Extract the complete ZIP.
2. Open its README.md. Use csv/ for spreadsheets, tables/ for Parquet, or spaceeye_ready.duckdb for SQL.
3. Run verify_package.py to verify every packaged file against its manifest.

The package includes 23 ready tables, boundaries, the separate training export, Arabic committee lists, complaint corpora, inspection contexts, synthetic visits, financial/priority exercises, current binary predictions/metrics and S1/S2/S3 handoff. Generated products retain Synthetic - for training only. None is actual fieldwork or validated operational forecasting.

`tables/current/ml_current.parquet` has four primary model methods; key: method/code/quarter. Its p_distressed and p_not_distressed sum to one. Secondary developer-holdout predictions are under current/ when that fixed split is supported; metric views are identified explicitly. No p_completed field is required.

Training ends 2024Q4; 2025Q1 is embargoed; time test is 2025Q2 through 2026Q1. Exclude censored/already-handed-over cutoffs from supervised work and use exactly the declared feature list. Not_distressed does not imply completion or guaranteed health.

[Scope decision](../../docs/data/BINARY_SCOPE_DECISION.md), [current report](../../docs/data/EW_REPORT_CURRENT.md), [remaining tasks](../../docs/REMAINING_TEAM_TASKS.md).

[ZIP SHA256](SpaceEye_R7_READY_DATA_2026-10-28_v5.zip.sha256.txt). Raw data, quarantines, private names/truth, credentials and model checkpoints are excluded. Earlier versioned ZIPs are historical snapshots; do not mix their targets/prediction schemas with v5.
