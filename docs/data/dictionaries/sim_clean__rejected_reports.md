# sim_clean/rejected_reports.parquet

Actual schema;5rows. Synthetic - for training only

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| code | str | registered compound codes plus a planted unknown code | key | Coded compound identifier; accepted prepared tables use registered R7 codes. Planted unknown codes occur only in raw/quarantined test inputs. |
| month | str | YYYY-MM, 2023-01..2026-09 | key | calendar month; the row is the state at the end of that month; grid |
| reported_pct | float64 | percent | generated | supervisor-engineer progress report, only in months where a report arrived. in months with a real announced value it IS that value; quarterly report of the true progress at quarter end; optimistic developers add 2-8 points; rounding probability 16% (final multiples-of-5 share is checked separately); 5 % missing (35 % while stalled) |
| report_date | datetime64[ns] | calendar date | generated | date of the report; 15-45 days after the quarter end (late-style developers up to 75); real publication date for announced values; see reported_pct |
| dq_reason | str | see meaning | generated/derived from generated | Observable reason for quarantine/rejection; phone masking also applies to rejected complaint text. |
