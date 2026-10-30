"""Install verified prepared review/training data from the checked-in v7 release."""

import argparse
import csv
import io
import json
import zipfile
from pathlib import Path

from src.pipeline.common import APP, BASE_DIR, PRIVATE
from src.pipeline.portable_io import install_files, relative_file, sha256

PACKAGE = BASE_DIR / "releases/ready-data/SpaceEye_R7_READY_DATA_2026-10-31_v7.zip"
PACKAGE_SHA256 = "c470f9884be5681d2b6d2ff0a5530d05e5e0eb07a959a2a78f84762764a38343"
REVIEW = BASE_DIR / "releases/ready-data/review"


def setup() -> int:
    if sha256(PACKAGE.read_bytes()) != PACKAGE_SHA256:
        raise ValueError("The frozen v7 ZIP hash differs")
    files = {}
    with zipfile.ZipFile(PACKAGE) as archive:
        prefix = "SpaceEye_R7_READY_DATA_2026-10-31_v7/"
        rows = list(csv.DictReader(io.StringIO(archive.read(prefix + "MANIFEST.csv").decode("utf-8-sig"))))
        expected = {prefix + r["file"] for r in rows} | {prefix + "MANIFEST.csv"}
        if set(archive.namelist()) != expected or len(archive.namelist()) != len(expected):
            raise ValueError("Unexpected or duplicate v6 archive entries")
        files[APP.parent / "ready-data/MANIFEST.csv"] = archive.read(prefix + "MANIFEST.csv")
        for row in rows:
            name = row["file"]
            relative_file(name)
            data = archive.read(prefix + name)
            if sha256(data) != row["sha256"] or len(data) != int(row["bytes"]):
                raise ValueError(f"v6 manifest mismatch: {name}")
            # Keep the complete unpacked release available for review.
            files[APP.parent / "ready-data" / relative_file(name)] = data
            for group, destination in (("real", "real"), ("operations", "sim_clean"),
                                       ("financial_paths", "scenarios"), ("review", "component_data")):
                if name.startswith(f"tables/{group}/"):
                    files[APP / destination / Path(name).name] = data
            if name.startswith("tables/inspection/"):
                files[APP / "data_completion" / Path(name).name] = data
            if name == "training/ml_dataset_extended.parquet":
                files[PRIVATE / "ml_dataset_extended.parquet"] = data
            if name == "training/metadata.json":
                metadata = json.loads(data)
                metadata["dataset"] = "ml_dataset_extended.parquet"
                metadata.pop("original_export_location", None)
                files[PRIVATE / "ml_dataset_extended_metadata.json"] = (json.dumps(metadata, indent=2) + "\n").encode()
    manifest = json.loads((REVIEW / "manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        data = (REVIEW / relative_file(name)).read_bytes()
        if sha256(data) != digest:
            raise ValueError(f"Review artifact hash mismatch: {name}")
        files[APP / relative_file(name)] = data
    return install_files(files)


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    count = setup()
    print(f"Installed {count} prepared review files. App data: {APP}; training data: {PRIVATE}")
    print("The prepared dataset supports case replay and binary evaluation. Original source caches, hidden generator "
          "truth and activity model weights were not installed. See docs/REVIEW_SETUP.md for a full rebuild.")


if __name__ == "__main__":
    main()
