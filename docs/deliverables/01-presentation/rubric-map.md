# Rubric map: criteria to evidence and slides

Task T-SA-01 (rubric received). Source rubric: [ACUD-Rubric.md](../requirements/ACUD-Rubric.md) (Arabic; ten criteria, weights sum to 100, levels 1-4, plus a +10 bonus). Level summaries below are English translations; items the rubric marks [؟] are "unclear in the source". Level estimates are the team's own draft, not a score from the panel. Every number quoted names its source file. Codes only, no names. Presentation length: 12 minutes (criterion 10).

Slide numbers refer to [presentation.md](presentation.md).

## 1. Problem and challenge (weight 10)

- **Level 3:** a specific challenge placed in the frame (type × pillar × condition); its goal and size measured from a source; decision owner and affected parties named.
- **Level 4:** links the challenge to stability, sustainability or citizen satisfaction as a chain: number → problem → measured impact; explains why now.
- **Evidence:** `docs/requirements/01-specs.md` section 0 (compass cell preventive · Buildings & Facilities · normal · stability; decision owner; decision served); slide 1 figures (more than 400 developers, more than 500 projects, about 7-8% seriously late, 6 mutual terminations) are ACUD chairman statements recorded in `docs/requirements/01-specs.md` section 12.
- **Gap to level 4:** the size figures are statements, not our measurement; no measured impact link (handover delay → investor or buyer effect) and no explicit "why now".
- **Slide:** 1, 2.

## 2. Current state, as-is (weight 10)

- **Level 3:** measured baseline for the indicators; a process map (who does what, when); pain points in numbers (times, volumes, errors).
- **Level 4:** root cause shown with evidence; comparison across areas or groups; shows what averages hide.
- **Evidence:** current practice "field review every 3 months" for all projects (`docs/requirements/01-specs.md` section 12 and the visit formula; `configs/cost_assumptions.yaml` `visits_per_year: 4`, `projects: 12`); per-compound K2/K3/K6 baselines in `docs/deliverables/kpi-cards.md`; per-case root-cause diagnosis of the backtest in `data/experiments/35_backtest_diagnosis/DIAGNOSIS.md`.
- **Gap to level 4:** no process map of today's inspection practice and no measured pain points (visit time, missed cases) from ACUD; the root-cause work covers the rule's misses, not the current process.
- **Slide:** no slide yet (slide 1 states the review cycle only).

## 3. Target state, to-be (weight 10)

- **Level 3:** targets (goal and objectives) on the same indicators; a picture of the new process and who decides in it.
- **Level 4:** targets justified by data or a reference standard (ISO 37120/37122, U4SSC) for normal and extreme conditions, with the limits of what the project does not cover.
- **Evidence:** new process: cycle list of capacity 4, levels 1-4 with actions, committee decides (`docs/requirements/01-specs.md` sections 2 and 7; `docs/deliverables/kpi-cards.md`); scope limits in `docs/requirements/01-specs.md` section 1 (out of scope).
- **Gap to level 4:** several KPI targets read "Set by owner" or "meaning pending confirmation" (`docs/deliverables/kpi-cards.md`); no ISO 37120/37122 or U4SSC reference; extreme (crisis) condition not covered.
- **Slide:** 2, 5 (partly).

## 4. Targets translated into a dashboard for its audience (weight 10)

- **Level 3:** designed for a named audience (operator, decision maker, leadership); answers its question; shows current against target with thresholds and alerts.
- **Level 4:** leads from alert to action; tested with audience representatives and changed after the test.
- **Evidence:** `app.py` (`SCREENS`: 1 Priority map, 2 Compound file, 3 District view, 4 Digital twin what if; track switch); committee guide `docs/deliverables/user-guide.md`; display-rules check and fixes `docs/deliverables/display-rules-check.md`; alert → action path: level → cycle list → inspection file → visit form (`docs/requirements/01-specs.md` sections 7 and 9).
- **Gap to level 4:** the ten-second test was taken by someone outside the team but its answer sheet and timings are not recorded in the repo (`docs/REMAINING_TEAM_TASKS.md`, T-NA-08); no change log "after the test".
- **Slide:** 6 (live demo).

