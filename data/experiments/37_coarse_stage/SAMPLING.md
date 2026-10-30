# Step 1a: sampling and image preparation (37 coarse stage)

Run 2026-10-30, following `PROTOCOL.md` (Step 1, sample / dates). No label, no feature other than the declared stratum value, no model. Scripts: `scripts/s1a_blocks.py`, `scripts/s1a_captures.py`, `scripts/s1a_mosaics.py`. Codes only; no compound or developer names in any file. Esri imagery (`cache/crops`, `cache/tiles`, `label_mosaics*`) stays local and is not committed.

## 1. Block grid and exclusions
- **Grid:** UTM 36N (EPSG:32636), 500 m cells aligned to multiples of 500 m; `block_id` = lower-left corner `x_y` (same format and alignment as the v8/v9 grid, e.g. `372500_3323000`). Study box lon 31.60-31.95, lat 29.90-30.10 (`29_height_final` v8 `config.py`). A block is kept if all four corners lie inside the box: **2,892 blocks**.
- **R7 exclusion:** the 12 R7 polygons (`Project/app_data/raw/boundaries.geojson`, codes C01..) buffered by 500 m; any block touching the buffer is removed: **54 blocks**. (`spaceeye-v6-fixes/app_data/real/compound_boundaries.geojson` does not exist; the `Project/app_data` file is the 12-polygon set named in `INVENTORY.md`.)
- **Urban-plan exclusion (proxy, no plan layer exists):** the project has no urban-plan layer. Proxy used = the OSM landuse polygons of the study box already cached in `05_geo_satellite/raw/osm_polygons_all_bbox.geojson` (244 polygons: landuse residential / construction / place; "plots"). A block with **less than 20 % of its area inside the union of these polygons** (i.e. more than 80 % outside) is excluded: **2,147 blocks** (not already removed by R7).
- **Why not the Dynamic World proxy suggested in the request:** built + bare + grass + trees sums to about 1 almost everywhere (desert is Dynamic World `bare`), so it cannot separate desert from plots; the OSM plot layer can. This also kept the Step 1a rule "compute only the grass+trees share". Limit: OSM plot coverage is community-mapped and incomplete, so some real urban land may be excluded.
- **Eligible blocks: 691** (list with plan share: `eligible_blocks.csv`).

## 2. Stratum and draw
- **Only feature computed:** Dynamic World V1 2025 (2025-01-01 to 2026-01-01) mean of grass + trees probability per block. Same method as `19_observed_stage/scripts/dw_classes_ee.py`: DW scenes whose Sentinel-2 L1C scene has cloud < 20 %, mean over 69 images, mean reducer at 10 m (Earth Engine project already used in the repo).
- **Tertiles** over the 691 eligible blocks (rank-based): T1 0.0435-0.0489 (230 blocks), T2 0.0489-0.0561 (230), T3 0.0561-0.2410 (231) (`tertile_cuts.csv`).
- **Draw:** seed 2036, `numpy.random.default_rng`, simple random within tertile. 220 is not divisible by 3, so **73 / 73 / 74** (the extra block in T3, the tertile that holds most of the S2 candidates). Result `blocks.csv` (220 rows: `block_id`, `lat`, `lon` of the centroid, `tertile`, and the stratum value `gt_share`; the rater never sees them).

## 3. Wayback captures (`captures.csv`)
- Targets: 30 June of 2019, 2021, 2023, 2025; a capture is kept only if within 9 calendar months of the target (window 2018-09-30..2020-03-30, 2020-09-30..2022-03-30, 2022-09-30..2024-03-30, 2024-09-30..2026-03-30).
- **Capture date = metadata `SRC_DATE2`**, not the release date. For each of the 112 Wayback releases from 2018-10-17 to 2026-09-24 the capture polygons of the whole box (layers 4, 5, 6 of the release metadata service) were downloaded once (geometry generalised to 0.0001 deg, about 10 m, to keep the download small) and tested at the block centroid. Per release and point the first layer with a hit is used in the order 5, 4, 6 (layer 5, 60 cm, map scale 1:1700-1:3400, is the layer of zoom 18); several polygons in a layer: latest date. A first attempt with order 4, 5, 6 hid all 2019-2022 captures behind layer-4 hits and was discarded before any crop was downloaded.
- Per block 7-9 distinct captures were found. The nearest capture to each target is chosen; `release_id` = earliest release that publishes that capture at the centroid. Resolution of the chosen captures (m): 2019 0.50 (206) / 0.31 (5); 2021 0.50 (111) / 0.31 (107); 2023 0.31 (156) / 0.46 (64); 2025 0.34 (192) / 0.31 (25) / 0.50 (2). (Counts over usable rows.)
- **Usable flag:** nearest capture within 9 months of the target AND every zoom-18 tile of the block exists in the release (blank share of the crop at most 1 %). Of the 880 block-date rows, 4 had no capture inside the window (one in 2021, three in 2025: `usable=False` with an empty `note` in `captures.csv`) and 10 had missing tiles (6 fully blank, 4 partly blank at 2-11 %; nine in 2019, one in 2021; `note=missing_tile(...)`). Cloud is not assessed here (the rater marks it).
- Note: one capture covers a whole block only at its centroid; blocks on a capture edge can mix two captures inside the crop.

## 4. Crops and label mosaics
- Zoom-18 tiles (about 0.5 m/px at this latitude), crop = bounding box of the full 500 m block (about 960 x 960 px), thin yellow outline of the block square. Local cache `cache/crops` (866 files, 1.3 GB), `cache/tiles`.
- **Pass 1:** the 866 usable rows are shuffled (seed 2039) and cut into mosaics of 6 crops (2 rows x 3 columns, 640 px per crop, about 1928 x 1284 px). Caption = random row id `r0001`..`r0866` only (ids drawn by a separate permutation, so id order does not follow mosaic order). No block id, tertile or Dynamic World value appears. Files `label_mosaics/mosaic_001.png`..`mosaic_145.png` (144 with 6 crops, the last with 2). Private key `private_key/rows.csv` (row_id, block_id, target_year, capture_date, mosaic file, position).
- **Capture date for the rater:** the protocol says the rater sees the capture date, but the request asked for captions with the row id only, so the date is given in a separate table `label_mosaics/row_dates.csv` (row_id, capture_date; no block id).
- **Pass 2 (agreement check):** 25 % of the pass-1 rows (216 of 866, seed 2037, simple random) re-shuffled (seed 2037) into new mosaics with **new random row ids**: `label_mosaics_pass2/mosaic_001.png`..`mosaic_036.png` (6 crops each), `label_mosaics_pass2/row_dates.csv`, key `private_key/rows_pass2.csv` (adds `row_id_pass1`). No pass-2 row keeps its pass-1 id; each pass-2 mosaic mixes crops from about 6 different pass-1 mosaics. The pass-2 set is drawn from all usable rows, before the rater marks any as unusable or mixed; the kappa set will be the pass-2 rows that pass 1 labelled S0/S1/S2.

## 5. Counts
| item | count |
| --- | --- |
| grid blocks in box | 2,892 |
| removed: R7 + 500 m | 54 |
| removed: > 80 % outside plot proxy | 2,147 |
| eligible | 691 |
| sampled blocks | 220 (T1 73, T2 73, T3 74) |
| block-date rows (220 x 4) | 880 |
| usable rows | 866 (2019: 211, 2021: 218, 2023: 220, 2025: 217) |
| unusable | 14 (4 capture outside 9 months, 10 missing tiles) |
| pass-1 mosaics | 145 |
| pass-2 rows / mosaics | 216 / 36 |

Not done in this step: any labelling, any other feature, any fitting.
