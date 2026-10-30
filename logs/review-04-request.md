# Review request 04: what closes ahmed's open tasks (T-AH-13, 14, 15, 18, 19, 22)

Prepared by the task owner on 30 October 2026 for the board reviewer (elsayed). This is a request, not a review: no "Review accepted" box is ticked here.

## Earlier reviews: status
- **review-01 (D1)** and **review-02 (D2):** all fixes are done, and the board records their acceptance (T-AH-01 to T-AH-09).
- **review-03 (D3/D5):**
  - H1 to H5 and M1 to M13 are fixed (commits listed in review-03 and on the board).
  - L4 (missing spaces in the R1/R2 report text) is fixed on `fix/data-v6`.
  - Decision 25 (a real-data rerun on the current commit) is done; see T-AH-22.
  - Decisions 19 to 24 are still owner decisions; see the last section.

## Per task: evidence to check

| Task | What to verify | Evidence |
| --- | --- | --- |
| T-AH-13 two runs identical | A fresh two-run PASS tied to a commit | `data/FULL_TRACK_A_REPRODUCIBILITY.json`: 301 equal artifacts, manifest sha256 b4c86dee…, run id R1-1846440cf3, git revision 75a581a, computed_on 2026-10-30. Both runs share one process (M11 option not taken). |
| T-AH-14 K1 fallback | The switch works, the default is unchanged, and the effect is measured without being used to choose | `activity.apply_source`, config key `activity.source: k1` (absent = model), `tests/test_activity_fallback.py`, `data/K1_FALLBACK_CHECK.md`, technical doc section "Activity fallback". |
| T-AH-22 real-data run | Steps 1 to 5 of the task line | (1) `team_run --full` and `full_repro` PASS. (2) Regenerated `BACKTEST_CURRENT.md` (frozen clock true at 4 quarters), quality report, R1/R2, current metrics. (3) separation and no_names PASS on the real `kpi_values`. (4) v2 Stage 1: `EW_REPORT_V2.md`, `EW_V2A_VS_V1.md` (protocol hash matched; v1 stays primary). (5) Numbers in the PR description. |
| T-AH-15 images | Pair rule, publication cutoffs, attribution, no Esri pixels in Git | Branch `feat/ah15-imagery-comparison`: `inspection_pair`, `get_images(quarter=…)`, `imagery_html`, `tests/test_imagery.py`. Two follow-ups before merge: (a) show the capture age at the as-of quarter in the caption (the latest capture is about 14 months old); (b) state that generated inspection HTML embeds Esri images and must not be committed or redistributed. |
| T-AH-18 roof uniformity | Owner decision: test or cut | Spec section 13 puts it first in the cut order ("cut at D4 anyway"). Proposed: cut, recorded on the board; no test is run. |
| T-AH-19 code freeze | Tag after the v6 and imagery merges | Tag `main` after both PRs merge. `make run` (`team_run --full`) is the one run command. |

## Owner decisions from review-03: confirmed by ahmed on 30 October 2026
19. **Canonical quality log:** `data_completion/quality_checks.csv` for the report, with the Track A record kept in `real/quality_checks_log.parquet`. Both already carry the same run id.
20. **State after a STOP:** keep the files and write no manifest. A STOP returns a non-zero exit and the release steps refuse to package.
21. **Backtest explanations:** keep the shared template and add one line per case from its own numbers (assessable quarters, first alert). No new criterion.
22. **Frozen-clock check:** accept "data cut, final model" and document it. Refitting A per quarter is out of scope.
23. **Two-run check:** keep it in one process for now, and add the code hash to `run_id` only at the next accepted bundle (this changes recorded run ids).
24. **2019Q2 data_or_city FLAG:** checked. Dynamic World image counts are normal: the median per compound is 10 in 2019Q1, 14 in 2019Q2 and 19 in 2019Q3, all above the minimum of 6. Only one compound had a level in 2019Q2, so a single compound with K2 = 1 makes the share 1 of 1. The flag comes from that one-compound denominator, not from a source event or a city event. It stays visible as FLAG with this note, and the gate is not changed after seeing it.

Implemented on `fix/data-v6`:
- 20: `run_all` writes no manifest on a STOP and removes an old one; `bundle` refuses to package without a manifest.
- 21: the backtest report has a "This case" column built from each case's own quarters.
- 22: the docstring and the technical doc state "data cut, final model".
- 19, 23 and 24: recorded here.
- T-AH-18: cut, as recorded on the board.
