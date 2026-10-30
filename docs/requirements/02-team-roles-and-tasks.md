# 02-team-roles-and-tasks.md

> Current technical decisions and unresolved approvals: [D1_DECISIONS_CURRENT](D1_DECISIONS_CURRENT.md). Implementation evidence: [partial-task closure](../../data/PARTIAL_TASKS_CLOSURE.md). Main checkboxes show verified implementation; separate review checkboxes remain pending for the human reviewer.

# SpaceEye: Team Roles and Task Board

ACUD AI & Data Readiness Program · Graduation project (D1-D6) · Team of 5
Source of every task: [`01-specs.md`](01-specs.md) (section numbers in brackets, e.g. §2). Data and columns: [current dataset contract](../../data/DATASET_CONTRACT.md). Repo layout: [`08-structure.md`](../project-definition/08-structure.md).

> **Synthetic data - for training only** on every generated table, chart and slide. Codes only (`C..`, `D..`), never a compound or developer name.

---

## Current implementation marks for human review

Updated on 30 October 2026 against 77 current IDs, including the added T-AH-22. Current approved binary scope and existing review records are preserved.

| State | Count | Meaning |
| --- | ---: | --- |
| Main task checked | 42 | Implemented, with evidence; 27 still await assigned review |
| Main task unchecked, open/partial | 34 | Original work/decision still unresolved |
| Main task unchecked, failed/excluded experiment | 1 | AH-17 ran and failed; no finishing feature delivered |
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
| **nada shady**       | Dashboard (5 screens, track switch) + cycle list download + `ops_visits` form   | R5 dashboard part                                                       | `app.py`, `src/dashboard/`                                                   |
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
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [ ] **T-AH-14** [Should] D3 · Fallback ready: if A fails on new quarters, K1 path documented and switchable in config (§13) · reviewer: elsayed **Partial; see [remaining work](../REMAINING_TEAM_TASKS.md).**

### D3-D4: images for the compound file

- [x] **T-AH-15** [Should] D3 · Check Esri Wayback terms; then 2 Wayback images per R7 compound (before/after) with capture date + attribution · `app_data/images/<code>_{before,after}.jpg` + `images.csv` · reviewer: elsayed **Implemented; review pending.**
  - Evidence: [use/rebuild guide](../../data/imagery/README.md), [source/method comparison](../../data/IMAGERY_COMPARISON.md), [pair index](../../data/imagery/images.csv), [validation](../../data/IMAGERY_VALIDATION.json). Local figures: 24 inspector-pair rows, 100 distinct Wayback observations and 528 quarterly Sentinel context figures. Esri pixels/report ZIP stay outside Git; metadata, hashes, supported acquisition and portable installation code are provided. Distinct-year pair rule and publication cutoffs are documented/tested. Images are inspector context, never model X or proof of finishing; current numerical v6 is unchanged by imagery.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-AH-16** [Should] D3 · Open Buildings height 2016-2023 + 2024 v4 estimate (context only; no fixed error guarantee) and vegetation series ready per compound for screen 2 (height is context, never in the level) · reviewer: elsayed **Done; review accepted.**
  - Evidence: [implementation/output](../deliverables/annual-context.md).
  - [x] Review accepted (logs/review-03.md, 2026-10-29; findings fixed in 236e051; review recorded in 7de6b7f; coverage figures come from data/ANNUAL_CONTEXT_COVERAGE.csv, not regenerated here).
- [ ] **T-AH-17** [Could] D4 · Finishing vision-model test (Qwen-VL on Wayback): pass condition ≥ 75% agreement on ~50 held-out compound-images labelled blind by salma (T-SA-12); log in `team_ideas.md`; **cut at D4 if not passed**; flag in the inspection file only · reviewer: elsayed **Failed experiment; feature excluded.** See [recorded outcome](../REMAINING_TEAM_TASKS.md).
- [ ] **T-AH-18** [Could] D4 · Roof slab uniformity test on Google heights 2016-2023 against a condition written before the test; cut at D4 if not passed · reviewer: elsayed

### D4-D5: freeze and hand over

- [ ] **T-AH-19** [Must] D4 · Code freeze for Track A; tag the commit; `run_all` is the one run command used in the presentation (deliverable 10) · reviewer: elsayed **Partial; see [remaining work](../REMAINING_TEAM_TASKS.md).**
- [x] **T-AH-20** [Must] D5 · Technical docs for Track A + monitoring plan (quarterly recompute, who runs `run_all`, what to check) · `docs/deliverables/technical-track-a.md` · reviewer: salma **Done; review accepted.**
  - Evidence: [implementation/output](../deliverables/technical-track-a.md).
  - [x] Review accepted (logs/review-03.md, 2026-10-29; findings fixed in 9fc8763 and f9be3f9; review recorded in 7de6b7f; the quarterly procedure has not been run end to end on the real data).
- [x] **T-AH-21** [Must] D5 · Knowledge transfer pack, one page (deliverable 9) · `docs/deliverables/knowledge-transfer.md` · reviewer: salma **Done; review accepted.**
  - Evidence: [implementation/output](../deliverables/knowledge-transfer.md).
  - [x] Review accepted (logs/review-03.md, 2026-10-29; findings fixed in f9be3f9; review recorded in 7de6b7f; the run command was not executed here because the real data is not available).

