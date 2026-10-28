# real/compounds.parquet

Actual schema;12rows. Public/derived table; register origins remain explicit.

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| code | str | registered compound codes plus a planted unknown code | key | compound code; from the compound; defect 4 replaces it in the configured number of rows |
| developer_code | str | see meaning | key | developer code; see current dataset contract and producing source module. |
| district | str | see meaning | real | district; see current dataset contract and producing source module. |
| land_area_m2 | float64 | see meaning | real/generated | Compound land area; adjacent land_area_origin states real or generated. |
| land_area_origin | str | see meaning | key | Origin of register land area; retain alongside generated financial assumptions. |
| floors_allowed | int64 | see meaning | generated | floors allowed; see current dataset contract and producing source module. |
| floors_origin | str | see meaning | key | floors origin; see current dataset contract and producing source module. |
| coverage_max | float64 | see meaning | real | coverage max; see current dataset contract and producing source module. |
| bua_m2 | float64 | see meaning | derived | bua m2; see current dataset contract and producing source module. |
| units | int64 | see meaning | real/generated | units; see current dataset contract and producing source module. |
| units_origin | str | see meaning | key | units origin; see current dataset contract and producing source module. |
| cover_pct | float64 | percent | derived | cover pct; see current dataset contract and producing source module. |
| first_deadline | str | see meaning | derived | first deadline; see current dataset contract and producing source module. |
| first_deadline_published | str | calendar date | derived | first deadline published; see current dataset contract and producing source module. |
| boundary_confidence | str | see meaning | real | boundary confidence; see current dataset contract and producing source module. |
| boundary_area_m2 | float64 | see meaning | real | boundary area m2; see current dataset contract and producing source module. |
| handover_first_published | str | calendar date | derived | handover first published; see current dataset contract and producing source module. |
