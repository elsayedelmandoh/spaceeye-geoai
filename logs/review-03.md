# Review 03: ahmed, D3 "backtest, gates, reproducibility" (T-AH-10 .. T-AH-13), D3-D4 images block (T-AH-16) and D5 (T-AH-20, T-AH-21)

Branch `feat/ml` at `25fae7f`. Method: I read `src/pipeline/{gates,backtest_check,partial_exports,quality_report,full_repro,run_all,team_run,common,complete_data,codify,build_real,delivery}.py`, `configs/data.yaml`, `Makefile`, `tests/`, the committed evidence in `data/` and `docs/deliverables/`, the task board sections "### D3: backtest, gates, reproducibility", "### D3-D4: images for the compound file" and "### D4-D5: freeze and hand over", and `docs/requirements/01-specs.md` §3, §4, §8 and §11.

The **Spec** axis is the seven task lines plus `01-specs.md` §3.4 and §3.6 (backtest, no leakage), §4 (adopted height context), §8 (10 gates table, outputs, lineage, fixed `computed_on`) and §11 (deliverables 2, 9, 10). The **Standards** axis is `CLAUDE.md` / `AGENTS.md` plus the general code-quality rules. These tasks landed across several commits, so I reviewed the current state of the files instead of a diff.

Reviewer: elsayed (independent, per board) · Date: 2026-10-29 · PR: #12 (feat/ml)

### What was run

- `.venv/bin/python -m pytest -q` → **77 passed, 1 skipped**.
- `.venv/bin/ruff check src tests --output-format concise` → **17 errors, not the expected 1**. The extra errors (C408, RUF100, I001, RUF046, RUF007) are in `src/analysis/ew_eval.py`, `src/generator/*` and `src/pipeline/activity.py:101`. None is in a D3/D5 file: `gates.py`, `backtest_check.py`, `partial_exports.py`, `quality_report.py`, `full_repro.py`, `run_all.py`, `team_run.py` and `common.py` are clean.
- `git diff --check` → clean.
- Searches for test coverage, stale "8 cases" wording, use of `heights_max_year` and markdown link targets. Every link in `technical-track-a.md`, `knowledge-transfer.md`, `annual-context.md` and `quality-report.md` resolves to an existing file.

### What could not be verified

- A throwaway `.venv/bin/python -c` check of the freshness boundary (`months_between` vs quarter difference) was blocked by the permission prompt. Every behavioural claim marked **(hand-derived)** comes from reading the code and doing the arithmetic by hand.
- I did not run `run_all`, `team_run`, `complete_data`, `full_repro`, `delivery` or `release`, and the external F: data is not mounted here. Everything about real outputs (`backtest/cases.csv`, `summary.json`, `quality_checks_log`, `manifest.csv`, the frozen-clock result, the 276-artifact equality) is judged only from the committed reports in `data/` and `docs/deliverables/`. I could not check that those reports match the current code, or that the reproducibility result still holds after the `native_path` change (`ff51f97`). `data/FULL_TRACK_A_REPRODUCIBILITY.json` was last touched by the path-move commit `9b73671`, and the file itself carries no run date or code revision.
- I could not check the "program template" schema of `quality_checks_log`: there is no template file in the repo.
- I did not check whether the published release ZIP is free of names. `g_no_names` does not open `.zip` files, and the ZIP lies outside `app_data`.

## Verdict

| Task                                     | Reviewer on board | Spec result                                                                                                                                                                                                                                                                  | Real test / evidence?                                                                                                                                                                                                                                                                                                                                |
| ---------------------------------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T-AH-10 frozen-clock backtest, R7        | elsayed             | **Partly met.** 6 R7 cases, 1 of 6, counts only and a backtest variant without overlapping plots are all present. The frozen-clock result is missing from the committed evidence; the competing explanation and "what next" are one template reused for all six cases. | **No test** of `backtest_check.readings`, `run` or `frozen_clock_check`. Evidence: `data/BACKTEST_CURRENT.md` (generated).                                                                                                                                                                                                             |
| T-AH-11 10 gates + log                   | elsayed           | **Partly met.** All 10 gates (plus `veg_pull_check`) exist with dimension, owner and decision. `no_names` does not scan outputs written after it runs or anything in `data/`; two gates PASS on empty input; freshness uses months instead of quarters.          | Partly: `test_separation_gate_rejects_an_undeclared_kpi_values_column`, `test_name_gate_matches_whole_words_in_english_and_arabic_and_ignores_accents`, `test_name_gate_distinguishes_generic_identifiers_from_standalone_names` (tests/test_pipeline.py). Nothing tests completeness, freshness, data_or_city, stuck_series or the exit code. |
| T-AH-12 quality report                   | elsayed             | **Partly met.** The "Impact on the indicator" column exists and comes from the saved check rows, but the source is `data_completion/quality_checks.csv`, not `quality_checks_log`, and one decision sentence is hard-coded.                                        | No test. Evidence: `docs/deliverables/quality-report.md` (generated).                                                                                                                                                                                                                                                                              |
| T-AH-13 two runs identical, `make run` | elsayed           | **Met on the letter (not re-verified here).** `make run` exists; the evidence JSON says PASS on 276 artifacts. The evidence is weak (same process, no hash or revision recorded).                                                                                    | No test. Evidence: `data/FULL_TRACK_A_REPRODUCIBILITY.json` (5 fields, booleans only).                                                                                                                                                                                                                                                             |
| T-AH-16 heights + vegetation context     | elsayed              | **Partly met.** Context only, never in the level, nulls kept, no height after 2024 in the data. But the docs claim OBT heights for 2016-2023 while the data has none for 2016-2019, and the 2024 cap can be bypassed.                                                  | No test of the year cap. Evidence: `data/ANNUAL_CONTEXT_COVERAGE.csv`, `docs/deliverables/annual-context.md`.                                                                                                                                                                                                                                    |
| T-AH-20 technical docs + monitoring plan | elsayed             | **Partly met.** Flow, rules and checks are documented, but the quarterly procedure never tells the operator to run `run_all` (`make run`) to recompute a new quarter.                                                                                              | Doc only; links valid.                                                                                                                                                                                                                                                                                                                               |
| T-AH-21 knowledge transfer, one page     | elsayed             | **Met.** About 380 words; links valid; numbers current (12 R7, capacity 4, 180 rows / 40 features). One gap: it gives no run command and no F: mount note.                                                                                                             | Doc only; links valid.                                                                                                                                                                                                                                                                                                                               |