### D4: real-data run on the F: drive (only ahmed has the data, about 5 GB, so it cannot be run elsewhere)

- [ ] **T-AH-22** [Must] D4 · On ahmed's machine with the F: data (WSL: `sudo mkdir -p /mnt/f && sudo mount -t drvfs F: /mnt/f`), on the latest `feat/ml`: (1) `uv run --locked --offline python -m src.pipeline.team_run --full`, then `uv run --locked --offline python -m src.pipeline.full_repro`; (2) regenerate and commit `data/BACKTEST_CURRENT.md` (with the frozen-clock result), `docs/deliverables/quality-report.md`, `data/FULL_TRACK_A_REPRODUCIBILITY.json` (manifest hash, run id, git revision), `data/R1_REPORT.md`, the current model metrics and EW reports; (3) confirm the separation and no_names gates on the real `kpi_values`; (4) run the v2 Stage 1 evaluation of `data/EW_PROTOCOL_V2.md` (check `sha256sum -c EW_PROTOCOL_V2.sha256` first; set `candidates.variant: v2` and `candidates.no_height_ablation: true`; v1 results stay labelled v1); (5) send the numbers, not the data, to the team · `data/*`, `docs/deliverables/quality-report.md`, `data/V2_MODEL_*`, `data/EW_REPORT_V2.md` · depends: coder fixes for review-03 committed, v2 protocol commit 8a16575 · reviewer: elsayed

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
  - Evidence: [implementation/output](../../src/inference/narrative.py). `draft_narrative` renders the two prompt templates from the attached facts only, checks approval and the call budget before each call, and returns `{paragraph, questions}` for `build_inspection_file(llm=...)`, or `None` on any failure (not approved, budget used, missing key, client error, not exactly 3 questions, a number or code not in the facts, forbidden wording), so the template-only file still works. Tests: `tests/test_narrative.py` (fake client, fabricated data, no network). Caveat: no live Gemini call has been made or checked; the first real call needs the key in the git-ignored `.env` and is the owner's to run.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [x] **T-EL-05** [Must] D3 · Verifier: every number, date and code matched against the source JSON; causal words ("because", "بسبب") flagged for manual review; verdicts logged · `ai_verification_log.csv` (correct / wrong number / unsupported claim / missing context) + test · reviewer: elsayed **Implemented; review pending.**
  - Evidence: [implementation/output](../../src/inference/verifier.py). `verify_text` matches every number, date, quarter and code of an AI text against the source JSON (Arabic-Indic digits normalised), flags causal wording ("because", "بسبب" and others) for manual review, and gives each token a verdict (correct / wrong number / unsupported claim / missing context); `append_log` writes tokens only, never the text, to `app_data/ai_verification_log.csv`. Tests: `tests/test_ai_verifier.py` (fabricated data). Caveats: the older `src/inference/verify.py` stays for its own tests; the verifier is not yet wired into the narrative step or run on a real model output; the two functions the merge `91c3940` dropped from `tools.py` are restored, so `tests/test_inspection_tools.py` passes again; `generate_inspection_brief` is restored in `generate.py` as a wrapper over the guarded narrative step with a deterministic fallback, so `tests/test_inference.py` passes again (full suite: 216 passed, 1 skipped); its test only imports the function and never calls it.
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [ ] **T-EL-06** [Must] D4 · Arabic HTML/PDF output with footer "Drafted by AI, reviewed by [name]" + model + time; 5 stored files for the presentation (deliverable 11) · `app_data/files/` · depends: T-AH-15 · reviewer: salma
- [x] **T-EL-07** [Should] D3 · Complaints masking: regex on numbers and names **before** any model (Law 151/2020); `assert_zero_phones` passes + test · reviewer: elsayed **Implemented; review pending.**
  - Evidence: [implementation/output](../../src/pipeline/privacy.py).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [ ] **T-EL-08** [Should] D4 · Complaints classifier: 5 classes (delay, stoppage, payment, quality, other) vs keyword baseline; extra test on `complaints_30.csv`; state that texts we wrote do not prove real accuracy · reviewer: elsayed **Partial; see [remaining work](../REMAINING_TEAM_TASKS.md).**
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
- [ ] **T-EL-12** [Could] D4 · S4 material cost +40%, S5 grace 12 → 6 months · reviewer: nada
- [ ] **T-EL-13** [Could] D4 · FPMI and SAF tests on generated data, conditions written before the run, logged in `team_ideas.md` · reviewer: ahmed
- [x] **T-EL-14** [Must] D4 · Code freeze for Track B; one command builds Track B after `run_all` · reviewer: ahmed **Implemented; review pending.**
  - Evidence: [implementation/output](../../data/BINARY_SCOPE_DECISION.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).

---

## 7. nada: dashboard

Goal: Streamlit, 5 screens, track switch on every screen, passes the ten-second test on screen 1. Everything reads stored files, no live computation (§9).

