# Wording audit: dashboard screens (T-SA-07)

Date: 2 November 2026. Branch `docs/T-SA-07-audit-20261102b`, based on `origin/main`.
Reference: the allowed / not-allowed table in `docs/requirements/01-specs.md` section 3, and the rule that the committee sees codes only.

## Scope and method

- Screens: `screen_priority_map`, `screen_compound_file`, `screen_district`, `screen_what_if` (with `render_progress_vs_baseline`) and the sidebar, banner and page header in `app.py`.
- Helpers that produce visible text, read in full: `app.py` render helpers (tiles, cards, charts, captions, empty states) and `src/dashboard/insights.py` (suggested action, claim text, progress and outcome labels, stored-reason cleaning).
- `src/dashboard/ops_visits.py` (visit form labels and result options) is included because the Compound file screen renders it.
- Stored reason sentences come from `src/pipeline/kpis.py` (`reason`); they are checked only where the dashboard shows them.
- Method: a text search for forbidden terms (distress, risk, fine, complete, progress, percent, 3D, real-time, owe, speculat, floors), then every visible string was read in context.
- Verdicts: VIOLATION = breaks a rule of the table; CHECK = allowed in part or unclear, needs a wording decision; SAFE = allowed wording or a caveat.
- Line numbers refer to the file on this branch.

## Findings

### A. Screen 1, Priority map

| # | File | Line | Text (as shown) | Rule | Verdict |
|---|---|---|---|---|---|
| D1 | app.py | 1009 | "Whom should the committee visit first?" | "Priority level" wording, decision support | SAFE |
| D2 | app.py | 485 | "colour = priority level, grey = not assessable" | Allowed term "priority level" | SAFE |
| D3 | app.py | 486-488 | "block height = mean building height (... latest year to 2024), drawn 10x taller" | Height only as approved context through 2024 | SAFE |
| D4 | app.py | 500-502 | "Visit X this cycle ... X comes first: [stored reason]" | Rule selects the list; no fitted probability | SAFE |
| D5 | app.py | 518 | Tile "To visit this cycle" | Operational wording | SAFE |
| D6 | app.py | 520-522 | Tile "At level 1", caption "inspect now" | Operational wording | SAFE |
| D7 | app.py | 524-525 | Tile "Fine-eligible months", caption "in N compounds - the contract decides the fine" | Allowed: "Eligible for review under contract terms for N months". "Fine-eligible" is not in the table. The caveat is present. | CHECK |
| D8 | app.py | 555 | "Suggested actions are proposals; the committee decides." | Caveat, human decision | SAFE |
| D9 | app.py | 566 | Download label "inspection file (includes generated figures)" | Generated tagged | SAFE |
| D10 | app.py | 576 | "Cycle list (CSV)" | Operational | SAFE |
| D12 | app.py | 347-350 | Error "no_names gate ... Display stopped." | Operational | SAFE |
| D13 | app.py | 413 | Section "Priority map" | Allowed term | SAFE |

### B. Screen 2, Compound file

