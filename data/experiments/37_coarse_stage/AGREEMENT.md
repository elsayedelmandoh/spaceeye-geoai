# Step 1 agreement check (PROTOCOL.md): PASS

- **Pass 1:** all 866 usable rows are labelled. S0 360, S1 224, S2 257, mixed 22, unusable 3.
  - The rows were labelled in six batches (files `labels_pass1_a` to `labels_pass1_f`).
  - Batch A rewrote its own file and lost rows. Those rows were labelled again by fresh raters (batches E and F) with the same instructions.
- **Pass 2:** 216 rows (25 %, seed 2037), labelled independently with new ids and a new order.
- **Cohen's kappa, all classes (S0/S1/S2/mixed), 216 pairs: 0.784 (≥ 0.70, gate passed).** Raw agreement is 0.856.
  - Kappa on S0/S1/S2 only: 0.828 (n = 207).
  - The main confusion is S0 vs S2 (11 pairs): blocks that are mostly bare with a finished strip along one edge.
- **Caveat:** both passes are blind visual passes by AI raters of the same model family, not by people. The agreement measures consistency, not field truth, and is likely higher than two human raters would reach.
- **Final labels:** pass 1 (`labels/`). Pairs: `labels/agreement_pairs.csv`.
