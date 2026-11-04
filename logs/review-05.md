# Review 05: team deliverables against the repository data (2026-11-01)

Scope: the teammates' delivered work on main at `f1d6c15` (PR #58): dashboard (T-NA), Track B and inspection files (T-VE), AI component, what-if and docs (T-EL), KPI cards, memo, slides and questions (T-SA). Every number below was recounted from the data in the repository: the v7 ready-data release (`releases/ready-data/SpaceEye_R7_READY_DATA_2026-10-31_v7.zip`, installed with `python -m src.pipeline.setup_review`) and the reports under `data/`. Branch: `fix/team-work-review`.

Method: each area was read in full and recounted with pandas, and the dashboard was run screen by screen on both tracks (Streamlit AppTest, then a browser). Findings are listed with the evidence and the change made. Items not changed are listed at the end with the reason.

## Dashboard (T-NA-02 .. T-NA-07)

| # | Finding | Evidence | Change |
| --- | --- | --- | --- |
| 1 | Screen 5 was always empty | it looked for `app_data/real/SpaceEye_R7_*/what_if`; setup_review installs `ready-data/what_if` | reads the installed release |
| 2 | With the files in place, S3 showed "45 of 12 change level" and cards said "changes level" next to reasons saying levels are unchanged | S3 changes list membership in 45 of 744 rows (28 at capacity 2, 17 at capacity 6) and never a level | screen rebuilt: latest period, one row per compound, list or level change versus its own baseline; S3 by capacity |
| 3 | Backtest table showed `True`/`False` as "What happened", "K2" as "Why", the freeze-date level as "Level reached" (all "Routine", also for C21 which warned 39 months early), and no point-in-time result | the thin `cases.csv` was read through loose column aliases | reads `current/backtest/cases_explained.csv` and `summary.json`; tiles for both readings (1 of 6, 0 of 6) |
| 4 | "B5 plan gap" column was `planned_pct` | `ml_dataset` has no B1-B5 columns | the screen says the flags are not stored |
| 5 | K5 months always "unknown" | the code read a column `K5`; the table has `K5_months` (C18: 45) | fixed; a missing value shows its stated status |
| 6 | "No announced handover date" next to K3 = 57 | it read a `handover_date` column that does not exist | uses `k3_first_deadline` (Dec 2021 for C18) |
| 7 | Track B probability came from one of four methods without saying which | `ml_current` holds four methods for every code and quarter | all four shown side by side for the latest quarter |
| 8 | Wayback images never showed | wrong folder | reads `app_data/images`, then `data/imagery/figures`; Screen 2 now leads with the curated single-capture frames |
| 9 | "Facts verified 1,009 of 1,026" was a fixed number from the spec | the statements table has 57 rows, 35 with a record id and a review verdict | tile computed from the table |
| 10 | K3 and K4 tagged as real | both are computed | tagged derived |
| 11 | Gates shown as "of 10" | the v7 log holds 11 gates (adds `veg_pull_check`) | 10 of 11 passed, 1 flagged |
| 12 | Visit form accepted any typed code | `D03` or `C99` could be saved | code picked from the monitored compounds; no future dates |

## Track B and inspection files (T-VE)

| # | Finding | Evidence | Change |
| --- | --- | --- | --- |
| 1 | The "enterprise" model was tuned on the test split | `grid_search_diagnostic.csv` picks C by test ROC-AUC; the protocol fixes logistic C=0.3, standard scaler, no search | METRICS.md and the method card report only the frozen-protocol models (logistic_combined macro-F1 0.615, recall@4 2 of 4; random 0.335) and mark the enterprise files exploratory |
| 2 | Complaint rules tuned while reading benchmark-test scores | METRICS.md records the rise from 68.3% to 93.3%; 21 rule phrases match only benchmark-test texts | 93.3% is described as not a clean test score; `complaints_30` is described as part of the benchmark test split, not an independent review |
| 3 | Dossiers targeted the wrong compounds with numbers that are not in the data | four of five were level 4 in 2026Q3; activity 0.596/0.603/0.612 appear nowhere in `kpi_values` | see "Inspection files" below |
| 4 | Every dossier named a reviewer and an AI model | the paragraph is the deterministic fallback text; no model call | see "Inspection files" below |
| 5 | Data audit said "33 virtual twins x 45 months" | the dataset is 12 compounds x 15 quarters = 180 rows | corrected; the unsupported lag claim is marked as such |

## AI component, what-if and docs (T-EL)

| # | Finding | Evidence | Change |
| --- | --- | --- | --- |
| 1 | The number check passed a wrong level ("C01 ... level 2" when the source says 4) | tokens were matched against all numbers in the source, not their field | see "Inspection files" below |
| 2 | Wording guards were English only | Arabic "distressed", "completion %" and causal words passed | see "Inspection files" below |
| 3 | PR #58 reopened T-EL-13, saying the label is not stored | `training/ml_dataset_extended` has `label_distress_next_6m`: 180 rows, 13 True, 143 False, 24 empty | board line restored to the reviewer's closure, with this correction |
| 4 | Complaints: TF-IDF accuracy below the trivial baseline | 23 of 104 versus 24 of 104 for always predicting the largest class | note added to T-EL-08 on the board |
| 5 | S1/S2 levels are Track B hypothetical levels | they must be compared with `baseline_hypothetical_level`, not `kpi_values` | stated in the scenario contract and on Screen 5 |
| 6 | User guide and knowledge transfer called Screens 4-5 and the agent unbuilt | both exist | updated |
| 7 | Scenario contract said task EL-14 and the v4 bundle | it is EL-11 and v7 | corrected |

