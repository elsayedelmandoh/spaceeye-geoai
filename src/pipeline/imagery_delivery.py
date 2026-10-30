"""Build/install a local static report; publish metadata only, never Esri pixels."""

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

from src.pipeline.common import APP, BASE_DIR, CFG
from src.pipeline.portable_io import install_files, relative_file

NAME = "SpaceEye_R7_IMAGERY_REVIEW_2026-10-30_v2"
RELEASE = APP.parent / "imagery_delivery"
PACKAGE = RELEASE / (NAME + ".zip")


def digest(data):
    return hashlib.sha256(data).hexdigest()


class ImageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.links.extend(value for key, value in attrs if key == "src")


def packaged_files(package=PACKAGE, app=APP):
    """Validate a published snapshot completely before returning install targets."""
    checksum = package.with_suffix(".zip.sha256.txt").read_text(encoding="utf-8").split()[0]
    if digest(package.read_bytes()) != checksum:
        raise ValueError("Imagery ZIP hash differs")
    files = {}
    with zipfile.ZipFile(package) as archive:
        raw = archive.read("IMAGERY_MANIFEST.csv")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
        expected = {r["file"] for r in rows} | {"IMAGERY_MANIFEST.csv"}
        if len(archive.namelist()) != len(expected) or set(archive.namelist()) != expected:
            raise ValueError("Imagery package contains unexpected or duplicate paths")
        for row in rows:
            relative = relative_file(row["file"])
            data = archive.read(row["file"])
            if len(data) != int(row["bytes"]) or digest(data) != row["sha256"]:
                raise ValueError("Imagery file integrity failed: " + row["file"])
            files[app / relative] = data
        files[app / "IMAGERY_MANIFEST.csv"] = raw
    return files