## 5. Transition from current to target (weight 10)

- **Level 3:** roadmap with phases, owners and resources; includes risks and training.
- **Level 4:** phased transition before execution with progress indicators, criteria for moving between phases, and a rollback plan.
- **Evidence:** next step "run one cycle with the list and record visit results" (slide 11); data request ordered by impact `docs/deliverables/data-request.md`; quarterly monitoring procedure `docs/deliverables/technical-track-a.md`; risks and fallbacks `docs/requirements/01-specs.md` section 13; roles `docs/requirements/01-specs.md` section 10.
- **Gap to level 4:** no written roadmap with phases, owners, resources, training, phase-gate criteria or rollback for ACUD adoption; this is the weakest documented criterion.
- **Slide:** no slide yet (slide 11 has one next step only).

## 6. Solution effectiveness: preventive (weight 12)

- **Level 3:** effectiveness measured for the solution type: reactive (time to detect and respond), preventive/predictive (precision, recall and false-alarm rate; unclear in the source), on past data.
- **Level 4:** adds feasibility (when the solution stays valid) and the trade-off between the cost of a false alarm and the cost of a missed event (unclear in the source).
- **Evidence:** frozen-clock backtest on six real R7 cases: 1 of 6 after-start, 0 of 6 point-in-time; criterion of 5 not lowered (`data/BACKTEST_CURRENT.md`); diagnosis of misses (`data/experiments/35_backtest_diagnosis/DIAGNOSIS.md`); generated-data recall@4 per method against random mean 0.335 (2,000 draws) (`data/EW_REPORT_CURRENT.md`); per-class recall and macro-F1 (`data/CURRENT_MODEL_METRICS.csv`, e.g. logistic_combined macro-F1 0.615); `docs/deliverables/method-card.md`.
- **Gap to level 4:** the real-case criterion was not met (1 of 6); the test holds only 4 distressed rows (`data/EW_REPORT_CURRENT.md`); no false-alarm rate on real cases and no false-alarm vs missed-case cost trade-off.
- **Slide:** 7, 8, 8b.

## 7. Return on investment (weight 12)

- **Level 3:** return measured in at least one unit (cost reduced or removed, work hours, resolution time), direct or indirect, with its cost (effort, cycles) (unclear in the source).
- **Level 4:** return in several units with a sensitivity calculation (best/worst) and a comparison with an alternative (doing nothing or another solution).
- **Evidence:** `configs/cost_assumptions.yaml`: three settings; "Under these assumptions, from -0.006 to 0.098 million EGP per year"; compared with the current policy of visiting all 12 compounds 4 times a year; formula in `docs/requirements/01-specs.md` section 12; `docs/deliverables/decision-memo.md`.
- **Gap to level 4:** one unit only (EGP); operating cost, missed cases and cost of late detection are PLACEHOLDER values (`configs/cost_assumptions.yaml`, T-SA-03); the conservative setting is negative; no work-hour or time-to-resolution unit.
- **Slide:** 9.

## 8. Governance (weight 10)

- **Level 3:** clear ownership of data, indicators and model; permissions; quality and privacy controls (Law 151 of 2020) (unclear in the source).
- **Level 4:** an integrated system: change and version control, audit log, periodic review, risk management with owners.
- **Evidence:** ownership, access and sharing per data group plus "Version and change controls" (`docs/deliverables/governance-cards.md`); quality gates and run id (`docs/deliverables/quality-report.md`); privacy, masking, Law 151/2020 note (`docs/deliverables/responsible-ai.md`); recorded reviews (`logs/review-05.md`); risks with fallbacks (`docs/requirements/01-specs.md` section 13).
- **Gap to level 4:** owner roles are proposed, not approved by ACUD (`docs/deliverables/governance-cards.md`); one quality FLAG still open (`docs/deliverables/quality-report.md`: 1 FLAG, 10 PASS); risks have fallbacks but no named owner role per risk; no periodic review schedule agreed.
- **Slide:** 10.

