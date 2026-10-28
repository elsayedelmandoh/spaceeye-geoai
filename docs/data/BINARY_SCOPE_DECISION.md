# Approved binary distress scope

28 October 2026. Authority: the team lead explicitly removed completion prediction from the plan and requested closure of AH-16, EL-01, EL-10, EL-11 and EL-17.

1. Predict **distressed / not_distressed** in the next six calendar months. Completion is no longer a class, probability or acceptance requirement. Not distressed does not mean completed or guaranteed healthy.
2. Keep source handover facts and descriptive may-be-complete/already-handed-over states. These remain necessary for rule caps, fine screening and cohort definition; they are not predicted completion classes.
3. AH-16 accepts the existing approved compound-level height context and vegetation export. Remove the fixed +/-2m guarantee from acceptance. No new height experiment or post-2024 product is required.
4. EL-01 is resolved by retiring the unattributed historical 92% claim. Recovery/attribution of that percentage is no longer required. Use current measured results.
5. EL-10/11/17 use the binary protocol, fixed-split logistic/boosting comparisons, repeatable outputs and a pinned revision/tag. Scientific limitations do not prevent completion of this implementation scope.

## Execution

- [x] Update target definitions and regression checks.
- [x] Freeze the revised protocol before refitting; retain chronological split and fixed parameters.
- [x] Evaluate binary models and verify normalized probabilities and repeat-fit equality.
- [x] Update current plans, handoff, guides, method card and dictionaries.
The producing implementation is pinned by tag `r7-binary-distress-2026-10-28`; package provenance records its revision. Publication follows the feature-branch/PR workflow.

Historical ZIPs and Git history retain the earlier experiment. Current files supersede that scope; historical scores are not relabelled as new results. No named teammate review/signature is invented.

Validation: 57 tests and touched-source lint passed; the current team workflow completed. Binary classes occur in primary train/test and the fixed-seed developer holdout fitted successfully. 13 fitted-output files reproduced byte-for-byte. All 40 feature columns and original boolean distress labels match the prior v4 export; only categorical outcome encoding/probability scope changed.
