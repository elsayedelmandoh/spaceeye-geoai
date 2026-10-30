"""Temporal availability, mosaic dates and geometry of observed imagery."""

import json
from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from src.inference.tools import get_images
from src.pipeline import imagery_sources as S


def test_fixed_reflectance_display_respects_source_offsets_and_nodata():
    dn = np.array([0, 1000, 4000, 7000, 10000], dtype=np.uint16)
    rgb = S.calibrate_rgb(dn, .0001, -.1)
    assert rgb[0] == 0 and rgb[1] == 0
    assert abs(int(rgb[2]) - 128) <= 1
    assert rgb[3] == 255 and rgb[4] == 255


def test_capture_age_is_completed_calendar_months_and_rejects_future():
    from src.pipeline.imagery_contract import capture_age_months
    assert capture_age_months("2025-07-23", "2026-09-30") == 14
    assert capture_age_months("2025-07-23", "2026-09-22") == 13
    with pytest.raises(ValueError, match="later"):
        capture_age_months("2026-10-29", "2026-09-30")


@pytest.mark.parametrize("bad,valid,expected", [(0, 1, True), (.1, .95, True), (.06, .94, False), (.11, 1, False)])
def test_sentinel_screen_requires_bad_and_valid_coverage(bad, valid, expected):
    from src.pipeline.imagery_compare import sentinel_quality_ok
    assert sentinel_quality_ok([{"bad_fraction": bad, "valid_fraction": valid}]) is expected


@pytest.mark.parametrize("date,valid,reason", [
    ("2026-10-29", 1, "outside the requested observation window"),
    ("2026-10-05", .94, "coverage requirements"),
])
def test_recorded_json_only_scene_cannot_bypass_cutoff_or_coverage(tmp_path, monkeypatch, date, valid, reason):
    from src.pipeline import imagery_compare as C
    monkeypatch.setattr(C, "START", "2026-10-01")
    monkeypatch.setattr(C, "OUT", tmp_path / "imagery_comparison")
    monkeypatch.setattr(C, "APP", tmp_path)
    info = {"capture_date": date, "quality_by_code": {"C01": {"bad_fraction": .06, "valid_fraction": valid}}}
    C.save_json(C.OUT / "sentinel_scenes/2026Q4.json", info)
    monkeypatch.setattr(C, "restore_selected_sentinel", lambda saved, polygons: (np.zeros((3, 4, 4)), None, saved))
    rows = C.quarterly_sentinel({"C01": box(31.7, 29.95, 31.71, 29.96)}, "2026-10-10")
    assert rows[0]["status"] == "unavailable" and reason in rows[0]["reason"]
    assert not (C.OUT / "sentinel_scenes/2026Q4.npz").exists()


def test_provider_rename_and_republication_do_not_inflate_capture_counts():
    from src.pipeline.imagery_compare import distinct_capture_states
    rows = [
        {"code": "C01", "capture_dates": ["2025-04-08"], "providers": ["New name"], "release_date": "2026-01-01"},
        {"code": "C01", "capture_dates": ["2025-04-08"], "providers": ["Old name"], "release_date": "2025-09-04"},
        {"code": "C01", "capture_dates": ["2025-07-23"], "providers": ["New name"], "release_date": "2026-09-24"},
    ]
    kept = distinct_capture_states(rows)
    assert len(kept) == 2
    assert kept[0]["release_date"] == "2025-09-04"


def test_pair_uses_a_distinct_year_old_capture_and_respects_publication():
    from src.pipeline.imagery_compare import inspection_pair
    rows = [
        {"capture_dates": ["2020-01-01"], "release_date": "2020-06-01"},
        {"capture_dates": ["2023-07-01", "2024-07-01"], "release_date": "2024-08-01"},
        {"capture_dates": ["2024-08-01"], "release_date": "2024-09-01"},
        {"capture_dates": ["2025-07-23"], "release_date": "2025-09-04"},
        {"capture_dates": ["2026-03-01"], "release_date": "2026-12-01"},
    ]
    pair = inspection_pair(rows, "2026-09-30")
    assert pair["after"] is rows[3]
    assert pair["before"] is rows[1]
    assert inspection_pair([rows[3]], "2026-09-30") == {"after": rows[3]}
    assert inspection_pair(rows, "2019-12-31") == {}


