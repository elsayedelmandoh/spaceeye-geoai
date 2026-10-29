# Review 02: ahmed, D2 "indicators, levels, cycle list" (T-AH-04 .. T-AH-09)

Lane: reviewer. Branch `feat/ml` at `4822040` (includes `f63a712`, `c23a860`). Method: manual read of `src/pipeline/kpis.py`, `src/pipeline/{common,build_real,run_all,complete_data,gates}.py`, `configs/data.yaml`, `tests/`, the task board §D2 and `docs/requirements/01-specs.md` §2-§3.

The **Spec** axis is the six task lines in `docs/requirements/02-team-roles-and-tasks.md` "### D2: indicators, levels, cycle list" plus `01-specs.md` §2 (K1-K6, level table, may-be-complete cap, "not started"/"not assessable", reason sentence, cycle list) and §3. The **Standards** axis is `CLAUDE.md` / `AGENTS.md` plus the general code-quality rules. No sub-agents were used. The tasks landed across several commits, so I reviewed the current state of the files instead of a diff.

### What was run

- `.venv/bin/python -m pytest -q` → **65 passed, 1 skipped**.
- `.venv/bin/ruff check src/pipeline/kpis.py tests --output-format concise` → **All checks passed**.
- `git diff --check` → one hit: `docs/requirements/02-team-roles-and-tasks.md:314: new blank line at EOF`. That comes from the uncommitted board edit in the working tree, not from ahmed's D2 code.

### What could not be verified

- Throwaway `.venv/bin/python -c` behaviour checks of `level_of`, `fine_months` and `months_between` were blocked by the session's permission prompt (it asked for approval). Every behavioural claim below marked **(hand-derived)** comes from reading the code and doing the arithmetic by hand, not from running it.
- I did not run `run_all`, `complete_data` or `team_run`, and the external data was not available. I did not open the real `kpi_values.parquet` or `cycle_list_2026Q3.csv`, so I have not checked the actual exported columns, encoding or rows.

## Verdict

| Task | Reviewer on board | Spec result | Real test? |
|------|-------------------|-------------|------------|
| T-AH-04 K6 never-started clock | elsayed | **Met** (judgement calls on gaps and rounding) | Yes: `test_launch_does_not_confirm_observed_construction_and_k6_waits_for_publication`, `test_k6_does_not_treat_missing_or_unassessable_history_as_no_start`, `test_start_evidence_ignores_future_publications_and_future_event_dates` (tests/test_pipeline.py), `test_k6_priority_and_promise_publication_fallback_have_no_future_leakage` (tests/test_spec_data.py) |
| T-AH-05 K5 eligible months (real part) | elsayed | **Met.** Month arithmetic differs from K3. | Yes: `test_fine_union_retains_exposure_and_does_not_double_count_grace`, `test_missing_contract_deadline_or_no_start_evidence_is_not_zero_fine` (tests/test_spec_data.py). Nothing tests that K5 never sets the level. |
| T-AH-06 level rule | elsayed | **Partly met.** Rule is correct; the required test was not updated for K6 and "not assessable" has no test. | Partly: `test_level_is_the_worst_signal_and_may_be_complete_caps_at_3` was **not** updated for K6. K6 levels are tested in `test_k6_priority_and_promise_publication_fallback_have_no_future_leakage`. |
| T-AH-07 reason sentence EN + `reason_ar` | verina | **Partly met.** The two named examples are not tested, there is no English test, and the AR template omits level and score. | One test: `test_arabic_reason_keeps_unknown_deadline_and_missing_start_distinct` (tests/test_partial_tasks.py). |
| T-AH-08 cycle list export | nada | **Partly met.** Export exists but is written from two places; `rank_cycle`/`cycle_list` have no test. | No test of `rank_cycle` or `cycle_list`. `test_capacity_scenarios_only_select_eligible_rows` tests a separate copy of the ordering (`complete_data.capacity_paths`). |
| T-AH-09 `origin`/`run_id`/`computed_at` | elsayed | **Partly met.** The row-level columns exist; the column-origin gate is bypassed for `kpi_values`. | No test. |

