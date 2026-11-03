> Current partial-task extension (28 October 2026): Arabic exports, full-run reproducibility and current observed-class diagnostics are now implemented. Read [PARTIAL_TASKS_CLOSURE.md](PARTIAL_TASKS_CLOSURE.md). Older no-fitting statements refer to the base data-only delivery. Binary distress prediction is the approved scope; no completion class/probability remains.

# SpaceEye: R7 Inspection Priority and Data Release

Updated: 28 October 2026. Current implementation contract; historical plans and the imported Notebook drafts are background.
Dataset contract: [DATASET_CONTRACT.md](DATASET_CONTRACT.md). Current handoff: [HANDOFF.md](HANDOFF.md).
Every generated output is labelled **Synthetic - for training only**. Public observations and statements retain their actual origin.

## Decision and scope

Help an inspection committee prioritize coded compounds in R7 and see the evidence behind the recommendation. The committee decides.
Current scope: 12 coded compounds; R8 sources remain archived for later. No real developer or compound name appears in application outputs.

The implemented data release includes public-data tables, inspected priority indicators, a historical synthetic reconstruction of internal operations,
prepared synthetic tables, a frozen binary evaluation dataset, an expanded dataset with equivalent boolean/categorical binary distress targets, and separate hypothetical forward financial scenarios.
A dashboard, inspection-file LLM, complaints classifier and visit-recording UI are not implemented by this data release.

## Public observations and priority

- A: a tested activity classifier using Dynamic World and Sentinel-2. The accepted mode is q2hold: the latest Q2 window is held until the next Q2 window.
  Quarterly input tables do not imply an independent new activity estimate every quarter.
- K2: consecutive inactive quarters after the legacy rule-start state. Missing observations do not count as inactivity.
- K3: months past the first published handover promise; later promises never reset the clock. Only already-published facts are available at each cutoff.
- K4: minimum image coverage and an accepted boundary.
- A published handover or sufficient vegetation suggests "may be complete"; it caps urgency and requests confirmation.
- User-requested imported-spec extension: K6 >24 adds level1; K6 13–24 adds level2. Capacity is now 4 (one third of12), selected before rebuilding, not from model scores.
  The R1 cycle list includes eligible levels 1–3 only; EW top-N evaluation is a separate fixed-budget comparison.

## Administrative launch and observed start

Legacy started/start_quarter are retained for the evaluated K2/priority rule: a sustained activity run or a published launch/delivery event can trigger them.
They must not be presented as a pure physical-start measurement.

New descriptive fields separate that legacy convention from observed evidence:
observed_started, observed_start_quarter, observed_start_source, launch_date_asof, launch_first_published, start_observation_sufficient and K6.
Observed start requires four consecutive assessable active quarters or an already-published delivery event. Launch alone does not establish it.
K6 is months since the first known launch or promise publication without a confirmed observed start. The reference date, publication and source are stored separately.
It is null after confirmed start or when reference/coverage is insufficient. It does not prove that no work occurred. It now enters the priority rule with the imported thresholds.

K5 stores cumulative screening months after the first deadline without observed start and after the12-month grace, with overlap counted once. It stops accruing at the first published handover; previously accumulated months remain. Missing deadline/evidence remains unknown. This is a research policy proxy, not verified contractual eligibility.
Generated-only K5_egp = K5_months × assumed monthly rate × assumed land value. The default 0.5% rate and land-price assumptions are explicit in configs/data.yaml, not legal/contract rates. No EGP fine enters the public-observation KPI table.

## Historical synthetic reconstruction

The generator reconstructs a plausible historical path consistent with public activity and announcements.
Progress/handover anchors are constructed first; simulated finance and imperfect observations follow them.
It supports a mechanism demonstration and data-quality exercises, not a measured claim that cash shortfalls caused the historical trajectory.

Two wide public tables are generated: fin_monthly and complaints. Hidden progress, cash, distress and complaint truth stay in private.
Deliberately dirty raw tables retain six documented defect types. A separate sim_clean stage removes monthly duplicates, applies the declared unit-repair rule,
suppresses report observations with inconsistent dates, quarantines unknown/out-of-range complaints and masks phone text.
Unobserved launch dates cannot be used to repair every pre-launch complaint; this limit is explicit.

## Binary training and evaluation

One training row is a compound and quarterly cutoff. X is the explicit feature list in ml_dataset_metadata.json.
The target is distress in the next six months, with censored targets null. Keys, hidden truth, administrative warning/status, fitted predictions and labels never enter X.
The historical binary evaluation/export remains frozen. The new private/ml_dataset_extended.parquet adds the proposed observed features and K5/K6, quarterly financial observations, and y_outcome_6m (distressed/not_distressed) alongside the binary target. Current fitting is documented separately in EW_REPORT_CURRENT.md.
The expanded dataset covers15quarterly cutoffs,2023Q1–2026Q3. Early unavailable history/trends remain null. Completed means new full-project handover within the next six months, never a partial handover; distress takes precedence. Already-completed cutoff rows are flagged for exclusion from a transition classifier. Censored targets are null.

Keep the declared time split and embargo. The old N=8 results are historical and do not evaluate current capacity4 or the expanded schema. No metric-based noise tuning.
Fit preprocessing on training only; future-contamination tests are required.
Report both ongoing-distress rows and genuinely new onsets, plus counts, inspection capacity and random baseline.
Generated-data performance is not operational accuracy. app_data/EW_REPORT.md is historical evaluation evidence; current data-only checks are in app_data/data_completion/audit.json and release_audit.json.

The real-case backtest uses information published by each cutoff and measures warning relative to the first announced delivery deadline,
not relative to the later publication of a delay. Failures remain visible.

## Separate forward financial scenarios

From the configured cutoff, preserve available history and simulate baseline, lower collections and higher imported cost with the same initial state and productivity draws.
Actual available operating cash and finite assumed credit constrain spending, and spending constrains progress.
Financial guarantees are not liquid cash. Working capital, opening debt/arrears, release share, future collections, costs and capacity assumptions are recorded explicitly.
No future real statements, handovers or private truth anchor the scenario outcomes. These paths are not handover/occupancy forecasts or measured ACUD causal effects.

## Quality, reproducibility and final command

Run locally, from the repository:

    uv run --locked --offline --with matplotlib python -m src.pipeline.complete_data

This data-only command reuses saved activity observations, rebuilds KPI/prepared data, quarterly financials, fine assumptions, capacity scenarios and the expanded dataset, then audits the outputs. It does not fit a model. Remove --offline if the environment is not cached.
The older src.pipeline.release command is a full rebuild including model fitting/evaluation and is not required for this data-only update. No live source downloads are performed.

Required checks include source/keys/scope/origin/name gates, historical hard realism checks and repeated seeded simulation,
valid prepared tables, feature/label separation, censoring, input/code hashes, scenario conservation and reproducibility.
Calibration failures are reported honestly. app_data/release_audit.json and manifests identify the exact release.

Data is outside Git in Project/app_data and Project/private. Private mappings/labels are never committed.
Older documents were backed up under Project/before_corrections/2026-10-28_data_release.
The imported Notebook texts are preserved under Project/notebook_sources/2026-10-28 and are proposals, not overrides of this implemented contract.

## Product work after data

The data release is suitable for building a future priority view and evidence drill-down with visible origins and limits.
Interface design, additional classifiers, new legal indicators, changed inspection capacity and new operational validation require their own defined scope.
