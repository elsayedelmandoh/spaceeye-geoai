# R7 observed imagery comparison

Snapshot date: 2026-10-30. The complete offline gallery stays under the configured local app_data/imagery_comparison directory. Git contains metadata and code only; no Esri images or imagery ZIP.

## Results

- 100 accepted dated Wayback static figures, 5-13 per compound; 26 have mixed capture dates.
- 528 Sentinel figures: 12 compounds across 44 quarters, 2016Q1 through partial 2026Q4; latest actual capture 2026-10-29.
- Wayback's latest accepted capture is 2025-07-23, even when its release was published in 2026. A publication-only refresh/provider rename is not another observation; five such same-date duplicates were removed during validation.
- Wayback source resolution metadata ranges 0.31-0.5 m. Sentinel RGB is 10 m. Rendering to a larger screen does not increase native resolution.

Wayback is the useful detailed visual context for roofs, road patterns and building footprints. Sentinel provides the continuous quarterly overview and the more recent 2026 context, with coarser detail. Neither source establishes finishing, legal handover, floor count or a completion percentage. Colour differences may reflect season, processing and illumination.

## Selection and accuracy limits

Wayback discovery checks metadata tile locations at a representative point and up to four other interior points, then queries intersecting metadata footprints for each candidate at the render scale. Visible sources are resolved in draw order. It is not an exhaustive per-pixel audit of the archive. Capture date sets are deduplicated, retaining the earliest encountered publication of a capture state; mixed source dates are shown as ranges and are not converted into a fabricated single date. Border-context credits are checked and supplemented with the source item's service attribution.

Sentinel uses one actual scene per quarter: public COG candidates closest to quarter-end minus 15 days, and closest to the observation end for the current partial quarter; up to five candidates are locally screened. Existing-account Earth Engine provides four early gap periods. Quality checks allow at most 10% classified cloud/shadow/no-data per compound, with at least 95% valid coverage; the observed maximum is 0.0642. COG quality uses SCL at 20 m; early Earth Engine checks sample SCL at 60 m. These are quality screens, not a guarantee of completely cloud-free pixels. Display frames retain actual capture dates and source IDs. Current selected products are L2A surface reflectance. Standard 8-bit preview TCI images were visibly saturated over this bright desert site. Final figures instead apply each original RGB band's declared scale/offset, then one fixed reflectance display range 0-0.6 with gamma 1.0 across every period. This is a display policy, not per-scene histogram fitting, sharpening or a model. The four 2016 acquisitions were reprocessed in 2023, as shown by their product IDs; they are real 2016 captures but not evidence that this processed product was available in 2016. Pixel colour change is not quantified as construction progress.

Sequence names such as `stage_02` mean chronological observation positions, not independently labelled construction stages. All sources use the same per-compound EPSG:3857 view extent and coded boundary. Sentinel display maps are 640 pixels wide to keep delivery size reasonable; the underlying observed resolution remains 10 m. Product processing/availability may postdate capture. The quarterly images are retrospective context, not additional historical model X or new physical measurements. The partial 2026Q4 frames extend beyond the frozen numerical dataset's 2026Q3 cutoff and are explicitly labelled. The operational image tool filters Wayback release/capture dates for requested historical quarters.

The inspector pair is a separate 24-row images.csv: after is the latest capture published by the numerical as-of; before is the latest available capture at least 12 months before after. Mixed dates use their maximum. A literal baseline measured only from the 2026Q3 as-of would select the same July 2025 capture for both roles, so the distinct-pair refinement prevents that misleading duplication. Both source releases must be available by as-of; missing baselines remain missing. All 100 states remain in wayback_timeline.csv. The 10 m Sentinel timeline cannot show facade finishing. Finishing detection and road-paving timing were rejected by the earlier experiments; this report does not reinstate those products.

## Method comparison

| Method | Execution | Result |
| --- | --- | --- |
| Wayback official static Print service | executed | 100 attributed static figures; 5-13 accepted capture states per compound |
| Public Earth Search Sentinel COGs | executed | 40 quarters; all 12 coded boundaries |
| Earth Engine existing-account thumbnails | executed | 4 early gap quarters; no new account/project; no credentials packaged |
| GIS rendering via Rasterio/GDAL | executed | Reprojected Sentinel windows to the same per-compound EPSG:3857 extent; current QGIS/ArcGIS applications were not installed |
| Default Sentinel TCI preview display | tested; replaced for final figures | Bright-desert previews were saturated; original calibrated RGB bands and one fixed reflectance range 0-0.6 were adopted |
| Manual Wayback browser workflow | unavailable in execution environment | Browser inventory returned no available browsers; used the supported Esri static rendering service |
| Google Earth manual export | unavailable in execution environment | No installed Earth application or controllable browser; no Google tile extraction or invented comparison |
| Separate licensed commercial/project imagery | not acquired | No applicable licensed R7 source collection found; no paid purchase or account creation performed |

## Per-compound coverage

| Code | Wayback frames | First accepted capture | Last accepted capture | Sentinel quarters |
| --- | ---: | --- | --- | ---: |
| C01 | 8 | 2019-10-06 | 2025-07-23 | 44 |
| C02 | 8 | 2018-08-18 | 2025-07-23 | 44 |
| C03 | 9 | 2022-06-13 | 2025-07-23 | 44 |
| C04 | 6 | 2021-04-09 | 2025-07-23 | 44 |
| C07 | 5 | 2022-06-13 | 2025-07-23 | 44 |
| C10 | 8 | 2019-10-06 | 2025-07-23 | 44 |
| C12 | 8 | 2019-10-06 | 2025-07-23 | 44 |
| C14 | 13 | 2018-08-18 | 2025-07-23 | 44 |
| C17 | 5 | 2022-06-13 | 2025-07-23 | 44 |
| C18 | 8 | 2019-10-06 | 2025-07-23 | 44 |
| C19 | 9 | 2022-06-13 | 2025-07-23 | 44 |
| C21 | 13 | 2018-08-18 | 2025-07-23 | 44 |

Per-compound counts and date spans: `comparison.csv`. Full frame metadata: `wayback_timeline.csv`, `sentinel_quarterly.csv`; source/legal notice: `THIRD_PARTY_IMAGERY.md`; validation: `validation.json`. No unavailable method is assigned a fabricated result.
