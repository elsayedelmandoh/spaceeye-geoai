# 02-team-roles-and-tasks.md

> Current technical decisions and unresolved approvals: [D1_DECISIONS_CURRENT](D1_DECISIONS_CURRENT.md). Implementation evidence: [partial-task closure](../../data/PARTIAL_TASKS_CLOSURE.md). Main checkboxes show verified implementation; separate review checkboxes remain pending for the human reviewer.

# SpaceEye: Team Roles and Task Board

ACUD AI & Data Readiness Program · Graduation project (D1-D6) · Team of 5
Source of every task: [`01-specs.md`](01-specs.md) (section numbers in brackets, e.g. §2). Data and columns: [current dataset contract](../../data/DATASET_CONTRACT.md). Repo layout: [`08-structure.md`](../project-definition/08-structure.md).

> **Synthetic data - for training only** on every generated table, chart and slide. Codes only (`C..`, `D..`), never a compound or developer name.

---

## Current implementation marks for human review

Updated on 3 November 2026 against 88 current IDs (recounted from the checkboxes; includes PRs #84 to #88 and branch `docs/T-EL-28-video-deck-v2`). Current approved binary scope and existing review records are preserved.

| State | Count | Meaning |
| --- | ---: | --- |
| Main task checked | 71 | Implemented, with evidence; 56 still await assigned review |
| Main task unchecked, open/partial | 15 | Original work/decision still unresolved (includes T-EL-13, partial; T-EL-24 open; T-NA-08 and T-NA-10 partial) |
| Main task unchecked, failed/excluded | 2 | T-NA-05 and T-NA-06: screens removed by owner decision (PR #60, 2 Nov 2026) |
| Review accepted | 15 recorded | Existing review records retained; no new reviewer acceptance inferred |

These are task counts, not effort percentages. Legacy D-day labels remain planning labels; actual program day/dates need team confirmation. Completion prediction is removed; no old three-class requirement is restored from the pasted copy.

## 1. How to use this file

- Task ID format: `T-<member>-<nn>` (`AH` ahmed, `EL` elsayed, `VE` verina, `NA` nada, `SA` salma). IDs never change, even if a task is cut.
- Each task: `- [ ] **ID** [tier] day · task · output · depends on · reviewer`.
- **Team-lead instruction, 28 October 2026:** main `[x]` means implemented and ready for human review. It does not mean reviewed/approved. The separate nested `Review accepted` checkbox is checked only after actual human acceptance with reviewer/date/PR recorded. Partial/open tasks stay `[ ]`; failed/excluded experiments are labelled explicitly.
- Tiers: `[Must]` never cut · `[Should]` cut from the bottom if behind at D4 · `[Could]` cut first. Cut order follows §13.
- One owner per deliverable; every output is reviewed by another member (§10).
- Work on a branch per task (`feat/T-AH-03-k6`), small commits, PR into `main`. Run `make lint` and `make test` before every PR.
- Calendar (§10): D1 = day 6 · D2 = day 7 · D3 = day 8 · day 9 no project work · D4 = day 10 mid-term review + **code freeze** · D5 = day 11 submission · D6 = day 12 presentation.

---

## 2. Who does what

| Member                     | Owns end to end                                                                   | Roles from §10 it covers                                               | Main code                                                                        |
| -------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **ahmed abdelhamid** | **Track A: images → rule → cycle list** (real data)                       | R1 data pipeline + R3 GIS and satellites + R4 Track A rule and backtest | `src/pipeline/`, `configs/data.yaml`                                         |
| **verina fouad**     | **Track B: generated ACUD data → `ml_dataset` → classifier → what-if** | R2 data and generator + R4 Track B classifier and early warning | `src/generator/`, `src/analysis/` |
| **elsayed elmandoh** | **AI component: inspection file agent + verification log + complaints classifier** | R4 agent part | `src/inference/`, `prompts/` |
| **nada shady**       | Dashboard (4 screens after the owner decision of 2 Nov 2026: Priority map, Compound file, District view, Digital twin what if; track switch) + cycle list download + `ops_visits` form   | R5 dashboard part                                                       | `app.py`, `src/dashboard/`                                                   |
| **salma magdy**      | KPI cards, value in EGP, governance docs, memo, presentation, independent checks  | R5 presentation part + doc parts of R1/R2/R3                            | `docs/deliverables/`, `configs/cost_assumptions.yaml`, `configs/kpis.yaml` |

### Hand-off contracts (so nobody waits)

| From → to                     | File (in `app_data/`)                                                                                                                                       | Ready by |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| ahmed → elsayed, verina, nada | `real/kpi_values.parquet` (A, K2-K6, level, reason, cycle_rank, origin, run_id), `real/compounds.parquet`, `real/compound_boundaries.geojson`           | D2       |
| ahmed → nada, salma           | `real/quality_checks_log.parquet`, `backtest/cases.csv`, `backtest/summary.json`                                                                        | D3       |
| elsayed → nada, verina        | `sim/fin_monthly.parquet`, `sim/complaints.parquet`, `ml/predictions.parquet` (code, quarter, p_distressed, p_not_distressed), `ml/metrics.csv` | D3       |
| elsayed → nada                | `scenarios/<S1..S3>/kpi_values.parquet` (same columns as the base)                                                                                          | D4       |
| verina → nada                 | `files/<code>_<quarter>.html`, `ai_verification_log.csv`                                                                                                  | D4       |

Until a contract file exists, consumers build on the first-build outputs (commit `a0f03fd`) with the same column names.

---

## 3. Shared tasks (whole team)

- [ ] **T-ALL-01** [Must] D1 · Sign the D1 decisions (§14): R7 only, light twin, two tracks, worst-of-signals rule incl. K6 and B triggers, K5 definition + assumed fine rate, binary label, thresholds frozen, boundary ≥ 80%, codes only, generated label text · signed list in `docs/requirements/05-project-compass.md` · reviewer: all **Partial; see [remaining work](../REMAINING_TEAM_TASKS.md).**
- [ ] **T-ALL-02** [Must] D1 · Fill open items 2 and 4 (§16): today's program day; how many of the 22 coded compounds and of the 8 backtest cases are in R7 · updated §16 + §10 · owner: ahmed (item 4), salma (item 2) **Partial; see [remaining work](../REMAINING_TEAM_TASKS.md).**
- [ ] **T-ALL-03** [Must] D4 · Mid-term review (10 min) rehearsed once · owner: salma
- [ ] **T-ALL-04** [Must] D5 · Cross-review: each member reviews one other member's deliverables end to end (ahmed ↔ elsayed, verina ↔ nada, salma reviews all docs) · review notes in PRs
- [ ] **T-ALL-05** [Must] D5 · Two timed rehearsals + backup video of the demo · owner: salma

---

## 4. ahmed: Track A end to end (real data)

Goal: one command (`python -m src.pipeline.run_all`) builds the R7 tables, A, K2-K6, levels, reason sentences, cycle list, backtest and 10 gates, twice identically.

### D1: scope and config

- [x] **T-AH-01** [Must] D1 · Confirm R7 boundaries (a boundary with a reviewed confidence label from the location audit; no numeric threshold is applied) and count R7 compounds (open item 4) · `compounds.district` checked, count in §16 · depends: - · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../../data/DATASET_CONTRACT.md).
  - [x] Review accepted (logs/review-01.md, 2026-10-29; findings fixed in f63a712 and c23a860, review recorded in 4822040).
- [x] **T-AH-02** [Must] D1 · Write config before any result: `cycle_capacity` ≈ a third of R7, K6 thresholds (`k6_l2: 13`, `k6_l1: 24`: level 2 from 13 months, level 1 above 24), K5 grace (`fines.grace_months: 12`), R7 filter key (`scope_districts`), in `configs/data.yaml` with a dated comment · depends: T-AH-01 · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../../data/DATASET_CONTRACT.md).
  - [x] Review accepted (logs/review-01.md, 2026-10-29; findings fixed in f63a712 and c23a860, review recorded in 4822040; the before-any-result claim rests on the setter's own statement of 2026-10-29, not on git).
- [x] **T-AH-03** [Must] D1 · Filter R8 out of every built table in `build_real` (audited R8 files stay untouched in `real_data/`) + test that no R8 code reaches `kpi_values` · depends: T-AH-02 · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../../data/DATASET_CONTRACT.md). Filter: `in_scope` in `src/pipeline/codify.py`; scope audit: `scope_checks` in `src/pipeline/release.py`. Tests in `tests/test_scope.py`: `test_in_scope_drops_r8_rows`, `test_scope_checks_pass_when_kpi_values_hold_only_known_codes`, `test_scope_checks_fail_when_kpi_values_hold_an_r8_code`, `test_scope_checks_fail_when_compounds_hold_an_r8_district` (fabricated tables; no workspace data). The filter runs in `codify`, not `build_real`.
  - [x] Review accepted (logs/review-01.md, 2026-10-29; findings fixed in f63a712 and c23a860, review recorded in 4822040).

