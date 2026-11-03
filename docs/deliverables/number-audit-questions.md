# Number audit - expected questions

Task T-SA-08, questions sheet.

Source checked: `docs/deliverables/expected-questions.md`. Line numbers refer to that file. Verdict counts and open items are at the end.

| # | Line | Number as written | Verdict | Source (file:line) and note |
|---|---|---|---|---|
| Q-01 | 8 | "N quarters" / "N months" (answer template) | CONTEXT | Placeholder in docs/deliverables/expected-questions.md:8; no value is claimed. |
| Q-02 | 9 | "r about 0.96" (Dynamic World vs Open Buildings) | NO SOURCE | Searched "0.96" and "r about" in allowed files: none. Only the answer's own placeholder mentions it. |
| Q-03 | 9 | "5 pre-registered tests" | MISMATCH | Answer says 5. data/K1_FALLBACK_CHECK.md:29 "pre-registered T1-T3 tests" (3); data/K1_FALLBACK_CHECK.md:13 lists T1, T2, T3 plus seasonal spread (4 checks). configs/data.yaml:63-66 defines T1 and T2 with T3 at :67. |
| Q-04 | 9 | "[verify in the dataset audit]" | CONTEXT | Placeholder text in docs/deliverables/expected-questions.md:9; the check is not yet recorded. |
| Q-05 | 10 | "1 of 6 real cases" | MATCH | data/BACKTEST_CURRENT.md:5 "After-start reading: 1 of 6." |
| Q-06 | 10 | "five missed sites" | MATCH | Derived: 6 cases minus 1 hit; data/BACKTEST_CURRENT.md:5. |
| Q-07 | 11 | "criterion of 5 cases" | MATCH | data/BACKTEST_CURRENT.md:5; configs/kpis.yaml:177 "5 cases (not reduced)". |
| Q-08 | 12 | "96 training rows" | MATCH | data/EW_REPORT_CURRENT.md:5 "Training: 96 rows." |
| Q-09 | 12 | "48 test rows" | MATCH | data/EW_REPORT_CURRENT.md:5 "Time test: 48 rows." |
| Q-10 | 12 | "4 distressed test cases" | MATCH | data/EW_REPORT_CURRENT.md:9 "the time test holds 4 distressed rows". |
| Q-11 | 13 | public and combined rules "3 of 4" | MATCH | data/EW_REPORT_CURRENT.md:13-14. |
| Q-12 | 13 | logistic satellite "1 of 4", combined "2 of 4" | MATCH | data/EW_REPORT_CURRENT.md:15-16. |
| Q-13 | 13 | boosting satellite "4 of 4", combined "1 of 4" | MATCH | data/EW_REPORT_CURRENT.md:17-18. |
| Q-14 | 13 | random-list baseline "0.335 (2,000 draws)" | MATCH | data/EW_REPORT_CURRENT.md:20 "Random: 2,000 draws, mean 0.335". |
| Q-15 | 15 | "0-100 score" | CONTEXT | Hypothetical scale used to explain why levels are used; not a model output. Only docs/deliverables/expected-questions.md:15 states it. |
| Q-16 | 16 | "0.007 to 0.102 million EGP per year" | MATCH | configs/cost_assumptions.yaml:39 wording. |
| Q-17 | 19 | "12 compounds" (12 coded R7 compounds) | MATCH | data/R1_REPORT.md:3 "Scope: R7 only, 12 coded compounds." |
| Q-18 | 21 | "104-row benchmark" | MATCH | docs/deliverables/complaints_eval.csv:2 n_total 104. |
| Q-19 | 21 | keyword baseline "0.27" on benchmark | MATCH | docs/deliverables/complaints_eval.csv:2 accuracy 0.2692. |
| Q-20 | 21 | TF-IDF plus logistic "0.22" on benchmark | MATCH | docs/deliverables/complaints_eval.csv:3 accuracy 0.2212. |
| Q-21 | 21 | "30-item check set" | MATCH | docs/deliverables/complaints_eval.csv:5 n_total 30. |
| Q-22 | 21 | keyword baseline "0.37" on check set | MATCH | docs/deliverables/complaints_eval.csv:5 accuracy 0.3667. |
| Q-23 | 21 | TF-IDF plus logistic "0.30" on check set | MATCH | docs/deliverables/complaints_eval.csv:6 accuracy 0.3000. |

## Summary

- Rows: 23 (one per number, grouped where one clause holds several values).
- MATCH: 18
- MISMATCH: 1
- NO SOURCE: 1
- CONTEXT: 3

Skipped on purpose: question numbers, task and item IDs (T-SA-09, K5, C21 when used as a label), and the "R7" scope label.

Checked against `docs/deliverables/complaints_eval.csv`: keyword 0.27 benchmark / 0.37 check set and TF-IDF plus logistic 0.22 / 0.30, with 104 and 30 rows, all MATCH (Q-18 to Q-23). The benchmark and check-set labels in the answer match the file's eval_set column.

## Open for owners

- Q-02 (line 9): "r about 0.96" for Dynamic World vs Open Buildings has no source in the searched files. The answer also cites docs/requirements/01-specs.md, which is outside the searched paths. Owner should add the recomputed correlation with its file, or remove the figure.
- Q-03 (line 9): "5 pre-registered tests" conflicts with the source. data/K1_FALLBACK_CHECK.md:29 names T1-T3 (3 tests), and data/K1_FALLBACK_CHECK.md:13 adds a seasonal-spread check (4 total). Owner should correct the number to what the file records (3, or 4 with seasonal spread).
- Q-04 (line 9) and Q-01 (line 8): placeholders "[verify in the dataset audit]" and "N quarters / N months" are still in the answers. Owner should fill or remove them before use.
- Q-15 (line 15): "0-100 score" is a hypothetical scale used to explain the choice of levels, not a model output. Owner should keep it labelled as hypothetical.
