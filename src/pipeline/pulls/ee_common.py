"""
propose: shared helpers for the earth engine pulls (restricted mode: batch, cache, no repeats).
input: app_data/raw/boundaries.geojson (codes only).
output: ee session, compound geometries by code, retry wrapper.
"""

import json
import os
import time
import warnings

import ee

from src.pipeline.common import RAW

warnings.filterwarnings("ignore")


def init() -> None:
    project = os.environ.get("SPACEEYE_EE_PROJECT")
    if not project:
        raise RuntimeError("Set SPACEEYE_EE_PROJECT to your Earth Engine-enabled Google Cloud project, "
                           "then authenticate with earthengine authenticate. Cached review needs no Earth Engine account.")
    ee.Initialize(project=project)


def geometries() -> dict[str, dict]:
    feats = json.loads((RAW / "boundaries.geojson").read_text(encoding="utf-8"))["features"]
    return {f["properties"]["code"]: f["geometry"] for f in feats}


def retry(fn, tries: int = 4, wait: int = 10):
    for i in range(tries):
        try:
            return fn()
        except (ee.EEException, OSError) as e:
            print("retry", i, str(e)[:100], flush=True)
            time.sleep(wait)
    raise RuntimeError("earth engine call failed")


def feature_collection(codes: list[str], geo: dict[str, dict]) -> "ee.FeatureCollection":
    return ee.FeatureCollection([ee.Feature(ee.Geometry(geo[c]), {"pid": c}) for c in codes])