Findings: **0 CRITICAL, 5 HIGH (2 fixed: H1=b3e3ed8, H4=3f16253; 3 open: H2/H3/H5), 13 MEDIUM, 10 LOW.** Do not tick "Review accepted" for T-AH-10, T-AH-11 or T-AH-20 until their HIGH items are fixed. H1 (final g_no_names scan + test) and H4 (frozen_clock_check merge) fixes applied to feat/ml; H2/H3/H5 still require fixes listed in Spec axis; v2b/v2c unbuilt; F: mount unverified.

## Spec axis

### T-AH-10: frozen-clock backtest: partly met

Spec §3.4: "apply the levels with data published before each quarter only. A frozen-clock check recomputes from data cut at the quarter and compares. Result: **1 of 6** warned ≥ 6 months early (target 5). Per case: what happened / why / what next, and a competing explanation rejected with a number. Small sample: counts, no percentages." Spec §3.6: "statements filtered by `published_date`; quarters ≤ as-of; … training plots that cover ≥ 50% of a compound are excluded in a backtest variant."

What is met:

- R7 only, 6 cases: `data/BACKTEST_CURRENT.md:3-14` lists E1, E4, E5, E6, E7 and E8 (codes only). `data/R1_REPORT.md` reports `eval_outcomes` = 6 rows.
- 1 of 6: `data/BACKTEST_CURRENT.md:5` "After-start reading: 1 of 6. Point-in-time reading: 0 of 6. Original criterion remains 5 cases". This matches spec §3.4. `min_cases: 5`, `months_before: 6` and `levels: [1, 2]` come from config (`configs/data.yaml:94-97`).
- Backtest variant of A: `run_all.py:80-82` refits without `activity.overlapping_plots()`, and `run_all.py:91-93` builds `kpi_bt` from it.
- Counts, no percentages: no `%` appears in `BACKTEST_CURRENT.md` or in the `backtest_check.run` summary.
- No future statements: `frozen_clock_check` cuts statements at `published_date <= qend(qi)` (`backtest_check.py:72`). `readings` only uses quarters with `qend(qi) <= first - 6 months` (`backtest_check.py:26`). Publication filtering inside `kpi_values` was reviewed in review-02.
- Determinism: no randomness; frames are sorted by `qi`.
- Stale N=8: every remaining "N=8" mention in `data/`, `docs/` and `src/` is labelled historical, except `backtest_check.py:8-9` (see LOW L1).

**HIGH H2 (FIXED — 2a77ba4)**: Tests added (`tests/test_backtest.py`); assertion (a) verified against `backtest_check.readings`; (b)/(c) structurally correct (backtest summary data unavailable — F: unverified). No test calls `backtest_check.readings`, `run` or `frozen_clock_check` (`grep -rn "backtest_check\|readings(\|frozen_clock" tests` → nothing). The 1-of-6 claim and the "no future data" property rest only on a generated report. Fix: add `tests/test_backtest.py` with
(a) `test_readings_counts_only_quarters_six_months_before_the_first_date`: build `kc` with three quarters (`qi` for 2022Q4, 2023Q2, 2023Q4), `level` `[2, 2, 2]`, `started` `[False, True, True]`, plus `quarter`, `K2` and `level_label`, and set `first = pd.Timestamp("2024-03-31")`. **(hand-derived)** The cutoff is 2023-09-30, so the eligible quarters are 2022Q4 and 2023Q2. Assert `after_start is True`, `first_alert_quarter == "2023Q2"` and `point_in_time is True`.
(b) `test_readings_with_no_eligible_quarter_returns_false_not_error`: use an empty `kc` and assert `after_start is False` and `point_in_time is False`.
(c) `test_run_counts_cases_not_percentages`: 2 fabricated cases, one hit. Assert `summary["after_start_reading"]["n"] == 1` and that no value in `json.dumps(summary)` contains `"%"`.

