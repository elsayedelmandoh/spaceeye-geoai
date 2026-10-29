# Review 01: ahmed, D1 "scope and config" (T-AH-01, T-AH-02, T-AH-03)

Lane: reviewer. Branch `feat/ml` at `637ee3d`. Method: manual read of `configs/data.yaml`, `src/pipeline/{codify,build_real,release,kpis}.py`, `tests/`, the task board and evidence docs.

Adaptation of `/code-review`: the skill assumes a diff against a fixed point, an issue tracker doc (`docs/agents/issue-tracker.md`, missing) and two sub-agents. None was supplied, so the **Spec** axis is the three task lines in `docs/requirements/02-team-roles-and-tasks.md` §4 and the **Standards** axis is the repo `CLAUDE.md`. No sub-agents were used. The three tasks landed across several commits, so I reviewed the current state of the files instead of a diff.

Not verified: `uv run --locked --offline pytest` could not run here (offline cache is missing `sqlglot==30.24.0`). Findings below come from reading code, not from a test run.

## Verdict

| Task | Reviewer on board | Result |
|------|-------------------|--------|
| T-AH-01 R7 boundaries and count | elsayed | Mostly met. Count is recorded; the 80% confidence rule is not enforced in code. |
| T-AH-02 config before results | salma | Met on values. Dated comment and the "before any result" claim are weak. |
| T-AH-03 R8 filter and test | elsayed | **Test missing.** Filter exists; the required test does not. |

Nothing here is CRITICAL. Two HIGH findings. Do not tick the "Review accepted" boxes for T-AH-03 until the test exists.

## Spec axis

### T-AH-03: HIGH, no test that R8 never reaches `kpi_values`
Spec: "+ test that no R8 code reaches `kpi_values`".
- The filter is `cm = cm[cm.district.isin(CFG["scope_districts"])]` in `src/pipeline/codify.py:186`, so it runs in `codify`, not in `build_real` as the task says.
- `release.py:32` checks `set(compounds.district) <= set(scope_districts)`. That covers the `compounds` table at release time only, not `kpi_values`, and it is a release audit, not a test.
- `grep -rn "R8\|scope_districts" tests` returns nothing. The required test does not exist.
- Fix: add a test that builds or loads `kpi_values` and asserts every `code` is in `compounds.code` and every `compounds.district` is in `scope_districts`. Add a negative case with a fabricated R8 row.

### T-AH-03: MEDIUM, "every built table" is not asserted
The filter happens once upstream on the code map. Tables built from other sources (satellite, geometry, facts, `eval_outcomes`) are assumed to inherit it. `release.audit` checks `*_known_codes` per table, which is a reasonable proxy, but the board wording ("every built table") deserves a test over all of `build_real.ORIGINS`.

### T-AH-01: HIGH, the boundary confidence ≥ 80% rule is a docstring only
Spec: "Confirm R7 boundaries (confidence ≥ 80%)".
- `codify.py:25` states "a compound enters only with a boundary (confidence >= 80%)", but `codify.py:30` maps the label to `"medium"` or the raw label. No numeric threshold is compared anywhere (`grep` for `0.8`/`>= 80` in `src configs tests` finds nothing relevant).
- `configs/data.yaml` has no key for the confidence threshold.
- `D1_DECISIONS_CURRENT.md` and `01-specs.md` say working boundaries "retain source confidence". That is a different, weaker statement than "≥ 80%".
- Fix: either put the threshold in config and enforce it in `codify`, or amend the task text and spec to say what is actually done.

### T-AH-01: LOW, count is recorded
`01-specs.md` §16 item 4 records "12 R7 compounds, six public backtest cases, capacity 4". `data/DATASET_CONTRACT.md` agrees (12 compound rows, 12 polygons). Spec met.

### T-AH-02: values are present and consistent
- `cycle_capacity: 4` with the comment "12 R7 compounds / 3, fixed before rebuilding". `complete_data.py:180` checks it equals `ceil(n * inspection_capacity_fraction)`.
- K6 thresholds `k6_l1: 24`, `k6_l2: 13` match "12 / 24" in intent: K6 ≥ 13 gives level 2, K6 > 24 gives level 1. The board says "12 / 24"; the config uses 13/24 boundaries. Same behaviour, different wording. Align the task text.
- K5 grace `grace_months: 12` exists under `fines`. **MEDIUM:** a second `grace_months: 12` sits under the generator `warnings` block (`data.yaml` ~line 230). Same name, different meaning (complaint warnings). Rename one to avoid reading the wrong one.
- R7 filter key: `scope_districts: [R7]`. Met.

