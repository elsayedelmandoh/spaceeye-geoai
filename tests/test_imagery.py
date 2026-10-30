"""Temporal availability, mosaic dates and geometry of observed imagery."""

import json
from datetime import UTC, datetime

import pandas as pd
import pytest
from shapely.geometry import box

from src.inference.tools import get_images
from src.pipeline import imagery_sources as S


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
