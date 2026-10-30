# SpaceEye: remaining team tasks

Portable review handoff (29 October 2026): [device setup, prepared model refitting and complete source-cache transfer](REVIEW_SETUP.md) are available, with seven saved audit artifacts. Task/review acceptance marks are preserved; this setup change does not complete any pending dashboard, agent or fieldwork task.

Data delivery v6 (30 October 2026): rebuilt with the current code after a review of the v5 data work (stale "start unknown" labels, synthetic_label columns, uninformative developer holdout, provenance comment, name gate on binaries, backtest crash in a full rebuild). Height experiments are closed (v10 lost the 2 % rule; 2024-2026 model values are candidates only). See data/DATASET_CONTRACT.md.

T-AH-10 handoff update (29 October 2026): [original case outputs, prepared inputs and replay command](../releases/ready-data/backtest/README.md) are published separately from the unchanged v5 ZIP. Case-count replay needs no external source drive; full activity refitting and raw-source clock checks still require the source caches. Review status is unchanged.

Updated on 28 October 2026 for approved binary scope and delivery v5. AH-16, EL-01, EL-10, EL-11 and EL-17 are no longer open implementation tasks; see [scope decision](../data/BINARY_SCOPE_DECISION.md). Based on the original **02-team-roles-and-tasks.md** supplied by the team lead. Original task IDs, owners and priority tiers are preserved.

This is an implementation snapshot, not an assessment of individual effort. Work on other branches or outside this repository requires evidence before being credited. The main task-board checkbox now means implemented/ready for review, as requested by the team lead. Separate Review accepted checkboxes require actual human acceptance; no reviewer is signed on anyone's behalf.

## 1. Start here

