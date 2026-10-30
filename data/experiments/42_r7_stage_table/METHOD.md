# R7 construction-stage table: how it was made (30 October 2026)

**Output:**
- `r7_stage_table.csv`: one row per compound and year, 2016-2026, for C01-C21 (12 compounds) plus reference C25. Each row has a stage and its source.
- `r7_stage_summary.csv`: construction start year and complete year per compound.
- Script: `build_table.py`.

## Sources, in priority order
1. **Sub-metre Wayback figures (about 30 cm), official renderer only:** 95 single-capture figures for the 12 compounds (2016-11 to 2025-07) and 3 for C25.
   - **Labels:** a blind visual pass by the assistant (Sonnet), in `37_coarse_stage/r7_vhr/r7_stage_codex_frames.csv`.
   - **Second look on 20 rows:** 19 of 20 agree; the one disagreement is C04 2025-07, borderline S0/S1.
   - A raw tile-mosaic series was rejected: it mixed wrong-date tiles and showed desert where Google heights show 25 m towers.
2. **Satellite and radar layer (10 m):** used only in years without a figure, and only for land or under construction.
   - The layer is pre-registered: Dynamic World, Sentinel-2, Sentinel-1 radar, night lights and Google heights.
   - Test macro recall 0.82; independent review "sound with caveats".
   - It cannot see the greenery that defines "complete", so it never sets S2.
3. **Context columns:** Google Open Buildings heights (2016-2023) and the activity model's share of active quarters.

## Stage definitions (team lead)
- **S0:** land or ground works.
- **S1:** under construction; finishing counts here.
- **S2:** complete, meaning finished buildings, visible greenery and paved internal roads.
- **mixed** is counted as S1.

## Rules
- The stage of a year is the latest figure in that year. Without a figure, the satellite layer is used, with S2 capped to S1.
- A construction start found only by the satellite layer is not accepted if a later figure still shows land.

## Result
- **Construction start:**
  - 2020: C12, C18, C21;
  - 2021: C01, C02, C03, C10, C17;
  - 2022: C14, C19;
  - 2024: C04, C07.
- **Complete by 2025-07-23 (latest available figure):** none of the 12. The reference compound C25 is complete in 2025.

## Caveats
- The labels come from an AI rater, not a site visit.
- Figures are irregular: none between 2019 and 2023 for some compounds, and none after 2025-07-23.
- 116 of the 220 blocks that trained the satellite layer lie west of the capital (New Cairo side), outside the New Administrative Capital.
- Adding a new R7 compound: render its official figures (`41_completed_reference/scripts/render_reference_any.py`), label them the same way, and rerun `build_table.py`.

## Radar and other satellite context (added the same day)
`r7_sat_radar_series.csv` (script `sat_radar_series.py`) gives yearly means inside each polygon:
- **ALOS PALSAR-2 L-band** HH/HV, yearly mosaic, 2016-2024. The building double-bounce raises HH from about -21 dB to -10 dB as structures rise; the median across compounds jumps in 2020-2021.
- **Sentinel-1 C-band** VV/VH.
- **Dynamic World** built / bare / green.
- **Sentinel-2** NDVI / NDBI.
- **VIIRS night lights.**

These are context columns in `r7_stage_table.csv`; they do not set the stage. None of these sensors sees the small gardens that define "complete": green and NDVI stay flat.

## Construction timeline (buildings, pauses, structure, finishing)
- **Labels:** `r7_components.csv` gives per figure the block counts (total, frames, finished facades, new since the previous figure), cranes, ground, greenery, roads, pools, cars and the change since the previous figure. It is a blind visual pass. C01, C02, C03, C04 and C07 were redone because the first pass could not display some images.
- **Timeline:** `timeline.py` writes `r7_timeline.csv` with these fields:
  - first building seen;
  - building counts over time;
  - last structural change (new blocks, vertical growth or cranes);
  - finishing first seen (finished facades, paved or partial roads, greenery or pools);
  - complete, meaning much greenery, paved roads and at least half the facades finished;
  - "no change" intervals between consecutive figures before completion. These are pauses only in the sense that nothing changed between two dates; figures are irregular.
- **Caveat:** counts are approximate for large compounds. Sheds and foundations count as 0 blocks.

## Compound profile (`profile.py` → `r7_profile.csv`)
One row per compound, combining:
- build pace (blocks per year between the first and the latest figure);
- the activity model per quarter (share of active quarters, longest inactive run, inactive quarters since 2023);
- Google heights in 2023;
- the radar jump (ALOS PALSAR HH 2024 minus 2018);
- night-light change (2025 minus 2019);
- the published plan from the statements table (first promise, number of postponements, first published handover);
- the state seen in the latest figure.

**Main contrast:** published handovers versus what the figures show. Every compound with a published delivery start or completion (C02, C03, C04, C10, C12, C19) is not complete by the owner's definition in the 2025-07-23 figure. This is not proof of a false claim; partial handovers happen before landscaping. It is a concrete question for an inspection visit.