### D2: indicators, levels, cycle list

- [x] **T-AH-04** [Must] D2 · K6 never-started clock in `kpis.py`: months since first published launch/promise with no 4-quarter activity run; level 1 if > 24, level 2 if 13-24 (§2) + tests · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../../src/pipeline/kpis.py). Tests: tests/test_pipeline.py::test_launch_does_not_confirm_observed_construction_and_k6_waits_for_publication, tests/test_pipeline.py::test_k6_does_not_treat_missing_or_unassessable_history_as_no_start, tests/test_pipeline.py::test_start_evidence_ignores_future_publications_and_future_event_dates, tests/test_pipeline.py::test_month_arithmetic_and_k5_k6_boundaries_are_pinned; tests/test_spec_data.py::test_k6_priority_and_promise_publication_fallback_have_no_future_leakage.
  - [x] Review accepted (logs/review-02.md, 2026-10-29; findings fixed in c837b52, 6c74934, 7e359c4 and 53db98a; review recorded in ea4cf4d; K6 and K3 keep nearest-month rounding and the strict K6 gap rule as recorded in 01-specs section 2; real-data run pending).
- [x] **T-AH-05** [Must] D2 · K5 fine-eligible months (real part): months past first deadline with no start + months past 12-month grace (K3 > 12); shown, never sets the level + test · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../../src/pipeline/kpis.py). Tests: tests/test_spec_data.py::test_fine_union_retains_exposure_and_does_not_double_count_grace, tests/test_spec_data.py::test_missing_contract_deadline_or_no_start_evidence_is_not_zero_fine; tests/test_pipeline.py::test_month_arithmetic_and_k5_k6_boundaries_are_pinned.
  - [x] Review accepted (logs/review-02.md, 2026-10-29; findings fixed in c837b52, 6c74934, 7e359c4 and 53db98a; review recorded in ea4cf4d; K5 keeps calendar-month arithmetic, documented against K3 in 01-specs section 2; real-data run pending).
- [x] **T-AH-06** [Must] D2 · Level rule = worst of K2, K3, K6 + "may be complete" cap at 3 + "not started" / "not assessable" (§2 table); update `test_level_is_the_worst_signal...` for K6 · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../../src/pipeline/kpis.py). Tests: tests/test_pipeline.py::test_level_is_the_worst_signal_and_may_be_complete_caps_at_3, tests/test_pipeline.py::test_not_assessable_kpi_row_has_no_level_and_keeps_lineage; tests/test_spec_data.py::test_k6_priority_and_promise_publication_fallback_have_no_future_leakage.
  - [x] Review accepted (logs/review-02.md, 2026-10-29; findings fixed in c837b52, 6c74934, 7e359c4 and 53db98a; review recorded in ea4cf4d; new "start unknown" label added for unknown K6; real-data run pending).
- [x] **T-AH-07** [Must] D2 · Reason sentence: one template, English in logs, **Arabic** for the committee (`reason_ar` column), filled by code, codes only (§2) + test on the two examples · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../../src/pipeline/kpis.py). Tests: tests/test_pipeline.py::test_reason_matches_spec_examples; tests/test_partial_tasks.py::test_arabic_reason_keeps_unknown_deadline_and_missing_start_distinct.
  - [x] Review accepted (logs/review-02.md, 2026-10-29; findings fixed in c837b52, 6c74934, 7e359c4 and 53db98a; review recorded in ea4cf4d; Arabic wording still needs a native-speaker review before committee use).
- [x] **T-AH-08** [Must] D2 · Cycle list export: top N with level 1-3, ordered by level, then K2, then K3 descending, then code (spec section 2), CSV (Arabic reason, level as a word) for the as-of quarter · `app_data/real/cycle_list_<asof>.csv` · depends: T-AH-04..07 · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../../src/pipeline/kpis.py). Tests: tests/test_pipeline.py::test_rank_cycle_takes_top_capacity_levels_1_to_3_in_spec_order; tests/test_spec_data.py::test_capacity_scenarios_only_select_eligible_rows.
  - [x] Review accepted (logs/review-02.md, 2026-10-29; findings fixed in c837b52, 6c74934, 7e359c4 and 53db98a; review recorded in ea4cf4d; run_all owns the real cycle-list CSV; real-data run pending).
- [x] **T-AH-09** [Must] D2 · `kpi_values` carries `origin`, `run_id`, `computed_at` for every new column (K5, K6, reason_ar); hand off to elsayed/verina/nada (contract §2) · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../../src/pipeline/kpis.py). Tests: tests/test_pipeline.py::test_not_assessable_kpi_row_has_no_level_and_keeps_lineage.
  - [x] Review accepted (logs/review-02.md, 2026-10-29; findings fixed in c837b52, 6c74934, 7e359c4 and 53db98a; review recorded in ea4cf4d; KPI_ORIGINS matches the recorded real schema but the separation gate was not run on the external F: data).

### D3: backtest, gates, reproducibility

- [x] **T-AH-10** [Must] D3 · Re-run the frozen-clock backtest on R7 only (backtest variant of A without overlapping plots); per case: what happened / why / what next + one competing explanation rejected with a number; counts only, no % · `backtest/cases.csv`, `summary.json` · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../../data/BACKTEST_CURRENT.md).
  - Files: [cases.csv](../../releases/ready-data/backtest/cases.csv), [saved summary.json](../../releases/ready-data/backtest/summary.json), [prepared-input replay](../../releases/ready-data/backtest/README.md).
  - [x] Review accepted (logs/review-03.md, 2026-10-29; findings fixed in 2a77ba4, 3f16253 and 236e051; review recorded in 7de6b7f; the frozen-clock line appears in data/BACKTEST_CURRENT.md only after the real-data regeneration in T-AH-22; the per-case explanations remain one shared template pending the owner's decision).
- [x] **T-AH-11** [Must] D3 · 10 gates pass or flag with dimension, owner, decision (§8); `no_names` scans every output incl. new CSVs; `separation` covers new columns · `quality_checks_log.csv` (program template) · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../../data/R1_REPORT.md).
  - [x] Review accepted (logs/review-03.md, 2026-10-29; findings fixed in b3e3ed8, 77fed1b and 236e051; review recorded in 7de6b7f; the gates are not yet run on the real data (T-AH-22); .tsv files are not scanned; what a STOP leaves on disk is an open owner decision).
- [x] **T-AH-12** [Must] D3 · Quality report with an "impact on the indicator" column, from the saved ten-gate checks (`data_completion/quality_checks.csv`; the Track A record stays `real/quality_checks_log.parquet`, same run id) · `docs/deliverables/quality-report.md` · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../deliverables/quality-report.md).
  - [x] Review accepted (logs/review-03.md, 2026-10-29; findings fixed in 236e051 and bfba593; review recorded in 7de6b7f; decision recorded 2026-10-29: the report is built from `data_completion/quality_checks.csv`, the Track A run keeps `real/quality_checks_log.parquet`, and both carry the same run id; the committed report is regenerated only in T-AH-22).
