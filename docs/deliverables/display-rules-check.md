# T-NA-08 display-rules check of the four screens

Update, 3 November 2026: the owner lifted forbidden mistake 3 (different-season comparison). Image comparisons now accept any two dates; the rows on that rule below are kept as the record of the earlier check.

Scope: the four sidebar screens in `app.py` (`SCREENS`, app.py:65-70) checked against the display rules and forbidden mistakes in `docs/requirements/01-specs.md` section 9 (line 312 onward, "Display rules" paragraph). Code basis: branch `docs/T-NA-08-display-20261102`, based on `origin/main` (4543426). Read-only check; no code changed.

Not covered by this check: the ten-second test with a person outside the team (recorded separately). Also not in the four screens: the spec's "Data trust" screen (spec screen 4) has no entry in `SCREENS`; the spec's screen 3 name "Would it have warned?" is "3 · District view" in code.

Verdict key: PASS = rule met in the rendered code; FAIL = rule broken or missing in the rendered code; NOT CHECKED = needs data or a runtime view that the code alone cannot settle.

Shared helpers referenced below: `metric_tile` (app.py:156-161) composes value, unit, denominator, as-of and origin; `_kpi_tile` (app.py:655-658) wraps it; `finding` (app.py:176).

## Screen 1 · Priority map (`screen_priority_map`, app.py:1008)

| Element | Rule | Found | Verdict |
| --- | --- | --- | --- |
| Main tiles | at most 4 | Four tiles from `render_summary_tiles` (`st.columns(4)`, app.py:516). Cycle cards (app.py:983) are cards, not tiles. | PASS (app.py:516) |
| Tile "To visit this cycle" | value, unit, denominator, as of, origin | Value, unit, "of N", as-of, origin all passed to `metric_tile` (app.py:518) | PASS |
| Tile "At level 1" | value, unit, denominator, as of, origin | Denominator text is "inspect now", which is an action, not a denominator (app.py:520-522) | FAIL (app.py:520-522) |
| Tile "Fine-eligible months" | value, unit, denominator, as of, origin | "in N compounds · the contract decides the fine", as-of, origin (app.py:524-525) | PASS |
| Tile "Promised dates ahead" | value, unit, denominator, as of, origin | "in N compounds", as-of, origin (app.py:527-528) | PASS |
| Headline sentence | as-of and origin on numbers | Built by `cycle_headline` (app.py:491-503) with "N of M compounds, as-of" | PASS |
| Percent without denominator (forbidden 1) | no bare % | No percentage shown on this screen | PASS |
| Truncated axis (forbidden 2) | axes start at zero | No chart on this screen (map and table only) | PASS |
| Different-season comparison (forbidden 3) | no cross-season pairs | No image comparison on this screen | PASS |
| Average hiding spread (forbidden 4) | no bare averages | No average shown | PASS |
| Unannounced coverage change (forbidden 5) | coverage change announced | Denominators "of N" (app.py:501, 518) and "Changes since" panel (app.py:588-605) list joins and leaves only; no coverage-change line exists in code | NOT CHECKED (needs a quarter pair with a coverage change to test) |
| Track switch on every screen | visible on screen | Sidebar selectbox (app.py:1453-1462), called from `main` for every screen (app.py:1490) | PASS |
| Generated numbers marked (Track B) | 🟠 on each generated number | Track B shows Track A numbers only; generated inspection-file buttons carry 🟠 (app.py:561-575) | PASS |
| Map hidden in Track B | no map in Track B | `render_map_slot` returns early when generated (app.py:411-412) | PASS |
| Level never by colour alone | word with colour | Level shown as a word via `level_word` (app.py:314, 548) | PASS |

## Screen 2 · Compound file (`screen_compound_file`, app.py:1024)