| # | File | Line | Text (as shown) | Rule | Verdict |
|---|---|---|---|---|---|
| D14 | app.py | 1025 | "Why this one? Evidence behind the priority level." | Allowed term | SAFE |
| D15 | app.py | 705 | Tile "Priority level" (value: level word), caption "worst of K2, K3, K6" | Allowed term; rule stated | SAFE |
| D16 | app.py | 707-708 | Tile "K2 no activity", "counted after the start: 4 active quarters or a published launch" | Allowed: "No building activity for X quarters" | SAFE |
| D17 | app.py | 712-713 | Tile "K3 handover clock", "since first announced handover date" | Allowed: "Passed its first announced date by Y months" | SAFE |
| D18 | app.py | 719-720 | Tile "K6 never started", value "does not apply", caption "construction start was observed" | Allowed: "No construction start N months after the first launch". "Never started" states a permanent fact from a stored window. | CHECK |
| D19 | app.py | 723 | Tile "K6 never started", unit "months", caption "since first launch/promise, no construction start" | As D18 | CHECK |
| D20 | app.py | 727-731 | Tile "K5 fine-eligible months", "no published deadline", caption "the contract decides the fine" | As D7 | CHECK |
| D21 | app.py | 740 | "Waiting for the A / Dynamic World series of [code] in real/kpi_values.parquet." | Operational | SAFE |
| D22 | app.py | 752 | Axis title "0-1" | Operational | SAFE |
| D23 | app.py | 777-778 | "First announced handover date: [month year] (the date K3 counts from)" | Allowed wording (announced date) | SAFE |
| D24 | app.py | 780 | "No announced handover date on file for this compound yet." | Caveat | SAFE |
| D25 | app.py | 781-782 | "derived ... gaps = quarters not assessable ... dashed lines = quarter of a published developer statement" | Origin labelled | SAFE |
| D26 | app.py | 786, 801, 849 | Stage words "under construction", "land or ground works", "complete" (S2 shown as "Stage in YYYY: complete") | "Complete" is a stage label, not a percentage, but it states a completion status for a real compound from images. Allowed: "observed stage" wording only. | CHECK |
| D27 | app.py | 812 | "Construction first seen in [year]." | Allowed (observed year, not a % or floors) | SAFE |
| D28 | app.py | 861-862 | "No inspection file stored for [code] in [asof]." | Operational | SAFE |
| D29 | app.py | 864 | "Open inspection file (Arabic HTML, includes generated figures)" | Generated tagged | SAFE |
| D30 | app.py | 885-886 | "Level N - [level word]. Suggested action: [action]. [why] Last recorded visit: [date] ([result])." Caption "The action is a suggestion; the committee decides." | Caveat present | SAFE |
| D31 | app.py | 1059 | "Why: [stored reason]" | Stored English reason, codes only | SAFE |
| D32 | app.py | 1088, 1134 | Button "Open [code]" | Operational | SAFE |
| D33 | app.py | 1041-1046 | Select label "Compound", format "[code] - [level word]" | Codes only | SAFE |
| D34 | app.py | 1119 | Frame caption "First capture after the alert", "Latest" | Operational | SAFE |
| D35 | app.py | 1070-1071 | "Visit form", "Record a visit" | Codes only; form tells the user not to write names | SAFE |
| D36 | src/dashboard/ops_visits.py | 29 | Visit result option "complete" (with "progressing", "stalled", "not done") | Visit result recorded by a person on site; "complete" states a completion status on a real compound. Needs a wording decision. | CHECK |
| D37 | src/dashboard/ops_visits.py | 96 | "Pick the compound code. Do not write compound or developer names in the note." | Codes only | SAFE |
| D38 | src/dashboard/ops_visits.py | 157 | Metric "Stalled", value "[n] of [total]" | Operational | SAFE |

### C. Screen 3, District view

