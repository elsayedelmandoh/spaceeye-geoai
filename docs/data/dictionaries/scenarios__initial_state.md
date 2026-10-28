# scenarios/initial_state.parquet

Actual schema;12rows. Synthetic - for training only

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| code | str | registered compound codes plus a planted unknown code | key | Coded compound identifier; accepted prepared tables use registered R7 codes. Planted unknown codes occur only in raw/quarantined test inputs. |
| cutoff | str | see meaning | generated/derived from generated | Last month whose observations may initialize the forward path. |
| initial_progress_pct | float64 | percent | generated/derived from generated | Latest supervisor progress report available by cutoff; explicit assumed zero if none exists. |
| progress_basis | str | see meaning | generated/derived from generated | Whether initial progress comes from a known report or assumed zero. |
| estimated_total_cost_egp | float64 | EGP | generated/derived from generated | Cutoff reported cost-to-complete divided by remaining reported fraction; estimate, not hidden true cost. |
| baseline_collections_egp | float64 | EGP | generated/derived from generated | Mean collections over configured past history, not future rows. |
| assumed_land_due_monthly_egp | float64 | EGP | generated/derived from generated | Past mean land obligation projected forward as an assumption. |
| capacity_pct_month | float64 | see meaning | generated/derived from generated | Declared monthly production capacity, estimated from past planned progress slope and clipped to configured bounds. |
| assumed_opening_cash_egp | float64 | EGP | generated/derived from generated | Past mean collections times assumed working-capital months. |
| assumed_opening_bank_debt_egp | float64 | EGP | generated/derived from generated | Zero opening bank debt assumed; not an observed company balance. |
| assumed_credit_limit_egp | float64 | EGP | generated/derived from generated | Past mean collections times configured assumed credit months. |
| synthetic_label | str | see meaning | generated/derived from generated | Synthetic - for training only; retained on generated products. |
