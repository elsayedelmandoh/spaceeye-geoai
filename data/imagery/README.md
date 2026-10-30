# Inspector imagery: use and rebuild

The observed figures are ready locally. Git contains source selections, metadata, hashes, code and documentation, plus, by owner decision on 30 October 2026 (private repository, educational project, team presentation), the **95 single-capture Wayback figures** in [figures/](figures/index.csv) (mixed-date frames left out): the 74 of the first release plus 21 older 2016-2018 frames, and one comparison panel per compound in `figures/compare/`. They keep their printed attribution and the [third-party notice](THIRD_PARTY_IMAGERY.md); remove them before the repository is ever made public. The full imagery report ZIP and raw tile caches stay outside Git.

## View the existing report

Under the configured data root, open `app_data/imagery_comparison/index.html`. It works offline. The local controlled-copy report is `imagery_delivery/SpaceEye_R7_IMAGERY_REVIEW_2026-10-30_v2.zip` alongside `app_data`; its `.zip.sha256.txt` verifies the archive. Do not upload it to this repository or treat the imagery as MIT-licensed training data.

A teammate with an appropriately shared copy can extract it and open `imagery_comparison/index.html`, or install it into their configured data root:

```sh
uv sync --locked
uv run --locked python -m src.pipeline.imagery_delivery --package /path/to/SpaceEye_R7_IMAGERY_REVIEW_2026-10-30_v2.zip
```

Replace the example path with the received file. The matching checksum must be beside it. Installation validates every member and preflights collisions before writing; differing existing files are preserved. `SPACEEYE_DATA_ROOT` relocates the destination. There is no public image-download URL implied by this guide. The normal `setup_review` command installs numerical v6 data, without imagery.

## What is available

- **Inspector pair:** 24 rows, one before/after pair per coded R7 compound. Runtime files are `app_data/images/<code>_before.jpg`, `<code>_after.jpg`, and `images.csv`.
- **Wayback chronology:** 100 distinct capture-date states, 5–13 per compound. The latest accepted capture is **2025-07-23**; a 2026 release label does not make it a 2026 capture. Twenty-six frames contain mixed source dates.
- **Sentinel context:** 528 figures, one actual scene per compound-quarter across 44 quarters, 2016Q1–2026Q4. Q4 is partial through **2026-10-30**; its selected capture is **2026-10-29**. Native RGB resolution is 10 m; it cannot show facade finishing.

See the [comparison](../IMAGERY_COMPARISON.md), [coverage](../IMAGERY_COVERAGE.csv), [methods](../IMAGERY_METHODS.csv) and [validation](../IMAGERY_VALIDATION.json).

## Fixed selection and date contract

The numerical as-of remains `configs/data.yaml: asof` (currently 2026Q3). After is the latest capture whose release and capture are both available by that quarter-end. Before is the latest eligible capture at least **12 calendar months before that after capture**. Mixed-date frames use their latest capture date for conservative selection. A literal baseline measured only from the current as-of would choose the same July 2025 observation for both roles, so the distinct-year refinement prevents duplicate pairs. Missing baselines remain missing.

`images.csv` contains the pair only. Minimum fields are `code`, `role`, `capture_date`, `publication_date`, `source`, `resolution_m`, `attribution`; compatibility fields include `image_type`, `release_date` and APP-relative `path`. `capture_date` is intentionally empty for a mixed-date mosaic: read `capture_dates`, `capture_date_min`, `capture_date_max` and `mixed_capture_dates`. `capture_age_months_at_asof` uses completed calendar months since the latest capture; current after frames are **14 months old** at the 2026-09-30 as-of. Gallery/inspector captions show this age; historical tool requests recompute it for their requested quarter. Resolution lists retain the underlying providers' metadata; screen pixels do not increase native resolution. `sha256` identifies the actual local figure. `wayback_timeline.csv` retains all 100 observations; `stage_02` etc. are chronological positions, not construction-stage labels.

The image tool gates both release date and latest capture date when given a historical quarter. It cannot infer historical availability from capture alone. The current pair may be unavailable at an earlier cutoff; the full chronology remains a separate review artifact. Image bytes are embedded only when rendering local HTML, never inserted into the model's factual context.

