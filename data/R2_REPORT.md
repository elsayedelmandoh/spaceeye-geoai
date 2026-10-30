# R2 current release report,28October2026

Synthetic - for training only

Scope12R7compounds. Raw reconstruction:543financial rows/1349complaints. Prepared:540financial rows/1334complaints. Quarterly financial rows:180. Expanded dataset:180rows/40features.

## Preparation

Removed3duplicates;repaired8thousand-EGP balances;removed5invalid report observations;quarantined15complaints;masked10phone texts. Raw retained;no private truth repairs. Missing public launch dates still prevent verifying every pre-launch defect. Quarterly sales,collections,land payments andkWhare summed flows;balances use the last month.

## Generated missing inputs

Twelve synthetic allocation/contract assumptions respect earliest evidence anchors and price vintage. Allocation is retrospective and excluded from X/public K6. Available generated installments determine land value when present. Fine rate1%is illustrative,not a published universal rate. News-supported50%relief/12-month scheduling are optional scenarios after2024-11-18;eligibility and expiry are unknown. Sources and limits:configs/synthetic_sources.json.

## Dataset and split

Keys/targets never enter X. Expanded metadata declares exact40features and origin/missingness.90-day complaints are normalized by units sold in the cutoff month,not cumulative inventory;this is a flow-normalized diagnostic,not buyer incidence.

| Split | Rows | Classes |
| --- | ---: | --- |
| train | 96 | {'not_distressed': 89, 'distressed': 7} |
| embargo | 12 | {'not_distressed': 10, 'distressed': 2} |
| time_test | 48 | {'not_distressed': 44, 'distressed': 4} |
| censored | 24 | {} |

Censored targets are null. Categorical and boolean targets represent the same next-six-month distress event;completion is not predicted. Already-handed-over cutoffs are flagged for cohort exclusion. The approved classifier is binary distressed/not_distressed,with both classes in training and test. Current observed-class diagnostics are separate in EW_REPORT_CURRENT.md;this data-only writer does not fit them. Old132-row/26-feature binary dataset and N=8scores are historical evidence,not validation of capacity4/new schema.

## Simulation limits

Historical progress is anchored reconstruction,not causal cash-to-progress history. Separate forward scenarios:648rows,baseline/collections drop/FX cost shock,same cutoff state and productivity draws,finite cash/credit/accounting constraints. They do not forecast handover/occupancy. Fine EGP fields are not deducted from historical/forward cash ledgers.

## Validation

Historical12hard/11calibration checks retained as evidence. Current data-only audit:61checks PASS;extension:15checks PASS. Saved full Track A/current model equality is recorded in FULL_TRACK_A_REPRODUCIBILITY.json and CURRENT_MODEL_REPRODUCIBILITY.json. A fresh data-only delivery run writes its own REPRODUCIBILITY.json/local delivery_reproducibility.json;do not infer operational accuracy. See dictionaries/README.md and HANDOFF.md.
