# real/sat_yearly.parquet

Actual schema;132rows. Public/derived table; register origins remain explicit.

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| code | str | registered compound codes plus a planted unknown code | key | Coded compound identifier; accepted prepared tables use registered R7 codes. Planted unknown codes occur only in raw/quarantined test inputs. |
| year | int64 | see meaning | key | year; see current dataset contract and producing source module. |
| veg_share | float64 | see meaning | derived | veg share; see current dataset contract and producing source module. |
| n_built_cells | float64 | see meaning | real | n built cells; see current dataset contract and producing source module. |
| height_mean_m | float64 | see meaning | real/derived | height mean m; see current dataset contract and producing source module. |
| height_p90_m | float64 | see meaning | real/derived | height p90 m; see current dataset contract and producing source module. |
| share_built_ge20m | float64 | see meaning | real/derived | share built ge20m; see current dataset contract and producing source module. |
| height_origin | str | see meaning | key | height origin; see current dataset contract and producing source module. |
| veg_origin | str | see meaning | key | veg origin; see current dataset contract and producing source module. |
