# scenarios/paths.parquet

Actual schema;648rows. Synthetic - for training only

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| scenario_id | str | see meaning | generated/derived from generated | Named hypothetical intervention; baseline stays separate. |
| code | str | registered compound codes plus a planted unknown code | key | compound code; from the compound; defect 4 replaces it in the configured number of rows |
| cutoff | str | see meaning | generated/derived from generated | Last month whose observations may initialize the forward path. |
| month | str | YYYY-MM, 2023-01..2026-09 | key | calendar month; the row is the state at the end of that month; grid |
| initial_progress_pct | float64 | percent | generated/derived from generated | Latest supervisor progress report available by cutoff; explicit assumed zero if none exists. |
| progress_before_pct | float64 | percent | generated/derived from generated | Simulated progress at the start of this forward month. |
| simulated_progress_pct | float64 | percent | generated/derived from generated | Prior simulated progress plus affordable spending divided by cost per percentage point; bounded0–100. |
| capacity_pct | float64 | percent | generated/derived from generated | Common productivity draw times capacity, limited by remaining work. |
| gross_collections_egp | float64 | EGP | generated/derived from generated | Baseline future collections times intervention multiplier; sum over horizon in summary. |
| collection_multiplier | float64 | see meaning | generated/derived from generated | 0.75for first6months of collections_drop; otherwise1. |
| cash_released_egp | float64 | EGP | generated/derived from generated | Declared released share of hypothetical collections; not financial guarantees. |
| restricted_cash_egp | float64 | EGP | generated/derived from generated | Cumulative collections not released to operating cash; tracked separately. |
| cost_multiplier | float64 | see meaning | generated/derived from generated | 1+0.40*0.30under FX cost shock; otherwise1. |
| desired_construction_spend_egp | float64 | EGP | generated/derived from generated | Capacity-limited desired progress times current cost per percentage point. |
| construction_spend_egp | float64 | EGP | generated/derived from generated | Actual affordable spending after obligations; sum over horizon in summary. |
| opening_cash_egp | float64 | EGP | generated/derived from generated | Operating cash carried into this simulated month. |
| closing_cash_egp | float64 | EGP | generated/derived from generated | Opening cash+released collections+credit draw-obligations paid-construction spending. |
| opening_debt_egp | float64 | EGP | generated/derived from generated | Bank debt carried into this simulated month. |
| credit_draw_egp | float64 | EGP | generated/derived from generated | Required borrowing limited by unused assumed credit. |
| closing_debt_egp | float64 | EGP | generated/derived from generated | Opening debt+new draw; repayments outside this model. |
| credit_limit_egp | float64 | EGP | generated/derived from generated | Finite assumed credit ceiling, fixed at cutoff. |
| opening_obligation_arrears_egp | float64 | EGP | generated/derived from generated | Unpaid obligations brought forward, not hidden observed arrears. |
| obligations_due_egp | float64 | EGP | generated/derived from generated | Prior arrears+land due+declared overhead+interest. |
| obligations_paid_egp | float64 | EGP | generated/derived from generated | Obligations actually covered before construction spending. |
| obligation_arrears_egp | float64 | EGP | generated/derived from generated | Due obligations minus paid obligations, carried forward. |
| cash_accounting_residual_egp | float64 | EGP | generated/derived from generated | Operating cash conservation residual; absolute value must not exceed1e-5EGP. |
| restricted_accounting_residual_egp | float64 | EGP | generated/derived from generated | Restricted cash conservation residual; absolute value must not exceed1e-5EGP. |
| synthetic_label | str | see meaning | generated/derived from generated | Synthetic - for training only; retained on generated products. |
