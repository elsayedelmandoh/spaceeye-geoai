# real/drivers_monthly.parquet

Actual schema;45rows. Public/derived table; register origins remain explicit.

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| month | str | YYYY-MM, 2023-01..2026-09 | key | calendar month; the row is the state at the end of that month; grid |
| usd_egp | float64 | EGP | real | usd egp; see current dataset contract and producing source module. |
| policy_rate_pct | float64 | percent | real | policy rate pct; see current dataset contract and producing source module. |
| rebar_egp_t | int64 | see meaning | real | rebar egp t; see current dataset contract and producing source module. |
| cement_egp_t | int64 | see meaning | real | cement egp t; see current dataset contract and producing source module. |
| materials_index | float64 | see meaning | derived | materials index; see current dataset contract and producing source module. |
| shock_month | bool | see meaning | derived | shock month; see current dataset contract and producing source module. |
| tmax_mean_c | float64 | see meaning | real | tmax mean c; see current dataset contract and producing source module. |
| days_tmax_ge40 | int64 | see meaning | real | days tmax ge40; see current dataset contract and producing source module. |
| ramadan_days | int64 | see meaning | derived | ramadan days; see current dataset contract and producing source module. |
| eid_days | int64 | see meaning | derived | eid days; see current dataset contract and producing source module. |
