# Protocol: FPMI and SAF tests (generated data only)

Status: APPROVED by the team lead on 2026-11-01 for the thresholds (section 3) and the missing-progress rule (section 2). Hashed before any run: see `protocol-fpmi-saf.sha256`. Synthetic - for training only.

## 1. Question

Do FPMI and SAF rank the generated R7 compounds in a way that matches the later distress label? Both are tested on generated data only, as diagnostics. Neither changes the Track A rule, the Track B features already in `ml_dataset`, or any priority level.

## 2. Inputs and rules

Unit: compound x quarter, as in `ml_dataset`. As-of quarter t. Label y = `label_distress_next_6m` (distress in any of the next six months, excluding the cutoff month; `docs/DATASET_CONTRACT.md` line 130).

- Escrow coverage ratio at t = `cover_balance_egp` / `cost_to_complete_egp`, both from the quarterly table at the last quarter-end on or before t (`data/dictionaries/sim_clean__fin_quarterly.md` lines 18-19).
- Building growth velocity at t = (reported_pct at the latest supervisor report on or before t minus reported_pct at the report before it) / months between those two reports. Source: `data/dictionaries/sim_clean__fin_monthly.md` line 10. **Missing-progress rule (approved):** velocity needs two reports on or before t. A compound with fewer than two reports has no velocity at t. Such rows are excluded from the FPMI test. Gaps are never filled, interpolated or carried forward.
- FPMI_t = escrow coverage ratio_t x velocity_t (defined only where velocity is defined).
- Remaining escrow balance = `cover_balance_egp` at t (same source as above).
- Material shock index 2024 = mean of `materials_index` over the months of 2024 that are on or before t (`data/dictionaries/` drivers table; `src/pipeline/build_real.py:177`). For t before 2024 it is undefined, and the row is excluded from the SAF test.
- SAF_t = remaining escrow balance_t / (cost_to_complete_t x material shock index 2024).

## 3. Conditions (approved thresholds)

- FPMI: Spearman rank correlation between FPMI_t and y over all rows where FPMI_t and y are defined. **Pass if rho > 0.20.** Otherwise fail.
- SAF: Spearman rank correlation between SAF_t and y over all rows where SAF_t and y are defined. **Pass if rho < -0.15** (lower SAF means more shock exposure). Otherwise fail.
- Minimum data: if fewer than 3 positive labels or fewer than 3 compounds remain for a test, the test is reported as NOT TESTABLE, not as pass or fail.
- Report for each test: rho, n rows, n compounds, n positive labels, the number of rows excluded and why (missing velocity, t before 2024 for SAF).

## 4. Leakage rules

Every input must be published on or before t. Excluded fields: any `true_*` column, `answer_key`, hidden truth, and any column the generator writes after t. A test that uses a value from after t fails the protocol.

## 5. Scope

Generated data only. Label "Synthetic - for training only" on every table and result. No refit of any existing model. Track A thresholds unchanged. Results are diagnostics, not accuracy claims.

## 6. Status line

Approved for thresholds and the missing-progress rule. The unit, label, velocity, shock-index and minimum-data definitions in sections 2-3 are the drafter's choices, marked here so the owner can object before the hash.