- [x] **T-AH-13** [Must] D3 · Two runs identical: run `run_all` twice, compare `manifest.csv` sha; add a `make run` target · depends: T-AH-22 (a fresh two-run pass on the real data) · reviewer: elsayed **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/FULL_TRACK_A_REPRODUCIBILITY.json).
  - Open before acceptance: a fresh two-run PASS on the current commit must be run on ahmed's F: machine (step 1 of T-AH-22: `team_run --full`, then `full_repro`), because the committed result predates the path change and records no hash or revision. `full_repro` now stores the manifest hash, run id, git revision and `computed_on`, so the new result can be tied to a commit. Until it exists, "two runs identical" must not be relied on in the slides or the memo, and this Review accepted box stays unticked.
  - Update 2026-10-30: fresh two-run PASS on ahmed's F: data at git revision 75a581a (branch fix/data-v6): 301 equal artifacts, protected simulation/history unchanged, manifest sha256 b4c86dee…, run id R1-1846440cf3, computed_on 2026-10-30 ([evidence](../../data/FULL_TRACK_A_REPRODUCIBILITY.json)). Both runs share one process (review-03 M11 option not taken). Review pending.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-AH-14** [Should] D3 · Fallback ready: if A fails on new quarters, K1 path documented and switchable in config (§13) · reviewer: elsayed **Implemented; review pending.**
  - Evidence: `activity.apply_source` (switch `activity.source: k1`), tests in `tests/test_activity_fallback.py`, effect on the current data in [K1_FALLBACK_CHECK.md](../../data/K1_FALLBACK_CHECK.md) (3 of 12 levels change at 2026Q3; backtest 2 of 6 instead of 1; not a reason to switch), doc section in [technical-track-a.md](../deliverables/technical-track-a.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).

### D3-D4: images for the compound file

- [x] **T-AH-15** [Should] D3 · Check Esri Wayback terms; then 2 Wayback images per R7 compound (before/after) with capture date + attribution · `app_data/images/<code>_{before,after}.jpg` + `images.csv` · reviewer: elsayed **Implemented; review pending.**
  - Evidence: [use/rebuild guide](../../data/imagery/README.md), [source/method comparison](../../data/IMAGERY_COMPARISON.md), [pair index](../../data/imagery/images.csv), [validation](../../data/IMAGERY_VALIDATION.json). Local figures: 24 inspector-pair rows, 100 distinct Wayback observations and 528 quarterly Sentinel context figures. Esri pixels/report ZIP stay outside Git; metadata, hashes, supported acquisition and portable installation code are provided. Distinct-year pair rule and publication cutoffs are documented/tested. Images are inspector context, never model X or proof of finishing; current numerical v6 is unchanged by imagery.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-AH-16** [Should] D3 · Open Buildings height 2016-2023 + 2024 v4 estimate (context only; no fixed error guarantee) and vegetation series ready per compound for screen 2 (height is context, never in the level) · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../deliverables/annual-context.md).
  - [x] Review accepted (logs/review-03.md, 2026-10-29; findings fixed in 236e051; review recorded in 7de6b7f; coverage figures come from data/ANNUAL_CONTEXT_COVERAGE.csv, not regenerated here).
- [x] **T-AH-17** [Could] D4 · Finishing vision-model test (Qwen-VL on Wayback): pass condition ≥ 75% agreement on ~50 held-out compound-images labelled blind by salma (T-SA-12); log in `team_ideas.md`; **cut at D4 if not passed**; flag in the inspection file only · reviewer: elsayed **Done 30 October 2026 by owner decision; review pending.** The earlier open-model run (Qwen3-VL, 0.559) was scored against labels from another AI rater, not a person. Final: the assistant is the finishing vision model. Blind outputs on a 17-area, 114-interval sub-metre kit (2016-2025) are frozen (A 73, B 22, C 19). No human reference was available, so accuracy is not measured; the owner accepts the model on trust. Finishing is a flag in the inspection file only, never in the warning level.
- [x] **T-AH-18** [Could] D4 · Construction stage test on Google heights 2016-2023 with free satellite data (first roof uniformity; then land / under construction / complete) against a condition written before the test; cut at D4 if not passed · reviewer: elsayed **Done 30 October 2026; review pending.** (1) Roof uniformity with a Sentinel-1 radar arm failed (balanced accuracy 0.495 / 0.551 / 0.543 against 0.75). (2) A pre-registered coarse stage test passed: land / under construction / complete (complete = visible greenery, paved roads and finished buildings) per 500 m block and year, 220 blocks outside R7, blind visual labels (two-pass kappa 0.78), free satellite features plus Google heights; test macro recall 0.82 (2025 rows 0.77), independently re-computed. Caveats: labels are from AI raters, not field checks; under construction is weak in 2024-2026 (3 of 8 test rows). On R7 the layer gives the start of construction (2020-2022) but does not detect completion: landscaped gardens inside R7 compounds are visible in sub-metre Wayback imagery (e.g. C12 in 2025) yet too small for the 10 m satellite features, so completion in R7 is judged on sub-metre imagery. Final R7 stage table (98 official sub-metre figures 2016-2025, blind visual labels, second look 19 of 20 agree; 10 m satellite, ALOS PALSAR and Sentinel-1 radar, Google heights and night lights as context): construction start 2020 (C12, C18, C21), 2021 (C01, C02, C03, C10, C17), 2022 (C14, C19), 2024 (C04, C07); none of the 12 complete by 2025-07-23 (owner definition: finished buildings, visible greenery, paved roads). Context only; it does not enter the warning level.

### D4-D5: freeze and hand over

- [x] **T-AH-19** [Must] D4 · Code freeze for Track A; tag the commit; `run_all` is the one run command used in the presentation (deliverable 10) · reviewer: elsayed **Implemented 30 October 2026; review pending.** Tag `track-a-freeze-2026-10-30` on the main merge commit of `chore/lint-cleanup` (258 tests and ruff pass). `make run` (`team_run --full`, which calls `run_all`) is the one run command.
- [x] **T-AH-20** [Must] D5 · Technical docs for Track A + monitoring plan (quarterly recompute, who runs `run_all`, what to check) · `docs/deliverables/technical-track-a.md` · reviewer: salma **Done; review accepted.**
  - Evidence: [implementation/output](../deliverables/technical-track-a.md).
  - [x] Review accepted (logs/review-03.md, 2026-10-29; findings fixed in 9fc8763 and f9be3f9; review recorded in 7de6b7f; the quarterly procedure has not been run end to end on the real data).
- [x] **T-AH-21** [Must] D5 · Knowledge transfer pack, one page (deliverable 9) · `docs/deliverables/knowledge-transfer.md` · reviewer: salma **Done; review accepted.**
  - Evidence: [implementation/output](../deliverables/knowledge-transfer.md).
  - [x] Review accepted (logs/review-03.md, 2026-10-29; findings fixed in f9be3f9; review recorded in 7de6b7f; the run command was not executed here because the real data is not available).

### D4: real-data run on the F: drive (only ahmed has the data, about 5 GB, so it cannot be run elsewhere)