| # | File | Line | Text (as shown) | Rule | Verdict |
|---|---|---|---|---|---|
| D39 | app.py | 1267 | "What does the system give the committee?" | Allowed | SAFE |
| D40 | app.py | 1104 | "No public late case in the backtest was flagged after construction started." | Backtest counts, no percentage | SAFE |
| D41 | app.py | 1111-1112 | "[code] was first flagged in [quarter], [n] months before its first handover date ([month])." | Allowed pattern (months before a date) | SAFE |
| D42 | app.py | 1113 | "What space saw. [stored reason sentence]" | Stored reason; no percentage | SAFE |
| D43 | app.py | 1118 | "What happened. [public outcome], reported [month]." | Public outcome quoted | SAFE |
| D44 | src/dashboard/insights.py | 202-206 | Outcome labels: "partly handed over late, completion postponed", "handover postponed twice, not yet delivered", "handed over late" | Quotes the public outcome; "completion" here is the developer's word for handover | SAFE |
| D45 | app.py | 1123, 1126 | "Flagged now, before any handover date passed" / "No compound on the visit list is flagged before a handover date." | Allowed | SAFE |
| D46 | src/dashboard/insights.py | 170-171 | Table cell "date passed, may be handed over: confirm on site" | Hedged, asks for a site check | SAFE |
| D47 | src/dashboard/insights.py | 189 | Action "Confirm handover on site": "The handover was announced and the compound may be complete." | "may be complete" is hedged; no percentage; the action is a check | SAFE |
| D48 | app.py | 1160-1161 | "[code]: as of [asof], [n] months past the first announced handover date ([month])." | Allowed pattern | SAFE |
| D49 | app.py | 1167, 1170, 1184, 1186 | "Homes in compounds with fine-eligible months", "[n] homes in [n] compounds with fine-eligible months", caption "Label = fine-eligible months of the compound." | As D7. Homes are the published unit count (real). | CHECK |
| D50 | app.py | 1190, 1205-1206 | "How late R7 promises ran" / "[n] R7 compounds began handing over [a]-[b] months after the promised date (median [m])." | Allowed pattern (months after the promised date) | SAFE |
| D51 | app.py | 1210 | "[code]: [outcome text]." | Public outcome | SAFE |
| D52 | app.py | 1214-1215, 1218, 1223, 1225 | Section "Fine-eligible months", "No compound has fine-eligible months.", chart axis "Fine-eligible months", "[n] fine-eligible months over [n] compounds today." | As D7. Sums the screening months; not an assessed fine. | CHECK |
| D53 | app.py | 1227 | "The contract decides the fine." | Caveat, consistent with the K5 rule | SAFE |
| D54 | src/dashboard/insights.py | 186 | Suggested action "Fine review": "[n] fine-eligible months (proposal: 12)." Shown in the visit table (app.py 538) and the compound header (app.py 885). | Action label on a real compound. "Fine" is close to the forbidden "Fined". Allowed: "Eligible for review under contract terms for N months". | CHECK |
| D55 | app.py | 1167 | Section "Homes in compounds with fine-eligible months" | As D49 | CHECK |
| D56 | app.py | 1230-1243 | Section "Developers with several compounds"; buttons "[code] - [level text]" | Codes only (developer codes are not shown; the group label is the developer code) | SAFE |
| D57 | app.py | 1246-1247 | "Level history, all compounds" | Operational | SAFE |

### D. Screen 4, Digital twin what if

| # | File | Line | Text (as shown) | Rule | Verdict |
|---|---|---|---|---|---|
| D58 | app.py | 1409 | Title "Digital twin what if", subtitle "Who would change if costs, collections or visit capacity changed?" | Allowed: "compound-level digital twin ... simulated finance". Not "3D" or "real-time". | SAFE |
| D59 | app.py | 1411 | "Digital twin what if uses generated data. Switch to Track B in the sidebar to open it." | Generated tagged | SAFE |
| D60 | app.py | 1396 | Section "Progress against the baseline run" | Shows progress as a percentage for generated data. Rule: no completion percentage. Labelled generated, but the word "progress" with % is what the table forbids. | CHECK |
| D61 | app.py | 1402 | Caption "GENERATED - latest month [m] - the baseline and both shocks come from one run" | Generated tagged | SAFE |
| D62 | src/dashboard/insights.py | 344-348 | Column headers "Baseline progress %", "S1 cost shock %", "S2 collections drop %" | As D60; the table is in percent of progress on generated data | CHECK |
| D63 | app.py | 1404-1405 | "Change in percent points of progress. A shock that moves no compound to another level or visit-list place is a result, not a missing value." | As D60; the second sentence is a good caveat | CHECK |
| D64 | app.py | 1337 | "Imported cost +30%." / "Collections -25% for six months." | Generated scenario. The spec names S1 "Dollar shock, USD/EGP +30%"; the label "Imported cost" differs. Align the label. | CHECK |
| D65 | app.py | 1347 | "Nobody crosses a threshold: no compound changes level or list position." | Operational | SAFE |
| D66 | app.py | 1352-1353, 1350-1351 | "hypothetical baseline [level], scenario [level], joins the list / leaves the list" | Hypothetical wording, generated | SAFE |
| D67 | app.py | 1323, 1325, 1333 | "2 visits instead of 4", "6 visits instead of 4", "The list does not change." | Capacity variants, generated | SAFE |
| D68 | app.py | 1380, 1398, 1421 | "Waiting for ready-data/... Run python -m src.pipeline.setup_review." | Operational | SAFE |
| D69 | src/dashboard/insights.py | 207 | "Hypothetical baseline (generated finance)" | Generated tagged | SAFE |