def test_configured_end_comes_from_asof_and_pair_csv_has_inspector_schema(tmp_path, monkeypatch):
    from PIL import Image

    from src.pipeline import imagery_compare as C
    monkeypatch.setattr(C, "APP", tmp_path)
    monkeypatch.setattr(C, "OUT", tmp_path / "imagery_comparison")
    monkeypatch.setattr(C, "CFG", {"asof": "2026Q3"})
    assert C.configured_through() == "2026-09-30"
    selected = []
    catalogue = {}
    for n, date in enumerate(["2020-01-01", "2023-07-01", "2024-08-01", "2025-07-23"]):
        selected.append({"code": "C01", "release_id": str(n), "release_date": date,
                         "capture_dates": [date], "providers": ["Provider"], "metadata_url": "https://example.invalid/meta",
                         "coverage_fraction": 1, "dated_coverage_fraction": 1,
                         "resolution_m": [.3], "accuracy_m": [5]})
        catalogue[str(n)] = {"itemID": "item" + str(n)}
    C.save_json(C.OUT / "wayback_selected.json", selected)
    C.save_json(C.OUT / "catalogue_snapshot.json", catalogue)
    monkeypatch.setattr(S, "cached_request", lambda *args: {"accessInformation": "Esri; provider"})
    monkeypatch.setattr(S, "static_wayback_map", lambda *args: (Image.new("RGB", (40, 30), "white"), None))
    timeline = C.wayback_render({"C01": box(31.7, 29.95, 31.71, 29.96)})
    frame = pd.read_csv(tmp_path / "images/images.csv")
    assert {"code", "role", "capture_date", "publication_date", "source", "resolution_m", "attribution"} <= set(frame.columns)
    assert frame.role.tolist() == ["before", "after"]
    assert frame.capture_date.tolist() == ["2023-07-01", "2025-07-23"]
    assert frame.path.tolist() == ["images/C01_before.jpg", "images/C01_after.jpg"]
    assert frame.capture_age_months_at_asof.tolist()[-1] == 14
    assert len(timeline) == 4


def test_map_extent_has_fixed_aspect_and_contains_the_whole_compound():
    polygon = box(31.70, 29.95, 31.71, 29.97)
    x0, y0, x1, y1 = S.frame_extent(polygon)
    assert (x1 - x0) / (y1 - y0) == pytest.approx(S.WIDTH / S.HEIGHT)
    from shapely import transform
    assert box(x0, y0, x1, y1).covers(transform(polygon, S.mercator, interleaved=False))


def test_esri_footprint_holes_are_not_reported_as_image_coverage():
    outer = list(box(0, 0, 4, 4).exterior.coords)
    hole = list(box(1, 1, 3, 3).exterior.coords)
    footprint = S._esri_polygon([outer, hole])
    assert footprint.area == 12
    assert not footprint.covers(box(1.5, 1.5, 2, 2))


def test_visible_mosaic_dates_preserve_two_sources_and_draw_order(monkeypatch):
    polygon = box(31.70, 29.95, 31.71, 29.96)
    left = box(31.70, 29.95, 31.705, 29.96)
    def feature(geometry, date, provider):
        stamp = int(datetime.fromisoformat(date).replace(tzinfo=UTC).timestamp() * 1000)
        return {"attributes": {"SRC_DATE2": stamp, "NICE_DESC": provider, "SRC_RES": .3, "SRC_ACC": 8},
                "geometry": {"rings": [list(geometry.exterior.coords)]}}
    # New footprint covers the left half. The older whole-area footprint is
    # counted only on the still-visible right half, not double-counted.
    monkeypatch.setattr(S, "cached_request", lambda *args, **kwargs: {"features": [
        feature(left, "2025-07-23", "Provider A"), feature(polygon, "2025-04-08", "Provider B")]})
    result = S.wayback_metadata(polygon, {"metadataLayerUrl": "https://example.invalid/metadata"})
    assert result["capture_dates"] == ["2025-04-08", "2025-07-23"]
    assert result["coverage_fraction"] == pytest.approx(1)
    assert result["dated_coverage_fraction"] == pytest.approx(1)
    assert sum(r["area_fraction_approx"] for r in result["visible_sources"]) == pytest.approx(1)


def test_timeline_tool_keeps_stages_and_filters_by_release_not_capture(tmp_path):
    path = tmp_path / "images.csv"
    pd.DataFrame([
        {"code": "C01", "image_type": "after", "sequence": 3, "capture_date": "2023-01-01", "capture_date_max": "2023-01-01",
         "release_date": "2025-01-01", "attribution": "Esri; source", "path": "images/after.jpg", "capture_dates": '["2023-01-01"]'},
        {"code": "C01", "image_type": "before", "sequence": 1, "capture_date": "2020-01-01", "capture_date_max": "2020-01-01",
         "release_date": "2020-06-01", "attribution": "Esri; source", "path": "images/before.jpg", "capture_dates": '["2020-01-01"]'},
        {"code": "C01", "image_type": "stage_02", "sequence": 2, "capture_date": None, "capture_date_min": "2021-01-01", "capture_date_max": "2021-07-01",
         "release_date": "2022-01-01", "attribution": "Esri; sources", "path": "images/stage.jpg", "capture_dates": '["2021-01-01","2021-07-01"]'},
    ]).to_csv(path, index=False)
    old = get_images("C01", path, quarter="2023Q4")
    assert [r["image_type"] for r in old["images"]] == ["before", "stage_02"]
    assert old["images"][1]["capture_date"] is None
    assert old["images"][1]["capture_dates"] == ["2021-01-01", "2021-07-01"]
    assert [r["image_type"] for r in get_images("C01", path)["images"]] == ["before", "stage_02", "after"]
    assert get_images("C01", path, quarter="2019Q4")["status"] == "missing"