- [x] **T-AH-22** [Must] D4 · On ahmed's machine with the F: data (WSL: `sudo mkdir -p /mnt/f && sudo mount -t drvfs F: /mnt/f`), on the latest `feat/ml`: (1) `uv run --locked --offline python -m src.pipeline.team_run --full`, then `uv run --locked --offline python -m src.pipeline.full_repro`; (2) regenerate and commit `data/BACKTEST_CURRENT.md` (with the frozen-clock result), `docs/deliverables/quality-report.md`, `data/FULL_TRACK_A_REPRODUCIBILITY.json` (manifest hash, run id, git revision), `data/R1_REPORT.md`, the current model metrics and EW reports; (3) confirm the separation and no_names gates on the real `kpi_values`; (4) run the v2 Stage 1 evaluation of `data/EW_PROTOCOL_V2.md` (check `sha256sum -c EW_PROTOCOL_V2.sha256` first; set `candidates.variant: v2` and `candidates.no_height_ablation: true`; v1 results stay labelled v1); (5) send the numbers, not the data, to the team · `data/*`, `docs/deliverables/quality-report.md`, `data/V2_MODEL_*`, `data/EW_REPORT_V2.md` · depends: coder fixes for review-03 committed, v2 protocol commit 8a16575 · reviewer: elsayed **Implemented; review pending.**
  - Evidence (2026-10-30, branch fix/data-v6). Run on Windows with the F: data rather than WSL; `.gitattributes` now keeps the frozen protocols LF so the v2 hash check passes on Windows.
    - (1) `team_run --full` and `full_repro`: PASS. A crash in the backtest step of a full rebuild (activity merged twice) is fixed in run_all. Reproducibility record: [FULL_TRACK_A_REPRODUCIBILITY.json](../../data/FULL_TRACK_A_REPRODUCIBILITY.json).
    - (2) Regenerated: [BACKTEST_CURRENT](../../data/BACKTEST_CURRENT.md) (frozen clock true at 2021Q4, 2023Q2, 2024Q4 and 2025Q3; 1 of 6 after start), [quality report](../deliverables/quality-report.md), [R1](../../data/R1_REPORT.md), [R2](../../data/R2_REPORT.md), current metrics and the EW report; ready data v6.
    - (3) separation and no_names: PASS on the real `kpi_values`.
    - (4) v2 Stage 1 (v2a, no height): [report](../../data/EW_REPORT_V2.md) and [side by side with v1](../../data/EW_V2A_VS_V1.md). v1 stays primary, as the protocol requires; boosting_satellite falls from 4 of 4 to 1 of 4.
    - (5) Numbers for the team: in the PR description.
  - [ ] Review accepted (record reviewer, date and PR after actual review).

---

## 5. verina: Track B end to end (generated data)

Goal: generated ACUD data for R7 → one `ml_dataset` (compound × quarter) → binary classifier → probabilities in the compound file + early-warning comparison + what-if scenarios S1-S3. Track B reads Track A outputs and never redoes image work.

### D1: protocol before any run

- [x] **T-VE-01** [Must] D1 ? Resolved implementation: retire the unattributed historical percentage claim; current method/view/denominator recorded in EW_REPORT_CURRENT.md ? approved scope: BINARY_SCOPE_DECISION.md ? reviewer: ahmed **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/BINARY_SCOPE_DECISION.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-VE-02** [Must] D1 · Write `EW_PROTOCOL.md` **before** the R7 run: label (2 classes, next 6 months), split (time; developer holdout only if ≥ 3 test developers), metrics (per-class recall, macro-F1, recall@N for `distressed` vs random top-N, 2,000 draws), pass condition · `app_data/EW_PROTOCOL.md` + wording copied to §0 · reviewer: salma **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/EW_PROTOCOL_CURRENT.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-VE-03** [Must] D1 · Assumed monthly fine rate for K5 in EGP (open item 3) in `configs/data.yaml` with `assumption: true` · reviewer: ahmed **Implemented; review pending.**
  - Evidence: [implementation/output](../../configs/data.yaml).
  - [ ] Review accepted (record reviewer, date and PR after actual review).

### D2: generator on R7

- [x] **T-VE-04** [Must] D2 · Regenerate on R7 only from ahmed's `kpi_values` (stories from real signals, reports equal real announced %, electricity meters only) (§5) · `sim/fin_monthly.parquet`, `sim/complaints.parquet`, private `answer_key` · depends: T-AH-09 · reviewer: ahmed **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/R2_REPORT.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-VE-05** [Must] D2 · 6 planted defects caught by the gates + hard and calibration realism checks pass · `realism_checks.csv`, `defects_log.csv` · reviewer: ahmed **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/DEFECT_AUDIT_CURRENT.json).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-VE-06** [Must] D2 ? Binary next-six-month distressed/not_distressed labels with censoring; boolean source label and equivalent categorical extended export; dictionary and regression checks ? src/pipeline/complete_data.py ? reviewer: verina **Implemented; review pending.**
  - Evidence: [implementation/output](../../src/pipeline/complete_data.py).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-VE-07** [Must] D2 · Data dictionaries for every generated table (column, type, unit, origin 🟠) · `dictionaries/*.md` · reviewer: salma **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/dictionaries/README.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).

### D3: ml_dataset and classifier

- [x] **T-VE-08** [Must] D3 · Build `ml_dataset` (1 row = compound × quarter, columns from the current DATASET_CONTRACT.md): X = Track A outputs + K3, K5, K6 + B1-B5; y = binary label; no feature reads `answer_key`; statements filtered by `published_date` · `app_data/ml/ml_dataset.parquet` + leakage test (corrupt data after the cutoff, features unchanged) · depends: T-VE-04, T-VE-06 · reviewer: ahmed **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/DATASET_CONTRACT.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-VE-09** [Must] D3 · B1-B5 triggers (§2) + K5 in EGP (eligible months × assumed rate × land value, 🟠) + rule with ACUD data (any of B1/B2/B3/B5 → level ≥ 2; B1 and K2 ≥ 2 → level 1; B4 context only) · reviewer: ahmed **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/IMPLEMENTED_DATA_SPEC.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-VE-10** [Must] D3 · Logistic regression baseline (never cut): per-class recall, macro-F1, recall@N for `distressed` vs random, counts as n of m · `ml/metrics.csv`, `ml/predictions.parquet` · reviewer: verina **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/CURRENT_MODEL_METRICS.csv).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-VE-11** [Should] D3 · Gradient boosting vs logistic, same split and metrics; if a model scores perfectly, document limitations; do not tune data/noise after viewing the test (current binary protocol) · reviewer: verina **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/CURRENT_MODEL_METRICS.csv).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-VE-12** [Must] D3 · Early-warning comparison on R7: images alone vs images + ACUD data vs random, plus the rule itself; check on the 8 real `eval_outcomes` (check set only) · `app_data/EW_REPORT.md` · reviewer: ahmed **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/EW_REPORT_CURRENT.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).

### D4: freeze and hand over (deliverables 5, 9, 10, 12 — method card, knowledge transfer, presentation, data request)

