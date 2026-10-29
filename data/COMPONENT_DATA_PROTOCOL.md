# Component-data completion protocol

Defined before generating outputs,28October2026. Data preparation only: no model fitting,LLM calls,UI work or real inspection claims. Continue on feat/share-ready-data-v2 and its pull request;never work/push directly on main.

## Outputs and fixed definitions

1. **Complaint labels:** join accepted masked complaints to the existing private category truth on complaint_id,for target creation only. Export text as the sole model input;desk labels and gold labels are separate. Group shared normalized body templates and duplicate families so they cannot cross split boundaries. Fixed seed/hash assignment,no tuning to model scores. Disclose split/class counts and any small/unavailable class. No raw answer key or hidden cause is distributed.
   The observed-feed holdouts are small and do not cover all classes. A separate generated benchmark allocates body-template families per class to train/validation/test BEFORE generating variants;secondary topics stay within that split. Eight variants per family,seed2026. Never combine the two corpora for evaluation:their original template families overlap. Neither is independent real-world accuracy evidence.
2. **Inspection contexts:** one coded,structured context per compound/quarter in2023Q1–2026Q3. Public statements,operations and observations are filtered by cutoff;targets/hidden truth are excluded. Source URLs/publishers containing forbidden project/developer names are withheld rather than disguised. Published facts and generated observations/visits occupy separate sections. Missing images are explicitly marked,not fabricated.
3. **Financial-to-priority data:** retain frozen cutoff public context and financial B1/B2/B3 flags. Project the contractual plan using its cutoff value plus the already-declared monthly capacity;apply only the existing B5 gap>20threshold to forward simulated progress. Existing B1+K2rule and completion cap are retained. Re-rank eligible levels1–3 at capacity4;compare with the same month's baseline. No future satellite activity,complaints,handover or assessed fines are invented as observations. This is a declared hypothetical rule,not validated operational accuracy.
4. **Synthetic visits:** derive a small scheduled-inspection exercise from eligible cycle selections and already-generated monthly truth. Fixed seed,visits5–14days after quarter end,results progressing/stalled/complete/not_done. Use cutoff state as an explicit assumed field state;no future hidden month is read. Mark every record generated;exclude from ML X and independent real evaluation. Never replace the empty real-visit template or claim an actual inspection occurred.

## Required checks

Known codes,unique keys,masked texts,no cross-split body/duplicate groups,cutoff filtering,no hidden truth in contexts,valid capacity ranks,baseline comparisons,explicit generated origins,manifest/ZIP integrity,and preservation of existing base tables. Supporting documents and helpers are English;Arabic complaint text remains data.

The obsolete docs/plan files are removed from tracking and ignored after a local backup,per user instruction. The current product design and data contracts remain authoritative. Updated ready-data bundle will replace the older published archive through the existing feature-branch pull request.