**HIGH H4 (FIXED — 3f16253)**: The frozen-clock result is now merged in partial_exports.backtest_report; BACKTEST_CURRENT.md line still needs saved data (F: unverified, see M12 note). `run_all.py:95` stores `frozen_clock_check` in `app_data/backtest/summary.json`. But `partial_exports.backtest_report` (`partial_exports.py:39`) calls `backtest_check.run(kpi, events)` again, so its `summary` has **no** `frozen_clock_check` and no `activity_variant`. `BACKTEST_CURRENT.md` therefore never states whether the cut-data recompute matched. The spec line "A frozen-clock check recomputes from data cut at the quarter and compares" cannot be verified from the repo. Fix: in `backtest_report`, read `saved = json.loads((APP / "backtest/summary.json").read_text(encoding="utf-8"))`, merge `summary["frozen_clock_check"] = saved["frozen_clock_check"]` and `summary["activity_variant"] = saved["activity_variant"]` (raise `RuntimeError("run src.pipeline.run_all first")` if either key is missing), and add the line `f"Frozen-clock recompute equal to the full run at: {', '.join(q for q, ok in saved['frozen_clock_check'].items() if ok)}; not equal at: {…}."` to `BACKTEST_CURRENT.md`.

**MEDIUM M7: the explanations are templates, and the report re-implements `readings` differently.** `partial_exports.py:44-45` defines "assessable" as `mine.K4` and alerts as `level.isin([1, 2])` (hard-coded), while `backtest_check.readings` uses `kpi.level.notna()` (`backtest_check.py:45`) and `B["levels"]`. A K4-true quarter with level NA ("not started" / "start unknown") is counted as assessable in the report but not in `readings`. All six cases get the same competing explanation ("solely due to no assessable quarter") and the same `what_next` string (`partial_exports.py:48-49`, `:61`). The rejection is numeric, so the letter of the spec is met, but the explanation is not specific to each case (judgement). Fix (coder): replace `[1, 2]` with `CFG["backtest"]["levels"]`, and rename the column to `k4_quarters_before_cutoff` or filter with `mine.level.notna()` so it matches `readings`. Whether each case needs its own explanation is for the owner to decide (see "Needs a human decision").

**MEDIUM M8: the frozen-clock check is narrower than its docstring.** `backtest_check.py:64-76`:

- It scores with the **full** model `model` (`run_all.py:95`), not a model refit on data up to the quarter, and compares with `kpi` (full model), not `kpi_bt`. It shows that `kpi_values` uses no future *data*; it does not show that A's fit has no temporal leakage. That is a design limit, but the docstring "recompute from data cut at the quarter" invites the stronger reading.
- The yearly cut is `yearly.year <= 2016 + qi // 4` (`:72`). For 2023Q2 that keeps vegetation year 2023, which is not over yet. **(hand-derived)** No leak today, because `kpis.veg_latest` already caps at `summer_year(qi)` (`kpis.py:285`), but then the check does not test the vegetation cut at all.
- The quarters `("2021Q4", "2023Q2", "2024Q4", "2025Q3")` are hard-coded magic values (`:68`).
- If `part[part.qi == qi]` is empty, `np.allclose` on empty arrays returns `True` (PASS on empty).
  Fix: use `yearly[yearly.year <= summer_year(qi)]`; move the quarter list to `CFG["backtest"]["frozen_check_quarters"]` (a new key, same values, not a threshold); add `if a.empty: out[q] = False`; extend the docstring: "uses the final fitted A; checks data cut-off, not model refit".

### T-AH-11: 10 gates: partly met

Spec §8 table (rule / owner / on failure) and "**no_names** … No compound or developer name in any output file". Board: "`no_names` scans every output incl. new CSVs; `separation` covers new columns".

Gate-by-gate against the §8 table (`src/pipeline/gates.py`):

| Gate         | Code                                                                                    | vs spec                                                                                                          |
| ------------ | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| source       | `:39-44`, FIX                                                                         | matches (100%, accepted verdicts, exclusions)                                                                    |
| completeness | `:47-51` uses `K4` (= `n_images >= CFG["n_images_min"]`, 6, `build_real.py:85`) | matches; **PASS on empty** (M1)                                                                            |
| validity     | `:54-62`, STOP                                                                        | matches                                                                                                          |
| uniqueness   | `:65-68`, STOP                                                                        | matches                                                                                                          |
| consistency  | `:71-78`, STOP                                                                        | matches; `n * 11` years is a magic number (L2)                                                                 |
| freshness    | `:81-85`, FLAG                                                                        | **months, not quarters** (M4)                                                                              |
| separation   | `:88-96` uses `KPI_ORIGINS`                                                         | matches; covers new `kpi_values` columns (tested)                                                              |
| data_or_city | `:99-104`, `share > 0.30`                                                           | matches "> 30%"; 0.30 is inline (L2)                                                                             |
| stuck_series | `:107-112`, 4 equal values                                                            | matches; bridges NA gaps (L3)                                                                                    |
| no_names     | `:176-187`, STOP                                                                      | **does not cover every output** (H1); PASS on 0 patterns (M2); misses Arabic in non-listed text files (M3) |

