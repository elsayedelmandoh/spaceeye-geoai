# ACUD data request, ordered by impact

Task T-EL-19. This is a proposed request, not evidence of access, approval or actual records received. Request a coded export through an authorized channel; keep identity mapping with the data custodian.

| Priority | Requested fields / grain | Why it matters | Current substitute or limit |
| --- | --- | --- | --- |
| 1 | Dated inspection and verified full-handover outcomes: code, event date, recorded/published date, result, evidence, reviewer; one row per event | Independent validation and meaningful distress/completion labels | Six public backtest cases; generated labels/visits are not independent field evidence |
| 1 | Allocation/contract register: code, allocation date, amendments, actual contractual deadline, grace, eligibility, fine basis/rate, relief decision and effective/publication dates | Replace assumed allocation, land value and K5 monetary policy | Synthetic stand-ins; screening exposure is not an assessed fine |
| 1 | Authorized parcel geometry: coded polygon, effective date, CRS, revision and confidence | Confirm working boundaries and satellite aggregation | Reviewed working polygons, not legal survey boundaries |
| 2 | Monthly financials: collections, due/paid installments, guarantees versus available cash, cost to complete, units sold flow and cumulative sold units, units, reporting/correction dates | Validate financial triggers, liquidity and complaint denominators | Generated monthly finance; complaint denominator is sales flow, not cumulative buyers |
| 2 | Supervisor reports: code, observation date, publication/receipt date, reported progress, scope and evidence | Separate physical observation from announcement and avoid cutoff leakage | Public statements plus generated reports |
| 2 | Masked complaints: coded ID, code, created/received date, channel, text, resolution, adjudicated category; representative independently labelled sample | Evaluate real complaint classification, drift and group errors | Two synthetic corpora; their accuracy would not establish real-world accuracy |
| 3 | Actual visits: code, planned/actual dates, outcome, follow-up, responsible role, evidence reference | Measure follow-through and verify committee actions | Empty real-visit template and separately labelled synthetic exercises |
| 3 | Licensed dated before/after imagery and surveyed/validated heights, with capture/availability dates and sharing rights | Supply inspection imagery and independently assess later heights | No bundled before/after imagery; approved heights end in 2024 |
| 3 | Team capacity, visit duration/cost and intervention outcomes by period | Replace assumed capacity and estimate incremental value without double counting | Capacity 4 with 2/4/6 comparisons; no validated EGP benefit estimate |

## Requested delivery contract

CSV/Parquet with a dictionary, units, null meaning, stable coded keys, coverage interval, source owner, access limits and retention/refresh policy. Include both event date and the date information became available. Distinguish missing, zero and not applicable. Provide revisions and duplicates explicitly, rather than silently overwriting history.

Agree purpose, lawful access, recipients and sharing conditions before receiving identifiable or commercially sensitive information. Ask for masked data and the minimum necessary fields. Keep source evidence available to authorized reviewers. A small verified sample is useful before a full export; no invented quantity or accuracy target is required to submit this request.
