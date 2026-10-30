# ruff: noqa  -- archived experiment script, kept as run
"""Per compound and year (2016-2025): ALOS PALSAR-2 L-band (HH, HV), Sentinel-1 C-band (VV, VH), Dynamic World (built, bare, green),
Sentinel-2 (NDVI, NDBI) and VIIRS night lights, averaged inside each polygon. Descriptive context for the stage table, not a model."""
import json

import ee
import pandas as pd

ee.Initialize(project=__import__("os").environ["SPACEEYE_EE_PROJECT"])
feats = []
for path, key in ((r"F:/ACUD AI Data Lab/Project/app_data/real/compound_boundaries.geojson", "code"),
                  (r"F:/ACUD AI Data Lab/Project/real_data/41_completed_reference/c25_boundary.geojson", "code")):
    for f in json.load(open(path, encoding="utf-8"))["features"]:
        feats.append(ee.Feature(ee.Geometry(f["geometry"]), {"code": f["properties"][key]}))
fc = ee.FeatureCollection(feats)


def s2mask(img):
    scl = img.select("SCL")
    return img.updateMask(scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7)))


rows = []
for y in range(2016, 2026):
    a, b = f"{y}-01-01", f"{y + 1}-01-01"
    bands = []
    palsar = ee.ImageCollection("JAXA/ALOS/PALSAR/YEARLY/SAR_EPOCH").filterDate(a, b)
    if palsar.size().getInfo():
        p = palsar.first().select(["HH", "HV"]).float()
        bands.append(p.pow(2).log10().multiply(10).subtract(83).rename(["palsar_hh_db", "palsar_hv_db"]))
    s1 = ee.ImageCollection("COPERNICUS/S1_GRD").filterDate(a, b).filterBounds(fc).filter(ee.Filter.eq("instrumentMode", "IW")).filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH")).select(["VV", "VH"])
    bands.append(s1.median().rename(["s1_vv_db", "s1_vh_db"]))
    dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterDate(a, b).filterBounds(fc).select(["built", "bare", "grass", "trees", "shrub_and_scrub"]).mean()
    bands.append(dw.select(["built", "bare"]).rename(["dw_built", "dw_bare"]))
    bands.append(dw.select("grass").add(dw.select("trees")).add(dw.select("shrub_and_scrub")).rename("dw_green"))
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterDate(a, b).filterBounds(fc).map(s2mask).median()
    bands.append(s2.normalizedDifference(["B8", "B4"]).rename("s2_ndvi"))
    bands.append(s2.normalizedDifference(["B11", "B8"]).rename("s2_ndbi"))
    ntl = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG").filterDate(a, b).select("avg_rad").mean().rename("viirs_rad")
    bands.append(ntl)
    img = ee.Image.cat(bands)
    out = img.reduceRegions(fc, ee.Reducer.mean(), scale=10).getInfo()
    for f in out["features"]:
        rows.append({"year": y} | f["properties"])
    print(y, flush=True)
d = pd.DataFrame(rows)
d.to_csv("r7_sat_radar_series.csv", index=False)
print(d.groupby("year")[[c for c in d.columns if c not in ("code", "year")]].median().round(2).to_string())