Board evidence: every D2 task points only at `src/pipeline/kpis.py`. That is code, not evidence. T-AH-04 and T-AH-05 have real tests; T-AH-06 and T-AH-07 have partial tests; T-AH-08 and T-AH-09 have **no** test. Update each Evidence line to name the test functions above.

Findings: **0 CRITICAL, 4 HIGH, 9 MEDIUM, 4 LOW**. Do not tick "Review accepted" for T-AH-06, T-AH-07, T-AH-08 or T-AH-09 until the HIGH items are fixed.

## Spec axis

### T-AH-04: K6 never-started clock: met
Spec: "Months since the first published launch or promise with **no construction start** (no 4-quarter run of activity)" and board "level 1 if > 24, level 2 if 13-24".
- Computed in `add_start_evidence`, `src/pipeline/kpis.py:78-143`. The reference is the earliest launch (event date capped at publication) or the earliest promise *publication*, filtered `pub <= asof` (`kpis.py:113`, `:118`). There is no future leakage, and a test covers it (`test_spec_data.py:29`, `test_pipeline.py:103`).
- `K6 = max(0, months_between(ref_date, asof))` only when not confirmed and the history is complete, otherwise `pd.NA` (`kpis.py:134`). Unknown stays unknown, as CLAUDE.md requires.
- Thresholds come from config: `k6_l1: 24`, `k6_l2: 13` (`configs/data.yaml:72-73`). Levels: `k6 > L["k6_l1"]` → 1 (`kpis.py:157`), `L["k6_l2"] <= k6 <= L["k6_l1"]` → 2 (`kpis.py:159`). **(hand-derived)** At the boundaries, 12 gives no K6 level, 13 → 2, 24 → 2, 25 → 1. 12, 13 and 25 are tested at `test_spec_data.py:30-32`. **24 is not tested.**

**MEDIUM (judgement, needs human decision): one gap quarter disables K6 permanently.** `kpis.py:123` needs *every* quarter from the reference to the as-of quarter to be K4-assessable with a known `active`. A single cloudy quarter (K4 false) anywhere after launch makes K6 `NA` for every later quarter. A compound launched before the first satellite quarter also never gets K6, because `reindex(..., fill_value=False)` fills the missing range with False. This is consistent with "unknown stays unknown", but it can silently hide the indicator for most of R7. Fix (coder, no behaviour change): add a column count or a log line of how many `kpi_values` rows have `K6` NA because `start_observation_sufficient` is False, so the owner can see the impact. Whether to tolerate gaps is a human decision.

**MEDIUM (judgement, needs human decision): K6 and K3 round to the nearest month.** `common.months_between` is `round(days / 30.44)` (`src/pipeline/common.py:48-50`). **(hand-derived)** With ref `2023-06-10` and as-of `2024-06-30` (386 days), K6 = round(12.68) = **13** → level 2, but only 12 calendar months have passed. The same rounding applies to K3 (`kpis.py:263-264`). This is not a threshold change, but changing it would change levels, so it needs the owner's decision. Fix (coder, now): add a test that pins the current behaviour at the boundary (`months_between(pd.Timestamp("2023-06-10"), pd.Timestamp("2024-06-30")) == 13`) and document "nearest month, not completed months" in the `months_between` docstring.

### T-AH-05: K5 fine-eligible months (real part): met
Spec: "months past the first deadline with construction never started, plus months past the 12-month grace (K3 > 12)"; "K5 does not set the level on its own".
- `fine_months`, `kpis.py:170-190`: `no_start` counts months from the deadline to the observed start (or to as-of when the start is unknown but the history is sufficient). `grace = elapsed - grace_months` with `grace_months` taken from `CFG["fines"]["grace_months"]` (`data.yaml:83`, value 12). Union: `no_start + grace - overlap` with `overlap = max(0, no_start - grace_months)`. **(hand-derived)** Both intervals start at the deadline month, so months 13..min(a,e) are the overlap. No double counting. Tested at `test_spec_data.py:14-20`.
- Unknown stays unknown: no deadline → all NA. Start unknown and history insufficient → `no_start`/`K5_months` NA while `post_grace` stays known (`kpis.py:187`). Tested at `test_spec_data.py:23-26`. Correct.
- Never sets the level: `level_of` has no K5 argument (`kpis.py:153`). Met by construction, but no test asserts it.
- `K5_basis = "policy proxy; contract eligibility unverified"` (`kpis.py:269`). This fits the CLAUDE.md "screening exposure, not a fine" rule.

