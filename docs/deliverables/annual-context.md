# Annual vegetation and height handoff

Task AH-16. Ready per compound/year in `sat_yearly`; the same coded table is exported as `partial_task_exports/annual_context.csv`. [Coverage by year](../data/ANNUAL_CONTEXT_COVERAGE.csv) records non-null values explicitly.

Vegetation is available for all 12 compounds for 2019–2026, with source/derived origin. Earlier missing years remain null. Approved heights are Google Open Buildings Temporal 2016–2023 and the v4 estimate for 2024. Later height rows stay null. A feature carrying the last known older height into a later quarter is not a new height measurement.

Source evidence: external `real_data/27_height_embedding/v4_builtmask/results.md`. The accepted product aggregates built cells and is contextual compound-level evidence. The task board's +/-2m wording is not a verified per-building or per-compound error guarantee and must not be shown as one. This is an explicit specification qualification, not a passed new height experiment.

Vegetation/height are ready for the compound screen; the screen itself remains NA-03. Height does not set the priority level. Preserve year, missingness, height_origin and veg_origin when joining or charting.
