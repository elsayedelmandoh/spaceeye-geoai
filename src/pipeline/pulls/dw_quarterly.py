"""
propose: dynamic world quarterly built_prob_mean for compounds with missing quarters (the 2 new boundaries), same method as the audit
(sentinel-2 cloud < 20 id filter, 10 m). skips what raw/dw_compounds_quarterly.csv already has.
input: raw/boundaries.geojson, raw/dw_compounds_quarterly.csv. output: raw/dw_compounds_new.csv.
"""

import ee
import pandas as pd

from src.pipeline.common import N_Q, RAW
from src.pipeline.pulls.ee_common import feature_collection, geometries, init, retry

OUT = RAW / "dw_compounds_new.csv"


def main() -> None:
    init()
    geo = geometries()
    have = pd.read_csv(RAW / "dw_compounds_quarterly.csv")
    done = pd.read_csv(OUT) if OUT.exists() else pd.DataFrame(columns=["code", "qi"])
    got = set(zip(have.code, have.qi)) | set(zip(done.code, done.qi))
    todo = {qi: [c for c in geo if (c, qi) not in got] for qi in range(N_Q)}
    rows = done.to_dict("records")
    allc = sorted({c for v in todo.values() for c in v})
    if not allc:
        return print("nothing to pull")
    bounds = feature_collection(allc, geo).geometry().bounds().buffer(2000)
    dw_all = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(bounds)
    s2 = ee.ImageCollection("COPERNICUS/S2_HARMONIZED").filterBounds(bounds)
    for qi, codes in todo.items():
        if not codes:
            continue
        start = ee.Date.fromYMD(2016 + qi // 4, 1 + 3 * (qi % 4), 1)
        ok_ids = s2.filterDate(start, start.advance(3, "month")).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).aggregate_array("system:index")
        col = dw_all.filterDate(start, start.advance(3, "month")).filter(ee.Filter.inList("system:index", ok_ids))
        img = col.select("built").mean().rename("pm")
        fc = feature_collection(codes, geo)
        res = retry(img.reduceRegions(fc, ee.Reducer.mean().setOutputs(["pm"]), scale=10, tileScale=8).getInfo)["features"]
        n = retry(col.size().getInfo)
        rows += [{"code": f["properties"]["pid"], "qi": qi, "n_images": n, "built_prob_mean": f["properties"].get("pm")} for f in res]
        pd.DataFrame(rows).to_csv(OUT, index=False)
        print(qi, n, flush=True)


if __name__ == "__main__":
    main()
