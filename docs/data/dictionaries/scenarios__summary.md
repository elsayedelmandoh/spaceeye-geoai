# scenarios/summary.csv

Actual schema;36rows. Synthetic - for training only

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| scenario_id | str | see meaning | generated/derived from generated | Named hypothetical intervention; baseline stays separate. |
| code | str | registered compound codes plus a planted unknown code | key | compound code; from the compound; defect 4 replaces it in the configured number of rows |
| initial_progress_pct | float64 | percent | generated/derived from generated | Latest supervisor progress report available by cutoff; explicit assumed zero if none exists. |
| final_progress_pct | float64 | percent | generated/derived from generated | Last simulated progress in the forward horizon, not forecast handover/completion. |
| gross_collections_egp | float64 | EGP | generated/derived from generated | Baseline future collections times intervention multiplier; sum over horizon in summary. |
| construction_spend_egp | float64 | EGP | generated/derived from generated | Actual affordable spending after obligations; sum over horizon in summary. |
| final_cash_egp | float64 | EGP | generated/derived from generated | Closing operating cash at last simulated month. |
| final_debt_egp | float64 | EGP | generated/derived from generated | Closing assumed bank debt at last simulated month. |
| final_obligation_arrears_egp | float64 | EGP | generated/derived from generated | Unpaid simulated obligations at last month. |
| progress_difference_vs_baseline_pp | float64 | see meaning | generated/derived from generated | Final simulated percentage-point difference from same compound's baseline. |
| synthetic_label | str | see meaning | generated/derived from generated | Synthetic - for training only; retained on generated products. |