Sentinel scenes are selected closest to quarter-end minus 15 days, or closest to the observation end for the partial quarter, with up to five local-quality checks. Per-compound bad-class fraction must be at most 10%, valid coverage at least 95%. This is a quality screen, not a guarantee of cloud-free pixels. Final display uses original RGB scale/offset, reflectance **0–0.6**, gamma **1.0**, identically across dates. There is no per-image auto-stretch, generative enhancement or measured progress percentage. Four real 2016 captures were reprocessed in 2023; capture is not historical processing availability.

## Rebuild figures from the recorded sources

Start on a feature branch with an isolated data root. Follow [device setup](../../docs/REVIEW_SETUP.md) for `SPACEEYE_DATA_ROOT` and prepared coded boundaries. Then:

```sh
uv sync --locked --extra imagery --extra pulls
uv run --locked --extra imagery --extra pulls python -m src.pipeline.setup_review
uv run --locked --extra imagery --extra pulls python -m src.pipeline.imagery_compare --phase prepare
uv run --locked --extra imagery --extra pulls python -m src.pipeline.imagery_compare --phase render
uv run --locked --extra imagery --extra pulls python -m src.pipeline.imagery_compare --phase sentinel --through 2026-10-30
uv run --locked --extra imagery --extra pulls python -m src.pipeline.imagery_compare --phase report
```

`prepare` installs recorded source selections, without pixels. `render` requests attributed static maps through Esri's official Print service; it does not collect a WMTS tile archive. Public Earth Search RGB COGs cover 40 quarters without an AWS account. Rebuilding the four early 2016 periods requires an existing authenticated Earth Engine account/project, with `SPACEEYE_EE_PROJECT` set locally; credentials/project identifiers are never supplied or created by this workflow. Without that existing access, those periods are honestly reported unavailable; the other quarters continue. A controlled report copy avoids requiring this access just to review existing figures.

The recorded product IDs preserve source selection. External rendering/source services can change or become unavailable; a fresh render is not promised to match the saved JPEG byte hash. No fabricated replacement is used when a recorded product fails. `--phase discover` explicitly discovers a fresh Wayback selection; it is not the frozen-selection replay above. Without `--through`, the observation end comes from the configured as-of quarter-end. An explicit later date extends visual context only, never the numerical model window.

`python -m src.pipeline.imagery_delivery --build` validates local figures, writes a new local report archive, and refreshes the metadata/report files. It refuses to overwrite an existing dated archive. Review the metadata diff and privacy checks before committing. The imagery extra is needed for source acquisition/rendering, not to read metadata or install a received archive.

## Presentation figures

`python -m src.pipeline.imagery_figures --phase discover|render|audit|compare` builds the presentation set without touching the frozen `wayback_selected.json`. `discover` probes older Wayback releases (tile zooms 15-18) and keeps a capture only when the zoom-17 metadata shows one date over the whole compound and zoom 18 has no partial footprint; the result is recorded in `wayback_extra.json`. `render` uses the same official Print path as `imagery_compare` and deletes frames whose pixels equal an earlier frame (the metadata can date a footprint later while the tiles are unchanged). `audit` writes `figures/figures_audit.csv`; `compare` writes `figures/compare/C??_compare.jpg` and the `in_presentation` and `note` columns of `figures/index.csv`. Checked locally: 2016-06-01 appears in no probed release for any R7 footprint (the earliest usable captures are 2016-11-08 and 2016-12-17).

## Rights and limits

Keep the [third-party notice](THIRD_PARTY_IMAGERY.md), source-item links, Esri/provider credits and Copernicus notices with the figures. Esri static-map educational/non-commercial use is subject to the applicable service/provider terms; it is not a blanket image redistribution or model-training licence. This delivery keeps Esri pixels outside Git. Sentinel figures contain modified Copernicus Sentinel data and are not represented as CC0.

Inspection HTML that embeds Esri pixels as base64 follows the same rule as the JPEGs: keep it local for attributed educational review; never commit or redistribute it. T-EL-06 report generation does not remove the underlying image rights. Only metadata/source-code files belong in Git.

These are inspector context only, outside model X and KPI computation. Current reviewed boundaries are used consistently; they do not establish historical allocation or cadastral accuracy. Images do not establish finishing, legal handover, floor count, height, construction percentage, or paved-road timing. Earlier finishing and road-timing experiments remain rejected. Review acceptance for T-AH-15 is still pending.