The log schema is `gate, dimension, rule, threshold, owner, on_failure, value, status, impact` (`gates.py:34`) plus `run_id, computed_at` in `run_all.py:109`. A STOP stops the run: `run_all.main` returns 1 (`run_all.py:113`), `team_run` raises (`team_run.py:16-17`) and `complete_data` raises before writing the CSV (`complete_data.py:237-238`).

**HIGH H1 (FIXED — b3e3ed8)**: Final `g_no_names` scan added (`final_no_names_scan` in gates.py) + `tests/test_gates.py`; covers app_data, repo data/, docs/deliverables/quality-report.md; raises on non-PASS. In the `team_run` order (`team_run.py:18-29`), the last full scan is in `complete_data.build` (`complete_data.py:234-235`). Everything written after it is never scanned in that run:

- `ops_visits_template.csv` and `audit.json` (`complete_data.py:240`, `:266`);
- `ml_current/*` and `data/CURRENT_MODEL_*`, `data/EW_REPORT_CURRENT.md` (`current_evaluation.py:198-214`);
- **the scenario exports** `partial_task_exports/S1|S2|S3/who_moved_and_why.csv` and `kpi_values.parquet`, `backtest/cases_explained.csv`, `annual_context.csv`, `scenario_contract.json`, `data/BACKTEST_CURRENT.md`, `data/ANNUAL_CONTEXT_COVERAGE.csv`, `data/DEFECT_AUDIT_CURRENT.json` (`partial_exports.py:63-70`, `:104-114`, `:148-153`);
- `docs/deliverables/quality-report.md` and `data/SOURCE_CATALOG.csv` (they filter URLs themselves but are not scanned as files).

`g_no_names` only walks `root=APP` plus private files (`gates.py:180`), so nothing under the repo `data/` or `docs/deliverables/` is ever scanned, and those are the files that get published. Inside `run_all`, the gate (`run_all.py:104`) runs before `quality_checks_log`, `run_log`, `spaceeye.duckdb` and `manifest.csv` are written (`:109-111`); it scans the *previous* run's DuckDB file. Failing input: if a scenario `reason` string ever carries a name (e.g. a new column copied from a private table), `team_run` finishes with exit 0 and the quality report says `no_names PASS`. Fix: at the end of `team_run.main` (after `sources()`), add
`scan = gates.g_no_names(extra=gates.generator_files() + sorted(p for p in (BASE_DIR / "data").rglob("*") if p.is_file()) + [BASE_DIR / "docs/deliverables/quality-report.md"])` and `if scan["status"] != "PASS": raise RuntimeError("no_names STOP after final exports: " + scan["value"])`. In `run_all.main`, move `qlog = gates.run_gates(...)` after `write_duckdb()`, or rerun `gates.g_no_names()` once after `manifest()` and fold it into the exit code. Test: `test_final_name_scan_covers_repo_data_files`: write a temp file containing a name from a monkeypatched `forbidden_names()` into a temp root passed via `extra`, and assert `status == "STOP"`.

**HIGH H3 (NOT YET FIXED — needs expanded tests/test_gates.py)**: Most gates have no test. Only `g_separation` and the name-pattern helpers are tested. `g_completeness`, `g_freshness`, `g_data_or_city`, `g_stuck` and the `run_all` exit code are untested. Fix: add `tests/test_gates.py` with one PASS and one fail case per gate, using small frames:
`g_stuck` (`built_prob_mean` `[0.5, 0.5, 0.5, 0.5]` → FLAG; `[0.5, 0.5, 0.5, 0.6]` → PASS);
`g_data_or_city` (5 of 12 compounds with `K2 == 1` and a level in one quarter → FLAG; 3 of 12 → PASS);
`g_completeness` (one compound with `K4 = False` at the as-of quarter → FLAG; no as-of rows → FLAG after M1);
`g_freshness` with `monkeypatch.setitem(CFG, "computed_on", ...)` (see M4).

**MEDIUM M1: `g_completeness` passes when the as-of quarter is missing.** `gates.py:51` uses `bool(now.K4.all())`. **(hand-derived)** If `sat` has no row at `asof`, `now` is empty, `.all()` is `True`, and the value reads "0 of 0 assessable" with status PASS. Fix: `ok = len(now) > 0 and bool(now.K4.all())`.

**MEDIUM M2: `g_no_names` passes with zero patterns.** If `forbidden_names()` returns an empty set (for example a renamed register column that is all NA), `pats == []`, nothing can match, and the gate returns PASS ("0 patterns"). Fix: in `g_no_names`, use `ok = bool(pats) and not bad` and pass `ok` to `_row`. Test: monkeypatch `gates.forbidden_names` to return `set()` and assert `status == "STOP"`.

**MEDIUM M3: Arabic names are missed in text files with unlisted extensions.** `TEXT_EXT` (`gates.py:28`) lacks `.html`, `.htm`, `.tsv` and `.xml`; those files fall to `read_bytes().decode("latin-1")` (`:167`). UTF-8 Arabic decoded as latin-1 is mojibake, so an Arabic compound name in the planned `app_data/files/*.html` inspection files (T-VE-06) would never match. English names would still match. Fix: add `".html", ".htm", ".tsv", ".xml"` to `TEXT_EXT`, and in the `else` branch yield `raw.decode("utf-8", errors="ignore")` before the latin-1 decode. Test: write `"<p>" + arabic_name + "</p>"` to `tmp_path / "x.html"` and assert one hit.

