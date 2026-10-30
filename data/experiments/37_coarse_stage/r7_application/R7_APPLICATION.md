# Coarse stage layer applied to R7 (arm H, refit on all 841 labelled rows; settings frozen)

**Method:**
- 500 m cells that overlap each compound, weighted by overlap area.
- One date per year (1 July, window ±6 months). 2026 is truncated at the data available on 2026-10-30.
- Heights: OBT for 2016-2023; OBT 2023 is carried forward for 2024-2026, with `height_age_years` 1, 2 and 3.
- No feature was missing in any year.
- Script: `r7_apply.py` and `r7_ee.py`. Table: `r7_stage_share.csv`. Chart: `r7_stage_share.png`.

**Result (majority stage):**
- Every compound is S0 (land) through 2019.
- Each switches to S1 (under construction) in 2020-2022:
  - 2020: C12, C18 and C21;
  - 2022: C19;
  - 2021: all the others.
- Each stays S1 through 2026. **No compound reaches S2 (complete and operating) in any year.** The S2 share stays at or below 0.09.

**Sanity check against the published delivery status (n = 12, descriptive only): it does not agree for completion.**
- C12 is "delivered_complete" (handover 2024), yet its S2 share in 2025 is only 0.06.
- Compounds with phase 1 delivered (C04, C10) also read S1.

**Reading:**
1. The **start of construction** (S0 → S1, 2020-2022) is plausible against the pipeline's activity-based start quarters, which are also 2019-2021.
2. The **completion** class does not transfer to R7. In training, S2 means "finished, with landscaping and signs of use". Newly delivered R7 compounds look like dense mid-rise blocks on bare ground and score S1. This matches the review's warnings: S1 recall in the 2024-2026 regime, the unit change from block to compound polygon, and the spatial transfer.
3. **Use:** for R7 the layer can show "construction started (year)". It must not be read as "complete / not complete". Completion for R7 has to come from ACUD handover records or from human imagery review (T-AH-15 pairs, the T-AH-17 labels).

Caveats from the independent review apply in full (`../RESULTS.md`). 2016-2018 are outside the trained years. 2024-2026 S1 recall is weak. 2026 is untested.

**Correction (same day, after the team lead checked the images):**
- Sub-metre Wayback imagery shows landscaped gardens, pools and paved paths inside R7 compounds. For example, C12 on 2025-07-23 has a central garden.
- The 10 m measurements inside the polygons miss them: the share of pixels with NDVI > 0.25 is ≤ 0.05 and the Dynamic World green share is 0 in every year (`r7_green_inside.csv`).
- So the statement "no R7 compound shows greenery" was wrong. The right reading is that free 10 m data cannot see R7 completion, and completion must be judged on sub-metre imagery.
