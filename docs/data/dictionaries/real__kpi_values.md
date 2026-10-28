# real/kpi_values.parquet

Actual schema;372rows. Public/derived table; register origins remain explicit.

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| code | str | registered compound codes plus a planted unknown code | derived | compound code; from the compound; defect 4 replaces it in the configured number of rows |
| quarter | str | see meaning | derived | Quarter of cutoff; flows cover its three months and stocks use its last month. |
| qi | int64 | see meaning | derived | qi; see current dataset contract and producing source module. |
| activity_prob | float64 | see meaning | derived | activity prob; see current dataset contract and producing source module. |
| active | boolean | see meaning | derived | active; see current dataset contract and producing source module. |
| started | bool | see meaning | derived | started; see current dataset contract and producing source module. |
| start_quarter | str | see meaning | derived | start quarter; see current dataset contract and producing source module. |
| K2 | float64 | see meaning | derived | K2; see current dataset contract and producing source module. |
| K3 | int64 | see meaning | derived | K3; see current dataset contract and producing source module. |
| K4 | bool | see meaning | derived | K4; see current dataset contract and producing source module. |
| may_be_complete | bool | see meaning | derived | may be complete; see current dataset contract and producing source module. |
| observed_started | bool | see meaning | derived | Four consecutive quality-valid active quarters or already-published handover; marketing launch alone is excluded. |
| observed_start_quarter | string | see meaning | derived | First quarter of observed start evidence, visible only once that evidence is known. |
| observed_start_source | string | see meaning | derived | activity_run or published_delivery. |
| start_observation_sufficient | bool | see meaning | derived | Positive start evidence, or uninterrupted assessable history from the known launch/promise reference. |
| launch_date_asof | datetime64[ns] | calendar date | derived | Known launch event date, clamped to publication if a future event date was supplied. |
| launch_first_published | datetime64[ns] | calendar date | derived | Date launch evidence was published, used for cutoff filtering. |
| K6 | Int64 | see meaning | derived | Months since first known launch/promise publication without confirmed observed start; null after start or insufficient evidence. Priority2 at13–24,priority1 above24. |
| start_reference_date_asof | datetime64[ns] | calendar date | derived | Event date of earliest known launch, or promise publication date; never future promise delivery date. |
| start_reference_published | datetime64[ns] | calendar date | derived | Publication time of the reference used at cutoff. |
| start_reference_source | str | see meaning | derived | launch or promise_publication. |
| K5_no_start_months | Int64 | see meaning | derived | Post-deadline months before observed start; stops before its start quarter; unknown with insufficient evidence. |
| K5_post_grace_months | Int64 | see meaning | derived | Months beyond12-month deadline grace, stopping accrual at first published handover. |
| K5_overlap_months | Int64 | see meaning | derived | Months satisfying both K5 conditions, subtracted once from the sum. |
| K5_months | Int64 | see meaning | derived | Union of screening months: no observed start after deadline and post12-month grace; overlap counted once; unknown remains null. Not contractual eligibility. |
| K5_basis | str | see meaning | derived | Research-policy proxy; actual contract eligibility remains unverified. |
| level | Int64 | see meaning | derived | level; see current dataset contract and producing source module. |
| level_label | str | see meaning | derived | level label; see current dataset contract and producing source module. |
| reason | str | see meaning | derived | reason; see current dataset contract and producing source module. |
| reason_ar | str | see meaning | derived | Committee-facing Arabic rule explanation, generated from the same cutoff evidence as reason. |
| level_word | str | see meaning | derived | Ordinal priority word; not an independent risk probability. |
| level_word_ar | str | see meaning | derived | Arabic ordinal priority word for committee export. |
| k3_first_deadline | datetime64[us] | see meaning | derived | k3 first deadline; see current dataset contract and producing source module. |
| cycle_rank | Int64 | see meaning | derived | cycle rank; see current dataset contract and producing source module. |
| origin | str | see meaning | derived | Declared provenance category; not a guarantee of operational validity. |
| run_id | str | see meaning | derived | run id; see current dataset contract and producing source module. |
| computed_at | str | see meaning | derived | computed at; see current dataset contract and producing source module. |
