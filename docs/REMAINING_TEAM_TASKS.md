# SpaceEye: current remaining work

Updated 30 October 2026 from the [current task board](requirements/02-team-roles-and-tasks.md), including the added T-AH-22. That board is authoritative for owners, dependencies, evidence and review records. Earlier snapshots used old owner/ID assignments; this handoff uses the current assignments.

There are **77 current task IDs**: **44 implemented**, including **15 with recorded review acceptance**, and **33 unchecked**. One unchecked task, T-AH-17, is a failed/excluded finishing experiment, not a missing production feature. These are task counts, not effort percentages. No acceptance is inferred from implementation or test results.

Use the current [v6 ready-data guide](../releases/ready-data/README.md), [device setup](REVIEW_SETUP.md), [data contract](../data/DATASET_CONTRACT.md), [current model evidence](../data/EW_REPORT_CURRENT.md) and [imagery handoff](../data/imagery/README.md). Scope remains 12 coded R7 compounds, inspection capacity 4, binary distressed/not_distressed. Numerical data and inspector imagery are separate products.

T-AH-15 is implemented locally: 24 inspector-pair rows, 100 unique Wayback capture-date states and 528 Sentinel context figures. Esri pixels and the local report ZIP stay outside Git. Source metadata, hashes, code, fixed selection rule and use/rebuild instructions are published. Independent review is pending. T-EL-02 can use installed images; absent images remain explicitly missing. This does not close the separate T-AH-22 full source/v2 run, five stored inspection reports, dashboard integration or fieldwork.

## Unchecked tasks and original acceptance requirements

The descriptions below preserve the current board requirements; an unchecked task may already have partial work. Check its code/branch and evidence before rebuilding it. The approved binary scope and negative finishing/road-timing results remain in force; do not restart those experiments just to tick a box. For T-AH-22, use portable data-root setup rather than assuming a particular device drive.

### Whole team

| ID | Remaining requirement |
| --- | --- |
| T-ALL-01 | [Must] D1 · Sign the D1 decisions (§14): R7 only, light twin, two tracks, worst-of-signals rule incl. K6 and B triggers, K5 definition + assumed fine rate, binary label, thresholds frozen, boundary ≥ 80%, codes only, generated label text · signed list in `docs/requirements/05-project-compass.md` · reviewer: all |
| T-ALL-02 | [Must] D1 · Fill open items 2 and 4 (§16): today's program day; how many of the 22 coded compounds and of the 8 backtest cases are in R7 · updated §16 + §10 · owner: ahmed (item 4), salma (item 2) |
| T-ALL-03 | [Must] D4 · Mid-term review (10 min) rehearsed once · owner: salma |
| T-ALL-04 | [Must] D5 · Cross-review: each member reviews one other member's deliverables end to end (ahmed ↔ elsayed, verina ↔ nada, salma reviews all docs) · review notes in PRs |
| T-ALL-05 | [Must] D5 · Two timed rehearsals + backup video of the demo · owner: salma |

### Ahmed: Track A

| ID | Remaining requirement |
| --- | --- |
| T-AH-17 | [Could] D4 · Finishing vision-model test (Qwen-VL on Wayback): pass condition ≥ 75% agreement on ~50 held-out compound-images labelled blind by salma (T-SA-12); log in `team_ideas.md`; **cut at D4 if not passed**; flag in the inspection file only · reviewer: elsayed **Failed experiment; feature excluded.** See [recorded outcome](REMAINING_TEAM_TASKS.md). |
| T-AH-18 | [Could] D4 · Construction stage test on Google heights 2016-2023 with free satellite data (first roof uniformity; then land / under construction / complete) against a condition written before the test; cut at D4 if not passed · reviewer: elsayed |

### Verina: Track B

| ID | Remaining requirement |
| --- | --- |

### Elsayed: AI and scenarios

| ID | Remaining requirement |
| --- | --- |
| T-EL-06 | [Must] D4 · Arabic HTML/PDF output with footer "Drafted by AI, reviewed by [name]" + model + time; 5 stored files for the presentation (deliverable 11) · `app_data/files/` · depends: T-AH-15 · reviewer: salma |
| T-EL-08 | [Should] D4 · Complaints classifier: 5 classes (delay, stoppage, payment, quality, other) vs keyword baseline; extra test on `complaints_30.csv`; state that texts we wrote do not prove real accuracy · reviewer: elsayed |
| T-EL-12 | [Could] D4 · S4 material cost +40%, S5 grace 12 → 6 months · reviewer: nada |
| T-EL-13 | [Could] D4 · FPMI and SAF tests on generated data, conditions written before the run, logged in `team_ideas.md` · reviewer: ahmed |

### Nada: dashboard