## 9. Documentation and knowledge transfer (weight 6)

- **Level 3:** technical documentation, user guide and a knowledge-transfer record (unclear in the source).
- **Level 4:** another team can run and maintain it without the original team.
- **Evidence:** `docs/deliverables/technical-track-a.md`, `docs/deliverables/user-guide.md`, `docs/deliverables/knowledge-transfer.md`, `docs/deliverables/method-card.md`, `docs/deliverables/final-checklist.md`.
- **Gap to level 4:** no record that a person outside the team rebuilt or ran the system from these documents; the user guide was checked against code, not in a browser (`docs/deliverables/user-guide.md`).
- **Slide:** no slide yet (mention in slide 11 or in answers).

## 10. Presentation and answers (weight 10)

- **Level 3:** a clear story from current to target state and a summary with the decision requested; 12 minutes; accurate and transparent answers (unclear in the source).
- **Level 4:** leadership-level persuasion: conveys the value strongly and handles hard questions with evidence and alternatives.
- **Evidence:** decision requested in `docs/deliverables/decision-memo.md` and slide 11; prepared answers `docs/deliverables/expected-questions.md`; deck text `docs/deliverables/presentation.md`.
- **Gap to level 4:** the deck is written for 12-15 minutes and must fit 12; the as-is to to-be story has no slide (criteria 2, 5); timed rehearsals are still open (`docs/REMAINING_TEAM_TASKS.md`, T-ALL-05).
- **Slide:** all; decision on 11.

## Bonus: transferability, scalability, sustainability (+10)

- **4-7:** transferable to another region or pillar with an alternative.
- **8-10:** proven transfer with a sustainability plan. (0-3: solution confined to one case.)
- **Evidence:** thresholds and capacity in configuration (`configs/data.yaml` per `docs/requirements/01-specs.md` section 2); public satellite sources not tied to R7; quarterly procedure (`docs/deliverables/technical-track-a.md`).
- **Gap:** only R7 is run (R8 excluded, `docs/requirements/01-specs.md` section 0); no transfer shown. State the transfer path (another region needs boundaries and statements) honestly; claim no proven transfer.
- **Slide:** no slide yet (one line on slide 11).

## Presentation plan for 12 minutes

| Order | Slide | Criteria | Time |
| --- | --- | --- | ---: |
| 0 | 0 Title: project, slogan, supervisor, team | - | 0:15 |
| 1 | 1 Problem in numbers | 1 | 0:45 |
| 2 | 2 Question and decision (add as-is → to-be in one line) | 1, 2, 3 | 0:45 |
| 3 | 3 Data | 2, 8 | 0:45 |
| 4 | 4 Seeing construction from space | 2, 6 | 0:30 |
| 5 | 5 Track A rule | 3, 4 | 1:00 |
| 6 | 6 Live demo | 4 | 1:30 |
| 7 | 7 Backtest: 1 of 6 and why | 6 | 1:45 |
| 8 | 8 Track B (generated) | 6 | 1:00 |
| 9 | 8b What-if scenario | 6 | 0:30 |
| 10 | 9 Value in EGP | 7 | 1:30 |
| 11 | 10 Risks and governance | 8, 9 | 1:00 |
| 12 | 11 Ask, transition step and next step | 5, 10, bonus | 0:45 |
| | **Total** | | **12:00** |

Criteria 6 and 7 (12 points each) get 5:00 of the 12 minutes. Criteria 2, 5 and 9 have no slide of their own; add one line each to slides 2, 11 and 10, or move them to prepared answers.
