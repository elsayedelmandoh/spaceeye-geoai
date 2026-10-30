# T-AH-17: human check of the finishing vision model. Pre-registered 2026-10-30, before any image or label exists.

## Why
The board requires the finishing vision model (Qwen3-VL-32B on Wayback) to be checked against blind labels by a person on the team (salma, T-SA-12). The earlier score (0.559) used labels from one AI rater, so it measured agreement between two models, not with a person. The model's saved test predictions (`29_height_final/finishing/vlm/vlm_test_predictions.csv`) are compared as they are. The model is not run again.

## Units and images
- **Blocks:** 25 of the 60 test blocks in `src_server/test_blocks.csv`, drawn at random with seed 2040.
- **Intervals:** each block gives 2 intervals (panel 1 → 2 and panel 2 → 3), so there are 50 decisions.
- **Images:** the same Wayback releases the model saw (2022-11-02, 2024-08-15, 2026-09-24), at zoom 19 (about 0.3 m/px). They are delivered at full resolution, one image per date, plus a side-by-side overview. The model saw the panels downscaled to 800 px; the person gets the full detail, as the team lead asked ("closer, high quality").
- **Blinding:**
  - Blocks are renamed S01 to S25 in a shuffled order (seed 2041).
  - The person never sees the model's verdicts, the earlier AI labels, block ids or coordinates.
  - The key is kept in `private_key/`.

## Labels (per interval)
- **A: new structure or vertical progress.** New building frames, new floors, new footprints.
- **B: finishing only.** Existing structures get facades, paint, windows, landscaping, paving or pools, with no new structure.
- **C: no visible change.**
- **U: cannot judge.** Cloud, missing image, or too unclear.
- Each label also gets a confidence (high or low) and an optional short note.

## Measure and gate (T-AH-17)
- **Primary:** agreement on finishing vs not (B vs A or C) between the model and the person, over the intervals that both labelled (not U).
- **Pass:** agreement ≥ 75 %.
- Also reported:
  - three-class agreement, Cohen's kappa (B vs not-B);
  - finishing recall, against the person's B;
  - a 90 % bootstrap interval by block;
  - the counts.
- If fewer than 40 intervals remain after removing U, the result is reported as "underpowered", with its numbers.

## Decision
- **Pass:** finishing from the vision model becomes a flag in the inspection file only, as the board says. It does not enter the warning level.
- **Fail:** T-AH-17 is closed as a failed experiment, recorded on the board and in `team_ideas.md`.
- No change to the blocks, classes or gate after any label is seen.

## Rights
Esri Wayback imagery is for this internal labelling only. It is not committed to Git and not redistributed.

## Amendment 1 (2026-10-30, before any label is returned and before any new model output): a better image set
The team lead looked at the kit and found the problem: the model's original test images (2022-11, 2024-08, 2026-09) start after 2022, and most blocks are already complete. Most intervals would therefore be "no change", and the test would say little about finishing. The kit was not sent, and no label exists.

- **New units:** 25 blocks from `37_coarse_stage`, all outside R7, chosen so that change is likely.
  - Each block has usable Wayback captures for the 2021, 2023 and 2025 target dates in `37_coarse_stage/captures.csv`; the actual capture dates and their release ids are used.
  - Intervals are 2021 → 2023 and 2023 → 2025, so there are 50 decisions.
  - The draw is stratified by the pass-1 stage labels of `37_coarse_stage`, an independent AI rater, used only to enrich the sample. Seed 2042:
    - 9 blocks with an S1 → S2 step in either interval (finishing likely);
    - 8 with S0 → S1 (new structure likely);
    - 4 with S1 → S1 (either);
    - 4 with S2 → S2 (no change likely).
  - If a stratum is short, the gap is filled from S1 → S1. The strata are never shown to the labeller.
- **Images:** the full-resolution mosaic at zoom 19 where the release has it, else zoom 18. The zoom used is recorded.
- **Model:**
  - The saved predictions no longer match these images, so the same model (Qwen3-VL-32B-Instruct, prompt v3 unchanged, vLLM) is run once on exactly the same three images per block, with the same 800 px side-by-side composite it was built for.
  - Only one A40 is now visible on the server. If the bf16 weights do not fit, the official FP8 weights of the same model are used, and this is recorded as a deviation.
  - Model outputs are saved and hashed before the person's labels are read.
- **Unchanged:** blinding, labels, measure, gate and decision. The old 25-block kit is kept only as a record.

## Amendment 2 (2026-10-30, before any label and before any new model output): dates from 2016
The team lead asked for dates starting in 2016, so that early construction is included. Amendment 1 is replaced as follows; everything not mentioned stays as in Amendment 1.