**MEDIUM: K5 uses calendar months and K3 uses rounded days.** `fine_months` uses `pd.Period(..., "M").ordinal` (`kpis.py:180-181`), and K3 uses `months_between` (`kpis.py:263`). **(hand-derived)** With deadline `2023-06-01` and as-of `2024-06-30`, K3 = round(395/30.44) = **13** (level 2, "past the grace"), yet `K5_post_grace_months = 12 - 12 = 0`. The spec defines post-grace as "K3 > 12", so the compound file would show "past grace" on the level and 0 post-grace months side by side. The gap appears only when the deadline is not a month end. Fix: needs a human decision on which arithmetic is canonical. A coder can add a test now that documents the case (`fine_months(pd.Timestamp("2023-06-01"), pd.Timestamp("2024-06-30"), None, True)["K5_post_grace_months"] == 0`), with a comment that it disagrees with K3 = 13.

### T-AH-06: level rule: partly met
Spec: "Level 1: K2 ≥ 4, or K3 > 24, or (K2 ≥ 2 and K3 > 12), or K6 > 24 / Level 2: K2 = 2-3, or K3 = 13-24, or K6 = 13-24 / Level 3: K2 = 1, or K3 = 1-12 / 4: otherwise (started) / Not started: no construction start, K6 ≤ 12 and no K3 date passed / Not assessable: K4 failed"; cap "level capped at 3".
- `level_of`, `kpis.py:153-167`: worst-of via the if/elif cascade; combo `k2 >= combo_k2 and k3 > combo_k3` (`kpis.py:157`); cap `max(lv, 3) if complete` (`kpis.py:167`); `None` when not started and nothing fires (`kpis.py:165-166`). **(hand-derived)** K3 12 → 3, 13 → 2, 24 → 2, 25 → 1; combo (2,12) → 2, (2,13) → 1. All match the table.
- "Not assessable": `level_of` is only called when `r.K4` (`kpis.py:270`), and `level_label`/`level_word` say "not assessable" (`kpis.py:272`, `:275`). Correct: no level is computed for K4-failed rows.

**HIGH: the required test update was not done.** Board: "update `test_level_is_the_worst_signal...` for K6". `tests/test_pipeline.py:17-24` has no K6 argument at all. The K6 cases live in a different test (`test_spec_data.py:29-33`), and "not assessable" has no test. Fix: add to `test_level_is_the_worst_signal_and_may_be_complete_caps_at_3` the asserts `kpis.level_of(0, 0, False, True, 25) == 1`, `kpis.level_of(0, 0, False, True, 24) == 2`, `kpis.level_of(0, 0, False, True, 13) == 2`, `kpis.level_of(0, 0, False, True, 12) == 4`, `kpis.level_of(0, 12, False) == 3`, `kpis.level_of(0, 13, False) == 2`, `kpis.level_of(0, 24, False) == 2`, `kpis.level_of(2, 12, False) == 2`, `kpis.level_of(0, 0, True, True, 30) == 3`. Add one `kpi_values`-level test (or a small helper test) asserting that a row with `K4 = False` has `level` NA and `level_label == "not assessable"`.

**MEDIUM (needs human decision): unknown K6 is labelled "not started".** `level_of` does `k6 = 0 if pd.isna(k6) else k6` (`kpis.py:156`). Using 0 so that an unknown K6 cannot *raise* the level is defensible: escalating on missing data would treat unknown as bad. But when `started=False`, K3 = 0 and K6 is NA (history has gaps), the row gets `level_label = "not started"` (`kpis.py:272`). The spec defines "Not started" as "K6 ≤ 12", which is not known here. Example input: `level_of(0, 0, False, False, pd.NA)` → `None` → "not started" / "watch", while the compound may have been unstarted for 30 months. The NA-as-zero is *not* a bug for the level number, but the label claims something unknown. Fix needs a human decision on the label (for example a separate "start unknown" label). Do not change thresholds.

