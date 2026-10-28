"""Build an allowlisted, standalone team bundle from final prepared data only."""

import csv
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import duckdb
import pandas as pd

from src.generator.defects import PHONE
from src.pipeline import gates
from src.pipeline.common import APP, BASE_DIR, PRIVATE

PROJECT = APP.parent
REPO = BASE_DIR
RELEASES = PROJECT / "releases"
TAG = "SpaceEye_R7_READY_DATA_2026-10-28_v3"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def main():
    from src.pipeline.component_data import main as prepare_components
    prepare_components()
    from src.pipeline.source_catalog import main as prepare_source_catalog
    prepare_source_catalog()
    target = RELEASES / TAG
    suffix = 2
    while target.exists() or target.with_suffix(".zip").exists():
        target = RELEASES / f"{TAG}_{suffix}"
        suffix += 1
    target.mkdir(parents=True)
    copied = []
    tables = []
    dictionary_links = []

    def copy(source, relative):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if sha(source) != sha(destination):
            raise RuntimeError(f"Copy mismatch: {relative}")
        copied.append({"file": relative, "source": source.relative_to(PROJECT.parent).as_posix(), "sha256": sha(source)})
        return destination

    real_names = ["compounds", "sat_quarterly", "sat_yearly", "statements", "eval_outcomes", "drivers_monthly", "rules", "kpi_values"]
    groups = [
        ("real", "real", real_names),
        ("sim_clean", "operations", ["fin_monthly", "fin_quarterly", "complaints", "fine_assumptions"]),
        ("scenarios", "financial_paths", ["initial_state", "paths"]),
        ("component_data", "review", ["synthetic_visits", "hypothetical_priorities"]),
    ]
    with duckdb.connect(str(target / "spaceeye_ready.duckdb")) as connection:
        for source_group, bundle_group, names in groups:
            for name in names:
                relative = f"tables/{bundle_group}/{name}.parquet"
                destination = copy(APP / source_group / f"{name}.parquet", relative)
                frame = pd.read_parquet(destination)
                csv_relative = f"csv/{bundle_group}/{name}.csv"
                (target / csv_relative).parent.mkdir(parents=True, exist_ok=True)
                frame.to_csv(target / csv_relative, index=False, encoding="utf-8-sig")
                table_name = f"{bundle_group}_{name}"
                connection.register("ready_frame", frame)
                connection.execute(f'CREATE TABLE "{table_name}" AS SELECT * FROM ready_frame')
                connection.unregister("ready_frame")
                tables.append({"table": table_name, "file": relative, "csv": csv_relative, "rows": len(frame), "columns": len(frame.columns)})
                dictionary = REPO / "docs" / "data" / "dictionaries" / f"{source_group}__{name}.md"
                if dictionary.exists():
                    doc = f"dictionaries/{source_group}__{name}.md"
                    copy(dictionary, doc)
                    dictionary_links.append(f"- [{table_name}]({Path(doc).name})")
        for source, relative, table_name in [
            (APP / "data_completion" / "cycle_list.csv", "tables/inspection/cycle_list.csv", "inspection_cycle_list"),
            (APP / "data_completion" / "inspection_capacity.csv", "tables/inspection/inspection_capacity.csv", "inspection_capacity"),
            (APP / "scenarios" / "summary.csv", "tables/financial_paths/summary.csv", "financial_paths_summary"),
        ]:
            destination = copy(source, relative)
            frame = pd.read_csv(destination)
            connection.register("ready_frame", frame)
            connection.execute(f'CREATE TABLE "{table_name}" AS SELECT * FROM ready_frame')
            connection.unregister("ready_frame")
            tables.append({"table": table_name, "file": relative, "rows": len(frame), "columns": len(frame.columns)})
        assert connection.execute("SELECT count(*) FROM real_compounds").fetchone()[0] == 12
        assert connection.execute("SELECT count(*) FROM operations_fin_quarterly").fetchone()[0] == 180

    copy(APP / "real" / "compound_boundaries.geojson", "tables/real/compound_boundaries.geojson")
    copy(APP / "data_completion" / "ops_visits_template.csv", "tables/inspection/ops_visits_template.csv")
    copy(APP / "scenarios" / "assumptions.json", "docs/financial_path_assumptions.json")
    copy(REPO / "configs" / "synthetic_sources.json", "docs/synthetic_sources.json")
    copy(REPO / "docs" / "data" / "REPRODUCIBILITY.json", "docs/source_build_reproducibility.json")
    for source_group, name in [("data_completion", "inspection_capacity"), ("scenarios", "summary")]:
        source = REPO / "docs" / "data" / "dictionaries" / f"{source_group}__{name}.md"
        copy(source, f"dictionaries/{source.name}")
        dictionary_links.append(f"- [{source_group}/{name}]({source.name})")
    write(target / "dictionaries" / "README.md", "# Included table dictionaries\n\nThese describe the included final tables only. No rejected or raw table is distributed.\n\n" + "\n".join(dictionary_links))
    components = APP / "component_data"
    for name in ("complaints_training", "complaints_benchmark"):
        for ext in ("parquet", "csv"):
            copy(components / f"{name}.{ext}", f"training/{name}.{ext}")
        copy(components / "dictionaries" / f"{name}.md", f"training/{name}_dictionary.md")
    copy(components / "complaints_metadata.json", "training/complaints_metadata.json")
    copy(components / "complaints_benchmark_metadata.json", "training/complaints_benchmark_metadata.json")
    for path in sorted((components / "inspection_contexts").rglob("*.json")):
        copy(path, "inspection/" + path.relative_to(components).as_posix())
    copy(components / "inspection_index.csv", "inspection/index.csv")
    copy(components / "metadata.json", "docs/component_validation.json")
    copy(REPO / "docs/data/COMPONENT_DATA_PROTOCOL.md", "docs/COMPONENT_DATA_PROTOCOL.md")
    for name in ("DATA_SOURCES_AND_GENERATION.md", "SOURCE_CATALOG.csv", "SOURCE_INPUTS.csv", "GENERATION_PARAMETERS.json"):
        copy(REPO / "docs/data" / name, "docs/" + name)

    data_path = copy(PRIVATE / "ml_dataset_extended.parquet", "training/ml_dataset_extended.parquet")
    data = pd.read_parquet(data_path)
    data.to_csv(target / "training" / "ml_dataset_extended.csv", index=False, encoding="utf-8-sig")
    metadata = json.loads((PRIVATE / "ml_dataset_extended_metadata.json").read_text(encoding="utf-8"))
    assert sha(data_path) == metadata["dataset_sha256"]
    metadata["original_export_location"] = metadata["dataset"]
    metadata["dataset"] = "training/ml_dataset_extended.parquet"
    metadata["package_note"] = "Ready-to-use table; original source hashes are provenance only, not bundled raw input dependencies. Exact X comes from features; exclude keys, targets, censor and already-completed flag."
    write(target / "training" / "metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))
    copy(PRIVATE / "dictionaries" / "ml_dataset_extended.md", "training/dictionary.md")

    codes = set(pd.read_parquet(target / "tables" / "real" / "compounds.parquet").code)
    checks = {
        "scope_12": len(codes) == 12,
        "financial_months_540": len(pd.read_parquet(target / "tables" / "operations" / "fin_monthly.parquet")) == 540,
        "financial_quarters_180": len(pd.read_parquet(target / "tables" / "operations" / "fin_quarterly.parquet")) == 180,
        "accepted_complaints_1334": len(pd.read_parquet(target / "tables" / "operations" / "complaints.parquet")) == 1334,
        "training_180_by_40_features": len(data) == 180 and len(metadata["features"]) == 40,
        "training_unique_keys": not data.duplicated(["code", "quarter"]).any(),
        "censored_targets_null": data.loc[data.label_censored, metadata["targets"]].isna().all().all(),
        "training_known_codes": set(data.code) == codes,
    }
    complaints = pd.read_parquet(target / "tables" / "operations" / "complaints.parquet")
    checks["masked_complaints"] = not complaints.text_ar.dropna().map(lambda text: bool(PHONE.search(text))).any()
    if not all(checks.values()):
        raise RuntimeError(f"Bundle checks failed: {checks}")
    source_audit = json.loads((APP / "release_audit.json").read_text(encoding="utf-8"))
    write(target / "docs" / "validation_summary.json", json.dumps({
        "package_checks": {k: bool(v) for k, v in checks.items()}, "source_release_status": source_audit["status"],
        "source_validation_scope": source_audit["validation_scope"], "historical_evaluation_status": source_audit["evaluation_status"],
        "limits": source_audit["limits"], "split_counts": metadata["split_counts"],
    }, ensure_ascii=False, indent=2))
    write(target / "TABLES.csv", pd.DataFrame(tables).to_csv(index=False))
    write(target / "PROVENANCE.json", json.dumps({
        "release": TAG, "scope": "12R7 compounds; final prepared data; no raw inputs", "files": copied,
        "source_commit": subprocess.check_output(["git", "-c", f"safe.directory={REPO.as_posix()}", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "excluded": ["raw inputs", "rejected/quarantined observations", "private names/evidence mapping", "answer keys and hidden truth", "legacy training exports", "models and checkpoints", "historical database/run logs"],
    }, ensure_ascii=False, indent=2))
    write(target / "README.md", """# SpaceEye ready-to-use team data

Release: 28 October 2026. Scope: 12 coded compounds in R7.
Generated operations and hypothetical financial paths are labelled: Synthetic - for training only.

## Quick start

1. Extract the complete archive to any folder on your computer.
2. Open `spaceeye_ready.duckdb` directly. It contains observation tables, prepared operations, financial paths and inspection selections.
3. Alternatively, read Parquet files under `tables/`. UTF-8 CSV copies are under `csv/`; inspection lists and the financial summary are CSV files alongside their tables.
4. `TABLES.csv` lists table names, file locations and row counts. Column definitions are under `dictionaries/`.
5. For modelling, use `training/ml_dataset_extended.parquet` with `training/metadata.json`. The training export is separate from the application database, and its targets are not features.

## Contents

- Observations and indicators: 12 compounds, 516 quarterly observations, 132 annual rows, 372 indicator rows and 57 published statements.
- Prepared operations: 540 monthly financial rows, 180 financial quarters, 1,334 complaints with phone masking, and 12 synthetic allocation/fine-assumption records.
- Hypothetical financial paths: 648 rows, initial states, comparison summary and declared assumptions.
- Inspection selections: baseline capacity 4, with alternatives 2 and 6. The visit template is empty; no visit outcomes were invented.
- Training export: 180 rows and 40 declared features, with binary and three-class targets kept separate from X.
- Complaint classification:100labeled masked texts from the existing feed with conservative group splits,plus a SEPARATE296-text generated five-class capability benchmark. Use the benchmark alone for balanced capability work;do not combine the corpora or claim real complaint accuracy.
- Inspection inputs:180cutoff-safe JSON contexts under `inspection/inspection_contexts/`,indexed in `inspection/index.csv`. Public facts and generated operations/visits are separated;no hidden targets are agent inputs. Missing imagery is marked rather than fabricated.
- Review extensions:`tables/review/synthetic_visits.parquet` has58generated exercise visits,not actual fieldwork. `hypothetical_priorities.parquet` has648financial-path priority rows with same-month baseline comparisons,using the declared frozen-context/projected-B5rule.

## Run the example

From the extracted bundle folder, using the project's locked environment:

```powershell
uv run --project "path/to/spaceeye-geoai" python examples/read_ready_data.py
uv run --project "path/to/spaceeye-geoai" python verify_package.py
```

Alternatively, use an existing Python environment containing pandas, pyarrow and duckdb:

```powershell
python examples/read_ready_data.py
python verify_package.py
```

This bundle is standalone for reading, analysis and interface development. It does not require the original F: drive or raw-source downloads. It is not a complete input archive for rebuilding the source-acquisition pipeline.

## Definitions and limits

- X is exactly the `features` list in the training metadata. Keys, targets, `label_censored` and `already_completed_at_cutoff` are not features.
- Training ends at 2024Q4; 2025Q1 is embargoed; the time test is 2025Q2–2026Q1. The final two quarters have incomplete future horizons and must be excluded from supervised fitting and target metrics.
- The three-class target requires new full-project handover within the next six months; partial handover is insufficient. Distress takes precedence. There are zero completed training examples and one completed test example, so this export does not establish a reliable three-class classifier.
- K5 is a research-policy screening proxy. Fine amounts, the illustrative 1% monthly rate and allocation records are generated assumptions, not assessed fines or verified contracts. Relief is an optional hypothetical case gated by the news publication date, not automatic entitlement.
- Retrospectively generated allocation dates do not enter X or replace public K6. Insufficient observation remains unknown; do not automatically replace missing values with zero.
- Monthly unit sales are flows and are summed over each quarter. The training complaint diagnostic is normalized by cutoff-month sales, not cumulative sold inventory or buyer incidence.
- Financial paths are hypothetical, not handover-date forecasts. Historical N=8 early-warning results do not evaluate current capacity 4 or the expanded dataset.
- The 2019Q2 coverage flag and other limitations remain recorded in `docs/validation_summary.json`; passing package-integrity checks does not remove them.

Raw inputs, quarantined/rejected observations, hidden answer keys, code-to-name mappings and models are excluded. Parquet is authoritative for types and null values; CSV is provided for convenient viewing. Original Arabic complaint text is data and remains unchanged.

Every distributed file has a SHA-256 entry in `MANIFEST.csv`. Run `verify_package.py` after extraction to check transfer integrity. Version3adds the missing component inputs;original prepared source tables remain unchanged. See docs/COMPONENT_DATA_PROTOCOL.md and docs/component_validation.json for definitions,split counts and limits.
""")
    write(target / "examples" / "read_ready_data.py", '''from pathlib import Path
import json
import duckdb
import pandas as pd

root = Path(__file__).resolve().parents[1]
with duckdb.connect(str(root / "spaceeye_ready.duckdb"), read_only=True) as con:
    print(con.execute("SELECT * FROM inspection_cycle_list ORDER BY cycle_rank").df())
meta = json.loads((root / "training/metadata.json").read_text(encoding="utf-8"))
data = pd.read_parquet(root / meta["dataset"])
mask = data.quarter.le("2024Q4") & ~data.label_censored & ~data.already_completed_at_cutoff
X_train = data.loc[mask, meta["features"]]
y_train = data.loc[mask, "label_distress_next_6m"]
print("Ready data:", len(data), "rows; X_train:", X_train.shape, "; binary positives:", int(y_train.sum()))
print("No model fitting performed. Inspect missingness and fit preprocessing on train only.")
''')
    write(target / "verify_package.py", '''import csv
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parent
with (root / "MANIFEST.csv").open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream))
for row in rows:
    path = (root / row["file"]).resolve()
    assert root in path.parents, "Unexpected path"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], row["file"]
print("PASS:", len(rows), "package files match SHA-256 manifest")
''')
    scan = gates.g_no_names(root=target, extra=[])
    if scan["status"] != "PASS":
        raise RuntimeError("Bundle name gate failed: " + scan["value"])
    manifest = [{"file": p.relative_to(target).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(target.rglob("*")) if p.is_file()]
    with (target / "MANIFEST.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["file", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(manifest)
    subprocess.run([__import__("sys").executable, str(target / "verify_package.py")], check=True)
    subprocess.run([__import__("sys").executable, str(target / "examples" / "read_ready_data.py")], check=True)
    archive = target.with_suffix(".zip")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(target.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(f"{target.name}/{path.relative_to(target).as_posix()}", date_time=(2026, 10, 28, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                bundle.writestr(info, path.read_bytes())
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        for row in manifest:
            assert hashlib.sha256(bundle.read(f"{target.name}/{row['file']}")).hexdigest() == row["sha256"]
    write(archive.with_suffix(".zip.sha256.txt"), f"{sha(archive)}  {archive.name}")
    print(json.dumps({"status": "PASS", "zip": str(archive), "bytes": archive.stat().st_size, "files": len(manifest) + 1, "ready_tables": len(tables), "training_rows": len(data), "features": len(metadata["features"]), "no_names": "PASS", "phones": "masked"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
