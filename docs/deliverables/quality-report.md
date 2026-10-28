# Track A quality report

Task T-AH-12. Snapshot of saved data-only checks; rendering this report does not rerun them.

Source: `app_data/data_completion/quality_checks.csv` (external configured input).
Source SHA256: `333f564c415c9d224e35d32cd92442bdb2405a93aff1ceb7f6ca331be3bf76f2`.

Results: 1 FLAG, 10 PASS.

| Gate | Dimension | Status | Observed result | Owner role | On failure | Impact on the indicator |
| --- | --- | --- | --- | --- | --- | --- |
| source | Accuracy | PASS | 0 bad of 57 | R2 | fix: excluded | bad statements would change K3 and may-be-complete |
| completeness | Completeness | PASS | 12 of 12 assessable at 2026Q3; 97.7% of all compound-quarters | R3 | flag: not assessable | a compound below the minimum gets no level |
| validity | Validity | PASS | 0 violations | R1 | stop | invalid values break K1, A and K3 |
| uniqueness | Uniqueness | PASS | 0 duplicates | R1 | stop | duplicates double-count a quarter |
| consistency | Consistency | PASS | 0 stray codes; counts ok=True | R1 | stop | a join that changes rows silently changes every KPI |
| freshness | Freshness | PASS | last quarter 2026Q3, 1 months before 2026-10-26 | R3 | flag: stale | stale data means levels describe the past |
| separation | Consistency | PASS | 0 columns without origin, 0 generated tables | R1 | stop | mixing generated and real numbers on the map |
| data_or_city | Accuracy | FLAG | 1 quarters flagged: 2019Q2 | R4 | flag the quarter and review | flagged quarters may be a data event, not the city |
| stuck_series | Accuracy | PASS | 0 stuck points | R3 | flag and review | a frozen series reads as 'no change' |
| veg_pull_check | Accuracy | PASS | max diff 0.0000 on 24 rows | R3 | flag | vegetation drives the may-be-complete flag |
| no_names | Privacy | PASS | 77 patterns, 341 files; files with a match: none | R1 | stop | names appear only in the backtest slide, never in data |

## Decisions and limits

STOP blocks delivery. FIX requires correction and a gate rerun. FLAG stays visible and requires review; it is not a PASS.

The 2019Q2 source-event FLAG remains unresolved. Review source coverage before interpreting that quarter as a physical construction change.

Owner codes are pipeline roles, not evidence of a named teammate's review or sign-off. Freshness is relative to the configured computation date, not the report rendering date.

These checks do not validate classifier accuracy, contractual fines, synthetic visits or actual field conditions. Historical backtest and model evaluations remain separate.

Refresh checks: `uv run --locked --offline python -m src.pipeline.complete_data`. Then render: `uv run --locked --offline python -m src.pipeline.quality_report`.