**LOW: level 3 hard-codes `k2 == 1`.** `kpis.py:161` uses the literal `1` instead of `1 <= k2 < L["k2_l2"]`. The result is the same today, but it would silently disagree if `k2_l2` ever changed. Fix: replace `k2 == 1` with `1 <= k2 < L["k2_l2"]`.

### T-AH-07: reason sentence: partly met
Spec: "one fixed template, filled by code, codes only. **Arabic** in everything the committee sees … English form: 'Level 1: no building activity for 4 quarter(s) (activity score 0.12); first announced handover date (Jun 2024) passed by 27 months; observation complete (14 images in the quarter).' Arabic example: 'مفيش نشاط بقاله 3 أرباع، والميعاد المعلن فات بـ 8 شهور'"; board "+ test on the two examples".
- English `reason`, `kpis.py:193-220`, reproduces the English template structure. Arabic `reason_ar`, `kpis.py:223-247`, is stored in the `reason_ar` column (`kpis.py:274`). Both use codes only: no names, and not even the code is interpolated.

**HIGH: the two named examples are not tested, and there is no English test.** The only test is `test_arabic_reason_keeps_unknown_deadline_and_missing_start_distinct` (`tests/test_partial_tasks.py:18`), which checks a *not-started* row, not either spec example. Fix: add `test_reason_matches_spec_examples` in `tests/test_pipeline.py`. Build a row dict `{"K4": True, "started": True, "K2": 4, "activity_prob": 0.12, "handover": False, "first_end": pd.Timestamp("2024-06-30"), "K3": 27, "may_be_complete": False, "K6": pd.NA, "n_images": 14, "level": 1}` and assert `kpis.reason(row) == "Level 1: no building activity for 4 quarter(s) (activity score 0.12); first announced handover date (Jun 2024) passed by 27 months; observation complete (14 images in the quarter)."` For the second example, use `K2 = 3`, `K3 = 8` and assert `"3" in kpis.reason_ar(row)` and `"8" in kpis.reason_ar(row)` and `"لم يرصد نشاط بناء" in ...` and `"تجاوز أول موعد تسليم معلن" in ...`. The spec Arabic example is colloquial and the code writes formal Arabic, so assert on the substrings, not exact equality.

**MEDIUM: the Arabic text is not the same template as the English.** `reason_ar` has no level head (English starts `Level N:` / `Not started:`, `kpis.py:219`), omits the activity score, and puts K6 *before* may-be-complete while English puts it *after* (`kpis.py:242-245` vs `:214-217`). The docstring says "using the same evidence as the English reason", which the code does not honour. The committee CSV does carry `level_word_ar` separately, so this is a consistency issue, not data loss. Fix: in `reason_ar`, prefix `f"المستوى {r['level']}: "` (or `"بداية غير مؤكدة: "` when the level is NA), add the activity score `f"(درجة النشاط {a:.2f})"` to the activity part, and move the K6 part after may-be-complete to match the English order.

### T-AH-08: cycle list export: partly met
Spec: "Cycle list: capacity 4, eligible priorities 1-3, ordered by priority level, descending K2/K3 and code"; board "top N with level 1-3, ordered K2 then K3 descending, CSV (Arabic reason, level as a word) for the as-of quarter · `app_data/real/cycle_list_<asof>.csv`".
- `rank_cycle`, `kpis.py:294-301`: filters `level.notna() & level <= 3`, sorts `["level", "k2", "K3", "code"]` ascending `[True, False, False, True]`, takes `CFG["cycle_capacity"]` (= 4, `data.yaml:75`). Ties are broken by `code`, so the order is deterministic. Spec §2 orders by level first; the board text omits "level". The code follows §2. Align the board wording.
- `cycle_list`, `kpis.py:304-306`: includes `level`, `level_word`, `level_word_ar`, `reason`, `reason_ar`, `origin`, `run_id`, `computed_at`. Level is given as a word and the reason in Arabic. Met.
- Written to `REAL / f"cycle_list_{CFG['asof']}.csv"` with `utf-8-sig` in **two** places: `src/pipeline/run_all.py:103` and `src/pipeline/complete_data.py:207` (the latter also writes `data_completion/cycle_list.csv` at `:206`). `asof: "2026Q3"` (`data.yaml:5`).