| Element | Rule | Found | Verdict |
| --- | --- | --- | --- |
| Main tiles | at most 4 | Five tiles: `st.columns(5)` in `render_kpi_tiles` (app.py:702), called at app.py:1061 | FAIL (app.py:702) |
| Tile "Priority level" | value, unit, denominator, as of, origin | Unit empty, denominator "worst of K2, K3, K6", as-of, origin (app.py:704-706) | PASS |
| Tile "K2 no activity" | all five parts | Unit "quarter(s)", denominator, as-of, origin via `_kpi_tile` (app.py:708-709) | PASS |
| Tile "K3 handover clock" | all five parts | Text branch passes unit "" (app.py:712-713); number branch complete | PASS (text branch carries its unit in the value; NOT CHECKED that the text states the unit) |
| Tile "K6 never started" | all five parts | Text branch "does not apply" with unit "" (app.py:719-720) | PASS (same note) |
| Tile "K5 fine-eligible months" | all five parts | Text branch "no published deadline" with unit "" (app.py:727-728) | PASS (same note) |
| Wayback tiles | value, unit, denominator, as of, origin | Two `st.metric` calls, "Captured" and "Stage in YEAR", with no denominator and no origin (app.py:848-849) | FAIL (app.py:848-849) |
| Percent without denominator (forbidden 1) | no bare % | No % shown; the activity score is on a 0-1 axis labelled "0-1" (app.py:752) | PASS |
| Truncated axis (forbidden 2) | axis not truncated | Curve y-axis fixed to domain [0, 1] (app.py:752); bars and strip have no domain override | PASS |
| Different-season comparison (forbidden 3) | comparisons same season | "Compare: from/to" selectboxes accept any two captures (app.py:824-832); capture slider has no season guard (app.py:834-852) | FAIL (app.py:824-832) |
| Average hiding spread (forbidden 4) | no bare averages | No average shown | PASS |
| Unannounced coverage change (forbidden 5) | coverage change announced | Not assessable shown as a warning for a missing row (app.py:1055); no coverage-change line | NOT CHECKED |
| Track switch on every screen | visible | Sidebar (app.py:1453-1462), `main` call (app.py:1490) | PASS |
| Generated numbers marked (Track B) | 🟠 on generated numbers | Inspection-file button 🟠 (app.py:855-866), shown only when generated (app.py:1067-1068) | PASS |
| Track B content: classifier probabilities and K5 in EGP (🟠) | spec section 9 screen 2 | No classifier or EGP output in `app.py` (no "probab", "EGP" or "distress" references in the screen) | FAIL (content not implemented; no unmarked generated number is shown) |
| Map hidden in Track B | no map | No map call on this screen; the only pydeck use is in `render_map_slot` (app.py:454-471) | PASS |

## Screen 3 · District view (`screen_district`, app.py:1266)

| Element | Rule | Found | Verdict |
| --- | --- | --- | --- |
| Main tiles | at most 4 | No `metric_tile` or `st.metric` on this screen (app.py:1266-1288) | PASS |
| Headline "N fine-eligible months over M compounds today" | as-of, origin | "today" replaces an as-of date; no origin marker (app.py:1225) | FAIL (app.py:1225) |
| Headline "N homes in M compounds" | as-of, origin | No as-of date or origin marker (app.py:1184) | FAIL (app.py:1184) |
| Percent without denominator (forbidden 1) | no bare % | No % on this screen | PASS |
| Truncated axis (forbidden 2) | axes start at zero | Bars without domain override: homes (app.py:1174-1178), late delays (app.py:1196-1198), fine months (app.py:1217-1222) | PASS |
| Different-season comparison (forbidden 3) | comparisons same season | Early-signal pair is "first capture after the alert" vs "latest" (app.py:1113-1119), built by `frame_pair` (insights.py:258-262) with no same-season check; claim pair is "nearest to the last claim" vs "latest" (app.py:1163) | FAIL (app.py:1119, 1163; insights.py:258-262) |
| Average hiding spread (forbidden 4) | range shown, not only an average | Late promises show min-max range and median (app.py:1205-1206) | PASS |
| Unannounced coverage change (forbidden 5) | coverage change announced | Counts of compounds and homes with no coverage-change line | NOT CHECKED |
| Track switch on every screen | visible | Sidebar (app.py:1453-1462), `main` call (app.py:1490) | PASS |
| Generated numbers marked (Track B) | 🟠 on generated numbers | Screen reads Track A data only (app.py:1271-1275); no generated number shown | PASS |
| Track B content: per-class recall, macro-F1, recall@N, B1-B5 | spec section 9 screen 3 | None in `app.py` (grep for recall, macro and B1 finds nothing) | FAIL (content not implemented; no unmarked generated number shown) |
| Map hidden in Track B | no map | No map on this screen | PASS |

