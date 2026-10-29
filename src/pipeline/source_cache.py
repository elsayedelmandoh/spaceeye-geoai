"""Check, export or install the exact cached inputs for a full current source rebuild."""

import argparse
import csv
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from src.pipeline.common import APP, BASE_DIR, SRC
from src.pipeline.portable_io import install_files, relative_file, sha256

INVENTORY = BASE_DIR / "data/REBUILD_INPUTS.csv"


def records(inventory: Path = INVENTORY) -> list[dict]:
    with inventory.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    keys = set()
    for row in rows:
        if row["root"] not in {"real_data", "app_data"}:
            raise ValueError("Unknown source root in inventory")
        relative_file(row["file"])
        key = row["root"] + "/" + row["file"]
        if key in keys:
            raise ValueError("Duplicate source inventory entry")
        keys.add(key)
    return rows


def roots() -> dict[str, Path]:
    return {"real_data": SRC, "app_data": APP}


def check_inputs() -> list[dict]:
    rows, problems = records(), []
    for row in rows:
        path = roots()[row["root"]] / relative_file(row["file"])
        if not path.is_file():
            problems.append(f"Missing: {row['root']}/{row['file']}")
        elif sha256(path.read_bytes()) != row["sha256"]:
            problems.append(f"Hash differs: {row['root']}/{row['file']}")
    if problems:
        raise ValueError("Source preflight failed:\n" + "\n".join(problems) +
                         "\nInstall the frozen source archive with python -m src.pipeline.source_cache --install ARCHIVE.zip. "
                         "See docs/REVIEW_SETUP.md; do not silently substitute refreshed source data.")
    return rows


def export_archive(destination: Path) -> int:
    rows = check_inputs()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for row in rows:
            data = (roots()[row["root"]] / relative_file(row["file"])).read_bytes()
            if sha256(data) != row["sha256"]:
                raise ValueError("A source changed during export")
            archive.writestr(row["root"] + "/" + row["file"], data)
    return len(rows)


def install_archive(source: Path) -> int:
    rows = records()
    expected = {r["root"] + "/" + r["file"]: r for r in rows}
    files = {}
    with zipfile.ZipFile(source) as archive:
        if len(archive.namelist()) != len(expected) or set(archive.namelist()) != set(expected):
            raise ValueError("Source archive must contain exactly the files in REBUILD_INPUTS.csv")
        for name, row in expected.items():
            data = archive.read(name)
            if sha256(data) != row["sha256"] or len(data) != int(row["bytes"]):
                raise ValueError(f"Source archive hash/size differs: {name}")
            files[roots()[row["root"]] / relative_file(row["file"])] = data
    return install_files(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--check", action="store_true", help="Verify every cached input (the default)")
    options.add_argument("--export", type=Path, help="Create a local source-only ZIP for controlled team transfer")
    options.add_argument("--install", type=Path, help="Install the source-only ZIP without overwriting changed files")
    options.add_argument("--download", help="Download a team-provided HTTPS archive URL and verify/install it")
    args = parser.parse_args()
    if args.export:
        count = export_archive(args.export)
        print(f"Exported {count} frozen inputs to {args.export}. This source archive is not a public data release.")
    elif args.install:
        print(f"Installed {install_archive(args.install)} new source-cache files; existing identical files retained.")
    elif args.download:
        if not args.download.startswith("https://"):
            parser.error("Use an HTTPS source-archive URL supplied by the team")
        with tempfile.TemporaryDirectory() as folder:
            downloaded = Path(folder) / "source.zip"
            with urllib.request.urlopen(args.download, timeout=60) as response:
                if not response.geturl().startswith("https://"):
                    raise ValueError("Source archive redirected outside HTTPS")
                downloaded.write_bytes(response.read())
            print(f"Installed {install_archive(downloaded)} verified source-cache files.")
    else:
        rows = check_inputs()
        print(f"Verified all {len(rows)} frozen inputs ({sum(int(r['bytes']) for r in rows):,} bytes).")


if __name__ == "__main__":
    main()