| ID | Remaining requirement |
| --- | --- |
| T-NA-01 | [Must] D1 · App skeleton: `app.py` runs `streamlit run app.py`, track switch (Track A default / Track B), orange banner "Synthetic - for training only" fixed in Track B, 🟠 on generated numbers, map hidden in Track B · reviewer: verina |
| T-NA-02 | [Must] D2 · Screen 1 priority map: R7 boundaries coloured by level (level written as a word, grey = not assessable), cycle list with Arabic reason, CSV download; Track B list only · depends: T-AH-08 · reviewer: ahmed |
| T-NA-03 | [Must] D3 · Screen 2 compound file: DW and A curves, height (to 2024), announced markers, first announced date, vegetation, two Wayback images, K2-K6, lineage line (origin, run_id), inspection file button; Track B: binary probabilities + K5 in EGP (🟠) · depends: T-AH-16, T-VE-10 · reviewer: ahmed |
| T-NA-04 | [Must] D3 · `ops_visits` form: code, date, result (progressing / stalled / complete / not done), note; saved to `app_data/ops_visits.csv` · reviewer: verina |
| T-NA-05 | [Must] D3 · Screen 3 would it have warned: Track A frozen-clock table (1 of 6 and why); Track B per-class recall, macro-F1, recall@N vs random, B1-B5 per compound · depends: T-AH-10, T-VE-12 · reviewer: elsayed |
| T-NA-06 | [Must] D3 · Screen 4 data trust: gates, coverage, not assessable, 1,009/1,026 facts, colour key 🟢🔵🟠 · depends: T-AH-11 · reviewer: ahmed |
| T-NA-07 | [Must] D4 · Screen 5 what if (twin): pick S1-S3, show which compounds change level and why; generated (🟠, banner, no map) · depends: T-VE-14 · reviewer: elsayed |
| T-NA-08 | [Must] D4 · Display rules check (§9): ≤ 4 main tiles, each with value + unit + denominator + "as of" + origin; the 5 forbidden mistakes; ten-second test on screen 1 with someone outside the team · reviewer: salma |
| T-NA-09 | [Should] D4 · `no_names` gate also scans dashboard exports; Arabic RTL renders correctly · reviewer: ahmed |
| T-NA-10 | [Must] D5 · User guide (how the committee uses screens 1, 2 and the visit form) · `docs/deliverables/user-guide.md` · reviewer: salma |

### Salma: value and delivery

| ID | Remaining requirement |
| --- | --- |
| T-SA-01 | [Must] D1 · Compass signed (use-case canvas, 8 checks); ask the instructor rubric + presentation length · `docs/requirements/05-project-compass.md` · reviewer: ahmed |
| T-SA-02 | [Must] D2 · KPI cards (10 fields + 2 tags, A K2 K3 K4 K5 K6) + KPI tree + levels table (deliverable 1), schema of `kpi_reference.csv` · `configs/kpis.yaml` + `docs/deliverables/kpi-cards.md` · reviewer: ahmed |
| T-SA-03 | [Must] D3 · Value in EGP, 3 settings, no double counting (§12 formula) · `configs/cost_assumptions.yaml` + "Under these assumptions, from X to Y million EGP per year" · reviewer: elsayed |
| T-SA-05 | [Must] D4 · Decision memo, one page Arabic + one page English, same facts and order (deliverable 8) · `docs/deliverables/decision-memo.md` · reviewer: verina |
| T-SA-06 | [Must] D4 · Slides 1-11 (§12): backtest slide is the only place real names may appear; slide 8 always quotes the denominator, the baseline, the scope and "generated data" · `docs/deliverables/01-presentation.md` + deck · reviewer: all |
| T-SA-07 | [Must] D4 · Wording audit of every doc, slide and screen against §3 allowed/forbidden table ("priority level" not "risk level", no "distressed" on a real compound, no completion %) · checklist in PR · reviewer: verina |
| T-SA-08 | [Must] D4 · Number audit: every number on slides and memo traced to `kpi_values`, `EW_REPORT.md` or `ai_verification_log` · reviewer: ahmed |
| T-SA-09 | [Must] D5 · Expected questions sheet (§12) with one-line answers · reviewer: elsayed |
| T-SA-10 | [Must] D5 · Final submission checklist: 13 deliverables (§11) ready, "done when" list (§14) ticked · reviewer: all |
| T-SA-11 | [Should] D2 · Update `docs/requirements/04-timeline.md` with today's program day and this board's D-days · reviewer: ahmed |
| T-SA-12 | [Could] D3 · Blind labeller for the finishing test (T-AH-17): label ~50 held-out compound-images without seeing the model output · reviewer: ahmed |

## Implemented outputs: review and reuse

| Owner / scope | Implemented IDs | Recorded review accepted |
| --- | --- | --- |
| Ahmed: Track A | T-AH-01, T-AH-02, T-AH-03, T-AH-04, T-AH-05, T-AH-06, T-AH-07, T-AH-08, T-AH-09, T-AH-10, T-AH-11, T-AH-12, T-AH-13, T-AH-14, T-AH-15, T-AH-16, T-AH-20, T-AH-21, T-AH-22 | T-AH-01, T-AH-02, T-AH-03, T-AH-04, T-AH-05, T-AH-06, T-AH-07, T-AH-08, T-AH-09, T-AH-10, T-AH-11, T-AH-12, T-AH-16, T-AH-20, T-AH-21 |
| Verina: Track B | T-VE-01, T-VE-02, T-VE-03, T-VE-04, T-VE-05, T-VE-06, T-VE-07, T-VE-08, T-VE-09, T-VE-10, T-VE-11, T-VE-12, T-VE-13, T-VE-14 | None recorded |
| Elsayed: AI and scenarios | T-EL-01, T-EL-02, T-EL-03, T-EL-04, T-EL-05, T-EL-07, T-EL-09, T-EL-10, T-EL-11, T-EL-14 | None recorded |
| Salma: value and delivery | T-SA-04 | None recorded |

Keep the board's separate Review accepted boxes pending until an actual review is recorded. The image code has an independent focused review and regression fixes, but that does not sign the assigned task reviewer on their behalf.
