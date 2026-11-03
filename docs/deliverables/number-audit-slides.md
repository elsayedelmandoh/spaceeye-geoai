# Number audit - slides

Task T-SA-08, slides sheet.

Source checked: `docs/deliverables/01-presentation/presentation.md`. Line numbers refer to that file. Verdict counts and open items are at the end.

| # | Line | Number as written | Verdict | Source (file:line) and note |
|---|---|---|---|---|
| S-01 | 3 | "12-15 min" (spec length note) | NO SOURCE | Searched "12-15" in allowed files: none. Length is still to be confirmed per the file. |
| S-02 | 7 | "400 developers" | NO SOURCE | Searched "400": no developer count in allowed files (only unrelated hit, data/SOURCE_CATALOG.csv:79). Figure is the chairman's statement cited on slide 1. |
| S-03 | 7 | "500 projects" | NO SOURCE | Searched "500": no project count in allowed files. |
| S-04 | 8 | "every 3 months" (field review) | MATCH | configs/cost_assumptions.yaml:7 "field review every 3 months (spec formula)". |
| S-05 | 9 | "7-8%" seriously late | NO SOURCE | Searched "7-8" and "7-8%": none. |
| S-06 | 9 | "6 mutual terminations" | NO SOURCE | Searched "mutual" and "terminat": none. |
| S-07 | 10 | "Sep-Oct 2026" (statement dates) | NO SOURCE | Searched "Sep-Oct" and "chairman": none. Statements are not in repo files. |
| S-08 | 18 | "12 coded compounds" | MATCH | data/R1_REPORT.md:3 "Scope: R7 only, 12 coded compounds." |
| S-09 | 18 | "reporting quarter 2026Q3" | MATCH | configs/kpis.yaml:7 reporting_quarter: 2026Q3. |
| S-10 | 18 | "cycle capacity 4" | MATCH | configs/kpis.yaml:8 cycle_capacity: 4; configs/data.yaml:83. |
| S-11 | 22 | "1,009" documented facts passed review | NO SOURCE | Searched "1,009" and "1009" in allowed files: none. Slide cites docs/requirements/01-specs.md section 12, which is outside the searched paths. |
| S-12 | 22 | "1,026" documented facts | NO SOURCE | Searched "1,026" and "1026": none in allowed files. Same spec citation as S-11. |
| S-13 | 22 | "0 invented" | NO SOURCE | Same spec figure as S-11; searched "invented": no count found. |
| S-14 | 30 | heights "to 2023" (Open Buildings) | MATCH | data/DATA_SOURCES_AND_GENERATION.md:24 "Google Open Buildings temporal product through 2023". |
| S-15 | 30 | "2024 value is an estimate" | MATCH | data/DATA_SOURCES_AND_GENERATION.md:24 "approved local v4 built-mask estimate for 2024"; data/DATASET_CONTRACT.md:41. |
| S-16 | 32 | "at least 6 Dynamic World images" | MATCH | configs/kpis.yaml:87 "at least 6 Dynamic World images in the quarter". |
| S-17 | 37 | vegetation share "0.10 or more" | MATCH | configs/kpis.yaml:155 "vegetation share >= 0.10"; configs/data.yaml:51 veg_complete: 0.10. |
| S-18 | 37 | level "at most 3" under the may-be-complete cap | MATCH | configs/kpis.yaml:156 "Cap level at 3". |
| S-19 | 37 | "3 of 12 levels: C03, C12 and C21" | NO SOURCE | Searched "3 of 12", "C03", "C12", "C21". Nearest hit data/K1_FALLBACK_CHECK.md:22 "Compounds whose level changes at 2026Q3 | 3 of 12" is a different comparison (fallback check), not the cap. Codes appear in data/K1_FALLBACK_CHECK.md:23 cycle lists only. |
| S-20 | 38 | levels 1 to 4 and their meanings | MATCH | configs/kpis.yaml:134-148: level 1 "Inspect now", 2 "Inspect this cycle", 3 "Document review", 4 "Routine". |
| S-21 | 39 | "12 months handover grace" | MATCH | data/DATA_SOURCES_AND_GENERATION.md:38 "post 12-month grace"; configs/data.yaml:91 grace_months: 12. |
| S-22 | 39 | "24 months right to refund" | NO SOURCE | Searched "24 month", "24-month", "refund": no 24-month refund term. Only configs/data.yaml:197 refund_reserve: 0.05 (decree 2184 art 3(6)). |
| S-23 | 39 | "Decree 2184/2022" | MATCH | data/DATA_SOURCES_AND_GENERATION.md:29 "Decree 2184/2022" (spacing differs); configs/data.yaml:24 decree file. |
| S-24 | 46 | "capacity 4" | MATCH | configs/kpis.yaml:160 capacity: 4. |
| S-25 | 46 | "levels 1-3" selected | MATCH | configs/kpis.yaml:9 eligible_levels: [1, 2, 3]. |
| S-26 | 50 | "1 of 6" (slide 7 title) | MATCH | data/BACKTEST_CURRENT.md:5 "After-start reading: 1 of 6." |
| S-27 | 52 | "six public R7 cases" | MATCH | data/BACKTEST_CURRENT.md:5 "of 6"; data/HANDOFF.md:5 "six public check cases". |
| S-28 | 53 | "1 of 6 cases" (after-start) | MATCH | data/BACKTEST_CURRENT.md:5; configs/kpis.yaml:175 "1 of 6". |
| S-29 | 53 | "0 of 6" (point-in-time) | MATCH | data/BACKTEST_CURRENT.md:5 "Point-in-time reading: 0 of 6." |
| S-30 | 54 | "criterion of 5 cases" | MATCH | data/BACKTEST_CURRENT.md:5; configs/kpis.yaml:177. |
| S-31 | 55 | "at least 10 images per quarter" | NO SOURCE | Searched "at least 10" and "10 images": none in allowed files. Cited DIAGNOSIS.md is under data/experiments/, outside the searched paths. |
| S-32 | 55 | "five missed cases" | MATCH | Derived: 6 cases minus 1 hit; data/BACKTEST_CURRENT.md:5. |
| S-33 | 62 | "12 coded compounds" | MATCH | data/R1_REPORT.md:3. |
| S-34 | 63 | "96 training rows" | MATCH | data/EW_REPORT_CURRENT.md:5 "Training: 96 rows." |
| S-35 | 63 | "48 test rows" | MATCH | data/EW_REPORT_CURRENT.md:5 "Time test: 48 rows."; data/R2_REPORT.md:23. |
| S-36 | 63 | "only 4 distressed rows" in test | MATCH | data/EW_REPORT_CURRENT.md:9 "the time test holds 4 distressed rows". |
| S-37 | 64 | "denominator 4" (recall@4) | MATCH | data/EW_REPORT_CURRENT.md:13 "3 of 4" (denominator is the 4 selected); data/EW_REPORT_CURRENT.md:9. |
| S-38 | 65 | public rule "3 of 4" | MATCH | data/EW_REPORT_CURRENT.md:13 "public_rule \| 3 of 4 \| 0.750". |
| S-39 | 65 | combined rule "3 of 4" | MATCH | data/EW_REPORT_CURRENT.md:14. |
| S-40 | 66 | logistic, satellite "1 of 4" | MATCH | data/EW_REPORT_CURRENT.md:15. |
| S-41 | 66 | logistic, combined "2 of 4" | MATCH | data/EW_REPORT_CURRENT.md:16. |
| S-42 | 67 | boosting, satellite "4 of 4" | MATCH | data/EW_REPORT_CURRENT.md:17. Caveat, not a mismatch: data/EW_V2A_VS_V1.md:13 gives 1 of 4 under v2a, and :20 says the 4 of 4 rested partly on height. |
| S-43 | 67 | boosting, combined "1 of 4" | MATCH | data/EW_REPORT_CURRENT.md:18. |
| S-44 | 68 | "2,000 draws" (random top-4) | MATCH | data/EW_REPORT_CURRENT.md:20 "Random: 2,000 draws". |
| S-45 | 68 | baseline "mean 0.335" | MATCH | data/EW_REPORT_CURRENT.md:20. |
| S-46 | 68 | "95% interval 0.000 to 0.750" | MATCH | data/EW_REPORT_CURRENT.md:20 "95% interval [0.000, 0.750]". |
| S-47 | 69 | "with 4 cases" | MATCH | data/EW_REPORT_CURRENT.md:9. |
| S-48 | 70 | keyword "0.27" accuracy, benchmark | MATCH | docs/deliverables/complaints_eval.csv:2 accuracy 0.2692 (benchmark_test). |
| S-49 | 70 | "104-row benchmark" | MATCH | docs/deliverables/complaints_eval.csv:2 n_total 104. |
| S-50 | 70 | keyword "0.37" on check set | MATCH | docs/deliverables/complaints_eval.csv:5 accuracy 0.3667 (check_30). |
| S-51 | 70 | "30 check set" | MATCH | docs/deliverables/complaints_eval.csv:5 n_total 30. |
| S-52 | 70 | TF-IDF "0.22" accuracy, benchmark | MATCH | docs/deliverables/complaints_eval.csv:3 accuracy 0.2212. |
| S-53 | 70 | TF-IDF "0.30" accuracy, check set | MATCH | docs/deliverables/complaints_eval.csv:6 accuracy 0.3000. |
| S-54 | 76 | S3 capacity "2 or 6 visits" | MATCH | data/DATASET_CONTRACT.md:116 "capacities 2/4/6". |
| S-55 | 76 | "45 of 744 rows" change list membership | NO SOURCE | Searched "45 of", "744 rows", "744": none in allowed files. |
| S-56 | 76 | "28" rows change at capacity 2 | NO SOURCE | Searched "28 at" and "capacity 2" against scenario and dataset files: no row counts found. |
| S-57 | 76 | "17" rows change at capacity 6 | NO SOURCE | Same search as S-56: no row count found. |
| S-58 | 76 | S1 and S2 "0 of 216 rows" | NO SOURCE | Searched "216 rows" and "0 of 216": no scenario row count; 216 appears only in unrelated hits. |
| S-59 | 80 | "3 settings" (heading) | MATCH | configs/cost_assumptions.yaml:15, :20, :25 (conservative, central, optimistic). |
| S-60 | 82 | "4 compounds per cycle" | MATCH | configs/cost_assumptions.yaml:8 cycle_list_visits: 4. |
| S-61 | 82 | "all 12" compounds | MATCH | configs/cost_assumptions.yaml:6 projects: 12. |
| S-62 | 82 | "16 visits a year" | MATCH | Derived: configs/cost_assumptions.yaml:7 visits_per_year: 4 times :8 cycle_list_visits: 4 = 16. |
| S-63 | 82 | "48" visits a year (all 12) | NO SOURCE | Derived as 12 x 4 from configs/cost_assumptions.yaml:6-7. "48 visits" is not stated; searched "48 visits": none. |
| S-64 | 83 | "-0.006" million EGP per year | MATCH | configs/cost_assumptions.yaml:31 wording. |
| S-65 | 83 | "0.098" million EGP per year | MATCH | configs/cost_assumptions.yaml:31 wording. |
| S-66 | 85 | cost per visit "2,000 EGP" | MATCH | configs/cost_assumptions.yaml:15 conservative cost_per_visit: 2000 (assumption). |
| S-67 | 85 | cost per visit "3,000 EGP" | MATCH | configs/cost_assumptions.yaml:20 central cost_per_visit: 3000 (assumption). |
| S-68 | 85 | cost per visit "4,000 EGP" | MATCH | configs/cost_assumptions.yaml:25 optimistic cost_per_visit: 4000 (assumption). |
| S-69 | 85 | "team of 3" | MATCH | configs/cost_assumptions.yaml:10 "team of 3 x daily salary + transport". |
| S-70 | 94 | "6 real cases" | MATCH | data/HANDOFF.md:31 "Real-case check ... One of six"; data/HANDOFF.md:5 "six public check cases". |
| S-71 | 94 | "4 test cases" | MATCH | data/EW_REPORT_CURRENT.md:9 (4 distressed rows in the time test). |
| S-72 | 96 | "Law 151/2020" | NO SOURCE | Searched "151/2020" and "151": no relevant hit. The team board that the slide cites is outside the searched paths. |
| S-73 | 103 | "Law 119" | MATCH | data/DATA_SOURCES_AND_GENERATION.md:29 "Law119/2008" (year and number match; spacing differs). |
| S-74 | 103 | "art. 54" (supervisor reports) | NO SOURCE | Searched "art. 54", "Art 54" and "54": no article reference in allowed files. |