- [ ] **T-NA-01** [Must] D1 · App skeleton: `app.py` runs `streamlit run app.py`, track switch (Track A default / Track B), orange banner "Synthetic - for training only" fixed in Track B, 🟠 on generated numbers, map hidden in Track B · reviewer: verina
- [ ] **T-NA-02** [Must] D2 · Screen 1 priority map: R7 boundaries coloured by level (level written as a word, grey = not assessable), cycle list with Arabic reason, CSV download; Track B list only · depends: T-AH-08 · reviewer: ahmed
- [ ] **T-NA-03** [Must] D3 · Screen 2 compound file: DW and A curves, height (to 2024), announced markers, first announced date, vegetation, two Wayback images, K2-K6, lineage line (origin, run_id), inspection file button; Track B: binary probabilities + K5 in EGP (🟠) · depends: T-AH-16, T-VE-10 · reviewer: ahmed
- [ ] **T-NA-04** [Must] D3 · `ops_visits` form: code, date, result (progressing / stalled / complete / not done), note; saved to `app_data/ops_visits.csv` · reviewer: verina
- [ ] **T-NA-05** [Must] D3 · Screen 3 would it have warned: Track A frozen-clock table (1 of 6 and why); Track B per-class recall, macro-F1, recall@N vs random, B1-B5 per compound · depends: T-AH-10, T-VE-12 · reviewer: elsayed
- [ ] **T-NA-06** [Must] D3 · Screen 4 data trust: gates, coverage, not assessable, 1,009/1,026 facts, colour key 🟢🔵🟠 · depends: T-AH-11 · reviewer: ahmed
- [ ] **T-NA-07** [Must] D4 · Screen 5 what if (twin): pick S1-S3, show which compounds change level and why; generated (🟠, banner, no map) · depends: T-VE-14 · reviewer: elsayed
- [ ] **T-NA-08** [Must] D4 · Display rules check (§9): ≤ 4 main tiles, each with value + unit + denominator + "as of" + origin; the 5 forbidden mistakes; ten-second test on screen 1 with someone outside the team · reviewer: salma
- [ ] **T-NA-09** [Should] D4 · `no_names` gate also scans dashboard exports; Arabic RTL renders correctly · reviewer: ahmed
- [ ] **T-NA-10** [Must] D5 · User guide (how the committee uses screens 1, 2 and the visit form) · `docs/deliverables/user-guide.md` · reviewer: salma

---

## 8. salma: KPIs, value, governance, presentation

Goal: every number in the docs and slides has a source or an origin mark and matches `kpi_values`; the story is honest (backtest failed, shown with the reason).

- [ ] **T-SA-01** [Must] D1 · Compass signed (use-case canvas, 8 checks); ask the instructor rubric + presentation length · `docs/requirements/05-project-compass.md` · reviewer: ahmed
- [ ] **T-SA-02** [Must] D2 · KPI cards (10 fields + 2 tags, A K2 K3 K4 K5 K6) + KPI tree + levels table (deliverable 1), schema of `kpi_reference.csv` · `configs/kpis.yaml` + `docs/deliverables/kpi-cards.md` · reviewer: ahmed
- [ ] **T-SA-03** [Must] D3 · Value in EGP, 3 settings, no double counting (§12 formula) · `configs/cost_assumptions.yaml` + "Under these assumptions, from X to Y million EGP per year" · reviewer: elsayed
- [x] **T-SA-04** [Must] D3 · Governance cards for the real and generated tables (owner, origin, refresh, who sees what) · `docs/deliverables/governance-cards.md` · reviewer: elsayed **Implemented; review pending.**
  - Evidence: [implementation/output](../deliverables/governance-cards.md).
  - [ ] Review accepted (record reviewer, date and PR after actual review).
- [ ] **T-SA-05** [Must] D4 · Decision memo, one page Arabic + one page English, same facts and order (deliverable 8) · `docs/deliverables/decision-memo.md` · reviewer: verina
- [ ] **T-SA-06** [Must] D4 · Slides 1-11 (§12): backtest slide is the only place real names may appear; slide 8 always quotes the denominator, the baseline, the scope and "generated data" · `docs/deliverables/01-presentation.md` + deck · reviewer: all
- [ ] **T-SA-07** [Must] D4 · Wording audit of every doc, slide and screen against §3 allowed/forbidden table ("priority level" not "risk level", no "distressed" on a real compound, no completion %) · checklist in PR · reviewer: verina
- [ ] **T-SA-08** [Must] D4 · Number audit: every number on slides and memo traced to `kpi_values`, `EW_REPORT.md` or `ai_verification_log` · reviewer: ahmed
- [ ] **T-SA-09** [Must] D5 · Expected questions sheet (§12) with one-line answers · reviewer: elsayed
- [ ] **T-SA-10** [Must] D5 · Final submission checklist: 13 deliverables (§11) ready, "done when" list (§14) ticked · reviewer: all
- [ ] **T-SA-11** [Should] D2 · Update `docs/requirements/04-timeline.md` with today's program day and this board's D-days · reviewer: ahmed
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