**HIGH: no test of `rank_cycle` or `cycle_list`.** The only ordering test, `test_capacity_scenarios_only_select_eligible_rows` (`tests/test_spec_data.py:42`), exercises `complete_data.capacity_paths`, a separate copy of the sort. Fix: add `test_rank_cycle_takes_top_capacity_levels_1_to_3_in_spec_order` in `tests/test_pipeline.py`. Use one quarter with 6 rows: levels `[1, 2, 2, 3, 4, NA]`, give the two level-2 rows equal K2 and different K3, and add a tie on K2 and K3 broken by code. Assert that `cycle_rank` is 1..4 on the expected codes, NA on the level-4 and NA-level rows, and that `cycle_list(out, q).columns` contains `reason_ar` and `level_word_ar`.

**MEDIUM: duplicated ordering logic.** `kpis.rank_cycle` (`kpis.py:299`) and `complete_data.capacity_paths` (`complete_data.py:37-38`) re-implement the same filter and sort. If one changes, the cycle list and the capacity scenarios drift apart. Fix: extract `kpis.eligible_order(group) -> pd.DataFrame` (filter level 1-3, add `k2`, sort) and call it from both.

**MEDIUM: shotgun write of the same file.** `cycle_list_<asof>.csv` is written by both `run_all.py:103` and `complete_data.py:207`, from `kpi` frames built with different `run_id`s (`complete_data.py:183` calls `run_all.make_run_id()` again). Whichever runs last wins. Fix: keep the write in one place (`run_all`), or make `complete_data` write only its own `data_completion/cycle_list.csv`. Which one is canonical is a judgement call for the owner.

### T-AH-09: `origin`, `run_id`, `computed_at`: partly met
Spec (board): "`kpi_values` carries `origin`, `run_id`, `computed_at` for every new column (K5, K6, reason_ar)".
- `kpis.py:290` sets row-level `origin = "derived"`, `run_id`, and `computed_at = CFG["computed_on"]` on every row, so every column, K5/K6/`reason_ar` included, sits on a row that carries the three fields. That meets the letter of the spec.

**HIGH: the column-origin gate is bypassed for `kpi_values`.** `gates.g_separation` (`src/pipeline/gates.py:89`) builds the allowed set for `kpi_values` as `{c: "derived" for c in kpi}`, i.e. from the frame itself, so a missing-origin column in `kpi_values` can never be flagged. `build_real.ORIGINS` (`build_real.py:169-184`) has no `kpi_values` entry. The new columns (`K5_*`, `K5_basis`, `reason_ar`, `level_word_ar`, `k3_first_deadline`, `cycle_rank`) have no declared origin anywhere. Fix: add an explicit `KPI_ORIGINS` dict in `kpis.py` listing every output column (derived vs key) and use it in `g_separation` instead of the self-generated dict. Add `test_every_kpi_values_column_has_a_declared_origin`, which builds `kpi_values` from a small fabricated input (reuse the frames from `test_k6_priority_and_promise_publication_fallback_have_no_future_leakage`) and asserts `set(out.columns) <= set(KPI_ORIGINS) | {"origin", "run_id", "computed_at"}`.

**LOW (judgement): `computed_at` is a fixed stamp.** `computed_on: "2026-10-26"` (`data.yaml:4`) predates the K6 config (`ca24988`, 2026-10-28). It is a reproducibility constant, not the actual computation date. Say so in the data dictionary so no one reads it as "K6 computed on 26 Oct".

## Standards axis (CLAUDE.md / AGENTS.md)

