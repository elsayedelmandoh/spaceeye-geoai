# real/eval_outcomes.parquet

Actual schema;6rows. Public/derived table; register origins remain explicit.

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| case | str | see meaning | key | case; see current dataset contract and producing source module. |
| code | str | registered compound codes plus a planted unknown code | key | Coded compound identifier; accepted prepared tables use registered R7 codes. Planted unknown codes occur only in raw/quarantined test inputs. |
| outcome_type | str | see meaning | real | outcome type; see current dataset contract and producing source module. |
| promise_original_period | str | see meaning | real | promise original period; see current dataset contract and producing source module. |
| promise_original_published | str | calendar date | real | promise original published; see current dataset contract and producing source module. |
| outcome_date | str | calendar date | real | outcome date; see current dataset contract and producing source module. |
| outcome_first_published | str | calendar date | real | outcome first published; see current dataset contract and producing source module. |
| delay_months_vs_promise | float64 | see meaning | real | delay months vs promise; see current dataset contract and producing source module. |
| evidence_gate | str | see meaning | real | evidence gate; see current dataset contract and producing source module. |
| outcome_visible_by_2024Q2 | bool | see meaning | real | outcome visible by 2024Q2; see current dataset contract and producing source module. |
| outcome_visible_by_2025Q2 | bool | see meaning | real | outcome visible by 2025Q2; see current dataset contract and producing source module. |
| promise_original_end | str | see meaning | real | promise original end; see current dataset contract and producing source module. |
| first_deadline | str | see meaning | derived | first deadline; see current dataset contract and producing source module. |
