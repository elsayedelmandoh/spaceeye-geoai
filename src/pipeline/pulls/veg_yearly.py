"""
propose: sentinel-2 summer vegetation share (NDVI > 0.2, JJAS median, SCL mask, cloud < 15) per compound and year 2019-2026,
same recipe as the audited a4_s2_recompute_ee.py. the audited file only covers 3 compounds, so all 22 are pulled once
(the 3 audited ones double as a check).
input: raw/boundaries.geojson. output: raw/veg_pulled.csv.
"""

import ee
import pandas as pd

from src.pipeline.common import RAW
from src.pipeline.pulls.ee_common import feature_collection, geometries, init, retry

OUT = RAW / "veg_pulled.csv"


def main() -> None:
    init()
    geo = geometries()
    fc = feature_collection(sorted(geo), geo)
    sr = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(fc.geometry().bounds().buffer(1000))
    rows = pd.read_csv(OUT).to_dict("records") if OUT.exists() else []
    done = {r["year"] for r in rows}
    for y in range(2019, 2027):
        if y in done:
            continue
        col = sr.filterDate(f"{y}-06-01", f"{y}-10-01").filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 15))
        col = col.map(lambda im: im.updateMask(im.select("SCL").remap([0, 1, 3, 8, 9, 10, 11], [0] * 7, 1).neq(0)).select(["B2", "B3", "B4", "B8"]))
        nd = col.median().divide(10000).normalizedDifference(["B8", "B4"])
        img = nd.gt(0.2).updateMask(nd.mask()).rename("veg").addBands(nd.rename("ndvi_mean"))
        n = retry(col.size().getInfo)
        res = retry(img.reduceRegions(fc, ee.Reducer.mean(), scale=10, crs="EPSG:32636", tileScale=4).getInfo)["features"]
        rows += [{"code": f["properties"]["pid"], "year": y, "n_scenes": n, "veg_share": f["properties"].get("veg"), "ndvi_mean": f["properties"].get("ndvi_mean")} for f in res]
        pd.DataFrame(rows).to_csv(OUT, index=False)
        print(y, n, flush=True)


if __name__ == "__main__":
    main()