## Summary

- Rows: 74 (one per number, grouped where one clause holds several values).
- MATCH: 55
- MISMATCH: 0
- NO SOURCE: 19
- CONTEXT: 0

Skipped on purpose: slide and section numbers, task and item IDs (for example T-SA-06, K2, B5, S1-S3, T-AH-19), compound codes (C03, C12, C21) when used only as labels, and the R7 scope label. Compound codes were checked only where the slide claims a value for them (S-19).

Checked against `docs/deliverables/complaints_eval.csv`: keyword 0.27 benchmark / 0.37 check set and TF-IDF 0.22 / 0.30 all MATCH (S-48 to S-53). Nothing to report on the complaints figures.

## Open for owners

- S-01 (line 3): spec length "12-15 min" has no source in the searched files.
- S-02, S-03 (line 7): "400 developers" and "500 projects" have no source in repo files; they are the chairman's statements.
- S-05, S-06, S-07 (lines 9-10): "7-8% seriously late", "6 mutual terminations" and the "Sep-Oct 2026" statement dates have no source in repo files.
- S-11, S-12, S-13 (line 22): "1,009 of 1,026" facts and "0 invented" cite docs/requirements/01-specs.md section 12, which is outside the searched paths. Owner should confirm the figures against that file.
- S-19 (line 37): "3 of 12 levels capped (C03, C12, C21)" has no source. The nearest hit, data/K1_FALLBACK_CHECK.md:22 "3 of 12", is a different comparison. Owner should confirm the count or drop it.
- S-22 (line 39): "24 months right to refund" has no source; only refund_reserve 0.05 appears (configs/data.yaml:197).
- S-31 (line 55): "at least 10 images per quarter" is not in the searched paths. Cited DIAGNOSIS.md sits under data/experiments/. Owner should check it there.
- S-55 to S-58 (line 76): scenario row counts "45 of 744", "28", "17" and "0 of 216" are not in the searched files. Owner should check against the scenario outputs.
- S-63 (line 82): "48 visits a year" (all 12 compounds) is derived arithmetic (12 x 4) and not stated in the repo. Owner should state it or change the slide.
- S-72 (line 96): "Law 151/2020" cites the team board, which is outside the searched paths.
- S-74 (line 103): "art. 54" for the supervisor-report obligation has no article reference in the searched files.
- Caveat, not a mismatch: S-42 (line 67) boosting satellite "4 of 4" matches the v1 report, but data/EW_V2A_VS_V1.md:13 gives 1 of 4 under v2a and :20 says the 4 of 4 rested partly on height. Owner should keep the v1 label on that slide.