**MEDIUM M4: freshness uses rounded months instead of quarters, and reports the config quarter rather than the data quarter.** Spec: "Last quarter ≤ 1 quarter before computation". Code: `lag = months_between(qend(last), computed_on)` and `lag <= 3` (`gates.py:83-85`). **(hand-derived)** With data ending 2026Q3 and `computed_on = 2027-01-14` (106 days → 3.48 → 3), the gate PASSes although the computation quarter 2027Q1 is **2** quarters after the data. The value text also prints `CFG['last_quarter']` (`:85`) instead of the computed `last`. If the data stopped at 2026Q1, the log would still say "last quarter 2026Q3". The current published result does not change (2026Q4 − 2026Q3 = 1 quarter → PASS). Fix: `lag_q = qindex_of(pd.Timestamp(CFG["computed_on"])) - last`, `ok = lag_q <= 1`, threshold text `"<= 1 quarter"`, value `f"last quarter {qlabel(last)}, {lag_q} quarter(s) before {CFG['computed_on']}"`. The value 1 is the spec's own threshold, not a change. Test: `computed_on` `"2027-01-14"` with data to 2026Q3 → FLAG; `"2026-10-26"` → PASS.

### T-AH-12: quality report: partly met

Board: "Quality report with an 'impact on the indicator' column, from `quality_checks_log`". Spec §8 outputs.

- The column is present (`quality_report.py:46`, header "Impact on the indicator") and filled from each saved row's `impact` field (`:49-50`), not hand-written per row. Met on the letter. The `impact` text is a fixed sentence per gate set in `gates._row`, so it does not change with the observed value (judgement, LOW).

**MEDIUM M5: the source is not `quality_checks_log`.** `quality_report.py:18` reads `app_data/data_completion/quality_checks.csv` (written by `complete_data.py:239` **without** `run_id` / `computed_at`), not `real/quality_checks_log.parquet` from `run_all.py:109`. The two diverge: `quality-report.md:22` says "77 patterns, **346** files" and `data/R1_REPORT.md:34` says "77 patterns, **344** files". Fix (coder): in `complete_data.build`, write `q.assign(run_id=run_id, computed_at=CFG["computed_on"])`, and in `quality_report.main` add a `Run id:` line from the first row. Which file is canonical is a human decision.

**MEDIUM M6: one decision sentence is hard-coded.** `quality_report.py:37` always prints "The 2019Q2 source-event FLAG remains unresolved." If a refresh clears that flag or flags another quarter, the report states something false. Fix: build that sentence from the rows, e.g. `flags = [r for r in rows if r["status"] == "FLAG"]` and `lines += [f"Unresolved FLAG: {r['gate']}: {r['value']}. Review before interpreting it." for r in flags]`, and drop the literal. Test: render from a two-row temp CSV with no FLAG and assert `"2019Q2" not in` the output (monkeypatch `APP` and `BASE_DIR` to `tmp_path`).

### T-AH-13: two runs identical: met on the letter, evidence weak

Board: "run `run_all` twice, compare `manifest.csv` sha; add a `make run` target". Spec §8: "`computed_on` is fixed so two runs are identical"; deliverable 10.

- `make run` → `uv run --locked --offline python -m src.pipeline.team_run --full` (`Makefile:9-10`), which calls `run_all.main` (`team_run.py:15-17`). Met.
- `full_repro.main` runs `run_all.main()` twice, sorts both manifests by file and compares them with `DataFrame.equals` (`full_repro.py:29-35`). The result file is written to `data/FULL_TRACK_A_REPRODUCIBILITY.json` (`:40`), in `data/` and not `docs/data`. Met.
- Volatile fields: `computed_at = CFG["computed_on"]` (`data.yaml:4`, fixed); `run_id` is a hash of config plus raw caches (`run_all.py:21-25`), so it is stable; HistGradientBoosting uses `random_state=SEED` (`activity.py:112`); DuckDB is hashed by table content, not bytes (`run_all.py:48-51`). No timestamp is written into a hashed file. Met.
- Path mapping: manifest paths are relative to `APP` (`run_all.py:46`) and `make_run_id` hashes `p.name` only, so the `F:` → `/mnt/f` mapping (`common.py:22-27`, tested at `tests/test_pipeline.py:332-334`) cannot change a hash.

**MEDIUM M11: the evidence cannot be tied to a run, and both runs share one process.** The JSON has only `equal_manifests`, `artifacts: 276`, a protected-files flag and `status`. It has no manifest sha, no `run_id`, no code revision and no date, so no one can tell which code produced "PASS", or whether it predates `ff51f97`. Both runs execute in one Python process, so any per-process nondeterminism (string-hash set order under `PYTHONHASHSEED`, module-level caches) is identical in both and cannot be detected (judgement). `manifest()` also skips every `.md` under `app_data` (`run_all.py:47`), e.g. `component_data/dictionaries/*.md`. Fix: add to `result` `"manifest_sha256": hashlib.sha256(manifests[0].to_csv(index=False).encode()).hexdigest()`, `"run_id": run_all.make_run_id()`, `"git_revision": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()`, `"computed_on": CFG["computed_on"]`. Optionally run each pass as `subprocess.run([sys.executable, "-m", "src.pipeline.run_all"], check=False).returncode`. Add a unit test that `manifest()` excludes `manifest.csv` (temp `APP` via monkeypatch).

