"""Small existing-account Sentinel thumbnail fallback for missing public-COG periods.

No sign-in, account creation, project switching or quota workaround is performed.
Returned pixels are retrospective visual context, never fitted model features.
"""

import io
import math
import os

import numpy as np
from PIL import Image
from shapely.ops import unary_union

from src.pipeline import imagery_sources as S

_READY = False


def thumbnail_window(polygons, start, end):
    import ee
    from rasterio.transform import from_bounds

    global _READY
    project = os.environ.get("SPACEEYE_EE_PROJECT")
    if not project:
        raise RuntimeError("Earth Engine fallback needs an existing account and SPACEEYE_EE_PROJECT; no account is created automatically")
    if not _READY:
        ee.Initialize(project=project)
        ee.data.setDeadline(60000)
        _READY = True
    union = unary_union(list(polygons.values()))
    region = ee.Geometry.Rectangle(list(union.bounds), geodesic=False)
    end_exclusive = ee.Date(end).advance(1, "day")
    collection_name = "COPERNICUS/S2_SR_HARMONIZED"
    collection = (ee.ImageCollection(collection_name).filterBounds(region).filterDate(start, end_exclusive)
                  .filter(ee.Filter.eq("MGRS_TILE", "36RUU")).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 25)))
    toa = collection.size().getInfo() == 0
    if toa:
        collection_name = "COPERNICUS/S2_HARMONIZED"
        collection = (ee.ImageCollection(collection_name).filterBounds(region).filterDate(start, end_exclusive)
                      .filter(ee.Filter.eq("MGRS_TILE", "36RUU")).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 25)))
    ids = collection.sort("system:time_start", False).limit(3).aggregate_array("system:id").getInfo()
    if not ids:
        raise ValueError("No Sentinel scene available in Earth Engine for this period")
    features = ee.FeatureCollection([ee.Feature(ee.Geometry(p.__geo_interface__), {"code": code})
                                    for code, p in polygons.items()])
    for asset in ids:
        image = ee.Image(asset)
        if toa:
            qa = image.select("QA60")
            bad = qa.bitwiseAnd(1 << 10).neq(0).Or(qa.bitwiseAnd(1 << 11).neq(0))
        else:
            scl = image.select("SCL")
            bad = scl.eq(0)
            for value in [1, 3, 8, 9, 10, 11]:
                bad = bad.Or(scl.eq(value))
        quality_image = bad.rename("bad").unmask(1).addBands(image.select("B4").mask().rename("valid").unmask(0))
        measurements = quality_image.reduceRegions(collection=features, reducer=ee.Reducer.mean(), scale=60).getInfo()
        quality = {f["properties"]["code"]: {
            "bad_fraction": float(f["properties"].get("bad") or 0),
            "valid_fraction": float(f["properties"].get("valid") or 0)} for f in measurements["features"]}
        if any(q["bad_fraction"] > .10 or q["valid_fraction"] < .95 for q in quality.values()):
            continue
        meta = image.toDictionary(["system:time_start", "CLOUDY_PIXEL_PERCENTAGE", "PRODUCT_ID"]).getInfo()
        import pandas as pd
        date = pd.to_datetime(meta["system:time_start"], unit="ms", utc=True).date().isoformat()
        extent = S.frame_extent(union)
        display_resolution = 10 / math.cos(math.radians(union.centroid.y))
        width = max(1, round((extent[2] - extent[0]) / display_resolution))
        height = max(1, round((extent[3] - extent[1]) / display_resolution))
        visual = image.select(["B4", "B3", "B2"]).visualize(min=0, max=3000, gamma=1.2)
        thumbnail = visual.getThumbURL({"region": ee.Geometry.Rectangle(list(extent), proj="EPSG:3857", geodesic=False),
                                       "dimensions": f"{width}x{height}", "crs": "EPSG:3857", "format": "png"})
        rgb_image = Image.open(io.BytesIO(S.cached_request(thumbnail, binary=True))).convert("RGB")
        rgb = np.moveaxis(np.asarray(rgb_image), -1, 0)
        info = {"scene_id": asset, "capture_date": date, "collection": collection_name,
                "product_created": None, "product_id": meta.get("PRODUCT_ID"),
                "source_crs": "EPSG:3857", "resolution_m": 10, "method": "earth_engine_existing_account_thumbnail",
                "local_bad_fraction": max(q["bad_fraction"] for q in quality.values()),
                "quality_by_code": quality, "tile_cloud_percent": meta.get("CLOUDY_PIXEL_PERCENTAGE"),
                "product_level": "L1C TOA" if toa else "L2A surface reflectance",
                "quality_method": "QA60 cloud/cirrus at 60 m; shadows not classified" if toa else "SCL classes sampled at 60 m",
                "visualization": "RGB B4/B3/B2; fixed min 0, max 3000, gamma 1.2",
                "visual_url": "https://developers.google.com/earth-engine/datasets/catalog/" + collection_name.replace("/", "_"),
                "note": "Retrospective visual thumbnail. L1C/TOA and L2A surface reflectance have different processing; no quantitative colour-change claim. No thumbnail access capability is published."}
        return rgb, from_bounds(*extent, rgb_image.width, rgb_image.height), info
    raise ValueError("Earth Engine candidate scenes failed per-compound cloud/coverage checks")