## KPI cards, memo, slides, questions (T-SA)

| # | Finding | Evidence | Change |
| --- | --- | --- | --- |
| 1 | "14-22 assessable quarters before the cutoff" | `assessable_quarters_before_cutoff`: 10, 9, 12, 6, 10, 3, so 3-12 | corrected |
| 2 | Slide 8b: "show which compounds move up in priority" | S1 and S2 change 0 of 216 rows; S3 changes only list membership | demo S3; S1/S2 said to change nothing |
| 3 | Level described without the may-be-complete cap | the cap sets 3 of 12 levels in 2026Q3 (C03, C12 with K2 = 6; C21 with K2 = 2) | cap added to slides, memo (both languages) and cards |
| 4 | "K2 counts only after construction started" | `started` is also set by a published launch or delivery event | start defined as 4 active quarters in a row or a published launch or delivery event |
| 5 | The single backtest hit (C21) read as a stall caught | the diagnosis attributes it to a publication-backdated start and activity lag | caveat added |
| 6 | Boundary answer cited a "required confidence" | no numeric threshold exists | reworded |
| 7 | Track B quoted without the random baseline in the memo and questions | random recall@4 0.335 over 2,000 draws | baseline added |

## Inspection files and verifiers

| # | Finding | Evidence | Change |
| --- | --- | --- | --- |
| 1 | Targets were hard-coded (C01, C02, C04, C07, C10) | in 2026Q3 the cycle list is C18, C07, C14, C03; C01, C02, C04, C10 are level 4 | targets read from `cycle_rank`; four files regenerated, the stale ones removed |
| 2 | Text contradicted the data: "construction stagnation" for active compounds, the may-be-complete reason replaced by "normal range", K5 written as fines due, "None شهر", an invented occupancy-certificate check and a fixed "27 images" | `kpi_values` and the inspection contexts for each code | every sentence takes its value from the context; the stored Arabic reason is reused; K5 is a screening indicator or "no published deadline" |
| 3 | Every file named a reviewer and an AI model | no model call was made | "not reviewed yet" unless a reviewer is given; "deterministic template, no AI model" unless a model wrote the text |
| 4 | Verifiers matched numbers against all numbers in the source and guarded English words only | a swapped level and a wrong K2 passed; Arabic "متعثر" and causal words passed | values checked against their own field; Arabic terms, causal words and non-code names flagged; failed drafts carry a do-not-use banner; tests added |

Independent check of this branch (before push) found and fixed: a missing K2 crashed the report and read as "K2 = 0" (now "unknown"); a published handover read as "no handover date" (now "handover announced, K3 = 0 by rule"); ordinary Arabic words after "compound" were taken as names (a name is now a quoted word, a Latin proper noun or a definite Arabic noun); Arabic level words had no word end. Note: "27 images in the quarter" still appears in the dossiers because it is part of the stored level reason in `kpi_values` (`reason`, `reason_ar`), not template text.

Regenerated values (2026Q3, as written in the files and recounted from `kpi_values`): C18 level 1, K2 0, K3 57, K5 45; C07 level 2, K2 2, K3 0, K5 no published deadline; C14 level 2, K2 0, K3 21, K5 9; C03 level 3, K2 6, K3 0, K5 no published deadline.

Tests on this branch: `uv run --locked --offline pytest -q` gives 302 passed, 2 skipped, 4 failed; the 4 failures (`test_backtest_replay`, `test_portable_review`) need `releases/ready-data`, which was not present in the partial checkout used for this review.

## Not changed, with reason

- `src/analysis/enterprise_pipeline.py` keeps its known issues (a rolling feature without grouping by compound, `qi` used as a feature, input paths that do not exist): its results are withdrawn, and a corrected Track B model needs a new frozen protocol first (AGENTS.md).
- The complaint rules were not re-derived from train and validation texts only; the documents state the limitation.
- `governance-cards.md` and the live Gemini outputs were not checked against data.

## Follow-up (2026-11-02)

The dashboard was rebuilt on the review branch's design (PR #60). Changes to the team deliverables and open findings from that work:

| # | Finding | Evidence | Change |
| --- | --- | --- | --- |
| 1 | The inspection files include generated figures on a real-data track | buyer complaints in each file are labelled simulated (C03 52, C07 65, C14 191, C18 116) | the dashboard offers the files on Track B only; the files are unchanged |
| 2 | The inspection files still carry an English setup note and method wording | "Imagery files are not installed ... Install the T-AH-15 imagery snapshot"; "deterministic template, no AI model" | not changed: needs the file owner |
| 3 | C01 and C18 share the same developer, land area and built-up area | `real/compounds.parquet`: both D14, 161,874 m2 land, 291,373 m2 BUA | not changed: needs the Track A data owner to confirm or correct |
| 4 | The user guide described the removed screens (backtest, data trust) | `docs/deliverables/user-guide.md` | rewritten for the four screens of PR #60 |
