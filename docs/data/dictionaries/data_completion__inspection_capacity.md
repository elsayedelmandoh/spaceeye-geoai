# data_completion/inspection_capacity.csv

Actual schema;1116rows. Synthetic - for training only

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| quarter | str | see meaning | generated/derived from generated | Quarter of cutoff; flows cover its three months and stocks use its last month. |
| code | str | registered compound codes plus a planted unknown code | key | compound code; from the compound; defect 4 replaces it in the configured number of rows |
| scenario_id | str | see meaning | generated/derived from generated | Named hypothetical intervention; baseline stays separate. |
| capacity | int64 | see meaning | generated/derived from generated | Proposed inspection count for this quarter;2,4or6,not building capacity. |
| eligible_rank | float64 | see meaning | generated/derived from generated | Rank among priority1–3 only, sorted by level,K2descending,K3descending,code; missing for ineligible rows. |
| selected | bool | see meaning | generated/derived from generated | Eligible rank is within this intervention's inspection capacity; no change to levels or finances. |
| level | float64 | see meaning | generated/derived from generated | level; see current dataset contract and producing source module. |
| origin | str | see meaning | generated/derived from generated | Declared provenance category; not a guarantee of operational validity. |
| assumption | bool | see meaning | generated/derived from generated | True: synthetic input or proposed operational capacity, not measured internal data. |
