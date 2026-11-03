# sim_clean/fin_quarterly.parquet

Actual schema;180rows. Synthetic - for training only

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| code | str | registered compound codes plus a planted unknown code | key | Coded compound identifier; accepted prepared tables use registered R7 codes. Planted unknown codes occur only in raw/quarantined test inputs. |
| quarter | str | see meaning | generated/derived from generated | Quarter of cutoff; flows cover its three months and stocks use its last month. |
| month | str | YYYY-MM, 2023-01..2026-09 | key | calendar month; the row is the state at the end of that month; grid |
| months_present | int64 | see meaning | generated/derived from generated | Number of observed financial months contributing to this quarter; required3. |
| collections_egp | float64 | EGP | generated | Sum over this quarter of monthly collections_egp. |
| land_due_egp | float64 | EGP | generated | Sum over this quarter of monthly land_due_egp. |
| land_paid_egp | float64 | EGP | generated | Sum over this quarter of monthly land_paid_egp. |
| kwh | float64 | kWh / month | generated | Sum over this quarter of monthly kwh. |
| units_sold | float64 | units / month | generated | Sum of units sold in the three months; monthly sales are flows, not cumulative inventory. |
| planned_pct | float64 | percent | generated | contractual plan: Weibull S-curve divided by its value at the end, 100 % exactly at the contractual delivery month; deadline = end of the first real promise when one exists, else plan start + 30-42 months (finished work: the month it really finished) |
| cover_required_egp | float64 | EGP | derived | financial cover the decree requires: class % (20 or 15) x cost to complete, until certified progress passes 30 % / 25 % (art. 4); cover_pct x cost_to_complete_egp |
| cover_balance_egp | float64 | EGP | generated | escrow cash plus the cover the developer keeps posted (a guarantee; shrinks when the developer is in arrears); releases only after a quarterly report: min(balance - 5 % refund reserve, certified cost so far x 1.05 - already released) |
| cost_to_complete_egp | float64 | EGP | derived | build cost still to spend on the certified (reported) progress; total cost x (1 - certified %); total cost follows the real dollar (40 %) and the real rebar/cement index (60 %) |
| land_months_late | int64 | months | derived | age of the oldest unpaid installment (0 when none); month - due month of the oldest unpaid installment |
| meters_active | int64 | meters | generated | residential meters with a contract (handed-over units with a contract); handed-over units x contract rate rising from 0.5 to 0.92 in 12 months |
| roads_paved_share | float64 | 0-1 | generated | share of internal roads paved; follows true progress above 35 % with a two-month lag, +-0.02 survey noise |
| reported_pct | float64 | percent | generated | supervisor-engineer progress report, only in months where a report arrived. in months with a real announced value it IS that value; quarterly report of the true progress at quarter end; optimistic developers add 2-8 points; rounding probability 16% (final multiples-of-5 share is checked separately); 5 % missing (35 % while stalled) |
| report_date | datetime64[ns] | calendar date | generated | date of the report; 15-45 days after the quarter end (late-style developers up to 75); real publication date for announced values; see reported_pct |
| land_value_from_known_installments_egp | float64 | EGP | generated/derived from generated | Median positive land installment available by cutoff times16; generated-ledger inference, null without positive dues. |
| K5_months | Int64 | see meaning | generated/derived from generated | Union of screening months: no observed start after deadline and post12-month grace; overlap counted once; unknown remains null. Not contractual eligibility. |
| K6 | Int64 | see meaning | generated/derived from generated | Months since first known launch/promise publication without confirmed observed start; null after start or insufficient evidence. Priority2 at13–24,priority1 above24. |
| assumed_land_value_egp | float64 | EGP | generated/derived from generated | Land area times generated price; in quarterly data replaced by value inferred from available installments when present. |
| fine_rate_month | float64 | see meaning | generated/derived from generated | Illustrative 0.5% monthly fraction; explicit assumption, not a published universal contract rate. |
| land_value_basis | str | see meaning | generated/derived from generated | Whether current value comes from available generated installments or vintage-based fallback. |
| K5_egp | Float64 | EGP | generated/derived from generated | K5_months times assumed land value times assumed monthly rate. Not an assessed fine or a cash-ledger deduction. |
| K5_egp_discount_scenario | Float64 | EGP | generated/derived from generated | Optional50%discount intervention; null before2024-11-18publication; no automatic entitlement or known expiry asserted. |
| K5_egp_installment_scenario_monthly | Float64 | EGP | generated/derived from generated | Gross assumed fine divided by12; separate scheduling intervention after2024-11-18, not combined automatically with discount. |
| relief_basis | str | see meaning | generated/derived from generated | Temporary relief is hypothetical project eligibility, not a recorded decision. |
| fine_assumption | bool | see meaning | generated/derived from generated | True: amount/rate is a generated policy intervention. |
| synthetic_label | str | see meaning | generated/derived from generated | Synthetic - for training only; retained on generated products. |
