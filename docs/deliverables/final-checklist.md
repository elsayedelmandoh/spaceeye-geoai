# Final submission checklist

Task T-SA-10. Built from the file listing of `docs/deliverables` and `docs/requirements`, a search for the log files, and spec sections 11 and 14. "File present" means a file with a matching name exists; it does not mean the deliverable is complete or reviewed. Roles only, no names. Files were checked against the current branch on 3 November 2026.

## The 13 deliverables (spec section 11)

| #   | Deliverable                                                                    | Owner role   | File seen                                                                                                                                            | Status                                                                                      |
| --- | ------------------------------------------------------------------------------ | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| 1   | KPI cards, tree, levels table                                                  | R5           | `docs/deliverables/kpi-cards.md`, `configs/kpis.yaml`                                                                                                | File present. Two tags per card still TODO (`kpi_reference.csv` not in repo).               |
| 2   | Pipeline with gates, `quality_checks_log.csv`, quality report                  | R1           | `docs/deliverables/quality-report.md`, `releases/ready-data/review/real/quality_checks_log.parquet`, `data/dictionaries/real__quality_checks_log.md` | Report and log present. The log is a parquet file, not CSV: confirm the format is accepted. |
| 3   | Analytical core: Track A rule, backtest, Track B dataset and binary classifier | R4           | `data/BACKTEST_CURRENT.md`, `data/EW_REPORT_CURRENT.md`                                                                                              | Reports present.                                                                            |
| 4   | Dashboard (track switch), cycle list, `ops_visits`                             | R5           | `app.py`, `src/dashboard/insights.py`, `src/dashboard/` (map click, 4 filters, code search, sidebar); `chatbot/` (hybrid RAG chatbot, floating button)          | Files present and verified 3 Nov 2026: code search, filters, map click with sidebar; chatbot moved to the hybrid RAG app 4 Nov 2026 (not run live); not run: confirm dashboard starts and visit records. |
| 5 | Method card and monitoring plan | R4 | `docs/deliverables/method-card.md`, `docs/deliverables/technical-track-a.md` | Method card present. The monitoring plan is a written quarterly procedure in `technical-track-a.md`; that file says no monitoring schedule, dashboard or deployment is implied. |                                     |
| 6   | Risks and responsible-AI note, `ai_verification_log`                           | R2 + R4      | `docs/deliverables/responsible-ai.md`, `app_data/ai_verification_log.csv`                                                                            | Both present. Not checked that every LLM number is logged.                                  |
| 7   | Technical docs, user guide, governance cards, data dictionaries                | R1 + R2 + R3 | `technical-track-a.md`, `user-guide.md`, `governance-cards.md`, `data/dictionaries/`                                                                 | Files present. Governance cards review still pending.                                       |
| 8   | Decision memo, Arabic and English                                              | R5           | `docs/deliverables/decision-memo.md`                                                                                                                 | File present.                                                                               |
| 9   | Knowledge transfer pack (one page)                                             | R1           | `docs/deliverables/knowledge-transfer.md`                                                                                                            | File present.                                                                               |
| 10  | One run command that works in the presentation                                 | R1           | `Makefile` target `run`                                                                                                                                            | Target present on origin/main (Makefile lines 9-10): `make run` runs `python -m src.pipeline.team_run --full`. Not executed in this check; no recorded run yet.                                                  |
| 11  | Inspection files for 5 compounds                                               | R4           | `docs/deliverables/INSPECTION_DOSSIERS.md`                                                                                                           | File present. The stored files are now the four cycle-list compounds (C18, C07, C14, C03; 2026Q3), not 5: confirm what the deliverable requires.                                                |
| 12  | Data request list to ACUD                                                      | R2           | `docs/deliverables/data-request.md`                                                                                                                  | File present.                                                                               |
| 13  | Final presentation                                                             | R5           | `docs/deliverables/01-presentation/presentation.md`, `.html`, `.pptx`, `palette.md`, `rubric-map.md`; `docs/deliverables/02-video/intro.md` + `intro.mp4`; build `make/build_pptx.js` | All files verified 3 Nov 2026; presentation review and rehearsal remain unrecorded; backup demo video and cross-reviews not recorded; intro video is not a dashboard demo. |

## "Done when" list (spec section 14)

| Condition                                                           | Status                                                                                       |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Success criterion shown honestly (it failed, shown with the reason) | Written in the memo, slide 7 and the expected-questions sheet. Not yet reviewed by the team. |
| One command builds everything, twice identically                    | Not verified here.                                                                           |
| Every gate has dimension, owner and decision                        | Not verified here (see the quality report).                                                  |
| Every number has a source or origin mark                            | Audit (T-SA-08) completed for the slides and expected questions; source gaps listed in `docs/deliverables/number-audit-slides.md` and `docs/deliverables/number-audit-questions.md` remain open, so the condition is not yet fully evidenced.                                                             |
| Every LLM number is in `ai_verification_log`                        | Not verified here.                                                                           |
| The 13 deliverables are ready and rehearsed twice                   | Not done: see the tables above. No rehearsal is recorded.                                    |

## Day D5 items (spec section 10)

Everything submitted, knowledge transfer pack, two timed rehearsals, backup video, cross-review, fixes only. None of these is recorded as done. The program day is still unconfirmed in the spec (open item 2).

## Open points

1. Two tags per KPI card are pending.
2. Presentation length and language are unconfirmed.
3. Operating cost and missed cases are labelled public proxies; the cost of late detection is still a placeholder that needs ACUD.
4. `kpi-cards.md` needs a short note that the new display-only assumed columns in `kpi_values` are assumptions and never set a level.
5. The monitoring plan exists only as a written procedure (see row 5); confirm that this is what the deliverable requires.
