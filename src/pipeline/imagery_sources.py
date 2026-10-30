"""Cached public metadata and supported static-map/COG clients for visual review.

Wayback tilemap requests retrieve update metadata only. Imagery is rendered by
Esri's public Print service; no WMTS tile harvesting or offline tile archive.
"""

import hashlib
import io
import json
import math
import textwrap
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely import transform
from shapely.geometry import Point, Polygon, box

from src.pipeline.common import APP

CONFIG_URL = "https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json"
WAYBACK = "https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer"
PRINT_URL = "https://utility.arcgisonline.com/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task/execute"
STAC = "https://earth-search.aws.element84.com/v1"
WORK = APP / "imagery_work"
WIDTH, HEIGHT = 1024, 768


def cached_request(url, params=None, post=False, binary=False):
    encoded = urllib.parse.urlencode(params or {})
    key = hashlib.sha256((url + "|" + encoded + "|" + str(post)).encode()).hexdigest()
    path = WORK / "requests" / (key + (".bin" if binary else ".json"))
    if path.exists():
        data = path.read_bytes()
        return data if binary else json.loads(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    target = url if post or not encoded else url + "?" + encoded
    request = urllib.request.Request(target, data=encoded.encode() if post else None,
                                     headers={"User-Agent": "SpaceEye-static-map-review/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=120 if post else 60) as response:
                data = response.read()
            value = data if binary else json.loads(data)
            if isinstance(value, dict) and value.get("error"):
                raise RuntimeError(str(value["error"])[:500])
            path.write_bytes(data)
            return value
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def mercator(x, y, z=None):
    return 6378137 * np.radians(x), 6378137 * np.log(np.tan(np.pi / 4 + np.radians(y) / 2))


def inverse_mercator(x, y):
    return np.degrees(x / 6378137), np.degrees(2 * np.arctan(np.exp(y / 6378137)) - np.pi / 2)


def frame_extent(polygon):
    projected = transform(polygon, mercator, interleaved=False)
    x0, y0, x1, y1 = projected.bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    width = max((x1 - x0) * 1.18, (y1 - y0) * 1.18 * WIDTH / HEIGHT)
    height = width * HEIGHT / WIDTH
    return cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2


def sample_points(polygon):
    x0, y0, x1, y1 = polygon.bounds
    points = [polygon.representative_point()]
    for a, b in ((.2, .2), (.2, .8), (.8, .2), (.8, .8)):
        candidate = Point(x0 + a * (x1 - x0), y0 + b * (y1 - y0))
        if polygon.covers(candidate):
            points.append(candidate)
    return points


def tile_coordinates(point, level=18):
    return (int((point.x + 180) / 360 * 2**level),
            int((1 - math.asinh(math.tan(math.radians(point.y))) / math.pi) / 2 * 2**level))


def local_releases(point, catalogue, through):
    ordered = sorted((key for key, value in catalogue.items() if value["itemTitle"][-11:-1] <= through),
                     key=lambda key: catalogue[key]["itemTitle"], reverse=True)
    positions = {key: i for i, key in enumerate(ordered)}
    col, row = tile_coordinates(point)
    release, result, visited = ordered[0], set(), set()
    while release and release not in visited:
        visited.add(release)
        value = cached_request(f"{WAYBACK}/tilemap/{release}/18/{row}/{col}")
        if not value.get("data", [0])[0]:
            break
        selected = str(value.get("select", [release])[0])
        if selected not in positions:
            break
        result.add(selected)
        index = positions[selected] + 1
        release = ordered[index] if index < len(ordered) else None
    return result


def _esri_polygon(rings):
    # Even/odd ring parity preserves multipart footprints and their holes.
    result = Polygon()
    for ring in rings:
        if len(ring) >= 4:
            result = result.symmetric_difference(Polygon(ring).buffer(0))
    return result


def wayback_metadata(polygon, item):
    extent = frame_extent(polygon)
    level = max(0, min(22, 23 - round(math.log2(156543.03392804097 / ((extent[2] - extent[0]) / WIDTH)))))
    viewport = transform(box(*extent), inverse_mercator, interleaved=False)
    geometry = {"rings": [list(map(list, viewport.exterior.coords))], "spatialReference": {"wkid": 4326}}
    value = cached_request(item["metadataLayerUrl"] + f"/{level}/query", {
        "f": "json", "geometry": json.dumps(geometry), "geometryType": "esriGeometryPolygon",
        "inSR": 4326, "outSR": 4326, "outFields": "*", "returnGeometry": "true",
        "spatialRel": "esriSpatialRelIntersects", "orderByFields": "DrawOrder DESC"})
    footprints, dates, providers, resolutions, accuracies = [], set(), set(), set(), set()
    remaining, context_remaining, context_providers = polygon, viewport, set()
    for feature in value.get("features", []):
        attrs = feature["attributes"]
        footprint = _esri_polygon(feature.get("geometry", {}).get("rings", []))
        provider = attrs.get("NICE_DESC") or attrs.get("SRC_DESC") or "Unknown imagery provider"
        context_visible = context_remaining.intersection(footprint)
        if not context_visible.is_empty and context_visible.area / viewport.area >= .0001:
            context_providers.add(provider)
            context_remaining = context_remaining.difference(footprint)
        visible = remaining.intersection(footprint)
        if visible.is_empty or visible.area / polygon.area < .0001:
            continue
        remaining = remaining.difference(footprint)
        stamp = attrs.get("SRC_DATE2")
        date = datetime.fromtimestamp(stamp / 1000, UTC).date().isoformat() if stamp else None
        if date:
            dates.add(date)
        providers.add(provider)
        if attrs.get("SRC_RES") is not None:
            resolutions.add(float(attrs["SRC_RES"]))
        if attrs.get("SRC_ACC") is not None:
            accuracies.add(float(attrs["SRC_ACC"]))
        footprints.append({"capture_date": date, "provider": provider, "source": attrs.get("NICE_NAME"),
                           "area_fraction_approx": visible.area / polygon.area})
    return {"capture_dates": sorted(dates), "providers": sorted(providers), "context_providers": sorted(context_providers),
            "resolution_m": sorted(resolutions), "accuracy_m": sorted(accuracies),
            "metadata_layer": level, "coverage_fraction": max(0, 1 - remaining.area / polygon.area),
            "dated_coverage_fraction": sum(s["area_fraction_approx"] for s in footprints if s["capture_date"]),
            "context_coverage_fraction": max(0, 1 - context_remaining.area / viewport.area),
            "visible_sources": footprints, "metadata_url": item["metadataLayerUrl"]}


def static_wayback_map(polygon, item, attribution="Esri and imagery licensors; see source item"):
    projected = transform(polygon, mercator, interleaved=False)
    extent = frame_extent(polygon)
    layer = {"id": "boundary", "featureCollection": {"layers": [{
        "layerDefinition": {"name": "Coded working boundary", "geometryType": "esriGeometryPolygon",
                            "drawingInfo": {"renderer": {"type": "simple", "symbol": {
                                "type": "esriSFS", "style": "esriSFSNull", "color": [0, 0, 0, 0],
                                "outline": {"type": "esriSLS", "style": "esriSLSSolid", "color": [0, 255, 255, 255], "width": 2}}}}},
        "featureSet": {"geometryType": "esriGeometryPolygon", "spatialReference": {"wkid": 3857},
                       "features": [{"geometry": {"rings": [list(map(list, projected.exterior.coords))]}, "attributes": {}}]}}]}}
    webmap = {"mapOptions": {"extent": dict(zip(("xmin", "ymin", "xmax", "ymax"), extent)) | {"spatialReference": {"wkid": 3857}}},
              "baseMap": {"title": item["itemTitle"], "baseMapLayers": [{"id": "wayback", "layerType": "WebTiledLayer",
                           "templateUrl": item["itemURL"], "title": item["itemTitle"], "copyright": attribution}]},
              "operationalLayers": [layer], "exportOptions": {"outputSize": [WIDTH, HEIGHT], "dpi": 96}}
    response = cached_request(PRINT_URL, {"f": "json", "Web_Map_as_JSON": json.dumps(webmap),
                                         "Format": "JPG", "Layout_Template": "MAP_ONLY"}, post=True)
    url = response["results"][0]["value"]["url"]
    image = Image.open(io.BytesIO(cached_request(url, binary=True))).convert("RGB")
    if image.size != (WIDTH, HEIGHT):
        raise ValueError(f"Unexpected static-map size: {image.size}")
    return image, url


def annotated_figure(image, polygon, extent, title, lines, destination):
    """Scientific map annotation only; source pixels are neither generated nor enhanced."""
    try:
        from matplotlib.font_manager import findfont
        font = ImageFont.truetype(findfont("DejaVu Sans"), 12 if image.width < 900 else 15)
        heading = ImageFont.truetype(findfont("DejaVu Sans"), 18 if image.width < 900 else 22)
    except OSError:
        font, heading = ImageFont.load_default(), ImageFont.load_default()
    width, height = image.size
    wrapped = [part for line in lines for part in textwrap.wrap(str(line), width=90 if width < 900 else 115)]
    top, bottom = 48, max(100, 20 * len(wrapped) + 15)
    result = Image.new("RGB", (width, height + top + bottom), "white")
    result.paste(image, (0, top))
    draw = ImageDraw.Draw(result)
    projected = transform(polygon, mercator, interleaved=False)
    x0, y0, x1, y1 = extent
    coords = [((x - x0) / (x1 - x0) * width, top + (y1 - y) / (y1 - y0) * height)
              for x, y in projected.exterior.coords]
    draw.line(coords, fill=(0, 255, 255), width=3)
    draw.text((12, 10), title, fill="black", font=heading)
    for i, line in enumerate(wrapped):
        draw.text((12, top + height + 8 + i * 20), line, fill="black", font=font)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.save(destination, "JPEG", quality=88)


def stac_candidates(bounds, start, end, collection="sentinel-2-c1-l2a"):
    params = {"collections": collection, "bbox": ",".join(map(str, bounds)),
              "datetime": start + "T00:00:00Z/" + end + "T23:59:59Z", "limit": 100,
              "query": json.dumps({"eo:cloud_cover": {"lt": 25}, "grid:code": {"eq": "MGRS-36RUU"}})}
    value = cached_request(STAC + "/search", params)
    return value.get("features", [])


def calibrate_rgb(values, scale, offset):
    """A fixed physical reflectance display; never a per-scene fitted stretch."""
    reflectance = values.astype(np.float64) * scale + offset
    result = np.rint(np.clip(reflectance / .6, 0, 1) * 255).astype(np.uint8)
    result[values == 0] = 0
    return result


def read_reflectance_window(item, polygons):
    import rasterio
    from rasterio.warp import transform_geom
    from rasterio.windows import from_bounds
    from shapely.geometry import shape
    from shapely.ops import unary_union

    geoms = [transform_geom("EPSG:4326", "EPSG:32636", p.__geo_interface__) for p in polygons]
    bounds = unary_union([shape(g) for g in geoms]).buffer(250).bounds
    channels, calibration, urls = [], {}, {}
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY=2,
                      GDAL_HTTP_RETRY_DELAY=1, GDAL_HTTP_TIMEOUT=60, CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
        for band in ("red", "green", "blue"):
            asset = item["assets"][band]
            metadata = asset.get("raster:bands", [{}])[0]
            if "scale" not in metadata or "offset" not in metadata:
                raise ValueError("Missing explicit source reflectance calibration: " + band)
            with rasterio.open(asset["href"]) as source:
                if source.crs.to_epsg() != 32636:
                    raise ValueError("Unexpected source CRS for R7 scene")
                window = from_bounds(*bounds, transform=source.transform).round_offsets().round_lengths()
                values = source.read(1, window=window, boundless=True, fill_value=0)
                transform_ = source.window_transform(window)
            channels.append(calibrate_rgb(values, metadata["scale"], metadata["offset"]))
            calibration[band] = {"scale": metadata["scale"], "offset": metadata["offset"]}
            urls[band] = asset["href"]
    return np.stack(channels), transform_, calibration, urls


def read_sentinel_window(item, polygons):
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.features import geometry_mask
    from rasterio.warp import transform_geom
    from rasterio.windows import from_bounds

    rgb, transform_, _, _ = read_reflectance_window(item, polygons)
    geoms = [transform_geom("EPSG:4326", "EPSG:32636", p.__geo_interface__) for p in polygons]
    bounds = rasterio.transform.array_bounds(rgb.shape[1], rgb.shape[2], transform_)
    with (rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY=2,
                       GDAL_HTTP_RETRY_DELAY=1, GDAL_HTTP_TIMEOUT=60, CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"),
          rasterio.open(item["assets"]["scl"]["href"]) as source):
        window = from_bounds(*bounds, transform=source.transform)
        scl = source.read(1, window=window, out_shape=rgb.shape[1:], resampling=Resampling.nearest,
                          boundless=True, fill_value=0)
    mask = geometry_mask(geoms, out_shape=rgb.shape[1:], transform=transform_, invert=True)
    bad = np.isin(scl, [0, 1, 3, 8, 9, 10, 11])
    fraction = float(bad[mask].mean()) if mask.any() else 1.0
    quality = []
    for geom in geoms:
        part = geometry_mask([geom], out_shape=rgb.shape[1:], transform=transform_, invert=True)
        quality.append({"bad_fraction": float(bad[part].mean()) if part.any() else 1.0,
                        "valid_fraction": float((scl[part] != 0).mean()) if part.any() else 0.0})
    return rgb, transform_, fraction, quality


def sentinel_figure(rgb, source_transform, extent, source_crs="EPSG:32636", width=640):
    from rasterio.enums import Resampling
    from rasterio.transform import from_bounds
    from rasterio.warp import reproject
    height = round(width * HEIGHT / WIDTH)
    target = np.zeros((3, height, width), dtype=np.uint8)
    for band in range(3):
        reproject(rgb[band], target[band], src_transform=source_transform, src_crs=source_crs,
                  dst_transform=from_bounds(*extent, width, height), dst_crs="EPSG:3857",
                  resampling=Resampling.nearest, src_nodata=0, dst_nodata=0)
    return Image.fromarray(np.moveaxis(target, 0, -1))
