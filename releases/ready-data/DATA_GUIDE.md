# SpaceEye v5 data guide

## Choose a table

| Need | Location | Meaning |
| --- | --- | --- |
| Public/derived observations and indicators | tables/real/ | Coded register, satellite/annual context, statements and KPIs |
| Prepared synthetic operations | tables/operations/ | Monthly/quarterly finance, masked complaints, assumed fine inputs |
| Inspection selection | tables/inspection/ | Capacity-limited cycle list and 2/4/6 comparisons |
| Current primary model outputs | tables/current/ml_current.parquet | 720 rows: four methods x 180 cutoffs; binary distressed/not_distressed probabilities |
| What-if KPI handoff | tables/current/S1.parquet, S2.parquet, S3.parquet | Frozen-context hypothetical priority changes; S3 changes capacity only |
| What-if explanations | what_if/ | Monthly baseline comparisons and trigger context |
| Training | training/ml_dataset_extended.parquet, metadata.json | 180 rows, exact 40-feature list, equivalent boolean/categorical binary distress targets |
| Complaint classification | See TABLES.csv and component protocol | Separate 100-text feed and 296-text benchmark; preserve their own splits and never merge them for evaluation |
| Inspection-agent inputs | inspection/ | 180 cutoff-safe JSON contexts; these are inputs, not verified final reports |
| Visits and priority exercises | tables/review/ | Explicitly synthetic exercises, not actual inspections |
| Secondary model check | current/developer_holdout_predictions.parquet when supplied | Fixed-seed chronological developer holdout; see metadata/status and metrics view |

TABLES.csv lists exact SQL names, paths and counts. CSV copies are under csv/. Field dictionaries and source/generation records are bundled. Parquet is authoritative for types/nulls.

## Model contract

Target: distressed/not_distressed in the next six months, excluding cutoff month. y_outcome_6m and label_distress_next_6m encode the same distress event. Completion is not predicted. Source handover facts and already_completed_at_cutoff remain descriptive/cohort information, excluded from X.

Train <=2024Q4; embargo 2025Q1; time test 2025Q2?2026Q1. Exclude censored/already-handed-over rows from fitting/evaluation. Censored targets stay null. Use only metadata.features as X; exclude keys, targets, censoring and cohort flags. Fit preprocessing on training data only.

Primary prediction key: method/code/quarter. p_distressed + p_not_distressed = 1. Not_distressed does not mean completed, continuously active or guaranteed healthy. Current metrics include class support, per-class recall, binary macro-F1 and recall@4 against 2,000 random draws. Repeated synthetic quarters are not independent real events. Read docs/EW_PROTOCOL_CURRENT.md and docs/EW_REPORT_CURRENT.md before interpreting scores.

## Important limits

- Public observation, derived calculation and generated assumption are separate origins. Keep the synthetic label on generated displays.
- Annual heights are contextual OBT observations through 2023 plus the approved 2024 estimate. Later heights stay unknown; no fixed +/-2m surveying guarantee remains in the plan.
- K5 and monetary fines are screening/assumption examples, not actual contractual assessments or measured savings.
- S1/S2 use last simulated month per quarter and explicitly freeze public context; S3 preserves levels and changes only capacity selection.
- Preserve publication cutoffs, missing values, masking, codes-only exports and the 2019Q2 quality FLAG.
- Current raw/template generation, real field collection, dashboard and inspection agent are separate from this standalone prepared bundle.

Run verify_package.py after extraction. See docs/BINARY_SCOPE_DECISION.md for the approved scope change. Older ZIPs preserve earlier experiment definitions; do not use their completion-class schema as a current requirement.
