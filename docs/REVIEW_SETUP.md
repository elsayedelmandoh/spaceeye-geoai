# Set up SpaceEye on another device

This is the starting point for reviewers. Use Python 3.12+ and uv. The checkout works on Windows, Linux, macOS and WSL; it does not require an F: drive. Use a feature branch for edits.

## 1. Get the code and prepared review data

```sh
git clone https://github.com/elsayedelmandoh/spaceeye-geoai.git
cd spaceeye-geoai
uv sync --locked
uv run --locked python -m src.pipeline.setup_review
uv run --locked python -m src.pipeline.rerun_backtest
```

The checked-in v6 ZIP is already downloaded by `git clone`; do not download another version. Setup verifies its SHA-256, all 292 manifest entries, and the seven [saved review artifacts](../releases/ready-data/review/README.md). It unpacks the complete release and installs the prepared tables/training inputs used by the current evaluation code. Repeating setup keeps identical files; a collision with different existing data stops before overwriting any file.

Default data locations, relative to the **repository root** (not the terminal working directory):

```text
<checkout-parent>/Project/
  ready-data/             complete unpacked v6 delivery
  app_data/              prepared tables, saved review logs and generated outputs
  private/               prepared training export; locally generated truth stays here
  real_data/             original source caches, only after source installation
```

For a separate data location, set one variable **before starting a command**. All three runtime paths move together:

PowerShell:

```powershell
$env:SPACEEYE_DATA_ROOT = "./.spaceeye"
uv run --locked python -m src.pipeline.setup_review
```

Linux, macOS or WSL:

```sh
export SPACEEYE_DATA_ROOT=./.spaceeye
uv run --locked python -m src.pipeline.setup_review
```

Relative environment paths are also anchored to the checkout. An absolute directory on any available drive/mount works too. Keep the same environment variable for subsequent commands. `.spaceeye/` is ignored by Git. Alternatively edit `paths` in `configs/data.yaml`; keep `real_data`, `app_data` and `private` under one shared parent.

## 2. Review or refit the prepared binary evaluation

Start with the [task board](requirements/02-team-roles-and-tasks.md), [data contract](../data/DATASET_CONTRACT.md), [current protocol](../data/EW_PROTOCOL_CURRENT.md), [metrics](../data/CURRENT_MODEL_METRICS.csv) and [backtest explanation](../data/BACKTEST_CURRENT.md). Source trace: [source catalogue](../data/SOURCE_CATALOG.csv) and [generation logic](../data/DATA_SOURCES_AND_GENERATION.md).

After setup, this command fits/evaluates the current binary models using the already-published prepared training table; it needs no original raw archive, generator answer keys or Earth Engine account:

```sh
uv run --locked python -m src.analysis.current_evaluation
```

It writes local checkpoints/predictions under `app_data/ml_current` and refreshes tracked current evaluation reports. Use a feature branch and review that diff. Generated targets are synthetic future distress labels, not independent field truth. Saved prediction files and the v6 package remain the comparison reference.

The separate backtest replay checks six real-case outputs from frozen prepared inputs. Expected counts are 1/6 after-start, 0/6 point-in-time, 2/6 literal. The fixed five-case success criterion is not met. Replay does not refit activity or rerun source-to-output clock checks.

## 3. Obtain the exact source caches for a complete rebuild

[REBUILD_INPUTS.csv](../data/REBUILD_INPUTS.csv) is the complete manifest: **84 files, 5,635,983 bytes before ZIP compression**. It extends the historical 71-file `SOURCE_INPUTS.csv` with ten source-register/reference files and three pre-pulled satellite caches. The wider 5.43 GB experiment archive is unnecessary for this current workflow.

The exact curated historical caches do not currently have a public download URL. They combine reviewed records and computed satellite windows; the source publishers do not host these exact CSVs. Request the frozen source-cache ZIP from the team. Do not substitute a fresh web scrape or satellite pull and claim the same historical run.

On a device that already has the verified sources, the owner creates the archive with:

```sh
uv run --locked python -m src.pipeline.source_cache --check
uv run --locked python -m src.pipeline.source_cache --export ../SpaceEye_REVIEW_SOURCE_CACHE_2026-10-29.zip
```

Place the downloaded/shared ZIP next to the checkout directory. The recipient installs it with:

```sh
uv run --locked python -m src.pipeline.source_cache --install ../SpaceEye_REVIEW_SOURCE_CACHE_2026-10-29.zip
uv run --locked python -m src.pipeline.source_cache --check
```

If the team hosts that exact archive, an alternative is `python -m src.pipeline.source_cache --download "https://<team-host>/<archive>.zip"`; replace the placeholder with the actual shared URL. No public endpoint is implied. Download/install verifies all expected filenames, byte sizes and hashes before writing. Different existing files are preserved. The manifest supplies the destination paths, so the recipient does not reconstruct folder names manually.

## 4. Rebuild from sources on an isolated data root

Use a fresh data root so the review does not replace accepted outputs. Install the source ZIP there first; prepared setup is optional for this full path.

```sh
uv run --locked python -m src.pipeline.team_run --full
```

This preflights all 84 inputs, codifies public evidence, fits operational/backtest activity variants, checks the frozen clock, generates historical synthetic data and local audit truth, cleans it, builds scenarios/features, prepares component data and runs current binary evaluation/reports. Private truth/name registries are generated locally for audit, not distributed as public review inputs or fed into model X. No prior private folder or saved model weights need to be copied. Review the reported FLAG/STOP outcomes rather than treating a finished command as predictive success.

## 5. Refreshing upstream data is a separate operation

The original source families and safe evidence links are documented in [DATA_SOURCES_AND_GENERATION](../data/DATA_SOURCES_AND_GENERATION.md) and `SOURCE_CATALOG.csv`. `src/pipeline/pulls/` contains the implemented cached satellite pulls; these do not reconstruct all curated fact/boundary/height inputs.

For an intentional new Earth Engine pull, install the optional dependency with `uv sync --locked --extra pulls`, run `uv run --locked earthengine authenticate`, and set `SPACEEYE_EE_PROJECT` to **your own** Earth Engine-enabled Cloud project before invoking a pull module. Cached review/rebuild needs no Earth Engine credentials. New upstream data needs a new reviewed inventory and run; it is not guaranteed to match the frozen hashes.

## Review acceptance

Record actual findings, revision, date and review evidence before accepting a task. Setup and replay do not automatically tick any review checkbox. Code changes, input refreshes and saved audit snapshots have different dates/scopes; record which one was verified.

## Executed validation

[Validation record](../data/PORTABLE_REVIEW_VALIDATION.json): 89 tests passed; isolated checkout launched from a different working directory; prepared setup and extracted-package verification passed; prepared and complete-source binary refits matched saved primary predictions/metrics; a clean full rebuild passed 61 data-audit checks and all four frozen-clock checks. This execution used Windows; POSIX/WSL path handling is implemented but those operating systems were not executed in this check. The original backtest success criterion and 2019Q2 FLAG remain unchanged.


## Optional observed imagery

The numerical setup does not install imagery. Follow the [imagery guide](../data/imagery/README.md) to view a controlled local report copy or rebuild figures from recorded source selections. Git contains metadata and code only, with no Esri JPEG/ZIP. The inspector pair and quarterly Sentinel context are outside model X. An Earth Engine account is only needed to rebuild four early periods, not to read metadata or install an appropriately shared report.
