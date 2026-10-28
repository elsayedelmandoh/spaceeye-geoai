# Ready data: start here

**[Download the ready-data ZIP](SpaceEye_R7_READY_DATA_2026-10-28_v4.zip?raw=1)**

This is the final prepared dataset for the team. No raw downloads or data-pipeline rebuild are needed to use it. All instructions and helpers are in English.

## Three steps

1. Download the ZIP and extract it.
2. Open the extracted `README.md`. For spreadsheets, use `csv/`; for Python, use Parquet; for SQL, open `spaceeye_ready.duckdb`.
3. Read [the short data guide](DATA_GUIDE.md) to choose the right tables.

## Python example

If you have cloned this repository, first run `uv sync --locked` from its root. After extracting the ZIP into this directory, run this from the repository root:

```powershell
uv run --locked python releases/ready-data/SpaceEye_R7_READY_DATA_2026-10-28_v4/examples/read_ready_data.py
```

The example reads the inspection list and prepares the training feature table. It does not fit a model. It also works in another Python environment with pandas, pyarrow and duckdb installed.

## What's included?

- 23 ready-use tables,plus boundary polygons and the empty real-visit template.
- A separate training dataset: **180 rows and 40 declared features**, with metadata explaining features and targets.
- **100 labeled feed complaints** plus a separate **296-text five-class benchmark**,with isolated template-family splits. Do not combine the corpora for evaluation.
- **180 inspection-input JSON contexts**,cutoff-filtered and indexed by code/quarter.
- **58 generated visit exercises** and **648 hypothetical financial-priority rows**,with explicit simulation labels and baseline comparisons. These are not actual fieldwork or validated forecasts.
- CSV copies, column dictionaries, a working example and a file-integrity checker.

Raw inputs, rejected records, hidden answer keys, name mappings, models and credentials are excluded. Version 4 adds Arabic committee reasons, current model diagnostics and S1/S2/S3 exports; observed source values and the training target definition are preserved. Generated operations and hypothetical financial paths are labelled **Synthetic - for training only**.

The optional [SHA-256 file](SpaceEye_R7_READY_DATA_2026-10-28_v4.zip.sha256.txt) verifies the ZIP. The extracted `verify_package.py` checks all package files. Version 4 is current. Version 3 remains available as a historical prepared-data snapshot.

Sources and how generated fields were made: [data sources and generation logic](../../docs/data/DATA_SOURCES_AND_GENERATION.md),[coded source catalog](../../docs/data/SOURCE_CATALOG.csv),[input-file hashes](../../docs/data/SOURCE_INPUTS.csv) and [exact generation settings](../../docs/data/GENERATION_PARAMETERS.json). Copies are also included inside the ZIP under docs/.

## Current extension

Arabic committee reasons and ordinal priorities are included in the inspection CSV. `tables/current/ml_current.parquet` contains four diagnostic methods; use `(method, code, quarter)` as its key. `p_completed` is null because training has no completed example. The other probabilities are conditional on observed classes. Read `docs/EW_REPORT_CURRENT.md` before interpreting them. `tables/current/S1.parquet`, `S2.parquet`, `S3.parquet` provide the what-if handoff; future public context is explicitly frozen.