- **Dates:** four per block. Each is the Wayback capture (capture date, not release date) nearest to mid-2016, mid-2019, mid-2022 and mid-2025.
  - A date is used only if it is within 12 months of its target.
  - Capture polygons for releases from 2016 on are fetched with the same method as `37_coarse_stage/scripts/s1a_captures.py`.
- **Units:** 17 blocks, each with 3 intervals (2016 → 2019, 2019 → 2022, 2022 → 2025), giving 51 decisions.
  - The blocks come from `37_coarse_stage` and are outside R7, with all four dates usable.
  - Strata use the pass-1 labels of 2019, 2021, 2023 and 2025:
    - F, an S1 → S2 step anywhere: 6 blocks;
    - N, S0 → S1 anywhere and not F: 5;
    - E, S1 in at least two years and not F or N: 3;
    - C, S2 in all four years: 3.
  - Shortfalls are filled from E. Seed 2044 for the draw, 2045 for the S01..S17 order.
- **Labels:** per interval (1→2, 2→3, 3→4), with the same A/B/C/U definitions. The kit shows four images per block plus an overview.
- **Model:** the same model and prompt, run on each interval as its own three-panel composite in the original format, with panels (t, t+1, t+1) so that the model's panel 1 → 2 decision is the interval. This is the closest match to the prompt it was built for.
  - Only the model's 1 → 2 verdict of each composite is used.
  - This adaptation is recorded as a deviation.
- **Gate:** unchanged (≥ 75 % B vs not-B agreement). "Underpowered" means fewer than 40 intervals left after removing U.

## Owner note (2026-10-30)
The gate is read on the point estimate (≥ 75 %), and the 90 % interval is reported but not gated, as in the main text. This was confirmed by the team lead before any label exists.

## Amendment 3 (2026-10-30, before any label and before any model output): every half-year from 2016 to 2026
The team lead asked for a half-yearly series from 2016 to 2026 and accepted the larger number of decisions. The 17 blocks and their order (Amendment 2) stay the same; only the dates change.

- **Dates:** for each block and each half-year from 2016H1 to 2026H2, the sub-metre Wayback capture (layers 4 and 5) whose capture date falls in that half-year, the one nearest its middle. A half-year with no such capture is skipped.
  - Coverage is uneven. For example, there is no capture in 2024H2 or in 2026 for most blocks.
  - The dates used are recorded in `private_key/`.
- **Intervals:** each pair of consecutive available dates of a block is one decision. The total is reported. The ≥ 40 "underpowered" floor is unchanged.
- **Kit:** one full-resolution image per date, plus overviews in strips of 4 consecutive dates, so that the sheets stay readable. The sheet has one row per interval.
- **Model:** the same as Amendment 2, one (t, t+1, t+1) composite per interval.
- **Measure and gate:** unchanged (B vs not-B agreement ≥ 75 %, point estimate). Also reported per interval length (≤ 12 months or longer).

## Amendment 4 (2026-10-30, before any label and before any model output): rater
At the team lead's request, the labels are made by a blind AI visual rater (a fresh agent that sees only the kit) instead of salma.
- **Consequence:** the result measures agreement between two AI systems, not with a person. It does not meet the board's wording "labelled blind by salma", and it is reported that way.
- If salma labels the same kit later, her labels are the primary result.

## Amendment 5 (2026-10-30, before any human label exists): the assistant is the vision model
The team lead decided that the vision model under test is the assistant itself, not a model on the server or the laptop. The server run of Qwen3-VL was stopped before it produced any output.
- **Model predictions:** the blind AI visual labels already frozen on kit v3 (`labels_ai_rater.csv`, sha256 9a8c477f…, made before any reference existed) are the model's outputs (A/B/C/U per interval).
- **Reference:** a person's blind labels on the same kit v3 (salma, or another team member who has not seen the model outputs), returned as `labels_salma.csv`.
- **Gate:** unchanged (B vs not-B agreement ≥ 75 %, point estimate; "underpowered" below 40 judgeable intervals).
- **No human labels:** without them T-AH-17 is recorded as "model outputs frozen; validation pending a human reference". Agreement of the model with another AI pass is never reported as accuracy.

## Closure (2026-10-30, owner decision)
- **Decision:** with no human reference available, the team lead accepts the assistant as the finishing vision model on trust.
- **Model outputs:** `labels_ai_rater.csv` (frozen, sha256 9a8c477f…): 114 intervals, A 73, B 22, C 19, U 0.
- **Accuracy:** not measured. No gate was evaluated. Any later human labels on kit v3 can still be scored under this protocol.
- **Qwen3-VL file:** an earlier queued server launch of Qwen3-VL wrote `spaceeye_vlm/pred/t17_v3.csv` before it was stopped. It is not used and was not read, as the owner decided.
- **Use:** finishing appears as a flag in the inspection file only. It never enters the warning level.
