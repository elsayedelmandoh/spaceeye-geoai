"""
propose: 12-month sentinel-2 / dynamic world windows ending at every quarter 2018Q1..2026Q3 for the compounds
(recipe of the audited p2_s4_windows.py; windows ending 30 June that the audit already pulled are not repeated).
input: raw/boundaries.geojson, raw/s4_windows_q2.csv. output: raw/s4_windows_compounds.csv.
"""

import ee
import pandas as pd

from src.pipeline.common import N_Q, RAW, qindex
from src.pipeline.pulls.ee_common import feature_collection, geometries, init, retry

OUT = RAW / "s4_windows_compounds.csv"
DWB = ["water", "trees", "grass", "flooded_vegetation", "crops", "shrub_and_scrub", "built", "bare", "snow_and_ice"]


def _mask_qa(im):
    q = im.select("QA60")
    return im.updateMask(q.bitwiseAnd(1 << 10).eq(0).And(q.bitwiseAnd(1 << 11).eq(0)))


def main() -> None:
    init()
    geo = geometries()
    have = pd.read_csv(RAW / "s4_windows_q2.csv", usecols=["pid", "qi"])
    got = set(zip(have.pid, have.qi))
    rows = pd.read_csv(OUT).to_dict("records") if OUT.exists() else []
    got |= {(r["pid"], r["qi"]) for r in rows}
    bb = ee.Geometry.Rectangle([31.55, 29.85, 32.0, 30.15])
    s2c = ee.ImageCollection("COPERNICUS/S2_HARMONIZED").filterBounds(bb)
    dwc = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(bb)
    for qi in range(qindex("2018Q1"), N_Q):
        codes = [c for c in geo if (c, qi) not in got]
        if not codes:
            continue
        en = ee.Date.fromYMD(2016 + (qi + 1) // 4, 1 + 3 * ((qi + 1) % 4), 1)  # first day after the quarter
        st = en.advance(-12, "month")
        flt = s2c.filterDate(st, en).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        n_s2 = retry(flt.size().getInfo)
        med = flt.map(_mask_qa).select(["B2", "B3", "B4", "B8", "B11", "B12"]).median().divide(10000)
        ndvi = med.normalizedDifference(["B8", "B4"]).rename("NDVI")
        ndbi = med.normalizedDifference(["B11", "B8"]).rename("NDBI")
        bsi = med.expression("((B11+B4)-(B8+B2))/((B11+B4)+(B8+B2))", {k: med.select(k) for k in ["B2", "B4", "B8", "B11"]}).rename("BSI")
        s2img = med.addBands([ndvi, ndbi, bsi])
        dcol = dwc.filterDate(st, en).filter(ee.Filter.inList("system:index", flt.aggregate_array("system:index")))
        n_dw = retry(dcol.size().getInfo)
        dimg = dcol.select(DWB).mean()
        fc = feature_collection(codes, geo)
        by = {c: {"pid": c, "qi": qi, "n_s2": n_s2, "n_dw": n_dw} for c in codes}
        for im, sc in [(s2img, 20), (dimg, 10)]:
            res = retry(im.reduceRegions(fc, ee.Reducer.mean(), scale=sc, tileScale=8).getInfo)["features"]
            for f in res:
                by[f["properties"]["pid"]].update({k: v for k, v in f["properties"].items() if k != "pid"})
        rows += list(by.values())
        pd.DataFrame(rows).to_csv(OUT, index=False)
        print(qi, len(codes), n_s2, n_dw, flush=True)


if __name__ == "__main__":
    main()
