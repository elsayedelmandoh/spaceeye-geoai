# Rubric map: criteria to evidence and slides

Task T-SA-01 (rubric received). Source rubric: [ACUD-Rubric.md](../../requirements/ACUD-Rubric.md) (Arabic; ten criteria, weights sum to 100, levels 1-4, plus a +10 bonus). Level summaries below are English translations; items the rubric marks [؟] are "unclear in the source". Level estimates are the team's own draft, not a score from the panel. Every number quoted names its source file. Codes only, no names. Presentation length: the rubric text says 12 minutes (criterion 10); the team lead confirmed on 2026-11-04 a 20-minute slot, so the talk is 14:30 with about 5:30 for questions.

Slide numbers in the "Slide:" lines are the deck labels used in [presentation.md](presentation.md) (0, 1, 2, 2a, 2b, 3, 4, 5, 6, 6b, 6c, 7, 8, 8b, 8c, 8d, 9, 10, 10b, 11). The first column of the plan table at the end is the PowerPoint number 1-20, the same as in [transcript.md](transcript.md).

## 1. Problem and challenge (weight 10)

- **Level 3:** a specific challenge placed in the frame (type × pillar × condition); its goal and size measured from a source; decision owner and affected parties named.
- **Level 4:** links the challenge to stability, sustainability or citizen satisfaction as a chain: number → problem → measured impact; explains why now.
- **Evidence:** `docs/requirements/01-specs.md` section 0 (compass cell preventive · Buildings & Facilities · normal · stability; decision owner; decision served); the figures on slide 1 (more than 500 developers, more than 600 projects, about 7-8% seriously late, 6 mutual terminations) are the ACUD chairman's statements, not our measurements, recorded in `docs/requirements/01-specs.md` section 12.
- **Added in the deck (slide 2 and the script of PowerPoint slide 3):** one line with the frame (preventive · Buildings & Facilities · normal conditions · stability, `docs/requirements/01-specs.md` section 0), the affected parties (buyers: 6,474 homes in the five late public cases, `docs/deliverables/decision-memo.md`) and why now (C18 is 57 months past its first announced handover date, `decision-memo.md`, `expected-questions.md`).
- **Added for level 4:** `docs/deliverables/decision-memo.md` (English and Arabic): chain from R7 counts (5 of 6 late cases, 18-33 months) to problem (delay seen late) to impact (6,474 homes, up to 153,816 home-months; 3 compounds, 3,624 homes past the 24-month refund line of Decree 2184/2022 art. 5) and an assumed money figure (5,000 EGP rent per home-month, labelled assumption, about 0.77 bn EGP); "why now" in three points.
- **Gap to level 4:** the money figure rests on an assumed rent; delays are counted from published promises, not contract dates.
- **Slide:** 1, 2 (and 2a for the as-is evidence).

## 2. Current state, as-is (weight 10)

- **Level 3:** measured baseline for the indicators; a process map (who does what, when); pain points in numbers (times, volumes, errors).
- **Level 4:** root cause shown with evidence; comparison across areas or groups; shows what averages hide.
- **Evidence:** current practice "field review every 3 months" for all projects (`docs/requirements/01-specs.md` section 12 and the visit formula; `configs/cost_assumptions.yaml` `visits_per_year: 4`, `projects: 12`); per-compound K2/K3/K6 baselines in `docs/deliverables/kpi-cards.md`; per-case root-cause diagnosis of the backtest in `data/experiments/35_backtest_diagnosis/DIAGNOSIS.md`.
- **Added for level 4:** `docs/deliverables/as-is.md`: process map rebuilt from public sources (mermaid, who/when/what is unknown); baseline in numbers (48 reviews a year; 5 of 6 public late cases 18-33 months late, median 25; 7 of 12 compounds with 106 fine-eligible months and 9,937 homes; level counts 1/2/3/6); three root causes with evidence (even effort, developer-sourced progress: C19 70% claimed vs 28% of built area at 20 m+, no pace-vs-promise check: C14 35% three months before its date); what the average hides (activity 0.03-0.90 around a 0.61 mean, developers with compounds at levels 1 and 4, delay range).
- **Added in the deck (slide 2a and its script):** one evidence line: C19 claimed 70% while 28% of its built area was 20 m or taller that year (different measures, a reason to look, not proof); C14 reported 35% three months before its promised date and moved it; activity ranges 0.03-0.90 around a 0.61 mean (`docs/deliverables/as-is.md`).
- **Gap to level 4:** no ACUD records (visit logs, visit time, warnings, supervisor reports); the process map must be confirmed with ACUD.
- **Slide:** 2a (as-is process map, baseline and root causes from `docs/deliverables/as-is.md`).

