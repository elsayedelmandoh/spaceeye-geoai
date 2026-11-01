# Current S1/S2/S3 handoff

Task EL-11. Synthetic - for training only. Rebuild with `python -m src.pipeline.team_run`; source implementation: `src/pipeline/partial_exports.py`.

| What-if case | Declared change | Export |
| --- | --- | --- |
| S1 | +30% cost on the imported cost component (FX-cost proxy) | S1/kpi_values.parquet; monthly who_moved_and_why.csv |
| S2 | Collections -25% for six months | S2/kpi_values.parquet; monthly who_moved_and_why.csv |
| S3 | Capacity 2 and 6 versus baseline 4, selection only | S3/kpi_values.parquet; who_moved_and_why.csv |

Files live under configured `app_data/partial_task_exports` and are distributed in the v7 bundle. S1/S2 take the last simulated month in each quarter, retain the base KPI column names and carry explicit `frozen_context_quarter`. Public activity/start/height/fine context is frozen at the source cutoff. Only simulated progress, projected B5, hypothetical level and selection change. Existing public source dates and `source_run_id` remain traceable; a separate what-if run ID identifies the derived output. These are hypothetical KPI-shaped records, not new observed future quarters.

S1/S2 levels are Track B hypothetical levels. Compare them with `baseline_hypothetical_level`, not with `kpi_values` (Track A levels): the two differ in 33 of the 72 code-quarter rows of each of S1 and S2 (a missing level counted as its own value; 30 of the 66 rows with a level on both sides).

S3 keeps original source quarters and levels; `scenario_id` distinguishes the two capacity variants. It never changes cash, progress or fine exposure. `who_moved_and_why` reports baseline selection/rank, current selection/rank and trigger context, including unchanged rows; it must not imply that every shock changes a ranking. Financial constraints sometimes produce identical selections.

No handover date, new satellite signal, new complaint feed or future assessed fine is forecast. Raw/base tables are not overwritten. The what-if screen is a separate dashboard task.