- [x] **T-VE-13** [Must] D5 · Method card for the Track B classifier (data, label, split, metrics, limits: generated data, ~150 rows, learns the generator) (deliverable 5) · `docs/deliverables/method-card.md` · reviewer: salma **Implemented; review pending.**
  - Evidence: [implementation/output](../deliverables/method-card.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-VE-14** [Must] D5 · ACUD data request list by impact (§12, deliverable 12) · `docs/deliverables/data-request.md` · reviewer: salma **Implemented; review pending.**
  - Evidence: [implementation/output](../deliverables/data-request.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).

---

## 6. elsayed: AI component + D4 digital twin what-if

Goal: inspection files for 5 compounds (AI) + scenario runner / what-if (D4: T-EL-10/11/12/13/14 / S1-S3). Reads `kpi_values`; never overwrites base run.

- [x] **T-EL-01** [Must] D1 · Confirm `GEMINI_MODEL` and the call budget; prompts in `prompts/system/` and `prompts/templates/` · reviewer: elsayed **Implemented; review pending.**
  - Evidence: `configs/ai.yaml` (model `gemini-3.1-flash-lite`, 30 calls in total, 3 per file, 1024 output tokens, temperature 0, approval approved by the owner on 2026-10-29), `src/inference/ai_config.py` (loader, approval guard, call counter; the key is read only from the environment or the git-ignored `.env` and is never echoed), `prompts/system/inspection_agent.md`, `prompts/templates/inspection_paragraph.md`, `prompts/templates/visit_questions.md`. Tests: `tests/test_ai_config.py` (fabricated values only). Caveat: the API key must be present in the git-ignored `.env` of the machine that runs generation; it cannot be checked from the repo.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-02** [Must] D2 · Agent tools as plain Python: `get_facts` (register + record_id + link), `get_kpis` (A, K2-K6, level, series), `get_images` (two Wayback images + capture date), `get_rules` (Decree 2184 articles) (§6 A) · `src/inference/tools.py` + tests on first-build data · reviewer: ahmed **Implemented; review pending.**
  - Evidence: [implementation/output](../../src/inference/tools.py). Tests: `tests/test_inference_tools.py` (quarter-end cutoff, unknown stays None, missing-image status, article filter, prepared-release real schema). T-AH-15 adds optional local before/after images with capture/publication cutoffs and offline HTML integration; absent images remain explicitly missing. See the [imagery handoff](../../data/imagery/README.md). The separate full source/v2 run remains T-AH-22; imagery does not complete it.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-03** [Must] D3 · Inspection file template filled by code (what happened · why + rejected explanation · what it means · what we do: action, owner, date, escalation trigger); works without the LLM · reviewer: salma **Implemented; review pending.**
  - Evidence: [implementation/output](../../src/inference/inspection_file.py). `build_inspection_file` fills what happened, why (facts with record ids and links, numeric rejected explanations, open explanations), what it means and what we do (action by level, owner role, due date from the quarter end, escalation trigger) with no model call; an optional AI paragraph goes only into a separate draft field. Tests: `tests/test_inspection_file.py` (all seven states, determinism, forbidden wording, evidence ids), plus `get_kpis` now returns the compound code. Caveats: the Arabic sentence templates need a native-speaker review; due-date constants and owner roles are proposals for the team to confirm; the final HTML/PDF with model and time is T-EL-06.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-04** [Should] D3 · Gemini writes one paragraph from attached facts only + 3 questions for the visit · reviewer: elsayed **Implemented; review pending.**
  - Evidence: [implementation/output](../../src/inference/narrative.py). `draft_narrative` renders the two prompt templates from the attached facts only, checks approval and the call budget before each call, and returns `{paragraph, questions}` for `build_inspection_file(llm=...)`, or `None` on any failure (not approved, budget used, missing key, client error, not exactly 3 questions, a number or code not in the facts, forbidden wording), so the template-only file still works. Tests: `tests/test_narrative.py` (fake client, fabricated data, no network). First real call 2026-10-30 (`gemini-3.1-flash-lite`, 5 compounds at 2026Q3, 2 calls each plus one earlier single-compound trial): 3 of 5 produced a paragraph and 3 questions (C01, C04, C07) with no wrong number, date or code; 2 (C02, C10) were rejected by the built-in check (a number, date or code not in the facts) and stayed template-only, as designed. Caveat: this is one run on 5 compounds, not an accuracy measure; the Arabic output still needs a native-speaker read (it mixed in the English words "priority level").
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-05** [Must] D3 · Verifier: every number, date and code matched against the source JSON; causal words ("because", "بسبب") flagged for manual review; verdicts logged · `ai_verification_log.csv` (correct / wrong number / unsupported claim / missing context) + test · reviewer: elsayed **Implemented; review pending.**
  - Evidence: [implementation/output](../../src/inference/verifier.py). `verify_text` matches every number, date, quarter and code of an AI text against the source JSON (Arabic-Indic digits normalised), flags causal wording ("because", "بسبب" and others) for manual review, and gives each token a verdict (correct / wrong number / unsupported claim / missing context); `append_log` writes tokens only, never the text, to `app_data/ai_verification_log.csv`. Tests: `tests/test_ai_verifier.py` (fabricated data). Caveats: the older `src/inference/verify.py` stays for its own tests; the verifier now runs inside the report builder and the CLI option `--log-path` appends token-only verdict rows; the 2026-10-30 live run logged 45 rows for C01, C04 and C07 to `app_data/ai_verification_tokens.csv` (git-ignored; a separate file because the older `app_data/ai_verification_log.csv` from the earlier module has a different column layout): 33 correct, 12 missing context, 0 wrong number, 0 unsupported claim. The 12 are one "text states no level" row for the paragraph and each of the 3 questions per file; a question need not state a level, so this check should run once per file, not per question (open); the two functions the merge `91c3940` dropped from `tools.py` are restored, so `tests/test_inspection_tools.py` passes again; `generate_inspection_brief` is restored in `generate.py` as a wrapper over the guarded narrative step with a deterministic fallback, so `tests/test_inference.py` passes again (full suite: 216 passed, 1 skipped); its test only imports the function and never calls it.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-06** [Must] D4 · Arabic HTML/PDF output with footer "Drafted by AI, reviewed by [name]" + model + time; 5 stored files for the presentation (deliverable 11) · `app_data/files/` · depends: T-AH-15 · reviewer: salma **Implemented; review pending.**
  - Evidence: [implementation/output](../../src/inference/inspection_report.py). `build_report` builds the inspection file, optionally drafts the paragraph and 3 questions through the guarded narrative step, checks them with the verifier, and writes one RTL Arabic HTML per compound; `python -m src.inference.inspection_report --quarter 2026Q3 --codes C01 C02 C04 C07 C10` wrote the 5 files to `app_data/files/<code>_2026Q3.html` (git-ignored, local). Tests: `tests/test_inspection_report.py` (fabricated data, no network). Footer: "Drafted by AI, reviewed by [reviewer]" with model and time appears only when an AI paragraph is present; otherwise the file says it was prepared by code. The reviewer stays a literal placeholder until a real reviewer is passed. Caveats: the 5 files were generated without a model call, so they carried no AI paragraph, model or time at first; after the live run of 2026-10-30 (`--use-model`) C01, C04 and C07 carry the AI draft with model `gemini-3.1-flash-lite` and time in the footer, while C02 and C10 stayed template-only because the draft failed the number/date/code check; no real images locally (explicit missing notice; embedding is off by default and such HTML stays local); no PDF tool is installed, so PDF is browser print of the HTML (print CSS provided); the Arabic wording needs a native-speaker review; the older teammate files `*_inspection.html` are untouched and still name a person as reviewer.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
  - Image-rights condition: generated HTML embedding Esri pixels stays local for attributed educational review; never commit or redistribute it. See [imagery rights](../../data/imagery/README.md).
- [x] **T-EL-07** [Should] D3 · Complaints masking: regex on numbers and names **before** any model (Law 151/2020); `assert_zero_phones` passes + test · reviewer: elsayed **Implemented; review pending.**
  - Evidence: [implementation/output](../../src/pipeline/privacy.py).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-08** [Should] D4 · Complaints classifier: 5 classes (delay, stoppage, payment, quality, other) vs keyword baseline; extra test on `complaints_30.csv`; state that texts we wrote do not prove real accuracy · reviewer: elsayed **Implemented; review pending.**
  - Evidence: [implementation/output](../../src/inference/complaints_eval.py), scores in [complaints_eval.csv](../deliverables/complaints_eval.csv). Local only (no provider call); text is masked before the TF-IDF model; the fixed keyword baseline was written before scoring. Results on the 104-row benchmark test split / the 30-item check set (accuracy): keyword baseline 0.27 / 0.37, TF-IDF + logistic 0.22 / 0.30, the teammate's hand-tuned phrase classifier 0.93 / 0.93. Tests: `tests/test_complaints_eval.py` (fabricated frames, plus the 30-row check set). Caveats: all texts were written by the team (generated), so these scores do not prove accuracy on real complaints; the 30-item check set is a subset of the benchmark test split (30 of 30 overlap), so it is not independent; the hand-tuned classifier uses phrases copied from the corpus and is optimistic, shown for reference only; the benchmark assigns disjoint template families to train and test, which explains the low TF-IDF score (the lane's reading of the release data contract, not re-derived here); the existing `complaints_metrics.csv` is left as it was.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-09** [Must] D5 · Risks and responsible-AI note (Law 151/2020, who sees what, fairness limits, misuse) with elsayed (deliverable 6) · `docs/deliverables/responsible-ai.md` · reviewer: salma **Implemented; review pending.**
  - Evidence: [implementation/output](../deliverables/responsible-ai.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).