### Rules that are honoured
- Codes only / no names: `reason`/`reason_ar` interpolate numbers and dates only.
- Unknown stays unknown: K6, K5 and K2 use `pd.NA`/`np.nan` and `Int64`. `inactive()` treats missing as neither active nor inactive (`kpis.py:34-36`).
- Publication cutoffs: statements, promises, handovers and events are filtered by `published_date <= qend(qi)` (`kpis.py:59`, `:109`, `:113`, `:118`, `:257`, `:260`).
- Thresholds from config: `levels`, `fines.grace_months`, `cycle_capacity`, `veg_complete`, `n_images_min` and `start.run_quarters` all come from `configs/data.yaml`.
- K5 is labelled a policy proxy (`kpis.py:16`, `:175`, `:269`). Arabic text is preserved as data (`reason_ar`, `level_word_ar`).
- Determinism: ranking ties are broken by `code`, and outputs are sorted by `["qi", "code"]`. There is no randomness in this module.

### MEDIUM: function length and nesting
- `add_start_evidence` is 66 lines (`kpis.py:78-143`), above the 50-line limit, with 11 parallel accumulator lists. Fix: extract `_k6_row(g, i, qi, ...) -> dict` that returns one row's evidence and build the frame from a list of dicts.
- `add_k2` nests four levels (`for code` → `for i` → `for j` → `if`, `kpis.py:52-72`). Fix: extract `_k2_at(g, i, st) -> int` for the inner backward count.

### MEDIUM: stale module docstring
`kpis.py:6` says "K5 was dropped on 26 Oct 2026 because it added nothing", which contradicts `kpis.py:16` and the K5 code in this file. `kpis.py:2` lists only "K2, K3, priority level…". Fix: delete the "K5 was dropped…" clause and list K5 (real part) and K6 on line 2.

### LOW: magic numbers / duplicated helpers
- `event_starts` hard-codes `(start.dt.year - 2016) * 4 + (start.dt.month - 1) // 3` (`kpis.py:44`), duplicating `common.qindex`. `veg_latest` also hard-codes 2016/2015 (`kpis.py:148`). Fix: add `common.qindex_of(ts)` and use it in both places (and at `kpis.py:122`).
- The level-to-word mappings are inline dict literals repeated in the row loop (`kpis.py:272`, `:275-276`). Fix: module constants `LEVEL_WORD`, `LEVEL_WORD_AR`, plus one helper `level_words(k4, lv) -> tuple[str, str, str]`.

### Note (no finding): mutation
`rank_cycle` copies first, then assigns with `.loc` (`kpis.py:296-300`). This is acceptable and does not mutate the caller's frame.

### LOW: board evidence
Every D2 Evidence line links only `../../src/pipeline/kpis.py`. Per CLAUDE.md ("Verify relevant behavior and document evidence"), each line should name its tests (see the Verdict table). Leaving the T-AH-08 and T-AH-09 main `[x]` without any test conflicts with "Do not infer completion from … a successful unrelated test".

## Fix list

### Fixable by a coder now (priority order)
1. T-AH-06: extend `test_level_is_the_worst_signal_and_may_be_complete_caps_at_3` with the K6/K3/combo boundary asserts listed above, and add a "not assessable" row test. (HIGH)
2. T-AH-07: add `test_reason_matches_spec_examples` (exact English example, Arabic substrings for the second example). (HIGH)
3. T-AH-08: add `test_rank_cycle_takes_top_capacity_levels_1_to_3_in_spec_order` covering filter, order, code tie-break and `cycle_list` columns. (HIGH)
4. T-AH-09: add `KPI_ORIGINS` in `kpis.py`, use it in `gates.g_separation` instead of `{c: "derived" for c in kpi}`, and add `test_every_kpi_values_column_has_a_declared_origin`. (HIGH)
5. Extract the shared eligible-order helper used by `rank_cycle` and `capacity_paths`. (MEDIUM)
6. Make `reason_ar` mirror the English template: level head, activity score, K6 after may-be-complete. (MEDIUM)
7. Fix the stale `kpis.py:1-6` docstring. (MEDIUM)
8. Split `add_start_evidence` (<50 lines) and flatten `add_k2` nesting. (MEDIUM)
9. Add tests pinning the current month arithmetic: `months_between("2023-06-10", "2024-06-30") == 13`, and `fine_months("2023-06-01", "2024-06-30", None, True)["K5_post_grace_months"] == 0` with a comment that K3 = 13 there. Add an assert that K6 = 24 → level 2. (MEDIUM, documents only)
10. Replace `k2 == 1` with `1 <= k2 < L["k2_l2"]`; add `common.qindex_of`; add `LEVEL_WORD`/`LEVEL_WORD_AR` constants. (LOW)
11. Update each D2 Evidence line on the board to name its test functions, and keep `docs/REMAINING_TEAM_TASKS.md` in sync. Remove the blank line at EOF of the board. (LOW)