## Screen 4 · Digital twin what if (`screen_what_if`, app.py:1408)

| Element | Rule | Found | Verdict |
| --- | --- | --- | --- |
| Main tiles | at most 4 | No tiles; charts and tables only | PASS |
| Progress table columns "Baseline progress %", "S1 cost shock %", "S2 collections drop %" | percent with denominator | Columns are percentages with no denominator named (app.py:1403; built in insights.py:339-346). The caption explains only the pp change (app.py:1404-1405) | FAIL (app.py:1403; insights.py:339-346) |
| Percent without denominator (forbidden 1), change column | pp change explained | "S1 change (pp)" and "S2 change (pp)" are explained in the caption (app.py:1404-1405) | PASS |
| Truncated axis (forbidden 2) | axis starts at zero | Scenario bars with no domain override (app.py:1361-1373) | PASS |
| Different-season comparison (forbidden 3) | same month | Baseline and both shocks come from one run, latest month (app.py:1402; insights.py:336-338) | PASS |
| Average hiding spread (forbidden 4) | no bare averages | No average shown | PASS |
| Unannounced coverage change (forbidden 5) | coverage change announced | No coverage line; table lists compounds from the latest month | NOT CHECKED |
| Track switch on every screen | visible | Sidebar (app.py:1453-1462), `main` call (app.py:1490); Track A shows a warning instead of data (app.py:1410-1411) | PASS |
| Generated numbers marked (Track B) | 🟠 on each generated number | Progress block caption 🟠 (app.py:1402); S1 and S2 block caption 🟠 (app.py:1384) | PASS |
| Generated numbers marked: S3 capacity variants | 🟠 on generated numbers | S3 blocks show generated selection changes with only the quarter as caption (app.py:1314-1338; caption at 1333) | FAIL (app.py:1333) |
| Map hidden in Track B | no map | No map on this screen | PASS |

## Summary

- Counts (all four screens, 54 rows): PASS 39, FAIL 11, NOT CHECKED 4. Counts are per row; the tables above are the source.
- FAIL with file:line:
  - app.py:520-522 (screen 1, "At level 1" tile has no denominator)
  - app.py:702 (screen 2, five main tiles, limit 4)
  - app.py:848-849 (screen 2, two `st.metric` tiles lack denominator and origin)
  - app.py:824-832 (screen 2, free comparison of any two captures; different-season risk)
  - app.py:1225 and app.py:1184 (screen 3, headline numbers with no as-of date)
  - app.py:1119 and app.py:1163, with insights.py:258-262 (screen 3, pairs of captures with no same-season check)
  - app.py:1403, with insights.py:339-346 (screen 4, percent columns with no denominator)
  - app.py:1333 (screen 4, S3 capacity blocks without the 🟠 generated marker)
  - Content gaps (spec section 9, not display rules): screen 2 classifier and EGP output, and screen 3 Track B recall, macro-F1 and B1-B5 (no code found).
- NOT CHECKED: unannounced coverage change on each of the four screens (needs a quarter pair with a coverage change to test). The K3, K5 and K6 text-branch tiles are PASS with a note that the unit is carried in the text.
- Track switch and the sidebar are PASS on all four screens. Map hidden in Track B is PASS on all four screens.
- Forbidden mistake 2 (truncated axis) is PASS: every chart either sets the 0-1 domain or leaves the default zero base.
- The ten-second test with a person outside the team is not part of this check.