def test_historical_view_does_not_invent_missing_publication_dates(tmp_path):
    path = tmp_path / "images.csv"
    pd.DataFrame([{"code": "C01", "image_type": "before", "capture_date": "2020-01-01",
                   "path": "images/before.jpg", "attribution": "source"}]).to_csv(path, index=False)
    assert get_images("C01", path, quarter="2021Q1")["status"] == "missing"


def test_stac_scene_search_has_exact_period_and_explicit_cloud_filter(monkeypatch):
    seen = {}
    def fake(url, params):
        seen.update(params)
        return {"features": [{"id": "real-scene-id"}]}
    monkeypatch.setattr(S, "cached_request", fake)
    assert S.stac_candidates((31.7, 29.9, 31.8, 30), "2023-01-01", "2023-03-31")[0]["id"] == "real-scene-id"
    assert seen["datetime"] == "2023-01-01T00:00:00Z/2023-03-31T23:59:59Z"
    assert json.loads(seen["query"])["eo:cloud_cover"]["lt"] == 25


def test_html_images_are_embedded_only_when_rendered_and_cannot_read_outside_data(tmp_path, monkeypatch):
    from PIL import Image

    from src.inference import imagery_html
    monkeypatch.setattr(imagery_html, "APP", tmp_path)
    path = tmp_path / "images/C01_stage_02.jpg"
    path.parent.mkdir()
    Image.new("RGB", (8, 8), "white").save(path)
    payload = {"status": "available", "images": [{"image_type": "stage_02", "path": "images/C01_stage_02.jpg",
        "capture_date": None, "capture_dates": ["2023-02-10", "2023-07-29"], "release_date": "2024-08-15",
        "attribution": "Esri <source>", "source_url": "https://example.invalid/item",
        "capture_age_months_at_asof": 14, "asof_date": "2026-09-30"}]}
    markup = imagery_html.render_imagery_html(payload)
    assert "data:image/jpeg;base64," in markup
    assert "2023-02-10 / 2023-07-29 (mixed capture dates)" in markup
    assert "Esri &lt;source&gt;" in markup
    assert "latest capture 14 completed months before as-of 2026-09-30" in markup
    assert "base64" not in json.dumps(payload)
    payload["images"][0]["path"] = "../outside.jpg"
    assert "data:image" not in imagery_html.render_imagery_html(payload)


def test_restored_context_builder_passes_its_cutoff_to_the_image_tool(monkeypatch):
    from src.inference import tools
    seen = {}
    monkeypatch.setattr(tools, "get_facts", lambda *args: {"cutoff_date": "2020-12-31"})
    monkeypatch.setattr(tools, "get_kpis", lambda *args: {})
    monkeypatch.setattr(tools, "get_complaints_summary", lambda *args: {})
    monkeypatch.setattr(tools, "get_rules", list)
    def fake_images(code, quarter):
        seen["quarter"] = quarter
        return {"status": "missing", "images": []}
    monkeypatch.setattr(tools, "get_images", fake_images)
    tools.build_inspection_context("C01", "2020Q4")
    assert seen["quarter"] == "2020Q4"


def test_prepared_imagery_install_checks_members_before_writing(tmp_path):
    import csv
    import hashlib
    import io
    import zipfile

    from src.pipeline.imagery_delivery import packaged_files
    package = tmp_path / "small.zip"
    data = b"code,image_type\nC01,before\n"
    manifest = io.StringIO()
    writer = csv.DictWriter(manifest, fieldnames=["file", "bytes", "sha256"], lineterminator="\n")
    writer.writeheader()
    writer.writerow({"file": "images/images.csv", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("IMAGERY_MANIFEST.csv", manifest.getvalue())
        archive.writestr("images/images.csv", data)
    package.with_suffix(".zip.sha256.txt").write_text(hashlib.sha256(package.read_bytes()).hexdigest())
    target = tmp_path / "new-device/app_data"
    planned = packaged_files(package, app=target)
    assert planned[target / "images/images.csv"] == data
    assert not target.exists()
    package.with_suffix(".zip.sha256.txt").write_text("0" * 64)
    with pytest.raises(ValueError, match="ZIP hash differs"):
        packaged_files(package, app=target)


def _layers(coarse_dates, coarse_coverage, full_dates, full_coverage):
    return {6: {"capture_dates": coarse_dates, "dated_coverage_fraction": coarse_coverage},
            5: {"capture_dates": full_dates, "dated_coverage_fraction": full_coverage}}


@pytest.mark.parametrize("layers,expected", [
    (_layers(["2018-08-18"], 1.0, [], 0), "2018-08-18"),
    (_layers(["2018-08-18"], 1.0, ["2018-08-18"], 1.0), "2018-08-18"),
    (_layers(["2018-08-18"], 1.0, ["2019-10-06"], 0.26), None),
    (_layers(["2018-08-18"], 1.0, ["2018-08-18"], 0.26), None),
    (_layers(["2018-08-18", "2019-10-06"], 1.0, [], 0), None),
    (_layers(["2018-08-18"], 0.5, [], 0), None),
])
def test_extra_frame_needs_one_capture_over_the_whole_compound(layers, expected):
    from src.pipeline.imagery_figures import single_capture
    assert single_capture(layers) == expected
