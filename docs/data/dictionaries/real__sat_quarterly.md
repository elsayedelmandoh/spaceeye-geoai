# real/sat_quarterly.parquet

Actual schema;516rows. Public/derived table; register origins remain explicit.

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| code | str | registered compound codes plus a planted unknown code | key | compound code; from the compound; defect 4 replaces it in the configured number of rows |
| quarter | str | see meaning | key | Quarter of cutoff; flows cover its three months and stocks use its last month. |
| qi | int64 | see meaning | key | qi; see current dataset contract and producing source module. |
| built_prob_mean | float64 | see meaning | derived | built prob mean; see current dataset contract and producing source module. |
| n_images | int64 | see meaning | real | n images; see current dataset contract and producing source module. |
| dw12_water | float64 | see meaning | derived | dw12 water; see current dataset contract and producing source module. |
| dw12_trees | float64 | see meaning | derived | dw12 trees; see current dataset contract and producing source module. |
| dw12_grass | float64 | see meaning | derived | dw12 grass; see current dataset contract and producing source module. |
| dw12_flooded_vegetation | float64 | see meaning | derived | dw12 flooded vegetation; see current dataset contract and producing source module. |
| dw12_crops | float64 | see meaning | derived | dw12 crops; see current dataset contract and producing source module. |
| dw12_shrub_and_scrub | float64 | see meaning | derived | dw12 shrub and scrub; see current dataset contract and producing source module. |
| dw12_built | float64 | see meaning | derived | dw12 built; see current dataset contract and producing source module. |
| dw12_bare | float64 | see meaning | derived | dw12 bare; see current dataset contract and producing source module. |
| dw12_snow_and_ice | float64 | see meaning | derived | dw12 snow and ice; see current dataset contract and producing source module. |
| K1 | float64 | see meaning | derived | K1; see current dataset contract and producing source module. |
| K4 | bool | see meaning | derived | K4; see current dataset contract and producing source module. |
| activity_prob | float64 | see meaning | derived | activity prob; see current dataset contract and producing source module. |
| active | boolean | see meaning | derived | active; see current dataset contract and producing source module. |
| K2 | float64 | see meaning | derived | K2; see current dataset contract and producing source module. |
| started | bool | see meaning | derived | started; see current dataset contract and producing source module. |
| start_quarter | str | see meaning | key | start quarter; see current dataset contract and producing source module. |
| observed_started | bool | see meaning | derived | Four consecutive quality-valid active quarters or already-published handover; marketing launch alone is excluded. |
| observed_start_quarter | string | see meaning | derived | First quarter of observed start evidence, visible only once that evidence is known. |
| observed_start_source | string | see meaning | derived | activity_run or published_delivery. |
| start_observation_sufficient | bool | see meaning | derived | Positive start evidence, or uninterrupted assessable history from the known launch/promise reference. |
| launch_date_asof | datetime64[ns] | calendar date | derived | Known launch event date, clamped to publication if a future event date was supplied. |
| launch_first_published | datetime64[ns] | calendar date | derived | Date launch evidence was published, used for cutoff filtering. |
| K6 | Int64 | see meaning | derived | Months since first known launch/promise publication without confirmed observed start; null after start or insufficient evidence. Priority2 at13–24,priority1 above24. |
| start_reference_date_asof | datetime64[ns] | calendar date | derived | Event date of earliest known launch, or promise publication date; never future promise delivery date. |
| start_reference_published | datetime64[ns] | calendar date | derived | Publication time of the reference used at cutoff. |
| start_reference_source | string | see meaning | derived | launch or promise_publication. |
