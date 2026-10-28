# hypothetical_priorities

Synthetic - for training only

648rows. See COMPONENT_DATA_PROTOCOL.md for definitions and limits.

| Column | Type | Meaning |
| --- | --- | --- |
| code | str | Compound code,key only,not text model input. |
| cutoff | str | Last observed month,held fixed for all forward paths. |
| month | str | Forward simulated month. |
| scenario_id | str | Intervention ID:baseline,collections_drop,usd_cost_shock. |
| frozen_public_level | object | Public priority at cutoff,not future observed priority. |
| K2_frozen | float64 | Cutoff inactivity count,held fixed. |
| K3_frozen | int64 | Cutoff delivery clock,held fixed. |
| frozen_B1 | bool | Cutoff financial guarantee below required amount,held fixed;operating cash is never used as the guarantee. |
| frozen_B2 | bool | Cutoff recorded land arrears>=2months,held fixed. |
| frozen_B3 | bool | Cutoff complaint-history percentile>=95%with12valid prior months,held fixed. |
| B3_assessable | bool | Whether sufficient valid complaint-rate history exists at cutoff. |
| projected_plan_pct | float64 | Cutoff contractual plan plus declared monthly capacity times elapsed months,capped100. |
| simulated_progress_pct | float64 | Forward-engine simulated progress,not satellite completion measurement. |
| projected_gap_pp | float64 | Projected plan minus simulated progress,in percentage points. |
| projected_B5 | bool | Projected gap>20pp,using existing B5threshold. |
| hypothetical_level | object | Frozen public/financial rules plus projected B5;completion cap retained,not validated accuracy. |
| origin | str | Generated/derived provenance,not actual observations. |
| synthetic_label | str | Synthetic - for training only |
| eligible_rank | Int64 | Rank among hypothetical levels1–3,ordered by level,K2,K3,code. |
| selected | boolean | Rank is within capacity4. |
| baseline_hypothetical_level | object | Same-month baseline level for this compound. |
| baseline_eligible_rank | Int64 | Same-month baseline eligible rank. |
| baseline_selected | boolean | Whether this compound is selected in the same-month baseline. |
| selection_changed | boolean | Selection differs from same-month baseline. |
| level_changed | bool | Level differs from same-month baseline. |