### T-AH-16: height and vegetation context: partly met

Board: "Open Buildings height 2016-2023 + 2024 v4 estimate (context only; no fixed error guarantee) and vegetation series ready per compound for screen 2 (height is context, never in the level)". Spec §4: "Adopted now: available OBT observations through 2023 and the approved v4 estimate for 2024 … No later experimental height or finishing product is published. Missing annual values stay null".

- Context only: `kpis.level_of` has no height argument (review-02), so height never sets the level. Met.
- Nulls kept: `sat_yearly` is a left merge on a full 2016-2026 grid (`build_real.py:96-97`) with no fill. `data/ANNUAL_CONTEXT_COVERAGE.csv` shows `heights_nonnull` 0 for 2025 and 2026. Met.
- `heights_max_year: 2024` (`configs/data.yaml:38`). The "fixed ±2 m guarantee" is removed (`annual-context.md:7`). Met.
- Vegetation: 12 of 12 compounds per year for 2019-2026, null for 2016-2018 (coverage CSV). Met.

**MEDIUM M10: the docs claim OBT heights for 2016-2023, but the data has none before 2020.** `data/ANNUAL_CONTEXT_COVERAGE.csv` reports `heights_nonnull` = 0 for 2016-2019, then 5, 9, 11, 10 and 10 of 12 for 2020-2024. Yet `annual-context.md:5` says "Approved heights are Google Open Buildings Temporal 2016–2023", `technical-track-a.md:9` "OBT 2016–2023" and `R1_REPORT.md:36` "OBT2016–2023". The claim is not backed by the data file. Fix: change those three places to "OBT where available (none for 2016-2019; 5-11 of 12 compounds per year for 2020-2023) and the v4 estimate for 2024 (10 of 12); see the coverage CSV". Edit the `delivery.py:158-166` string for the R1 report.

**MEDIUM M9: the 2024 cap is bypassed when the height file has a `published` column.** `codify.py:151`: `h = h[h.published] if "published" in h else h[h.year <= CFG["heights_max_year"]]`. The config comment (`data.yaml:34-35`) expects a v6 file with a `published` column. Failing input: a v6 row `year=2025, published=True` reaches `sat_yearly`, which contradicts §4 and CLAUDE.md ("No unsupported height … product enters the observed data"). Fix: `keep = h.year <= CFG["heights_max_year"]` and `if "published" in h: keep &= h.published.astype(bool)`, then `h = h[keep]`. Test: `test_heights_after_max_year_are_dropped_even_when_published`: call the filter (extract it as `codify.height_rows(h)`) on a 2-row frame (2024 and 2025, both `published=True`) and assert only 2024 remains.

### T-AH-20: technical docs + monitoring plan: partly met

Board: "Technical docs for Track A + monitoring plan (quarterly recompute, who runs `run_all`, what to check)". Deliverables 5 and 7.

- Flow and rules match the current code: K6 thresholds "13–24 and above 24 months" (`technical-track-a.md:9`, `data.yaml:72-73`); capacity 4 with order level, K2 desc, K3 desc, code; height context; `data/` paths, not `docs/data`; `make data`, `make current` and `make run` match the `Makefile`; `full_repro` and the 276 artifacts match the JSON. All links resolve.
- Who: "Proposed accountable operator: Track A owner; reviewer: another team member" (`:29`). What to check: steps 2-5.

**HIGH H5 (NOT YET FIXED — needs docs/deliverables/technical-track-a.md)**: The quarterly procedure never recomputes a new quarter. Step 3 says "Run the preparation steps" (`technical-track-a.md:33`), i.e. the data-only commands in `:15-21` (`complete_data`, `component_data`, `source_catalog`, `quality_report`). None of them ingests new satellite quarters or rescored A: `codify` / `build_real` / `activity.score` only run inside `run_all`. A new quarter therefore needs `make run` (`team_run --full`) after the caches and `asof` / `last_quarter` / `computed_on` are updated. The board line explicitly asks "who runs `run_all`", and the word `run_all` does not appear in the procedure. Fix: in step 3, write "Run `make run` (`uv run --locked --offline python -m src.pipeline.team_run --full`, which runs `src.pipeline.run_all`) after updating `asof`, `last_quarter` and `computed_on`; it exits non-zero on any STOP." Add "then compare `app_data/manifest.csv` with the previous accepted bundle and run `python -m src.pipeline.full_repro` if code changed" to step 4.

**LOW L7:** `:7` says "English reasons" but `kpi_values` also carries `reason_ar`, `level_word_ar` and the start-unknown label. `:15` uses a `powershell` fence with no WSL note. Fix: "English and Arabic reasons (`reason`, `reason_ar`)"; add one line "On WSL, F: paths are read as `/mnt/f/...` (`common.native_path`); mount first: `sudo mkdir -p /mnt/f && sudo mount -t drvfs F: /mnt/f`".

### T-AH-21: knowledge transfer, one page: met

