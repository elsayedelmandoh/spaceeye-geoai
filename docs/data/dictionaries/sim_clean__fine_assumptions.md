# sim_clean/fine_assumptions.parquet

Actual schema;12rows. Synthetic - for training only

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| code | str | registered compound codes plus a planted unknown code | key | compound code; from the compound; defect 4 replaces it in the configured number of rows |
| land_area_m2 | float64 | see meaning | generated/derived from generated | Compound land area; adjacent land_area_origin states real or generated. |
| land_area_origin | str | see meaning | generated/derived from generated | Origin of register land area; retain alongside generated financial assumptions. |
| allocation_date_assumed | datetime64[us] | calendar date | generated/derived from generated | Generated allocation6–18months before first public/observed anchor, bounded below by2016-01-01; retrospective calibration, excluded from X/public K6. |
| calibration_anchor_date | datetime64[us] | calendar date | generated/derived from generated | Earliest public publication or observed-start quarter used retrospectively to constrain synthetic allocation. |
| allocation_origin | str | see meaning | generated/derived from generated | Explicit generated/retrospective provenance, never an observed allocation record. |
| assumed_land_price_egp_m2 | float64 | EGP/m2 | generated/derived from generated | Generated vintage-based price;2500–5000pre2023,5000–12000otherwise. News supports context, not individual contract price. |
| assumed_land_value_egp | float64 | EGP | generated/derived from generated | Land area times generated price; in quarterly data replaced by value inferred from available installments when present. |
| fine_rate_month | float64 | see meaning | generated/derived from generated | Illustrative1%monthly fraction; explicit assumption, not a published universal contract rate. |
| assumption | bool | see meaning | generated/derived from generated | True: synthetic input or proposed operational capacity, not measured internal data. |
| assumption_available_from | datetime64[us] | see meaning | generated/derived from generated | Hypothetical contract availability date; allocation is retrospectively calibrated and not used as an ML feature. |
| price_context_source | str | see meaning | generated/derived from generated | Source IDs resolved in configs/synthetic_sources.json; context only. |
| rate_source | str | see meaning | generated/derived from generated | Explicit lack of a source supporting the exact assumed contract rate. |
| synthetic_label | str | see meaning | generated/derived from generated | Synthetic - for training only; retained on generated products. |