## 3. Target state, to-be (weight 10)

- **Level 3:** targets (goal and objectives) on the same indicators; a picture of the new process and who decides in it.
- **Level 4:** targets justified by data or a reference standard (ISO 37120/37122, U4SSC) for normal and extreme conditions, with the limits of what the project does not cover.
- **Evidence:** new process: cycle list of capacity 4, levels 1-4 with actions, committee decides (`docs/requirements/01-specs.md` sections 2 and 7; `docs/deliverables/kpi-cards.md`); scope limits in `docs/requirements/01-specs.md` section 1 (out of scope).
- **Added for level 4:** `docs/deliverables/to-be.md`: new process map with roles; proposed targets on the as-is indicators, each with a data reason (capacity 4 covered every level 1-2 compound in 31 of 31 quarters; K4 met in all 372 compound-quarters; K2 threshold from `configs/data.yaml`); normal vs extreme conditions (load above capacity via S3, finance shocks S1/S2 move nothing, data outage); ISO 37122 and U4SSC mapping stated honestly (no matching indicator); limits. KPI cards A and K2 now carry proposed targets.
- **Added in the deck (slide 2b and its script):** ISO 37122 and U4SSC have no matching project-level indicator, so the targets rest on R7 data (31 of 31 quarters); scenario S3 tests load above capacity (`docs/deliverables/to-be.md`).
- **Gap to level 4:** targets are proposals; the U4SSC indicator list was checked at framework level only; the backtest bar (5 of 6) is not met.
- **Slide:** 2, 2b (the to-be process as a flowchart, with roles and proposed targets from `docs/deliverables/to-be.md`), 5 (partly).

## 4. Targets translated into a dashboard for its audience (weight 10)