Board: "Knowledge transfer pack, one page (deliverable 9)". About 380 words in 28 lines, so it fits one page. All six links resolve (`releases/ready-data/README.md`, `DATA_GUIDE.md`, `technical-track-a.md`, `data/HANDOFF.md`, `data/DATA_SOURCES_AND_GENERATION.md`, `data/PARTIAL_TASKS_CLOSURE.md`). Numbers match the repo: 12 R7 codes, capacity 4, 180 rows / 40 features (`data/EW_PROTOCOL_CURRENT.md:9`, `data/R2_REPORT.md:5`), binary target, heights after 2024 not approved. It names roles, not people.

**MEDIUM M13: no run command.** `knowledge-transfer.md:26` says "configure local paths and run `uv sync --locked`" but never names the current run command or the F: mount requirement. A new owner has to find `team_run` elsewhere. Fix: add one sentence: "Current run: `make current` (or `uv run --locked --offline python -m src.pipeline.team_run`); add `--full` / `make run` to refit Track A. Tests: `uv run --locked --offline pytest -q`. On WSL, mount F: at `/mnt/f` first." Do not add a test count; it goes stale.

## Standards axis (CLAUDE.md / AGENTS.md)

### Rules that are honoured

- Codes only: `BACKTEST_CURRENT.md` and `quality-report.md` carry case IDs and codes. `g_no_names` reports paths and counts, never the matched name (`gates.py:184-187`), as CLAUDE.md requires.
- Unknown stays unknown: annual heights and vegetation are left null; the backtest returns `None` for missing quarters (`backtest_check.py:32-39`).
- Publication cutoffs: frozen check statements at `published_date <= qend(qi)`.
- Fixed seed and `computed_on`; no threshold changed after a score. `BACKTEST_CURRENT.md:5` keeps the criterion at 5 despite 1 of 6.
- Thresholds from config: `n_images_min`, `backtest.*`, `heights_max_year`, `cycle_capacity`. Exceptions are listed in L2.
- English for code and docs.

### MEDIUM M12 (judgement): STOP does not prevent bad outputs from staying on disk

`run_all.main` writes every table, the cycle list, DuckDB and the manifest (`run_all.py:102-111`) and only then returns 1 on STOP. After a `no_names` or `separation` STOP, the offending files remain in `app_data` next to a fresh `manifest.csv`, and nothing marks them as failed. `complete_data` likewise writes `ml_dataset_extended*` before its gate. The exit code is correct; the leftover state is a decision for the owner (quarantine folder, a `STOP` marker file, or skipping `manifest()` on STOP). Listed under human decisions.

### LOW

- **L1** `backtest_check.py:2-9`: the docstring cites retired documents ("DATA_PLAN_FINAL section 3", "FIXES_PROTOCOL section 5"), keeps "literal 8, point in time 0, after start 0 of 8", and says "the other 14 compounds flagged". With 12 compounds and 6 cases there are 6 others. Fix: replace with "the other R7 compounds (6) flagged"; keep the before-corrections numbers only with "(historical, 8 cases)"; drop the retired document names.
- **L2** Magic numbers: `0.30` (`gates.py:102`), `0.02` (`:196`), `3` (`:85`, superseded by M4) and `n * 11` years (`:75`). `gates.py:37` heads the section "the nine gates" (10 gates plus one extra check). Fix: add `quality.data_or_city_share: 0.30` and `quality.veg_pull_max_diff: 0.02` to `configs/data.yaml` with the **same values**; use `len(range(2016, 2027))` or a `YEARS` constant shared with `build_real.sat_yearly`; rename the header to "the ten gates".
- **L3** `g_stuck` calls `dropna()` before `shift` (`gates.py:110`), so values on both sides of an NA gap count as consecutive. **(hand-derived)** `[0.5, NA, 0.5, 0.5, 0.5]` is flagged although no 4 consecutive quarters are equal. Fix: drop the `.dropna()`; `NaN == NaN` is False, so gaps then break the run naturally.
- **L4** `data/R1_REPORT.md` (T-AH-11 evidence) has missing spaces ("Scope:R7only,12coded", "K2retains", "Capacity4;capacity scenarios2/4/6", "remainsq2hold") coming from the literals in `delivery.py:158-166`. Fix: restore the spaces in those literals. The same pattern appears in `AGENTS.md` and `data/R2_REPORT.md`.
- **L5** `full_repro.py:14` hard-codes the backup folder `"2026-10-28_partial_tasks"`. Fix: use `f"{CFG['computed_on']}_full_repro"`. `Makefile:37-38` `test` runs `uv run pytest tests/ -v` without `--locked --offline`, unlike CLAUDE.md. Fix: `uv run --locked --offline pytest -q`.
- **L6** `run_all.main` is about 55 lines (`run_all.py:58-113`), above the 50-line limit. Fix: extract `_backtest(t, model, thr, mode, leak, kpi, run_id) -> None` for lines 91-98.
- **L8** `make_run_id` hashes config and raw caches but not code (`run_all.py:21-25`), so two code versions produce the same `run_id`. Fix (lineage, judgement): include `sha` of `src/pipeline/*.py` in the hash. This would change the `run_id` values, so record it before the next accepted bundle.
- **L9** Task-board evidence: T-AH-10 to T-AH-13 point at generated reports and T-AH-16, T-AH-20 and T-AH-21 at docs; none names a test. `annual-context.md:3` writes "Task AH-16" instead of "T-AH-16". Fix: name the new tests from H2, H3 and M9 in the Evidence lines, correct the ID, and keep `docs/REMAINING_TEAM_TASKS.md` in sync.
- **L10 (outside D3)** Ruff reports 17 errors repo-wide instead of the single expected RUF100. None is in a reviewed file; record it and fix separately (`ruff check --fix` handles 12 of them).