- [Ready-data download and English guide](https://github.com/elsayedelmandoh/spaceeye-geoai/blob/feat/binary-distress-scope/releases/ready-data/README.md).
- [Implementation evidence and limitations](https://github.com/elsayedelmandoh/spaceeye-geoai/blob/feat/binary-distress-scope/data/PARTIAL_TASKS_CLOSURE.md).
- [Current model report](https://github.com/elsayedelmandoh/spaceeye-geoai/blob/feat/binary-distress-scope/data/EW_REPORT_CURRENT.md).
- [Original board](requirements/02-team-roles-and-tasks.md), [current data contract](../data/DATASET_CONTRACT.md), [technical decisions](requirements/D1_DECISIONS_CURRENT.md).

Use **SpaceEye_R7_READY_DATA_2026-10-30_v6.zip**: 23 ready tables, with binary model outputs. It includes prepared observations, generated operations, 180-row/40-feature training data, complaint corpora, inspection contexts, synthetic visit exercises, current model diagnostics and S1/S2/S3 outputs. Raw sources, private name mappings, hidden truth and model checkpoints are excluded.

Current scope: **12 R7 compounds, six public backtest cases, inspection capacity 4**. Older references to 22 compounds, eight cases or capacity 8 are historical. The rough implementation estimate is approximately halfway complete, not an estimate of remaining hours.

## 2. Status definitions and coverage

- **Build:** requested functionality/output still needs implementation; input data may already exist.
- **Partial:** useful implementation exists; complete the specific missing behavior below.
- **Data/decision:** acceptance requires data or a real team decision, not simply more code.
- **Qualification:** usable output exists, but an original claim or condition is unsupported.
- **Optional:** may be deferred using the original Could/Should cut order.

The list below covers **39 IDs with an unresolved implementation, evidence, decision or optional condition**. Section 10 lists **36 IDs with implementation/output evidence awaiting their original review**, and section 9 records **one failed/excluded experiment**. Together these account for all **76 original IDs**; they are not equally sized jobs.

## 3. Shared tasks

| ID / tier | Owner | Existing work | Remaining action and acceptance |
| --- | --- | --- | --- |
| T-ALL-01 / Must | Whole team | Technical decisions implemented/documented. | Obtain actual agreement/signatures, including the approved binary scope and contextual-height description. Do not invent signatures. |
| T-ALL-02 / Must | Ahmed + Salma | R7 counts/capacity resolved. | Confirm the training-program day and update actual dates. Calendar date alone does not establish D1–D6. |
| T-ALL-03 / Must | Salma | No completed rehearsal evidence identified. | Prepare/rehearse the ten-minute mid-term review and retain a brief record. |
| T-ALL-04 / Must | Whole team | Artifacts, evidence and PRs exist. | Perform the original cross-review: Ahmed/Sayed, Verina/Nada, Salma on docs. Record findings and actual acceptance in PRs. |
| T-ALL-05 / Must | Salma | Final demo remains incomplete. | Complete two timed rehearsals and a working backup demo video after integration. |

## 4. Ahmed: Track A

| ID / tier | Status / existing work | Remaining action and acceptance |
| --- | --- | --- |
| T-AH-14 / Should | Implemented 30 Oct: `activity.source: k1` switch, tests and effect check (data/K1_FALLBACK_CHECK.md). | Review pending. |
| T-AH-15 / Should | Build: experimental imagery exists locally; the required compound-level handoff is not ready. | Check permitted use; provide two before/after images per compound, capture dates, attribution and images.csv. Do not substitute map-release dates for verified capture dates. |
| T-AH-18 / Could | Optional: matching completed roof-uniformity evidence was not established. | Locate existing evidence first. If retained, register acceptance before testing Google-height roof/slab uniformity; otherwise record deferral/cut. |
| T-AH-19 / Must | Partial: full command and reproducibility evidence exist. | Agree/tag the accepted presentation revision and document its command. Two full runs already matched; do not repeat fitting for documentation-only changes. |

Reuse [technical operations](deliverables/technical-track-a.md), [annual context](deliverables/annual-context.md), [backtest](../data/BACKTEST_CURRENT.md), [full-run evidence](../data/FULL_TRACK_A_REPRODUCIBILITY.json).

## 5. Elsayed: Track B

| ID / tier | Status / existing work | Remaining action and acceptance |
| --- | --- | --- |
| T-EL-15 / Could | Optional: S1/S2/S3 ready; extra cases incomplete. | If retained, implement S4 material cost +40% and S5 grace 12 to 6 months with separate outputs/assumptions. Fine-relief examples are not these tests. |
| T-EL-16 / Could | Optional: matching FPMI/SAF deliverables were not established. | Locate prior results first. If missing and retained, write conditions before testing and log in team_ideas.md; otherwise defer. |

Reuse [protocol](../data/EW_PROTOCOL_CURRENT.md), [method card](deliverables/method-card.md), [metrics](../data/CURRENT_MODEL_METRICS.csv), [fit reproducibility](../data/CURRENT_MODEL_REPRODUCIBILITY.json), [S1/S2/S3 contract](../data/SCENARIO_CONTRACT_CURRENT.md).

## 6. Verina: inspection AI and complaints

| ID / tier | Status / existing work | Remaining action and acceptance |
| --- | --- | --- |
| T-EL-01 / Must | Configuration, prompts, approval guard and tests are done. The model and call budget were confirmed and approved by the project owner on 2026-10-29. | The API key must be present in the git-ignored `.env` on the machine that runs generation; this cannot be checked from the repository. Keep credentials out of Git. |
| T-EL-02 / Must | Implemented in src/inference/tools.py (get_facts, get_kpis, get_images, get_rules) with tests, including one on the real-schema tables of the prepared v5 release. | Images stay an explicit missing status until T-AH-15; full F: data run pending. |
| T-EL-03 / Must | Implemented in src/inference/inspection_file.py: sections filled by code with evidence ids, numeric rejected explanations, action, owner role, due date and escalation trigger; works without the model. | Arabic sentence templates need a native-speaker review; due-date constants and owner roles to be confirmed; HTML/PDF output is T-EL-06. |
| T-VE-04 / Should | Build: project-specific Gemini paragraph workflow not complete. | Generate one paragraph from attached facts plus three visit questions. Flag unsupported/causal claims for review. |
| T-VE-05 / Must | Build: data checks are not an AI claim verifier. | Match generated numbers/dates/codes to JSON; flag causal/unsupported claims. Produce ai_verification_log.csv with original verdict categories and meaningful tests. |
| T-VE-06 / Must | Build: final stored inspection reports not ready. | Produce five Arabic HTML/PDF files with actual model/time and truthful review footer. Never invent reviewer sign-off. Integrate permitted imagery when ready. |
| T-VE-08 / Should | Partial: 100 labelled feed texts and separate 296-text benchmark ready with splits. | Train/evaluate five classes against keyword baseline; locate/prepare separate complaints_30.csv check set and document origin. Preserve template-family splits; never merge the two corpora for evaluation. |

Reuse [component protocol](../data/COMPONENT_DATA_PROTOCOL.md), [responsible use](deliverables/responsible-ai.md), and src/pipeline/privacy.py. Masking is implemented; general real-text review remains necessary. Synthetic complaint accuracy is not evidence of real-world accuracy.

## 7. Nada: dashboard and user guide

Current app.py prints settings; it is not the requested Streamlit dashboard. Existing data readiness does not count as implemented screens.

| ID / tier | Remaining output | Dependency / acceptance |
| --- | --- | --- |
| T-NA-01 / Must | Streamlit entrypoint, Track A/B switch, fixed synthetic banner and generated-value marks. | Runnable app, Track A default; no map in Track B. |
| T-NA-02 / Must | Priority map, cycle list, Arabic reasons and CSV download; Track B list only. | AH-08 data ready. Coded boundaries, priority words, distinct start-unknown and unassessable states. |
| T-NA-03 / Must | Compound screen: series, publication markers, annual context, imagery, KPIs, lineage, inspection report access. | Most inputs ready; imagery/report depend on AH-15/VE-06. Display p_distressed and p_not_distressed; no completion probability is required. |
| T-NA-04 / Must | Real ops_visits form and persistence: code/date/result/note. | Empty template and synthetic exercises exist. Store actual entries separately from synthetic examples. |
| T-NA-05 / Must | Would-it-have-warned screen. | Use current six-case check and capacity-4 metrics/limits; do not present historical eight-case/N=8 figures as current. |
| T-NA-06 / Must | Data-trust screen: quality, coverage, unassessable records and origin key. | Current logs ready. Preserve 2019Q2 FLAG; verify old fixed fact-count figures before display. |
| T-NA-07 / Must | S1/S2/S3 what-if screen with changes and explanations. | Exports ready. Show frozen public context/generated assumptions; no Track B map or operational forecasting claim. |
| T-NA-08 / Must | Display-rules review and external-user ten-second test. | At most four main tiles; each has value, unit, denominator, as-of and origin. Record actual feedback. |
| T-NA-09 / Should | Arabic RTL rendering and no_names checks on dashboard exports. | Reuse the gate and include interface output locations. |
| T-NA-10 / Must | Committee guide for map, compound screen and visit form. | Document implemented behavior, not planned screens. |

## 8. Salma: value and final delivery

T-SA-04 governance cards are already written and need review.

| ID / tier | Remaining output | Dependency / acceptance |
| --- | --- | --- |
| T-SA-01 / Must | Agree current use-case compass; obtain signatures, instructor rubric and presentation duration. | Technical decisions exist; generic earlier compass text is not signed acceptance. |
| T-SA-02 / Must | A/K2/K3/K4/K5/K6 cards with required fields/tags; KPI tree, levels table, kpi_reference schema. | Create project-specific configs/kpis.yaml; the unrelated utility-demo file was retired. |
| T-SA-03 / Must | Three explicit EGP-value settings without double counting. | Create project-specific configs/cost_assumptions.yaml for this use case. Assumed fines are not measured savings or actual penalties. |
| T-SA-05 / Must | One-page decision memo in Arabic and English, same facts/order. | Use current evidence and binary model limitations. |
| T-SA-06 / Must | Actual slides/deck and presentation script. | The presentation script/deck have not been created; the empty placeholder was retired. Quote method, denominator, capacity, scope and generated-data status; preserve the original restricted backtest-slide name exception. |
| T-SA-07 / Must | Wording audit with recorded checklist across docs/slides/screens. | Use priority level; never label a real compound financially distressed from synthetic data. |
| T-SA-08 / Must | Trace every presented number to data/report/verifier evidence. | Complete after memo, slides and agent verification outputs exist. |
| T-SA-09 / Must | Expected-questions sheet with concise answers. | Cover synthetic data, unsuccessful experiments, approved binary scope and actual inspection use. |
| T-SA-10 / Must | Final thirteen-deliverable and done-when checklists. | Check artifacts, working demo and real reviewer acceptance; prepared data alone is insufficient. |
| T-SA-11 / Should | Current timeline with real program day, dates and owners. | Team input required; do not copy retired milestones as current dates. |
| T-SA-12 / Could | Blind labelling support only if a new finishing experiment is retained. | Locate prior labels first. Existing finishing product was rejected; do not restart solely to tick an obsolete experiment. |

## 9. Failed experiment: do not restart by default

**T-AH-17 / Could:** the Qwen-VL/Wayback finishing experiment ran and failed: recorded VLM balanced accuracy 0.559, below the 0.75 gate. Preserve its negative result and exclusion under the original cut rule. No approved finishing feature is published. Board-specific named labelling/reviewer acceptance is not implied by experimental labels.

This is a failed experiment, rather than missing application implementation. It does not automatically justify another run.

## 10. Existing outputs: review and reuse

These 36 IDs have implementation/output evidence. These main task-board checkboxes are marked complete for implementation and have separate pending human-review checkboxes. Retain actual review requirements; do not rebuild already supplied outputs.

| Owner | IDs | Existing output |
| --- | --- | --- |
| Ahmed | T-AH-01, T-AH-02, T-AH-03, T-AH-04, T-AH-05, T-AH-06, T-AH-07, T-AH-08, T-AH-09, T-AH-10, T-AH-11, T-AH-12, T-AH-13, T-AH-16, T-AH-20, T-AH-21 | Scope/config/rule, Arabic CSV, lineage, checks, explained backtest, two full-run reproducibility, technical operations and handover. Running/reporting the backtest is complete; its original success criterion was not achieved. |
| Elsayed | T-EL-01, T-EL-02, T-EL-03, T-EL-04, T-EL-05, T-EL-06, T-EL-07, T-EL-08, T-EL-09, T-EL-10, T-EL-11, T-EL-12, T-EL-13, T-EL-14, T-EL-17, T-EL-18, T-EL-19 | Protocol, synthetic data/labels, dictionaries/features, fine assumptions, current comparisons, S1/S2/S3, method card and ACUD request. Pre-launch defect validation uses private generator audit; public launch coverage remains incomplete. |
| Verina | T-VE-07, T-VE-09 | Masking baseline/tests and responsible-use note; these do not implement the AI verifier. |
| Salma | T-SA-04 | Governance cards; roles/policies need actual acceptance. |

Saved validation: 57 tests and touched-source Ruff passed; two full Track A runs matched 276 manifest entries; repeated current-model fits produced 13 identical files; 23 saved realism checks passed; six planted defects matched; ZIP CRC and all 291 manifest hashes passed. The current team_run command completed. Make itself was not installed here.

## 11. Recommended sequence

1. Agree supported model scope, program day and optional cuts. Read the current bundle/limitations.
2. Build the dashboard skeleton/map/compound/visit form and deterministic inspection tools/template using existing inputs; assign separate owners if working in parallel.
3. Finish verifier, stored inspection reports and complaint-classifier comparison. Add optional LLM prose after the deterministic path works.
4. Integrate trust/evaluation/what-if screens; complete KPI/value cards and committee guidance. Display missing imagery and model uncertainty honestly.
5. Complete memo/deck, number/wording audits, cross-review, accepted revision tags, rehearsals and backup video.

Could-tier experiments/S4/S5 are cut first. Wayback images may be deferred under the original Should-tier cut order if access/terms/preparation remain unresolved. Keep the deterministic report and binary logistic baseline. Completion prediction is outside the plan.

## 12. Git and distribution status

The previous v4 delivery and task document were pushed. This v5 update changes the approved model scope, target encoding, current fits, plans and bundle; it must be committed and published on the binary-scope feature branch. Raw sources, hidden truth and checkpoints remain excluded.

The previous implementation review is [PR #3](https://github.com/elsayedelmandoh/spaceeye-geoai/pull/3). Feature-branch publication is distinct from merge/reviewer acceptance; check its current GitHub state before assuming main contains the latest delivery.

## 13. Related requests outside the original board

Water/gas meter connection counts are not implemented in v5. The original Track B task explicitly specified electricity meters only. The existing generated meters_active field is the stock of active electricity meters at each month, not new connections during that month. Satellite dw12_water describes surface-water context, not utility connections or consumption.

The published roads_paved_share is generated. The attempted real roads detector did not meet its acceptance gates. Do not replace generated labels with real-observation labels. These utility/roads qualifications do not add new IDs to the original 76-task count; any additional implementation should receive an explicit owner and scope.