### Needs a human decision
12. Label for "started = False, K3 = 0, K6 unknown": keep "not started" or introduce a separate "start unknown" label.
13. Canonical month arithmetic: rounded `days/30.44` (K3, K6) vs calendar months (K5). Changing either changes levels or exposures, so the owner must decide *and* record that no score was looked at.
14. Whether one non-assessable quarter should disable K6 for all later quarters (current strict rule), at minimum reported as a count.
15. Which pipeline step owns `app_data/real/cycle_list_<asof>.csv` (`run_all` vs `complete_data`).
16. Board wording for T-AH-08 ("level, then K2, then K3, then code" per spec §2).

## Required before accepting D2

1. Update the T-AH-06 level test for K6 and add the not-assessable test (fix 1).
2. Add the T-AH-07 spec-example reason test (fix 2).
3. Add the T-AH-08 `rank_cycle`/`cycle_list` test (fix 3).
4. Declare `kpi_values` column origins and stop the gate from generating them from the frame (fix 4).
5. Point each D2 Evidence line at its tests (fix 11).
6. Record the human decisions 12-15 (or explicitly defer them) before claiming the K6 and cycle-list behaviour is final.
7. Re-run `.venv/bin/python -m pytest -q`, Ruff on touched files and `git diff --check`.

Reviewer identity, date and PR are intentionally left blank: this is a draft review, not a sign-off. Record them only after a human reviewer accepts.

## Resolution status (working tree, not yet reviewed by a human)

Fixes applied by the coder lane and verified by the orchestrator (65 -> 75 passed, 1 skipped; Ruff clean on touched files apart from an old RUF100 in `activity.py`; a differential run of old vs new `add_k2`/`add_start_evidence` on 60 random fixtures gave identical frames; `KPI_ORIGINS` equals the 37 columns of the real `kpi_values` schema recorded in `data/dictionaries/real__kpi_values.md`).

| Fix | State |
|-----|-------|
| 1 level test for K6/K3/combo boundaries, "not assessable" test | DONE |
| 2 spec-example reason test | DONE |
| 3 `rank_cycle`/`cycle_list` test | DONE |
| 4 declare `kpi_values` column origins, stop the gate generating them | DONE (`kpis.KPI_ORIGINS`, used by `gates.g_separation` and the dictionary writer; the real run itself was not executed because the external F: data is not available here) |
| 5 shared ordering helper | DONE (`kpis.eligible_order`) |
| 6 `reason_ar` mirrors the English template | DONE (level head, activity score, K6 after may-be-complete); the Arabic wording still needs a native-speaker review before committee use |
| 7 stale module docstring | DONE |
| 8 split `add_start_evidence`, flatten `add_k2` | DONE, behaviour preserved |
| 9 pin month arithmetic | DONE |
| 10 small cleanups | DONE (`summer_year`, `qindex_of`, level-word constants) |
| 11 board Evidence lines name their tests; T-AH-08 wording | DONE |
| 12 label for unknown start | DONE: "start unknown" when K4 passes, no construction start and K6 is unknown; spec table and dictionary updated; scenario exports keep the label |
| 13 month arithmetic | KEPT as is and documented (spec section 2 and `months_between`) |
| 14 strict K6 gap rule | KEPT and documented (spec section 2) |
| 15 owner of `cycle_list_<asof>.csv` | DONE: `run_all` owns the real path; `complete_data` writes only its own `data_completion/cycle_list.csv` |
| 16 T-AH-08 board wording | DONE |

Small remaining note: for "start unknown" rows the Arabic reason head still reads "بداية غير مؤكدة", while `level_word_ar` reads "بداية غير معروفة".

Reviewer identity, date and PR remain blank; no D2 "Review accepted" box is ticked.