(The impact-column judgement under T-AH-12 is noted inline and not counted separately.)

## Fix list

### Fixable by a coder now (priority order)

1. **H1** Final `g_no_names` scan at the end of `team_run.main` covering `app_data`, private files, repo `data/**` and `docs/deliverables/quality-report.md`, raising on non-PASS. In `run_all`, scan after `write_duckdb()` and `manifest()`. Add `test_final_name_scan_covers_repo_data_files`.
2. **H4** `partial_exports.backtest_report`: merge `frozen_clock_check` and `activity_variant` from `app_data/backtest/summary.json` and print the frozen-clock result in `data/BACKTEST_CURRENT.md`.
3. **H2** `tests/test_backtest.py`: `readings` window, empty input, and `run` counts with no `%`.
4. **H3** `tests/test_gates.py`: PASS and fail cases for completeness, freshness, data_or_city and stuck_series.
5. **H5** `technical-track-a.md` step 3: `make run` / `team_run --full` (runs `run_all`) after updating `asof` / `last_quarter` / `computed_on`; step 4: manifest comparison and `full_repro`.
6. **M1** `g_completeness`: `ok = len(now) > 0 and bool(now.K4.all())`.
7. **M2** `g_no_names`: STOP when `pats` is empty, plus a test.
8. **M3** `TEXT_EXT` += `.html .htm .tsv .xml`; decode unknown files as UTF-8 before latin-1, plus a test.
9. **M4** `g_freshness`: quarter difference `<= 1` (the spec value); value text from the data's `last`, plus a test.
10. **M9** `codify`: combine `published` with `year <= heights_max_year`, plus `test_heights_after_max_year_are_dropped_even_when_published`.
11. **M10** Correct the height-coverage claims in `annual-context.md:5`, `technical-track-a.md:9` and the `delivery.py` R1 text.
12. **M6** `quality_report`: build the FLAG sentence from the rows, plus a test.
13. **M5** Add `run_id` / `computed_at` to `quality_checks.csv` and print the run id in the report.
14. **M11** Add `manifest_sha256`, `run_id`, `git_revision` and `computed_on` to `FULL_TRACK_A_REPRODUCIBILITY.json`; test that `manifest()` excludes `manifest.csv`.
15. **M8** Frozen check: cut vegetation at `summer_year(qi)`, move the quarter list to config (same values), return False on empty, fix the docstring.
16. **M7** `backtest_report`: use `CFG["backtest"]["levels"]` and the same "assessable" definition as `readings`.
17. **M13** `knowledge-transfer.md`: one line with the run command, tests command and WSL mount.
18. **L1-L9** Docstring, magic numbers, `g_stuck` gaps, R1 report spaces, backup name and `make test`, `run_all.main` length, `run_id` code hash, board evidence lines and the "AH-16" ID.

### Needs a human decision

19. Which quality log is canonical for the report: `real/quality_checks_log.parquet` (`run_all`) or `data_completion/quality_checks.csv` (`complete_data`) (M5). The board says `quality_checks_log`.
20. What a STOP should leave on disk (quarantine, marker file, or no manifest) (M12).
21. Whether each backtest case needs its own competing explanation and "what next", instead of the shared template (M7). The spec asks "per case".
22. Whether the frozen-clock check should also refit A on data up to each quarter, or the current "data cut, final model" scope is accepted and documented (M8).
23. Whether `full_repro` should run the two passes as separate processes (M11), and whether `run_id` should include a code hash (L8). The latter changes recorded `run_id` values.
24. The 2019Q2 `data_or_city` FLAG still needs the owner's explicit review decision (named in `quality-report.md:28` and `technical-track-a.md:33`).
25. Any real-data confirmation (F: drive): rerun `team_run --full` and `full_repro` on the current commit to refresh `BACKTEST_CURRENT.md`, the quality report and the reproducibility JSON after fixes 1, 2 and 14.

## Required before accepting D3

1. T-AH-11: fix 1 (full `no_names` coverage) and fix 4 (gate tests); fixes 6-9 for gates that cannot fail on empty or mis-specified input.
2. T-AH-10: fix 2 (frozen-clock result in the evidence) and fix 3 (backtest tests).
3. T-AH-20: fix 5 (quarterly recompute names `run_all` / `make run`).
4. T-AH-16: fixes 10-11 (year cap test, coverage claims).
5. T-AH-12: fix 12, and decision 19 recorded.
6. T-AH-13: fix 14, then decision 25 (a fresh two-run PASS on the current commit) before the "two runs identical" claim is relied on in the presentation.
7. Update each Evidence line on the board to name its tests (L9) and sync `docs/REMAINING_TEAM_TASKS.md`.
8. Re-run `.venv/bin/python -m pytest -q`, Ruff on the touched files and `git diff --check`.
