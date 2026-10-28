# Ready data: start here

**[Download the ready-data ZIP](SpaceEye_R7_READY_DATA_2026-10-28_v2.zip?raw=1)**

This is the final prepared dataset for the team. No raw downloads or data-pipeline rebuild are needed to use it. All instructions and helpers are in English.

## Three steps

1. Download the ZIP and extract it.
2. Open the extracted `README.md`. For spreadsheets, use `csv/`; for Python, use Parquet; for SQL, open `spaceeye_ready.duckdb`.
3. Read [the short data guide](DATA_GUIDE.md) to choose the right tables.

## Python example

If you have cloned this repository, first run `uv sync --locked` from its root. After extracting the ZIP into this directory, run this from the repository root:

```powershell
uv run --locked python releases/ready-data/SpaceEye_R7_READY_DATA_2026-10-28_v2/examples/read_ready_data.py
```

The example reads the inspection list and prepares the training feature table. It does not fit a model. It also works in another Python environment with pandas, pyarrow and duckdb installed.

## What's included?

- 17 ready-use tables, plus boundary polygons and an empty visit-record template.
- A separate training dataset: **180 rows and 40 declared features**, with metadata explaining features and targets.
- CSV copies, column dictionaries, a working example and a file-integrity checker.

Raw inputs, rejected records, hidden answer keys, name mappings, models and credentials are excluded. Prepared source tables are unchanged from the validated local v2 bundle. Generated operations and hypothetical financial paths are labelled **Synthetic - for training only**.

The optional [SHA-256 file](SpaceEye_R7_READY_DATA_2026-10-28_v2.zip.sha256.txt) verifies the ZIP. The extracted `verify_package.py` checks all package files.