### D4: digital twin what-if

- [x] **T-EL-10** [Must] D4 · Scenario runner: change one input from the as-of quarter onward, re-run generator + rule, never overwrite the base run · `src/generator/scenarios.py` + determinism test · reviewer: ahmed **Implemented; review pending.**
  - Evidence: [implementation/output](../../src/generator/scenarios.py).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-11** [Must] D4 · S1 dollar shock (USD/EGP +30%), S2 collections drop (−25% for 6 months), S3 capacity N ± 2 (re-rank only) · `scenarios/S1..S3/` + "who moved up and why" table · reviewer: nada **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/SCENARIO_CONTRACT_CURRENT.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-12** [Could] D4 · S4 material cost +40%, S5 grace 12 → 6 months · reviewer: nada **Implemented; review pending.** S4: material cost +40% from the shock month (`src/generator/scenarios.py`, `cost_multiplier_for`; tests `tests/test_scenarios_s4.py`). S5: the warning clock runs with a 6-month grace (`generator.scenarios.grace_months_s5` in `configs/data.yaml`; `complaint_grace_months` stays 12) through `observe.acud(..., grace_months)` and `simulate.grace_shortened_table()`, which writes no base outputs (tests `tests/test_grace_shortened.py`). Design chosen with verina: S5 feeds the warning clock. Caveat: the real-data run of S5 (base vs S5 digest) has not been done. Branch `feat/T-EL-12-on-ml` (commits `d33187b`, `d4c4f46`); full suite 317 passed, 1 skipped on that branch.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [ ] **T-EL-13** [Could] D4 · FPMI and SAF tests on generated data, conditions written before the run, logged in `team_ideas.md` · reviewer: ahmed **Partial; protocol approved by the team lead (thresholds FPMI rho > 0.20, SAF rho < -0.15; missing-progress rule: velocity only between reported months), hashed and committed on branch `feat/T-EL-13-fpmi-saf-protocol`. Runner built and hash-checked. Results BLOCKED: the Track B label `label_distress_next_6m` is built by the full pipeline (`src/analysis/early_warning.py` `prepare()`) and is not stored in the installed data. No result is recorded until the label is available from that pipeline.**
- [x] **T-EL-14** [Must] D4 · Code freeze for Track B; one command builds Track B after `run_all` · reviewer: ahmed **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/BINARY_SCOPE_DECISION.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).

### Added 2 November 2026: dashboard, presentation, chatbot and media (owner: elsayed)

- [x] **T-EL-21** [Should] D5 · Search, filters and map click on screen 1 (T-NA-11/12/13 scope) · `app.py`, `src/dashboard/insights.py` + tests · reviewer: ahmed **Implemented; review pending.** Merged in PR #87; real-browser map click checked on real data.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-22** [Must] D5 · Deck rebuilt to the instructor rubric: 12 minutes, lines for as-is, transition and documentation, the committee decision as the closing slide · `docs/deliverables/01-presentation/presentation.md` + HTML · reviewer: salma **Implemented; review pending.** Merged in PR #84 (12 slides, speaker notes total 12:00). The timed rehearsal stays under T-ALL-05.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-23** [Should] D5 · Compound details on map click: a sidebar panel with level, K2, K3, K6, reason, next action and the latest capture, each part opening a deeper view (compound file, signal history, images) · `app.py` + test · reviewer: ahmed **Implemented; review pending.** Merged in PR #87; rows without a level show their stored state (not started, start unknown, not assessable).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [ ] **T-EL-24** [Should] D5 · Document Q&A chatbot (normal RAG with citations) answering from the project docs, the cited Egyptian laws (Decree 2184/2022, Law 119/2008 art. 54, Law 151/2020), ACUD public pages, the satellite data docs (Dynamic World, Open Buildings, Wayback) and public summaries of ISO 37120/37122 and the SLA notion behind the KPIs; answers only from retrieved passages; any model call needs owner approval · `src/chatbot/` + sidebar + tests · reviewer: verina **Open; built on branch `feat/T-EL-24-rag-chatbot` (383 tests pass, nine sourced documents in `data/knowledge/`); ranking and off-topic refusal are being generalised against a 15-question evaluation table before the PR.**
- [x] **T-EL-25** [Must] D5 · PowerPoint deck built from the instructor rubric (`docs/requirements/ACUD-Rubric.md`) and the team's rubric deck; the slide content is kept in `docs/deliverables/01-presentation/presentation.md` · `presentation.pptx` · reviewer: salma **Implemented; review pending.** Merged in PR #84; colors follow `docs/deliverables/01-presentation/palette.md` (T-EL-28); rebuilt with `01-presentation/make/build_pptx.js`.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-26** [Could] D5 · Intro video before the ACUD discussion: Arabic narration, no compound or developer names · `docs/deliverables/02-video/intro.mp4` · reviewer: salma **Implemented; review pending.** First version merged in PR #85; rebuilt in T-EL-28 (56 s, team-supplied narration, cuts on narration pauses).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-27** [Must] D5 · Salma's tasks: record what is finished on this board and carry out the open parts that do not need a human (wording fixes from the T-SA-07 audit, the checklist follow-ups) · reviewer: salma **Implemented; review pending.** Merged in PR #86. Four dashboard labels in `app.py` still read "fine-eligible months"; the rename is open under T-SA-07.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-28** [Should] D5 · Deliverables v2: presentation files in `docs/deliverables/01-presentation/`, video files in `docs/deliverables/02-video/` with references updated; project slogan "رادار العاصمة الجديدة: شركة تمتلك مدينة."; intro video re-cut to the team narration with slogan title card, supervisor and team credits, partner logos (MCIT, Egyptian Military Academy, Digilians, ACUD), ACUD palette and crossfades; deck recolored to `palette.md`; both rebuildable from their `make/` folders · reviewer: salma **Implemented; review pending.** Branch `docs/T-EL-28-video-deck-v2`; every video cut lands on a narration pause (3.5 s title + pause midpoint); deck renders 12 slides, 12 notes.
  - [ ] Review accepted (record reviewer, date and PR after actual review).

---

## 7. nada: dashboard


