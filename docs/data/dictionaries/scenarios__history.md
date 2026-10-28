# scenarios/history.parquet

Actual schema;326rows. Synthetic - for training only

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| code | str | registered compound codes plus a planted unknown code | key | compound code; from the compound; defect 4 replaces it in the configured number of rows |
| month | str | YYYY-MM, 2023-01..2026-09 | key | calendar month; the row is the state at the end of that month; grid |
| planned_pct | float64 | percent | generated | contractual plan: Weibull S-curve divided by its value at the end, 100 % exactly at the contractual delivery month; deadline = end of the first real promise when one exists, else plan start + 30-42 months (finished work: the month it really finished) |
| reported_pct | float64 | percent | generated | supervisor-engineer progress report, only in months where a report arrived. in months with a real announced value it IS that value; quarterly report of the true progress at quarter end; optimistic developers add 2-8 points; rounding probability 16% (final multiples-of-5 share is checked separately); 5 % missing (35 % while stalled) |
| report_date | datetime64[ns] | calendar date | generated | date of the report; 15-45 days after the quarter end (late-style developers up to 75); real publication date for announced values; see reported_pct |
| units_sold | int64 | units / month | generated | units sold in the month; hazard (launch spike, slow tail) x demand (policy rate, Ramadan, post-float boom 2-4 months after 6 Mar 2024), negative-binomial noise |
| avg_price_egp | float64 | EGP | generated | average contract price of the units sold in the month (empty when none sold); launch price per m2 = cost x U(1.4, 2.0); list jumps 15-40 % after the float; +0.5 %/month |
| collections_egp | float64 | EGP | generated | buyer payments received in the month (all go into escrow); 8.5 % down payment at sale + equal monthly installments over 7-12 years x payment rate (3 % late, 8 % for 6 months after the float, weaker before a stall) |
| cover_required_egp | float64 | EGP | derived | financial cover the decree requires: class % (20 or 15) x cost to complete, until certified progress passes 30 % / 25 % (art. 4); cover_pct x cost_to_complete_egp |
| cover_balance_egp | float64 | EGP | generated | escrow cash plus the cover the developer keeps posted (a guarantee; shrinks when the developer is in arrears); releases only after a quarterly report: min(balance - 5 % refund reserve, certified cost so far x 1.05 - already released) |
| cost_to_complete_egp | float64 | EGP | derived | build cost still to spend on the certified (reported) progress; total cost x (1 - certified %); total cost follows the real dollar (40 %) and the real rebar/cement index (60 %) |
| land_due_egp | float64 | EGP | generated | land installment falling due in the month (0 in other months); 16 quarterly installments, land price 2,500-12,000 EGP/m2 x land area |
| land_paid_egp | float64 | EGP | generated | land money paid in the month (a lump when arrears are cleared); paid when cash covers it and a month of spending; arrears pay 1 %/month penalty |
| land_months_late | int64 | months | derived | age of the oldest unpaid installment (0 when none); month - due month of the oldest unpaid installment |
| roads_paved_share | float64 | 0-1 | generated | share of internal roads paved; follows true progress above 35 % with a two-month lag, +-0.02 survey noise |
| meters_active | int64 | meters | generated | residential meters with a contract (handed-over units with a contract); handed-over units x contract rate rising from 0.5 to 0.92 in 12 months |
| kwh | float64 | kWh / month | generated | electricity billed: occupied homes x 153 x temperature seasonality + standby of empty meters + the site meter while building; 4 % estimated reads; real monthly max temperature; site load follows the work done |
| status_level | str | on_plan / behind / late / distressed | derived | level ACUD recorded at its last quarterly review; K3 > 24 or no reported progress for 6 months or land arrears with cover below the minimum -> distressed; K3 > 0 -> late; reported 10+ points under plan -> behind |
| warning_issued | bool |  | generated | a warning letter was issued in the month; 12-month grace expired (decree art. 5), or 3 months with no reported progress at a quarterly review (every 6 months while it lasts) |
