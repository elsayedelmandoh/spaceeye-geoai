# real/statements.parquet

Actual schema;57rows. Public/derived table; register origins remain explicit.

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| statement_id | str | see meaning | key | statement id; see current dataset contract and producing source module. |
| code | str | registered compound codes plus a planted unknown code | key | Coded compound identifier; accepted prepared tables use registered R7 codes. Planted unknown codes occur only in raw/quarantined test inputs. |
| kind | str | see meaning | real | kind; see current dataset contract and producing source module. |
| subtype | str | see meaning | real | subtype; see current dataset contract and producing source module. |
| detail | str | see meaning | real | detail; see current dataset contract and producing source module. |
| published_date | str | calendar date | real | published date; see current dataset contract and producing source module. |
| scope | str | see meaning | real | scope; see current dataset contract and producing source module. |
| period_start | str | see meaning | real | period start; see current dataset contract and producing source module. |
| period_end | str | see meaning | real | period end; see current dataset contract and producing source module. |
| value | float64 | see meaning | real | value; see current dataset contract and producing source module. |
| qualifier | str | see meaning | real | qualifier; see current dataset contract and producing source module. |
| record_id | str | see meaning | real | record id; see current dataset contract and producing source module. |
| verdict | str | see meaning | real | verdict; see current dataset contract and producing source module. |
| origin | str | see meaning | real | Declared provenance category; not a guarantee of operational validity. |
