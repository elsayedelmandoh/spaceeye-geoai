# Annual vegetation and height handoff

Task T-AH-16 implementation complete under the team lead's revised acceptance on 28 October 2026. Ready per compound/year in `sat_yearly`; the same coded table is exported as `partial_task_exports/annual_context.csv`. [Coverage by year](../../data/ANNUAL_CONTEXT_COVERAGE.csv) records non-null values explicitly.

Vegetation is available for all 12 compounds for 2019–2026, with source/derived origin. Earlier missing years remain null. Approved heights are OBT where available (none for 2016-2019; 5-11 of 12 compounds per year for 2020-2023) and the v4 estimate for 2024 (10 of 12); see data/ANNUAL_CONTEXT_COVERAGE.csv. Later height rows stay null. A feature carrying the last known older height into a later quarter is not a new height measurement.

Source evidence: external `real_data/27_height_embedding/v4_builtmask/results.md`. The accepted product aggregates built cells and is contextual compound-level evidence. Its historical 210-unit-year consistency check reported MAE 1.765m, but the test had already been seen and is not an independent 2024 survey validation. The fixed +/-2m guarantee has been removed from task acceptance; no further height training is required to close this task.

Vegetation/height are ready for the compound screen; the screen itself remains NA-03. Height does not set the priority level. Preserve year, missingness, height_origin and veg_origin when joining or charting.