### T-AH-02: MEDIUM, "dated comment" and "before any result"
- Dated comments exist on `scope_districts` (2026-10-27) and `backtest` (2026-10-26). `cycle_capacity`, `levels` and the K6 keys carry no date.
- `computed_on: "2026-10-26"` is still in the file, but `cycle_capacity` was added or changed on 2026-10-27/28 (`fe71e5b`, `ca24988`). "Fixed before rebuilding" is a claim that git history alone cannot confirm; `k6_l1/l2` were added by the imported-spec extension on 28 Oct (see `kpis.py:14-15`), i.e. after earlier scores existed. This conflicts with CLAUDE.md: "Do not change thresholds, data or noise after looking at a score." Please record the date, the author and that no score had been seen.

## Standards axis (CLAUDE.md)

### Evidence links broken (HIGH for traceability)
Every D1 task cites `[implementation/output](../data/DATASET_CONTRACT.md)`. From `docs/requirements/` that resolves to `docs/data/`, which does not exist. The files live in the repo-root `data/` directory (`git ls-files` shows `data/DATASET_CONTRACT.md`; teammate commit 9b73671 2026-10-29 "drop docs/data/ prefix; use top-level data/" moved it deliberately) (resolved, see Resolution status), while `CLAUDE.md` says "current source contracts live in docs/data". Either the folder moved or the links and CLAUDE.md are stale. Fix the links (`../../data/...`) or move the folder, and keep `docs/REMAINING_TEAM_TASKS.md` in sync. The evidence also points at one generic contract file, not at a per-task artifact (the exact config lines, the test).

### Task board rules
- Main `[x]` with "Implemented; review pending" and an unchecked "Review accepted" box matches the CLAUDE.md convention. Good: no invented reviewer sign-off.
- Because the T-AH-03 test is missing, the main `[x]` for T-AH-03 is not supported by evidence. Per CLAUDE.md ("Do not infer completion from a placeholder... or a successful unrelated test") it should be unchecked until the test lands, or relabelled partial.

### Code smells (judgement calls)
- Possible Mysterious Name: `scope_districts` is the only filter key; the board calls it "R7 filter key". Consistent enough, but name it in the task text.
- Possible Duplicated Code: scope filtering is applied in `codify.py` and re-checked in `release.py` in different forms. Acceptable as defence in depth if tested.
- Lint: no ruff run (CLAUDE.md asks to lint touched Python). `git diff --check` is clean on the working tree.

## Required before accepting D1

1. Add the R8 test (T-AH-03). Blocks acceptance.
2. Decide and enforce or reword the ≥ 80% boundary confidence rule (T-AH-01).
3. Fix the `../data/` evidence links or the folder location, and CLAUDE.md. (resolved, see Resolution status)
4. Date the `cycle_capacity` and K6 config lines and state that no score had been seen (T-AH-02).
5. Rename the duplicate `grace_months`; align "12 / 24" with 13/24 in the task text.
6. Re-run `uv run --locked --offline pytest -q` and Ruff once dependencies are in the offline cache.

Reviewer identity, date and PR are intentionally left blank: this is a draft review, not a sign-off. Record them only after a human reviewer accepts.

## Resolution status (working tree, not yet reviewed by a human)

1. R8 test: DONE (tests/test_scope.py 4 scope + per-table parametrized; codify.py in_scope(); release.py scope_checks(); 65 passed, 1 skipped).
2. 80% boundary confidence: DONE by REWORDING — categorical label, no numeric % exists; docs/docstrings now say "reviewed confidence label, no numeric threshold".
3. Evidence links/folder: DONE — top-level data/ (commit 9b73671); links ../../data/...; CLAUDE.md/AGENTS.md/README updated.
4. Dated config: DONE. configs/data.yaml has "recorded <date> in commit <hash>" comments (cycle_capacity 215980b 2026-10-26; k6_l1 ca24988 2026-10-28). The person who set these values stated on 2026-10-29 that they were set before any score was seen; git cannot prove it, and the earliest committed score outputs (7de6acb, 2026-10-28 20:19 +03:00) came after both config commits, which is consistent with the statement.
   - git evidence only: `cycle_capacity` first appears in 215980b (2026-10-26 02:13 +03:00, "add data config and the codify step"); `k6_l1` first appears in ca24988 (2026-10-28 17:20 +03:00). The earliest tracked score outputs (docs/data/BACKTEST_CURRENT.md, EW_REPORT_CURRENT.md, later moved to data/) were added in 7de6acb (2026-10-28 20:19 +03:00), i.e. after both config commits. Scores computed locally and never committed are invisible to git, so "no score seen" is still the owner's statement to make.
5. Duplicate grace_months: DONE — complaint_grace_months=12; board text aligned (13-24 L2, >24 L1).
6. Offline pytest/ruff: pytest 65p/1s via .venv; uv --offline fails (sqlglot missing); ruff old warnings only (I001, RUF100).

Required items 1-6 left unticked per instructions; reviewer / date / PR blank.
