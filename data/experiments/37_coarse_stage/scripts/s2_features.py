# ruff: noqa  -- archived experiment script, kept as run
"""Step 2 (PROTOCOL.md, Amendment 1): satellite and OBT height features per block x 12-month window centred on the capture date.
Writes features/ee_window_features.csv (one row per row_id) and features/obt_features.csv (block x OBT year). Codes only."""
import sys
import time
from pathlib import Path

import ee
import pandas as pd

sys.dont_write_bytecode = True
ROOT = Path("F:/ACUD AI Data Lab/Project/real_data/37_coarse_stage")
FEATURE_DIR = ROOT / "features"
EE_PROJECT = __import__("os").environ["SPACEEYE_EE_PROJECT"]
EPSG = 32636
BLOCK_M = 500
SCALE_M = 10
OBT_SCALE_M = 4
HALF_WINDOW_MONTHS = 6
OBT_YEARS = (2017, 2019, 2021, 2023)
PRESENCE_THRESHOLD = 0.5
TALL_M = 20
DW_CLASSES = ["built", "bare", "grass", "trees", "water"]
S2_CLEAR_SCL = [3, 8, 9, 10, 11, 0, 1]  # shadow, cloud, cirrus, snow, no-data, saturated
S2_MAX_CLOUD_PCT = 60
RETRIES = 4


def block_collection(block_ids: list[str]) -> ee.FeatureCollection:
    feats = []
    for block_id in block_ids:
        x, y = (int(v) for v in block_id.split("_"))
        geom = ee.Geometry.Rectangle([x, y, x + BLOCK_M, y + BLOCK_M], f"EPSG:{EPSG}", False)
        feats.append(ee.Feature(geom, {"block_id": block_id}))
    return ee.FeatureCollection(feats)


def dw_mean(start: ee.Date, end: ee.Date) -> ee.Image:
    return ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterDate(start, end).select(DW_CLASSES).mean()


def s2_features(start: ee.Date, end: ee.Date) -> ee.Image:
    def prep(img):
        clear = img.select("SCL").remap(S2_CLEAR_SCL, [0] * len(S2_CLEAR_SCL), 1).neq(0)
        img = img.updateMask(clear).divide(10000)
        return img.select(["B2", "B3", "B4", "B8", "B11"]).addBands(img.normalizedDifference(["B8", "B4"]).rename("ndvi_scene"))

    col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", S2_MAX_CLOUD_PCT))
        .map(prep)
    )
    med = col.median()
    return ee.Image.cat(
        med.normalizedDifference(["B8", "B4"]).rename("s2_ndvi"),
        med.normalizedDifference(["B11", "B8"]).rename("s2_ndbi"),
        med.select(["B2", "B3", "B4"]).reduce(ee.Reducer.mean()).rename("s2_brightness"),
        med.select("B11").divide(med.select("B8")).rename("s2_swir_nir"),
        col.select("ndvi_scene").reduce(ee.Reducer.percentile([90])).rename("s2_ndvi_p90"),
    )


def s1_features(start: ee.Date, end: ee.Date) -> ee.Image:
    col = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterDate(start, end)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.eq("orbitProperties_pass", "ASCENDING"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VV", "VH"])
    )
    med = col.median()
    std = col.reduce(ee.Reducer.stdDev())
    return ee.Image.cat(
        med.select("VV").rename("s1_vv"),
        med.select("VH").rename("s1_vh"),
        med.select("VV").subtract(med.select("VH")).rename("s1_vv_minus_vh"),
        std.select("VV_stdDev").rename("s1_vv_std"),
        std.select("VH_stdDev").rename("s1_vh_std"),
    )


def ntl_mean(start: ee.Date, end: ee.Date) -> ee.Image:
    col = ee.ImageCollection("NASA/VIIRS/002/VNP46A2").filterDate(start, end)
    return col.select("Gap_Filled_DNB_BRDF_Corrected_NTL").mean()


def window_image(capture_date: str) -> ee.Image:
    centre = ee.Date(capture_date)
    start = centre.advance(-HALF_WINDOW_MONTHS, "month")
    end = centre.advance(HALF_WINDOW_MONTHS, "month")
    prev_start = start.advance(-12, "month")
    dw_now, dw_prev = dw_mean(start, end), dw_mean(prev_start, start)
    ntl_now, ntl_prev = ntl_mean(start, end), ntl_mean(prev_start, start)
    return ee.Image.cat(
        dw_now.rename([f"dw_{c}" for c in DW_CLASSES]),
        dw_now.subtract(dw_prev).rename([f"dw_{c}_chg" for c in DW_CLASSES]),
        s2_features(start, end),
        s1_features(start, end),
        ntl_now.rename("ntl"),
        ntl_now.subtract(ntl_prev).rename("ntl_chg"),
    )


def reduce_blocks(image: ee.Image, block_ids: list[str], reducer, scale: int) -> pd.DataFrame:
    fc = block_collection(block_ids)
    for attempt in range(RETRIES):
        try:
            out = image.reduceRegions(fc, reducer, scale=scale, crs=f"EPSG:{EPSG}", tileScale=4).getInfo()
            break
        except ee.EEException as err:
            print("retry", attempt, str(err)[:120], flush=True)
            time.sleep(20 * (attempt + 1))
    else:
        raise RuntimeError("Earth Engine request failed after retries")
    return pd.DataFrame([f["properties"] for f in out["features"]])


def obt_year_features(year: int, block_ids: list[str]) -> pd.DataFrame:
    img = (
        ee.ImageCollection("GOOGLE/Research/open-buildings-temporal/v1")
        .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
        .mosaic()
    )
    present = img.select("building_presence").gte(PRESENCE_THRESHOLD)
    height = img.select("building_height").updateMask(present)
    stack = ee.Image.cat(
        present.rename("h_presence"),
        height.rename("h_mean"),
        height.gte(TALL_M).updateMask(present).rename("h_share_tall"),
    )
    mean_df = reduce_blocks(stack, block_ids, ee.Reducer.mean(), OBT_SCALE_M)
    p90_df = reduce_blocks(height.rename("h_p90"), block_ids, ee.Reducer.percentile([90]), OBT_SCALE_M)
    out = mean_df.merge(p90_df.rename(columns={"p90": "h_p90"})[["block_id", "h_p90"]], on="block_id")
    out["obt_year"] = year
    return out


def main() -> None:
    ee.Initialize(project=EE_PROJECT)
    rows = pd.read_csv(ROOT / "private_key" / "rows.csv")
    FEATURE_DIR.mkdir(exist_ok=True)

    window_path = FEATURE_DIR / "ee_window_features.csv"
    if not window_path.exists():
        parts = []
        for capture_date, group in rows.groupby("capture_date"):
            block_ids = sorted(group.block_id.unique())
            feats = reduce_blocks(window_image(capture_date), block_ids, ee.Reducer.mean(), SCALE_M)
            feats["capture_date"] = capture_date
            parts.append(feats)
            print("window", capture_date, len(block_ids), flush=True)
        windows = pd.concat(parts)
        out = rows[["row_id", "block_id", "target_year", "capture_date"]].merge(windows, on=["block_id", "capture_date"], how="left")
        out.to_csv(window_path, index=False)

    obt_path = FEATURE_DIR / "obt_features.csv"
    if not obt_path.exists():
        block_ids = sorted(rows.block_id.unique())
        pd.concat([obt_year_features(y, block_ids) for y in OBT_YEARS]).to_csv(obt_path, index=False)
        print("obt done", flush=True)


if __name__ == "__main__":
    main()