### E. Sidebar, banner and page header

| # | File | Line | Text (as shown) | Rule | Verdict |
|---|---|---|---|---|---|
| D70 | app.py | 36 | Banner "Synthetic - for training only" | Retain "Synthetic - for training only" for generated outputs | SAFE |
| D71 | app.py | 1446, 1460 | Brand "SpaceEye / R7 Observatory"; help "Track B: adds generated ACUD-style data." | Codes/origin labels | SAFE |
| D72 | app.py | 1474 | "Generated numbers tagged, map hidden" | Origin labelled | SAFE |
| D73 | app.py | 1477 | "REAL - DERIVED" pill | Origin labelled | SAFE |
| D74 | app.py | 1485 | Page title "SpaceEye - R7 Observatory" | Allowed | SAFE |
| D75 | app.py | 65-69 | Screen names "1 - Priority map", "2 - Compound file", "3 - District view", "4 - Digital twin what if" | Allowed | SAFE |
| D76 | app.py | 1009, 1267 (subtitles) | "Whom should the committee visit first?" / "What does the system give the committee?" | Decision support; human decides | SAFE |

### F. Action labels and developer claims (helpers that feed the screens)

| # | File | Line | Text (as shown) | Rule | Verdict |
|---|---|---|---|---|---|
| D77 | src/dashboard/insights.py | 191, 193 | Suggested action "Written warning": "[n] months past the first announced date (proposal: 12)." / "[n] quarters without activity (proposal: 4)." | A formal sanction label on a real compound. Not in the allowed table; the caveat "proposal" is present. Needs a wording decision. | CHECK |
| D78 | src/dashboard/insights.py | 78, 83 | Claim text "progress [n]%" (also "over" / "about" [n]%), shown in the developer-claims tables (app.py 945, 1141, 1162) | Quotes a developer's stated percentage on a real compound, next to satellite captures. Allowed only if it is shown as the developer's claim. The table header "Claim" does not say so. Rule: no completion percentage from images. | CHECK |
| D79 | src/dashboard/insights.py | 200 | Action "Visit now": "Highest priority this quarter." | Allowed term | SAFE |
| D80 | src/dashboard/insights.py | 196-199 | "Routine level.", "Check the file before spending a visit.", "On the visit list this quarter." | Operational | SAFE |

## Counts

Rows D1-D80 (D11 is not used): 79 rows, one per visible text or helper. Totals:

| Verdict | Count |
|---|---|
| VIOLATION | 0 |
| CHECK | 16 |
| SAFE | 63 |

## Violations

No VIOLATION was found on the dashboard screens. The forbidden terms "distressed", "risk level", "high-risk", "fined", "owes", "speculator", "3D", "real-time", "floors built" and "completion" with a number do not appear in any visible text. The CHECK items are the wording decisions for the owner: the "Fine-eligible" family (D7, D20, D49, D52, D54), "K6 never started" (D18, D19), the stage label "complete" (D26), the visit result "complete" (D36), the progress percentages (D60, D62, D63, D78), "Written warning" (D77), and the scenario label "Imported cost" (D64, spec: "Dollar shock").

## Points for the owner

1. "Fine-eligible" is not in the allowed table. The allowed phrase is "Eligible for review under contract terms for N months", and the action label "Fine review" (D54) is close to the forbidden "Fined". A rename to "Contract review (eligible)" would remove the risk.
2. The generated progress percentages (D60-D63) are labelled "Generated", but the table rule forbids completion percentages. Renaming to "simulated progress index" would be safer.
3. The developer's own progress percentage (D78) should be labelled as the developer's statement in the Claim column.