- **Level 3:** designed for a named audience (operator, decision maker, leadership); answers its question; shows current against target with thresholds and alerts.
- **Level 4:** leads from alert to action; tested with audience representatives and changed after the test.
- **Evidence:** `app.py` (`SCREENS`: 1 Priority map, 2 Compound file, 3 District view, 4 Digital twin what if, 5 Real names and sources; track switch); committee guide `docs/deliverables/user-guide.md`; display-rules check and fixes `docs/deliverables/display-rules-check.md`; alert → action path: level → cycle list → inspection file → visit form (`docs/requirements/01-specs.md` sections 7 and 9).
- **Added for level 4:** `docs/deliverables/audience-test.md`: change log of what the teammate reviews found and what changed (PR #101, PR #102), and a ten-second test sheet for screen 1 with an answer key from the current release.
- **Added for the deck (slides 6b and 6c):** evidence for 6b: a search box and four filters on screen 1 (as-of quarter, priority level, developer code, minimum K2/K3/K6, plus "Cycle list only"), and a map click that opens the "Selected compound" sidebar panel (`app.py` `render_filters`, `open_clicked_compound`, `render_selected_compound_panel`; `insights.filter_compounds`; board tasks T-NA-11, T-NA-12, T-NA-13, T-EL-21). Evidence for 6c: the four screens and the question each answers (subtitles from `docs/deliverables/user-guide.md`), the alert → action path (level → cycle list → compound file → visit form → recorded visit), `docs/deliverables/audience-test.md` and `docs/deliverables/display-rules-check.md`.
- **Chatbot (slide 8c; slide 8d serves criteria 8 and 9):** the hybrid RAG chatbot (`chatbot/`, opened from the dashboard's 💬 button, port 8001) answers the audience's question in Arabic with the stored values and their origin labels.
- **Gap to level 4:** the reviewers were team members, not committee members; the supervisor (outside the team) took a ten-second test on 2026-11-01, but no answers or timings were recorded; a recorded test with a real committee member still has to be run on the sheet (T-NA-08).
- **Added in the script (slide 6c):** names who uses each screen (the committee; the field visit lead for the visit form; screen 4 is generated) and says the supervisor took an unrecorded ten-second test while a recorded test with a committee member is still to be run.
- **Slide:** 6 (live demo), 6b (search, filters and map click), 6c (four screens, alert to action), 8c (chatbot); slide 5 (rule and thresholds) is shared with criterion 3.

## 5. Transition from current to target (weight 10)

- **Level 3:** roadmap with phases, owners and resources; includes risks and training.
- **Level 4:** phased transition before execution with progress indicators, criteria for moving between phases, and a rollback plan.
- **Evidence:** next step "run one cycle with the list and record visit results" (slide 11); data request ordered by impact `docs/deliverables/data-request.md`; quarterly monitoring procedure `docs/deliverables/technical-track-a.md`; risks and fallbacks `docs/requirements/01-specs.md` section 13; roles `docs/requirements/01-specs.md` section 10.
- **Added for level 4:** `docs/deliverables/transition-plan.md`: three phases (pilot cycle, ACUD data, quarterly operation then R8) with scope, owner roles, resources and training; proposed gate criteria between phases; six progress indicators counted each quarter; rollback table with triggers (the fixed 3-month review keeps running through phase 2, so rollback costs at most one rerun).
- **Added in the script (slide 11):** each phase's owner role and risk; training, gate criteria, dates and owners to be agreed with ACUD; the pilot needs no extra visits and counts visit results recorded out of 12 each quarter; rollback "at most one rerun" (`docs/deliverables/transition-plan.md`).
- **Gap to level 4:** all of it is proposed: people, dates and the committee's own gate numbers need ACUD; nothing has been executed yet.
- **Slide:** 11 (phases with owner, risk and rollback per phase; gate criteria and indicators are in the plan), 2b (the to-be loop and roles), 10b (launch, controls and STOP / rollback).

## 6. Solution effectiveness: preventive (weight 12)

- **Level 3:** effectiveness measured for the solution type: reactive (time to detect and respond), preventive/predictive (precision, recall and false-alarm rate; unclear in the source), on past data.
- **Level 4:** adds feasibility (when the solution stays valid) and the trade-off between the cost of a false alarm and the cost of a missed event (unclear in the source).
- **Evidence:** frozen-clock backtest on six real R7 cases: 1 of 6 after-start, 0 of 6 point-in-time; criterion of 5 not lowered (`data/BACKTEST_CURRENT.md`); diagnosis of misses (`data/experiments/35_backtest_diagnosis/DIAGNOSIS.md`); generated-data recall@4 per method against random mean 0.335 (2,000 draws) (`data/EW_REPORT_CURRENT.md`); per-class recall and macro-F1 (`data/CURRENT_MODEL_METRICS.csv`, e.g. logistic_combined macro-F1 0.615); `docs/deliverables/method-card.md`.
- **Added for level 4:** District view sections "When the solution fails" (failure modes per case, what the stall rule can do, with no real case confirming it) and "A false alarm against a missed case" (calculator with labelled assumptions; break-even of about 6.7 false alarms per missed case at the central setting); same text in `docs/deliverables/technical-track-a.md` ("When the rule fails and what an error costs").
- **Added in the deck (slide 7 and its script):** "0 of 6 point-in-time" is said aloud; no false-alarm rate on real cases (all six were late); at the central assumptions one missed case equals about 6.7 false alarms, a calculator on assumed inputs (`configs/cost_assumptions.yaml` via `docs/deliverables/technical-track-a.md`).
- **Gap to level 4:** the real-case criterion was not met (1 of 6); the test holds only 4 distressed rows (`data/EW_REPORT_CURRENT.md`); no false-alarm rate on real cases (all six backtest cases were late); cost inputs are assumptions.
- **Slide:** 7, 8, 8b.

## 7. Return on investment (weight 12)

- **Level 3:** return measured in at least one unit (cost reduced or removed, work hours, resolution time), direct or indirect, with its cost (effort, cycles) (unclear in the source).
- **Level 4:** return in several units with a sensitivity calculation (best/worst) and a comparison with an alternative (doing nothing or another solution).
- **Evidence:** `configs/cost_assumptions.yaml`: three settings; "Under these assumptions, from 0.007 to 0.102 million EGP per year"; compared with the current policy of visiting all 12 compounds 4 times a year; formula in `docs/requirements/01-specs.md` section 12; `docs/deliverables/decision-memo.md`.
- **Added in the deck (slide 9 and its script):** a second unit, 16 field visits a year instead of 48 (12 x 4; the 48 is the as-is baseline in `docs/deliverables/as-is.md`); still "not a measured saving".
- **Gap to level 4:** EGP and visits per year only; operating cost and missed cases are labelled public proxies and cost of late detection is a PLACEHOLDER (`configs/cost_assumptions.yaml`, T-SA-03); no work-hour or time-to-resolution unit.
- **Slide:** 9.

## 8. Governance (weight 10)

- **Level 3:** clear ownership of data, indicators and model; permissions; quality and privacy controls (Law 151 of 2020) (unclear in the source).
- **Level 4:** an integrated system: change and version control, audit log, periodic review, risk management with owners.
- **Evidence:** ownership, access and sharing per data group plus "Version and change controls" (`docs/deliverables/governance-cards.md`); quality gates and run id (`docs/deliverables/quality-report.md`); privacy, masking, Law 151/2020 note (`docs/deliverables/responsible-ai.md`); recorded reviews (`logs/review-05.md`); risks with fallbacks (`docs/requirements/01-specs.md` section 13).
- **Added for level 4:** `docs/deliverables/governance.md`: RACI over nine activities, risk register with an owner role and early sign per risk, review schedule (quarterly to yearly), decision log (2026-10-26 to PR #107), and the 2019Q2 FLAG explained (1 compound with a level, so 1 of 1) with a proposed review decision.
- **Added for the deck (slide 8d):** chatbot governance: model calls only with approval and a call budget (`configs/ai.yaml`: `chatbot.approval: approved`, `max_calls_total: 200`, approved by the project owner on 2026-11-04; counter in `chatbot/vector_db/gemini_calls.json`, then local answers), codes only, generated items labelled, not legal advice.
- **Added in the deck (slides 10 and 10b and their scripts):** slide 10 risk cards carry an owner role where `docs/deliverables/governance.md` names one, plus a line that each risk has an owner role and an early sign there; the script of slide 10b says the controls (thresholds and capacity change only by reviewed decision; chatbot model calls capped at 200 with approval; every visit result recorded in `ops_visits`).
- **Real and generated data (level 1 of the rubric mentions use of real or personal data):** every number carries an origin mark (real, derived, generated); generated content shows "Synthetic - for training only" (slides 8, 8b, 8c); names stay in codes only and the chatbot sees only generated complaints (`docs/deliverables/responsible-ai.md`).
- **Gap to level 4:** roles, schedule and the FLAG decision are proposals; the second reviewer and ACUD have not signed them.
- **Slide:** 10, 10b, 8d, 3 (origin key).

## 9. Documentation and knowledge transfer (weight 6)

- **Level 3:** technical documentation, user guide and a knowledge-transfer record (unclear in the source).
- **Level 4:** another team can run and maintain it without the original team.
- **Evidence:** `docs/deliverables/technical-track-a.md`, `docs/deliverables/user-guide.md`, `docs/deliverables/knowledge-transfer.md`, `docs/deliverables/method-card.md`, `docs/deliverables/final-checklist.md`.
- **Added for level 4:** clean-room run recorded in `docs/REVIEW_SETUP.md` (2026-11-04): fresh clone of main, section 1 only, setup 323 files, backtest replay 1 of 6, 451 tests passed, all five screens open with no page errors; the stale v6 name in the setup page and "four screens" in the README fixed.
- **Added for the deck (slide 8d):** the chatbot's knowledge is a list of sourced documents, `chatbot/knowledge/SOURCES.csv` (9 entries with URL and retrieval date), and its own small checks (`chatbot/evaluation_results.json`: 8 of 8 intent tests; `chatbot/retrieval_evaluation_results.json`: 5 of 5 retrieval checks), which are the team's tests, not an accuracy claim.
- **Added in the script (slide 10):** the handover documents are named (technical guide, user guide, knowledge-transfer pack, method card, final checklist) with the clean-room run (fresh clone, 451 tests passed, `docs/REVIEW_SETUP.md`), and "nobody outside the team has rebuilt it" is kept.
- **Gap to level 4:** the clean-room run was done by the team, not by a person outside it.
- **Slide:** 10 (knowledge-transfer bullet), 10b (launch and operation), 8d (chatbot knowledge and sources).

## 10. Presentation and answers (weight 10)

- **Level 3:** a clear story from current to target state and a summary with the decision requested; 12 minutes; accurate and transparent answers (unclear in the source).
- **Level 4:** leadership-level persuasion: conveys the value strongly and handles hard questions with evidence and alternatives.
- **Evidence:** decision requested in `docs/deliverables/decision-memo.md` and slide 11; prepared answers `docs/deliverables/expected-questions.md`; deck text `docs/deliverables/01-presentation/presentation.md`.
- **Added for level 4:** eight prepared answers for the new material (as-is and to-be, why now, buyers affected, when it fails, false alarm vs missed case, safe start, responsibility, other districts) in `docs/deliverables/expected-questions.md`; the one-page decision is `docs/deliverables/decision-memo.md`, next to the team's one-page proposal `docs/deliverables/03-proposal/proposal.md`.
- **Added in the transcript:** Q&A one-liners now also cover as-is and to-be, why now, buyers affected, false alarm against a missed case and other districts (`docs/deliverables/expected-questions.md`).
- **Time:** the rubric text says 12 minutes; the team lead confirmed a 20-minute slot on 2026-11-04, so the talk is 14:30 and about 5:30 remain for questions.
- **Gap to level 4:** the as-is and to-be story now has slides 2a and 2b; timed rehearsals at 14:30 are still open (T-ALL-05).
- **Slide:** all; decision on 11.

## Bonus: transferability, scalability, sustainability (+10)

- **4-7:** transferable to another region or pillar with an alternative.
- **8-10:** proven transfer with a sustainability plan. (0-3: solution confined to one case.)
- **Evidence:** thresholds and capacity in configuration (`configs/data.yaml` per `docs/requirements/01-specs.md` section 2); public satellite sources not tied to R7; quarterly procedure (`docs/deliverables/technical-track-a.md`).
- **Added:** transfer path in `docs/deliverables/knowledge-transfer.md` ("Use it in another district"): five steps (coded boundaries, dated statements, satellite windows, configuration, checks before use). Said in the script of slide 11: thresholds and capacity are configuration; another district needs its boundaries and statements; only R7 has been run, no transfer is proven.
- **Gap:** only R7 is run; no dry run on another district (its source caches are not in the checkout); no transfer is claimed.
- **Slide:** 11 (one bullet: "Only R7 has been run; no transfer is proven"); no slide of its own.

## Presentation plan for 14:30 (20-minute slot)

| PowerPoint no. | Deck label and slide | Criteria | Time |
| --- | --- | --- | ---: |
| 1 | 0 Title: project, slogan, supervisor, team | - | 0:30 |
| 2 | 1 Problem in numbers | 1 | 0:30 |
| 3 | 2 Question and decision (as-is → to-be in one line) | 1, 2, 3 | 0:30 |
| 4 | 2a As-is: how R7 is followed today (process map, baseline, root causes) | 2, 1 | 0:45 |
| 5 | 2b To-be: the new process (flowchart, roles, proposed targets) | 3, 5 | 0:45 |
| 6 | 3 Data | 2, 8 | 0:30 |
| 7 | 4 Seeing construction from space | 2, 6 | 0:30 |
| 8 | 5 Track A rule | 3, 4 | 0:45 |
| 9 | 6 Live demo (Track A) | 4 | 1:00 |
| 10 | 6b Search, filters and map click | 4 | 0:30 |
| 11 | 6c Four screens, one path from alert to action | 4 | 0:30 |
| 12 | 7 Backtest: 1 of 6 and why | 6 | 1:15 |
| 13 | 8 Track B (generated) | 6 | 0:45 |
| 14 | 8b What-if scenario | 6 | 0:30 |
| 15 | 8c Ask the project: the chatbot | 4 | 0:45 |
| 16 | 8d What the chatbot knows, and its limits | 8, 9 | 0:30 |
| 17 | 9 Value in EGP | 7 | 1:15 |
| 18 | 10 Risks and responsible use | 8, 9 | 1:00 |
| 19 | 10b Launching in production | 5, 9 | 0:45 |
| 20 | 11 Decision, transition and next step | 5, 10, bonus | 1:00 |
| | **Total** | | **14:30** |

The first column is the PowerPoint number (1-20, as in `transcript.md`); the second starts with the deck label used in the "Slide:" lines above. Criterion 6 (12 points) gets slides 7, 8 and 8b = 1:15 + 0:45 + 0:30 = 2:30 (it had 3:00 in the 14-slide plan). Criterion 7 (12 points) gets slide 9 = 1:15 (it had 1:30). Criterion 4 (10 points) has slides 6, 6b, 6c and 8c = 1:00 + 0:30 + 0:30 + 0:45 = 2:45 of its own (slide 5 is shared); slide 8d (0:30) serves criteria 8 and 9 next to slide 10. Criterion 3 gets slide 2b (0:45) and criterion 2 gets slide 2a (0:45). Criterion 5 has slides 2b, 10b and 11; criterion 9 has slides 8d, 10 and 10b. The 2:30 added on 2026-11-04 (12:00 to 14:30) went to slides 0, 2, 2a, 2b, 6c, 7, 9, 10, 10b and 11 (15 seconds each) so that each criterion's missing level-3 or level-4 point can be spoken. The new total was set by the team lead (2026-11-04); the split of the extra time is the team's proposal.