**Goal:** Streamlit, 4 screens (owner decision, 2 Nov 2026, PR #60: Priority map, Compound file, District view, Digital twin what if), track switch on every screen, passes the ten-second test on screen 1. Everything reads stored files, no live computation (§9).

* [x] **T-NA-01** [Must] D1 · App skeleton: `app.py` runs `streamlit run app.py`, track switch (Track A default / Track B), orange banner "Synthetic - for training only" fixed in Track B, 🟠 on generated numbers, map hidden in Track B · reviewer: verina **Done; review accepted.**
  * Evidence: `app.py` (App skeleton, track state management, dark CSS theme, `enforce_no_names` gate).
  * Review accepted (verina).

* [x] **T-NA-02** [Must] D2 · Screen 1 priority map: R7 boundaries coloured by level (level written as a word, grey = not assessable), cycle list with Arabic reason, CSV download; Track B list only · depends: T-AH-08 · reviewer: ahmed **Done; review accepted.**
  * Evidence: `app.py` (`render_map_slot`, `render_cycle_list`, `load_boundaries`, `load_latest_kpis`). PR merged to main.
  * Review accepted (ahmed).

* [x] **T-NA-03** [Must] D3 · Screen 2 compound file: DW and A curves, height (to 2024), announced markers, first announced date, vegetation, two Wayback images, K2-K6, lineage line (origin, run_id), inspection file button; Track B: binary probabilities + K5 in EGP (🟠) · depends: T-AH-16, T-VE-10 · reviewer: ahmed **Implemented; review pending.**
  * Evidence: `app.py` `screen_compound_file` and its panels (commit 47fca5e; Track B K5 from `app_data/ml/ml_dataset.parquet`, commit 937479c). Verified on the v7 release data installed into a fresh local root (`setup_review`, 323 files): Track A renders 12 compounds with no exception; compound C01 shows level 4 (labelled "Routine" in `app.py`), K2 = 0 quarters, K3 = 0 months and K6 = unknown, which match `real/kpi_values.parquet` for 2026Q3. Not verified on data: the DW and A curves, the Wayback images, the lineage caption and the inspection file button. Track B shows "Waiting for ml/predictions.parquet" and "Waiting for ml/ml_dataset.parquet" because those files are not in the installed root. Screens 4 and 5 are still `Skeleton page` stubs in `app.py`.
  * [ ] Review accepted (record reviewer, date and PR after actual review).

* [x] **T-NA-04** [Must] D3 · `ops_visits` form: code, date, result (progressing / stalled / complete / not done), note; saved to `app_data/ops_visits.csv` · reviewer: verina **Done; review accepted.**
  * Evidence: `src/dashboard/ops_visits.py` (`render_ops_visits_form`, appends entries safely to `app_data/ops_visits.csv`). Integrated into `app.py`.
  * Review accepted (verina).

* [ ] **T-NA-05** [Must] D3 · Screen 3 would it have warned (backtest): **Removed from the dashboard by owner decision (PR #60, Ahmed; the team lead approved the removal on 2 Nov 2026). Not in the four-screen sidebar; the backtest results stay in `data/BACKTEST_CURRENT.md`.** Original scope: Track A frozen-clock table (1 of 6 and why); Track B per-class recall, macro-F1, recall@N vs random, B1-B5 per compound · depends: T-AH-10, T-VE-12 · reviewer: elsayed
  * Evidence (historical, before removal): `app.py` `screen_backtest` and renderers (commits 89cadfc and 3139d7a). The code is no longer in `app.py` on `main`.
  * [ ] Review accepted (record reviewer, date and PR after actual review).

* [ ] **T-NA-06** [Must] D3 · Screen 4 data trust (gates, coverage, not assessable, facts, colour key): **Removed from the dashboard by owner decision (PR #60, approved 2 Nov 2026). Not in the four-screen sidebar.** Original scope: gates, coverage, not assessable, 1,009/1,026 facts, colour key 🟢🔵🟠 · depends: T-AH-11 · reviewer: ahmed
  * Evidence (historical, before removal): `app.py` `screen_data_trust` (commit ec70a7b). The code is no longer in `app.py` on `main`.
  * [ ] Review accepted (record reviewer, date and PR after actual review).

* [x] **T-NA-07** [Must] D4 · Digital twin what if (screen 4; was Screen 5 before PR #60): S1 cost shock and S2 collections drop progress against the baseline run from the same seed (`what_if/progress_vs_baseline.csv`, written by `src/generator/twin_progress.py`); S3 capacity list changes; generated (🟠, banner, no map) · depends: T-VE-14 · reviewer: elsayed **Implemented; review pending.**
  * Evidence: `app.py` `screen_what_if` and `render_progress_vs_baseline`; `src/generator/twin_progress.py` (5 tests in `tests/test_twin_progress.py`); branch `feat/twin-what-if-20261102`, commit `46a59b7`. Renamed to "Digital twin what if". A headless run on Track B renders the screen with no exception. Result: S1 and S2 move progress by at most 1.0 and 0.95 points at 2026-09 and change no level or list place. Not done: the stored file is not in any release yet (v7 is pinned by SHA-256 in `setup_review`); it is written by `python -m src.generator.twin_progress --out <ready-data>/what_if/progress_vs_baseline.csv` on a machine with the real simulation inputs.
  * [ ] Review accepted (record reviewer, date and PR after actual review).

* [ ] **T-NA-08** [Must] D4 · Display rules check (§9): ≤ 4 main tiles, each with value + unit + denominator + "as of" + origin; the 5 forbidden mistakes; ten-second test on screen 1 with someone outside the team · reviewer: salma **Partial.** The display-rules check of the four screens is done (`docs/deliverables/display-rules-check.md`, PR #73) and its failures are fixed: tiles, denominators, as-of dates and origin marks (PR #75), same-season comparisons only (PR #77), and the Track B content on screens 2 and 3 (PR #78). Open: the ten-second test was taken by the project supervisor, who is outside the team (reported 2026-11-01), but the answer sheet and timings are not recorded in the repo.
  - [ ] Review accepted (record reviewer, date and PR after actual review).

* [x] **T-NA-09** [Should] D4 · `no_names` gate also scans dashboard exports; Arabic RTL renders correctly · reviewer: ahmed **Implemented; review pending.** Export helper `src/dashboard/exports.py` (`check_export`, `export_csv`) guards the cycle-list CSV download in `app.py`: a forbidden name column is dropped, and a bad code value shows an error and omits the button. The scenario-view CSV was removed with the Scenarios screen rebuild (PR #60), so one CSV download remains. Tests: `tests/test_dashboard_exports.py`; full suite 318 passed, 1 skipped. Caveat: the Arabic RTL rendering of the export and the live page were not checked in a browser. Branch `feat/T-NA-09-export-hookups`, commit `dd029dc`.
  - [ ] Review accepted (record reviewer, date and PR after actual review).

* [x] **T-NA-10** [Must] D5 · User guide (how the committee uses the four screens and the visit form) · `docs/deliverables/user-guide.md` · reviewer: salma **Implemented; review pending.** The guide is rewritten for the four screens (PR #69).
  * Evidence: [user guide](../deliverables/user-guide.md), rewritten for Priority map, Compound file, District view and Digital twin what if; every behaviour statement is traced to a function in `app.py` or `src/dashboard/`.
  * [ ] Review accepted (record reviewer, date and PR after actual review).

* [x] **T-NA-11** [Should] D5 · Search on screen 1: one box that narrows the map and the visit list to a compound code (C..) or a developer code (D..); codes only · `app.py` + test · reviewer: ahmed **Implemented; review pending.** Merged in PR #87 (search box, four filters, map click selects the compound; 394 tests pass; real-browser click on C04 checked on 3 Nov 2026).
  * [ ] Review accepted (record reviewer, date and PR after actual review).

* [x] **T-NA-12** [Should] D5 · Filters on screen 1, applied to the map and the visit list: priority level (1-4), developer code, signal thresholds (K2 quarters, K3 months, K6 months), cycle list only or all compounds, and the as-of quarter · `app.py` + test · reviewer: ahmed **Implemented; review pending.** Merged in PR #87 (search box, four filters, map click selects the compound; 394 tests pass; real-browser click on C04 checked on 3 Nov 2026).
  * [ ] Review accepted (record reviewer, date and PR after actual review).

* [x] **T-NA-13** [Should] D5 · Map click: clicking a compound on the priority map opens screen 2 (Compound file) with that compound selected · `app.py` + test · reviewer: ahmed **Implemented; review pending.** Merged in PR #87 (search box, four filters, map click selects the compound; 394 tests pass; real-browser click on C04 checked on 3 Nov 2026).
  * [ ] Review accepted (record reviewer, date and PR after actual review).
---

## 8. salma: KPIs, value, governance, presentation

Goal: every number in the docs and slides has a source or an origin mark and matches `kpi_values`; the story is honest (backtest failed, shown with the reason).

- [ ] **T-SA-01** [Must] D1 · Compass signed (use-case canvas, 8 checks); ask the instructor rubric + presentation length · `docs/requirements/05-project-compass.md` · reviewer: ahmed **Partial; the instructor rubric is received and recorded (`docs/requirements/ACUD-Rubric.md`, ten criteria summing to 100 plus a +10 transferability bonus; presentation 12 minutes, criterion 10) and mapped to project evidence with a 12-minute slide plan (`docs/deliverables/01-presentation/rubric-map.md`). Open: the instructor's sign-off of the compass is not recorded.**
- [x] **T-SA-02** [Must] D2 · KPI cards (10 fields + 2 tags, A K2 K3 K4 K5 K6) + KPI tree + levels table (deliverable 1), schema of `kpi_reference.csv` · `configs/kpis.yaml` + `docs/deliverables/kpi-cards.md` · reviewer: ahmed **Implemented; review pending.** The two tags are the "Leading/lagging" and "International axis" rows of the KPI card table in `01-specs.md`, filled per KPI in `configs/kpis.yaml` and `kpi-cards.md` (PR #64). Reviewer to confirm: `kpi_reference.csv` is not in the repo.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [ ] **T-SA-03** [Must] D3 · Value in EGP, 3 settings, no double counting (§12 formula) · `configs/cost_assumptions.yaml` + "Under these assumptions, from X to Y million EGP per year" · reviewer: elsayed **Partial; operating cost, missed cases and late-detection cost are PLACEHOLDER values in `configs/cost_assumptions.yaml`, and the reviewer's values are needed.**
- [x] **T-SA-04** [Must] D3 · Governance cards for the real and generated tables (owner, origin, refresh, who sees what) · `docs/deliverables/governance-cards.md` · reviewer: elsayed **Implemented; review pending.**
  - Evidence: [implementation/output](../deliverables/governance-cards.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-SA-05** [Must] D4 · Decision memo, one page Arabic + one page English, same facts and order (deliverable 8) · `docs/deliverables/decision-memo.md` · reviewer: verina **Implemented; review pending.**
  - Evidence: [decision memo](../deliverables/decision-memo.md) has an English and an Arabic section, each citing its source files. Page length and the same-order check were not verified.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [ ] **T-SA-06** [Must] D4 · Slides 1-11 (§12): backtest slide is the only place real names may appear; slide 8 always quotes the denominator, the baseline, the scope and "generated data" · `docs/deliverables/01-presentation/presentation.md` + deck · reviewer: all **Partial; slide notes closed (PR #65), deck HTML on main (12 sections, PR #72), every figure sourced or reworded and the slide-8 caveat added (PR #76). Open: no browser or print-preview check yet, and the deck length (12-15 min) is not confirmed.**
- [ ] **T-SA-07** [Must] D4 · Wording audit of every doc, slide and screen against §3 allowed/forbidden table ("priority level" not "risk level", no "distressed" on a real compound, no completion %) · checklist in PR · reviewer: verina **Partial; the audit is done (`wording-audit-dashboard.md`, `wording-audit-docs.md`, PR #71): dashboard 0 violations and 16 checks; documents 1 violation and 26 checks. Open: the violation at `AI_AGENT_CONFIG.md:39` (a 0% error claim, Elsayed's document, not changed) and the checks.**
- [x] **T-SA-08** [Must] D4 · Number audit: every number on slides and memo traced to `kpi_values`, `EW_REPORT.md` or `ai_verification_log` · reviewer: ahmed **Implemented; review pending.** The number audits are in `number-audit-slides.md`, `number-audit-questions.md` and `number-audit-memo.md` (PR #70). Every slide figure now has a source or was reworded (PR #76): 16 sourced, 2 reworded (the Sep-Oct 2026 dates and "48 visits"), and slide 8 carries the height caveat. The questions sheet is corrected (PR #75). Caveats: the slide 1 figures rest on the spec, which records them as the ACUD chairman's statements; "0 invented" is the spec's figure, not a recount.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-SA-09** [Must] D5 · Expected questions sheet (§12) with one-line answers · reviewer: elsayed **Implemented; review pending.**
  - Evidence: [expected questions](../deliverables/expected-questions.md): 14 questions, each with a one-line answer and a named source file. PR #66 corrected the complaints answer to the `complaints_eval.csv` figures; branch `fix/display-rules-20261102` replaces the unsourced satellite claims ("5 pre-registered tests", r about 0.96) with the T1-T3 result from `data/K1_FALLBACK_CHECK.md`. Caveat: the EGP answer quotes the placeholder range from `configs/cost_assumptions.yaml`, so it must change when T-SA-03 gets real values.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [ ] **T-SA-10** [Must] D5 · Final submission checklist: 13 deliverables (§11) ready, "done when" list (§14) ticked · reviewer: all **Partial; the checklist matches the repo (PR #68): item 10 points to the `make run` target, and the deck HTML is now on main (item 13, PR #72). Open: the §14 done-when items are still not met.**
- [ ] **T-SA-11** [Should] D2 · Update `docs/requirements/04-timeline.md` with today's program day and this board's D-days · reviewer: ahmed **Partial; the timeline is refreshed to the board counts of 2 Nov 2026 (PR #68). Open: today's program day is still unconfirmed, so the D-day update is not done.**
- [ ] **T-SA-12** [Could] D3 · Blind labeller for the finishing test (T-AH-17): label ~50 held-out compound-images without seeing the model output · reviewer: ahmed

---

## 9. Deliverables map (§11)

| #  | Deliverable                                                                 | Owner                                          | Tasks                              |
| -- | --------------------------------------------------------------------------- | ---------------------------------------------- | ---------------------------------- |
| 1  | KPI cards + tree + levels table                                             | salma                                          | T-SA-02                            |
| 2  | Pipeline with gates + `quality_checks_log.csv` + quality report           | ahmed                                          | T-AH-11, T-AH-12                   |
| 3  | Track A rule (K2-K6), backtest, Track B `ml_dataset` + binary classifier | ahmed (A), elsayed (B)                         | T-AH-04..10, T-VE-08..12           |
| 4  | Dashboard (track switch) + cycle list + `ops_visits`                      | nada                                           | T-NA-01..08                        |
| 5  | Method card + monitoring plan                                               | elsayed (method card), ahmed (monitoring plan) | T-EL-18, T-AH-20                   |
| 6  | Risks and responsible-AI note + `ai_verification_log`                     | verina                                         | T-EL-05, T-EL-09                   |
| 7  | Technical docs, user guide, governance cards, data dictionaries             | ahmed, nada, salma, elsayed                    | T-AH-20, T-NA-10, T-SA-04, T-VE-07 |
| 8  | Decision memo (Arabic / English)                                            | salma                                          | T-SA-05                            |
| 9  | Knowledge transfer pack                                                     | ahmed                                          | T-AH-21                            |
| 10 | One run command for the presentation                                        | ahmed                                          | T-AH-13, T-AH-19                   |
| 11 | Inspection files for 5 compounds                                            | verina                                         | T-EL-06                            |
| 12 | Data request list to ACUD                                                   | elsayed                                        | T-VE-14                            |
| 13 | Final presentation                                                          | salma                                          | T-SA-06, T-ALL-05                  |

---

## 10. If behind at D4 (cut order from §13)

1. T-AH-17, T-AH-18 (finishing and roof tests; cut at D4 anyway)
2. T-VE-16 (FPMI / SAF), T-VE-15 (S4 / S5)
3. T-VE-11 (gradient boosting; keep logistic)
4. T-EL-07, T-EL-08 (complaints)
5. T-EL-04 (LLM paragraph; the template stays)
6. T-AH-15 (Wayback images)
7. T-NA-05 becomes a slide

**Never cut:** Track A rule and cycle list (T-AH-01..13), Track B logistic baseline (T-VE-08..10). If the what-if screen is not ready, say "observatory", not "digital twin" (§13).

## Approved binary-scope closure, 28 October 2026

AH-16, EL-01, EL-10, EL-11 and EL-17 are implemented under BINARY_SCOPE_DECISION.md: contextual height with no fixed error guarantee, retired historical percentage claim, and reproducible binary distress models/workflow. Producing implementation tag: r7-binary-distress-2026-10-28. Main task marks indicate implementation; separate review checkboxes retain the human acceptance requirement. No colleague acceptance is signed automatically. Completion prediction is not an outstanding task.

