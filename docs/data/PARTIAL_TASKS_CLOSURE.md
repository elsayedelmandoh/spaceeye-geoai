# Closure of tasks previously estimated above 40 percent

Scope authorized on 28 October 2026: AH-07/08/09/10/13/16, EL-01/02/05/10/11/12/14/17, VE-07 and the unfinished shared decisions/scope items. Existing completed documentation remains subject to named reviewer acceptance.

## Execution plan

- [x] Add Arabic indicator reasons, committee CSV and explicit lineage without changing priority values.
- [x] Complete pre-model masking for supplied names and phone formats, with regression checks.
- [x] Freeze current evaluation protocol before fitting; report unsupported classes honestly.
- [x] Fit current logistic/boosting baselines and compare satellite-only, combined, rule and seeded random at capacity 4.
- [x] Re-evaluate real-case backtest with the saved overlap-excluded activity model; add numeric alternative checks.
- [x] Export S1/S2/S3 with change explanations; audit planted defects and annual context coverage.
- [x] Verify two full Track A runs and refresh prepared data/components; the current bundle is version 4.
- [x] Update current handoff/spec open items and task-level evidence; preserve teammates' changes; publish through feat/complete-partial-tasks.

## Preconditions and limits

Training data currently has no `completed` target. No synthetic completion event will be inserted or test row moved to training to hide that limitation. Models may fit the two observed classes; completed probability must remain null and three-class acceptance must remain unmet. The prior N=8 binary experiment and prepared v3 ZIP remain historical artifacts.

The original first-build 92% attribution must be verified from an archived artifact before it is assigned to a particular model/view. Program day, signatures, rubric and named reviewer acceptance cannot be invented. The +/-2m height wording is not an established per-building guarantee. Public-launch validation may remain unknown even when a planted synthetic defect is verifiable in a private generator audit.

## Task evidence and exact remaining conditions

| Task | Implemented evidence | Remaining condition |
| --- | --- | --- |
| AH-07/08/09 | reason_ar, ordinal level words, coded UTF-8 committee CSV with quarter/origin/run_id/computed_at; dictionaries updated | Named reviewer acceptance |
| AH-10 | Full Track A rerun, frozen-clock checks, explained six-case CSV and BACKTEST_CURRENT.md | Original success criterion is not met; this is an experimental result, not unfinished execution |
| AH-13 | Two full run_all runs; identical manifests across 276 artifacts; make run / team_run --full entrypoint | Make is not installed here; Python paths executed directly |
| AH-16 | Annual context CSV and coverage table; approved height/vegetation handoff | +/-2m wording explicitly unverified; no later-height product invented |
| EL-01 | Current method/view/denominator documented; unsupported historical percentage claim retired in specs | Exact original first-build 92% attribution remains unverified; do not assign it by guesswork |
| EL-02 | Current frozen protocol, fixed split/parameters/capacity/random baseline and acceptance conditions | Three-class data support condition fails |
| EL-05 | Six planted defects match expected counts; 23 saved realism checks have no failures | Pre-launch check uses private generator audit only; public launch dates remain incomplete |
| EL-10/11 | Logistic/boosting, satellite/combined fits; class recalls, macro-F1, confusion counts and predictions | Completed is absent in training: three-class fitting/acceptance remains unmet; p_completed is null |
| EL-12 | Capacity-4 public/combined rules, fitted diagnostics, 2,000 random draws and separate real-case check | Generated scores are not independent real-world validation |
| EL-14 | S1/S2 quarterly KPI-shaped exports, monthly change reasons, S3 capacity comparison; same base KPI columns | Future public context is explicitly frozen; dashboard screen remains separate |
| EL-17 | One current Track B command; deterministic fitted outputs and local models; committed implementation | Original three-class release cannot be declared complete without supported labels |
| VE-07 | Pre-model phone/name baseline, supplied-name option, accepted/rejected masking and assertions/tests | General real-text anonymization still needs review; regex is not an exhaustive NER system |
| ALL-01/02 | Current technical decision register; 12 R7 compounds / six cases / capacity 4; specs open items updated | Team signatures, program day and named approvals require actual team input |

## Validation and interpretation

57 tests passed; touched-source Ruff and whitespace checks passed. The current team_run command completed. Full Track A reproducibility passed for 276 manifest entries. A repeated current-model fit produced eight identical files, including local model checkpoints. The six-defect audit matched all six; 23 saved realism checks passed. The existing 2019Q2 FLAG remains visible.

Current time-test recall@4 counts: public rule 3/4, combined rule 3/4, logistic satellite 1/4, logistic combined 2/4, boosting satellite 4/4, boosting combined 1/4. These are repeated synthetic quarterly labels, not four independent real events. Missing completed probability remains null. No performance-driven noise or threshold changes were made.

The previous v3 ZIP and historical binary data/evaluation are preserved. Current prepared exports add fields/diagnostics; raw/source/private data and model checkpoints are not published. Changes remain on a feature branch under the configured human identity.

Current prepared delivery: `SpaceEye_R7_READY_DATA_2026-10-28_v4.zip`, 23 ready tables, 292 files. [ZIP validation](READY_V4_VALIDATION.json) records CRC, every manifest hash, common what-if schema, priority labels and missing-class probability checks. The producing implementation is pinned in package PROVENANCE.json.