def build():
    import numpy as np
    import pandas as pd
    from PIL import Image

    from src.pipeline import imagery_compare as C

    polygons = C.boundaries()
    C.report(polygons)
    out = C.OUT
    wayback = pd.read_csv(out / "wayback_timeline.csv")
    sentinel = pd.read_csv(out / "sentinel_quarterly.csv")
    public_images = pd.read_csv(APP / "images/images.csv")
    through = str(sentinel.observation_end.max())
    assert set(wayback.code) == set(sentinel.code) == set(polygons)
    assert wayback.groupby("code").size().min() >= 2
    assert not wayback.duplicated(["code", "capture_dates"]).any()
    assert not sentinel.duplicated(["code", "quarter"]).any()
    assert sentinel.status.eq("available").all()
    assert sentinel.groupby("code").size().eq(len(pd.period_range(C.START, through, freq="Q"))).all()
    assert (pd.to_datetime(wayback.capture_date_max) <= pd.to_datetime(wayback.release_date)).all()
    assert wayback.capture_date_max.le(through).all() and wayback.release_date.le(through).all()
    assert wayback.metadata_dated_coverage_fraction.ge(.99 - 1e-9).all()
    assert sentinel.compound_bad_fraction.le(.10).all()
    assert sentinel.compound_valid_fraction.ge(.95).all()
    assert sentinel.retrospective_visual_context.all()
    assert sentinel.resolution_m.eq(10).all()
    assert sentinel.visualization_policy.eq("fixed_reflectance_0_0.6").all()
    assert public_images.project_cutoff_eligible.all()
    from src.pipeline.setup_review import PACKAGE as data_package
    from src.pipeline.setup_review import PACKAGE_SHA256
    assert digest(data_package.read_bytes()) == PACKAGE_SHA256
    for code in polygons:
        rows = public_images[public_images.code.eq(code)].sort_values("sequence")
        assert len(rows) == 2 and set(rows.role) == {"before", "after"}
        assert rows.image_type.iloc[0] == "before" and rows.image_type.iloc[-1] == "after"
        assert pd.Timestamp(rows.capture_date_max.iloc[0]) <= pd.Timestamp(rows.capture_date_max.iloc[-1]) - pd.DateOffset(months=12)
        reference = json.loads(rows.bbox_3857.iloc[0])
        for value in pd.concat([rows.bbox_3857, sentinel[sentinel.code.eq(code)].bbox_3857]):
            assert np.allclose(json.loads(value), reference, atol=1e-6)
    for row in sentinel.itertuples():
        quarter = pd.Period(row.quarter, freq="Q")
        assert quarter.start_time.date() <= pd.Timestamp(row.capture_date).date() <= min(quarter.end_time.date(), pd.Timestamp(through).date())
    files = {}
    for frame in (wayback, sentinel):
        for row in frame.itertuples():
            path = APP / relative_file(row.path)
            data = path.read_bytes()
            assert digest(data) == row.sha256
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
            files[row.path] = data
    parser = ImageLinks()
    parser.feed((out / "index.html").read_text(encoding="utf-8"))
    for link in parser.links:
        target = (out / link).resolve()
        assert target.is_relative_to(APP.resolve()) and target.is_file(), link
    counts = wayback.groupby("code").size()
    comparison = pd.read_csv(out / "comparison.csv")
    mixed = int(wayback.mixed_capture_dates.sum())
    source_resolutions = [float(value) for cell in wayback.source_resolution_m for value in json.loads(cell)]
    methods = [
        {"method": "Wayback official static Print service", "status": "executed", "result": f"{len(wayback)} attributed static figures; {counts.min()}-{counts.max()} accepted capture states per compound"},
        {"method": "Public Earth Search Sentinel COGs", "status": "executed", "result": f"{sentinel[sentinel.method.eq('earth_search_public_cog')].quarter.nunique()} quarters; all 12 coded boundaries"},
        {"method": "Earth Engine existing-account thumbnails", "status": "executed", "result": f"{sentinel[sentinel.method.str.startswith('earth_engine')].quarter.nunique()} early gap quarters; no new account/project; no credentials packaged"},
        {"method": "GIS rendering via Rasterio/GDAL", "status": "executed", "result": "Reprojected Sentinel windows to the same per-compound EPSG:3857 extent; current QGIS/ArcGIS applications were not installed"},
        {"method": "Default Sentinel TCI preview display", "status": "tested; replaced for final figures", "result": "Bright-desert previews were saturated; original calibrated RGB bands and one fixed reflectance range 0-0.6 were adopted"},
        {"method": "Manual Wayback browser workflow", "status": "unavailable in execution environment", "result": "Browser inventory returned no available browsers; used the supported Esri static rendering service"},
        {"method": "Google Earth manual export", "status": "unavailable in execution environment", "result": "No installed Earth application or controllable browser; no Google tile extraction or invented comparison"},
        {"method": "Separate licensed commercial/project imagery", "status": "not acquired", "result": "No applicable licensed R7 source collection found; no paid purchase or account creation performed"},
    ]
    C.save_csv(out / "method_comparison.csv", methods)
    validation = {"status": "PASS", "study_start": C.START, "study_through": through,
                  "project_data_cutoff": CFG["asof"], "compounds": len(polygons), "wayback_frames": len(wayback),
                  "wayback_min_per_compound": int(counts.min()), "wayback_max_per_compound": int(counts.max()),
                  "mixed_date_wayback_frames": mixed, "sentinel_frames": len(sentinel),
                  "sentinel_quarters": int(sentinel.quarter.nunique()), "sentinel_missing_frames": 0,
                  "sentinel_latest_capture": sentinel.capture_date.max(), "partial_quarter": str(pd.Period(through, freq="Q")),
                  "per_compound_cloud_shadow_nodata_max": float(sentinel.compound_bad_fraction.max()),
                  "wayback_source_resolution_range_m": [min(source_resolutions), max(source_resolutions)],
                  "same_extent_per_compound": True, "numerical_release_modified": False,
                  "numerical_release": data_package.name, "numerical_release_sha256": PACKAGE_SHA256,
                  "sentinel_display_policy": "Fixed physical RGB reflectance 0-0.6, gamma 1.0; source scale/offset applied; no per-scene fitting",
                  "context_metadata_coverage_min": float(wayback.metadata_context_coverage_fraction.min()),
                  "image_source_code_sha256_lf": {str(p.relative_to(BASE_DIR)): digest(p.read_bytes().replace(b"\r\n", b"\n")) for p in [
                      BASE_DIR / "src/pipeline/imagery_sources.py", BASE_DIR / "src/pipeline/imagery_compare.py",
                      BASE_DIR / "src/pipeline/imagery_earth_engine.py"]},
                  "no_training_or_threshold_change": True,
                  "limits": ["Static map context only; no finishing, completion, height or accuracy claims.",
                             "Mixed capture dates remain mixed; source accuracy is not cadastral accuracy.",
                             "Sentinel frames are retrospective selected scenes; no historical availability proof.",
                             "Source display/rendering paths are not independent sensors or field validation."]}
    C.save_json(out / "validation.json", validation)
    rights = """# Third-party imagery rights

The repository's software licence does not license the underlying imagery.

Wayback: limited attributed static educational map report figures, rendered by Esri's official Print service. Esri and the imagery licensors retain their rights. No WMTS tile archive, raw imagery dataset, fitted image model, or blanket redistribution licence is supplied. Keep the per-figure attribution and source-item link with each figure. Do not use the Wayback figures to train/test/validate an image model without separately confirming the applicable licence.

Generated inspection HTML embeds these pixels as base64 and follows the same restrictions as the JPEGs: keep it local for attributed educational review; never commit it or redistribute it. A file extension does not remove the underlying image rights.

- Static-map policy: https://doc.arcgis.com/en/arcgis-online/reference/static-maps.htm
- Esri terms: https://www.esri.com/en-us/legal/terms/web-site-service
- Agreement, static representations/offline restrictions: https://assets.esri.com/content/dam/esrisites/en-us/media/legal/ma-translations/english.pdf
- Wayback source metadata: https://www.esri.com/arcgis-blog/products/arcgis-living-atlas/imagery/wayback-with-world-imagery-metadata

Sentinel: derived RGB report figures contain modified Copernicus Sentinel data of the stated capture year. Keep that notice and the individual public source/collection IDs. Source notice: https://sentinel.esa.int/documents/247904/690755/Sentinel_Data_Legal_Notice ; https://dataspace.copernicus.eu/terms-and-conditions . Earth Search: https://registry.opendata.aws/sentinel-2-l2a-cogs/ . Current STAC collections identify their licence via that Sentinel legal notice; they are not represented here as CC0.

The static-image attribution includes image providers for the viewed area and the source item's service credits. The same current reviewed boundary is overlaid for temporal comparison; it is not evidence of historical land allocation or a legal survey.
"""
    (out / "THIRD_PARTY_IMAGERY.md").write_text(rights, encoding="utf-8")
    report = f"""# R7 observed imagery comparison

Snapshot date: {through}. The complete offline gallery stays under the configured local app_data/imagery_comparison directory. Git contains metadata and code only; no Esri images or imagery ZIP.

## Results

- {len(wayback)} accepted dated Wayback static figures, {counts.min()}-{counts.max()} per compound; {mixed} have mixed capture dates.
- {len(sentinel)} Sentinel figures: 12 compounds across {sentinel.quarter.nunique()} quarters, 2016Q1 through partial 2026Q4; latest actual capture {sentinel.capture_date.max()}.
- Wayback's latest accepted capture is {wayback.capture_date_max.max()}, even when its release was published in 2026. A publication-only refresh/provider rename is not another observation; five such same-date duplicates were removed during validation.
- Wayback source resolution metadata ranges {min(source_resolutions):g}-{max(source_resolutions):g} m. Sentinel RGB is 10 m. Rendering to a larger screen does not increase native resolution.

Wayback is the useful detailed visual context for roofs, road patterns and building footprints. Sentinel provides the continuous quarterly overview and the more recent 2026 context, with coarser detail. Neither source establishes finishing, legal handover, floor count or a completion percentage. Colour differences may reflect season, processing and illumination.

## Selection and accuracy limits

Wayback discovery checks metadata tile locations at a representative point and up to four other interior points, then queries intersecting metadata footprints for each candidate at the render scale. Visible sources are resolved in draw order. It is not an exhaustive per-pixel audit of the archive. Capture date sets are deduplicated, retaining the earliest encountered publication of a capture state; mixed source dates are shown as ranges and are not converted into a fabricated single date. Border-context credits are checked and supplemented with the source item's service attribution.

Sentinel uses one actual scene per quarter: public COG candidates closest to quarter-end minus 15 days, and closest to the observation end for the current partial quarter; up to five candidates are locally screened. Existing-account Earth Engine provides four early gap periods. Quality checks allow at most 10% classified cloud/shadow/no-data per compound, with at least 95% valid coverage; the observed maximum is {sentinel.compound_bad_fraction.max():.4f}. COG quality uses SCL at 20 m; early Earth Engine checks sample SCL at 60 m. These are quality screens, not a guarantee of completely cloud-free pixels. Display frames retain actual capture dates and source IDs. Current selected products are L2A surface reflectance. Standard 8-bit preview TCI images were visibly saturated over this bright desert site. Final figures instead apply each original RGB band's declared scale/offset, then one fixed reflectance display range 0-0.6 with gamma 1.0 across every period. This is a display policy, not per-scene histogram fitting, sharpening or a model. The four 2016 acquisitions were reprocessed in 2023, as shown by their product IDs; they are real 2016 captures but not evidence that this processed product was available in 2016. Pixel colour change is not quantified as construction progress.

Sequence names such as `stage_02` mean chronological observation positions, not independently labelled construction stages. All sources use the same per-compound EPSG:3857 view extent and coded boundary. Sentinel display maps are 640 pixels wide to keep delivery size reasonable; the underlying observed resolution remains 10 m. Product processing/availability may postdate capture. The quarterly images are retrospective context, not additional historical model X or new physical measurements. The partial 2026Q4 frames extend beyond the frozen numerical dataset's 2026Q3 cutoff and are explicitly labelled. The operational image tool filters Wayback release/capture dates for requested historical quarters.

The inspector pair is a separate 24-row images.csv: after is the latest capture published by the numerical as-of; before is the latest available capture at least 12 months before after. Mixed dates use their maximum. A literal baseline measured only from the 2026Q3 as-of would select the same July 2025 capture for both roles, so the distinct-pair refinement prevents that misleading duplication. Both source releases must be available by as-of; missing baselines remain missing. All 100 states remain in wayback_timeline.csv. The 10 m Sentinel timeline cannot show facade finishing. Finishing detection and road-paving timing were rejected by the earlier experiments; this report does not reinstate those products.

## Method comparison

"""
    report += "| Method | Execution | Result |\n| --- | --- | --- |\n" + "\n".join(f"| {r['method']} | {r['status']} | {r['result']} |" for r in methods)
    report += "\n\n## Per-compound coverage\n\n| Code | Wayback frames | First accepted capture | Last accepted capture | Sentinel quarters |\n| --- | ---: | --- | --- | ---: |\n"
    report += "\n".join(f"| {r.code} | {r.wayback_frames} | {r.wayback_first_capture} | {r.wayback_last_capture} | {r.sentinel_available_quarters} |" for r in comparison.itertuples())
    report += "\n\nPer-compound counts and date spans: `comparison.csv`. Full frame metadata: `wayback_timeline.csv`, `sentinel_quarterly.csv`; source/legal notice: `THIRD_PARTY_IMAGERY.md`; validation: `validation.json`. No unavailable method is assigned a fabricated result.\n"
    (out / "IMAGERY_REPORT.md").write_text(report, encoding="utf-8")
    # The two source tables and report index refer to the APP-relative layout,
    # which is preserved exactly in the standalone ZIP.
    extra = [APP / "images/images.csv"] + [out / name for name in (
        "index.html", "wayback_timeline.csv", "sentinel_quarterly.csv", "comparison.csv", "method_comparison.csv",
        "validation.json", "THIRD_PARTY_IMAGERY.md", "IMAGERY_REPORT.md")]
    for path in extra:
        files[path.relative_to(APP).as_posix()] = path.read_bytes()
    # No machine-specific paths, stored authentication or capability URLs may
    # escape through the metadata/report files.
    forbidden = re.compile(r"(?:[A-Z]:[/\\]|/Users/|access_token=|refresh_token|client_secret|helpful-cipher)")
    for name, data in files.items():
        if Path(name).suffix in {".csv", ".json", ".html", ".md"} and forbidden.search(data.decode("utf-8-sig")):
            raise ValueError("Private path/token marker in delivery: " + name)
    manifest = io.StringIO(newline="")
    writer = csv.DictWriter(manifest, fieldnames=["file", "bytes", "sha256"], lineterminator="\n")
    writer.writeheader()
    for name, data in sorted(files.items()):
        writer.writerow({"file": name, "bytes": len(data), "sha256": digest(data)})
    files["IMAGERY_MANIFEST.csv"] = manifest.getvalue().encode()
    RELEASE.mkdir(parents=True, exist_ok=True)
    if PACKAGE.exists():
        raise FileExistsError("Published snapshot already exists; create a new dated version instead of replacing it")
    with zipfile.ZipFile(PACKAGE, "x", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            archive.writestr(name, data)
    PACKAGE.with_suffix(".zip.sha256.txt").write_text(digest(PACKAGE.read_bytes()) + "  " + PACKAGE.name + "\n", encoding="utf-8")
    verified = packaged_files()
    assert len(verified) == len(files)
    validation["package_files"] = len(files)
    validation["package_bytes"] = PACKAGE.stat().st_size
    validation["package_sha256"] = digest(PACKAGE.read_bytes())
    (BASE_DIR / "data/IMAGERY_VALIDATION.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    for name, target in (("IMAGERY_REPORT.md", "IMAGERY_COMPARISON.md"), ("comparison.csv", "IMAGERY_COVERAGE.csv"),
                         ("method_comparison.csv", "IMAGERY_METHODS.csv")):
        destination = BASE_DIR / "data" / target
        destination.write_bytes((out / name).read_bytes())
    metadata = BASE_DIR / "data/imagery"
    metadata.mkdir(parents=True, exist_ok=True)
    for path in [APP / "images/images.csv"] + [out / name for name in (
        "wayback_timeline.csv", "sentinel_quarterly.csv", "wayback_selected.json", "catalogue_snapshot.json",
        "sentinel_selection.json", "service_item_metadata.json", "THIRD_PARTY_IMAGERY.md")]:
        content = path.read_bytes()
        if forbidden.search(content.decode("utf-8-sig")):
            raise ValueError("Private path/token marker in public metadata: " + path.name)
        (metadata / path.name).write_bytes(content)
    return validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="Build the one-time dated snapshot from validated local figures")
    parser.add_argument("--package", type=Path, default=PACKAGE, help="Controlled local report ZIP to install; never downloaded from Git")
    args = parser.parse_args()
    if args.build:
        print(json.dumps(build(), indent=2))
    else:
        print(f"Installed {install_files(packaged_files(args.package))} imagery report files; open {APP / 'imagery_comparison/index.html'}")


if __name__ == "__main__":
    main()
