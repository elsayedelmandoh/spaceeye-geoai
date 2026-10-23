"""Reference data: zones, roads, buildings, assets, sensors (+ GeoJSON)."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .common import Ctx

# Zone rectangles on a local km grid (x east, y north) — same arrangement as the Day 1 map slide.
ZONE_RECT = {
    "Z01": (0.000, 1.225, 1.800, 2.375),
    "Z02": (0.000, 0.000, 1.800, 1.150),
    "Z03": (1.875, 1.225, 3.375, 2.375),
    "Z04": (1.875, 0.000, 3.375, 1.150),
    "Z05": (3.450, 0.000, 4.600, 2.375),
    "Z06": (4.675, 0.000, 6.000, 2.375),
}
KM_LAT, KM_LON = 110.9, 96.3

# segment_id, name_en, name_ar, zone_id, lanes, speed_limit, x0, y0, x1, y1
ROADS = [
    ("RD-01", "Oasis Boulevard (west)", "شارع الواحة (الغربي)", "Z02", 3, 80, 0.0, 1.19, 1.84, 1.19),
    ("RD-02", "Oasis Boulevard (centre)", "شارع الواحة (الأوسط)", "Z04", 3, 80, 1.84, 1.19, 3.41, 1.19),
    ("RD-03", "Oasis Boulevard (east)", "شارع الواحة (الشرقي)", "Z05", 3, 80, 3.41, 1.19, 6.0, 1.19),
    ("RD-04", "North Ring Road", "الطريق الدائري الشمالي", "Z01", 3, 80, 0.0, 2.375, 6.0, 2.375),
    ("RD-05", "South Ring Road", "الطريق الدائري الجنوبي", "Z02", 3, 80, 0.0, 0.0, 6.0, 0.0),
    ("RD-06", "Government Avenue", "شارع الحكومة", "Z03", 2, 60, 1.84, 1.19, 1.84, 2.375),
    ("RD-07", "Market Street", "شارع السوق", "Z04", 2, 60, 1.84, 0.0, 1.84, 1.19),
    ("RD-08", "Palm Avenue", "شارع النخيل", "Z05", 2, 60, 3.41, 0.0, 3.41, 2.375),
    ("RD-09", "Park Drive", "طريق المتنزه", "Z06", 2, 50, 4.64, 0.0, 4.64, 2.375),
    ("RD-10", "Jasmine Street", "شارع الياسمين", "Z01", 2, 50, 0.6, 1.225, 0.6, 2.375),
    ("RD-11", "Olive Street", "شارع الزيتون", "Z01", 2, 50, 1.2, 1.225, 1.2, 2.375),
    ("RD-12", "Garden Street", "شارع الحديقة", "Z01", 1, 40, 0.0, 1.8, 1.8, 1.8),
    ("RD-13", "Lotus Street", "شارع اللوتس", "Z02", 2, 50, 0.6, 0.0, 0.6, 1.15),
    ("RD-14", "Fountain Street", "شارع النافورة", "Z02", 2, 50, 1.2, 0.0, 1.2, 1.15),
    ("RD-15", "School Street", "شارع المدارس", "Z02", 1, 40, 0.0, 0.58, 1.8, 0.58),
    ("RD-16", "Ministries Street", "شارع الوزارات", "Z03", 2, 60, 1.875, 1.8, 3.375, 1.8),
    ("RD-17", "Council Street", "شارع المجلس", "Z03", 1, 40, 2.6, 1.225, 2.6, 2.375),
    ("RD-18", "Commerce Street", "شارع التجارة", "Z04", 2, 50, 1.875, 0.58, 3.375, 0.58),
    ("RD-19", "Exchange Street", "شارع البورصة", "Z04", 2, 50, 2.6, 0.0, 2.6, 1.15),
    ("RD-20", "Bazaar Street", "شارع البازار", "Z05", 1, 40, 3.45, 0.6, 4.6, 0.6),
    ("RD-21", "Crescent Street", "شارع الهلال", "Z05", 2, 50, 4.0, 0.0, 4.0, 2.375),
    ("RD-22", "Lake Road", "طريق البحيرة", "Z06", 1, 40, 4.675, 1.6, 6.0, 1.6),
    ("RD-23", "Cedar Street", "شارع الأرز", "Z05", 1, 40, 3.45, 1.8, 4.6, 1.8),
    ("RD-24", "Stadium Road", "طريق الملعب", "Z06", 2, 50, 5.4, 0.0, 5.4, 2.375),
]

BUILDING_MIX = {  # zone -> {use_type: count}
    "Z01": {"residential": 90, "school": 4, "mosque": 3, "clinic": 2, "commercial": 3},
    "Z02": {"residential": 80, "school": 4, "mosque": 3, "clinic": 2, "commercial": 3},
    "Z03": {"government": 18, "mosque": 1, "clinic": 1},
    "Z04": {"commercial": 35, "government": 2, "mosque": 1},
    "Z05": {"residential": 45, "commercial": 20, "school": 2, "mosque": 2, "clinic": 2},
    "Z06": {"commercial": 3, "mosque": 1},
}
SENSOR_SPLIT = {
    "traffic": {"Z01": 7, "Z02": 7, "Z03": 6, "Z04": 8, "Z05": 7, "Z06": 5},
    "pressure": {"Z01": 4, "Z02": 4, "Z03": 2, "Z04": 3, "Z05": 4, "Z06": 3},
    "parking": {"Z01": 2, "Z02": 2, "Z03": 3, "Z04": 3, "Z05": 1, "Z06": 1},
    "bins": {"Z01": 35, "Z02": 30, "Z03": 10, "Z04": 25, "Z05": 35, "Z06": 15},
    "cameras": {"Z01": 10, "Z02": 10, "Z03": 8, "Z04": 10, "Z05": 14, "Z06": 8},
    "noise": {"Z01": 1, "Z02": 1, "Z03": 1, "Z04": 2, "Z05": 2, "Z06": 3},
    "air": ["Z01", "Z02", "Z03", "Z04", "Z05", "Z06", "Z04", "Z05"],
    "streetlights": {"Z01": 65, "Z02": 65, "Z03": 55, "Z04": 55, "Z05": 80, "Z06": 80},
    "signals": {"Z01": 3, "Z02": 3, "Z03": 3, "Z04": 4, "Z05": 3, "Z06": 2},
}


def to_latlon(ctx: Ctx, x, y):
    d = ctx.cfg["district"]
    return (np.round(d["origin_lat"] + np.asarray(y) / KM_LAT, 6), np.round(d["origin_lon"] + np.asarray(x) / KM_LON, 6))


def points_in_zone(rng, zone, n, margin=0.06):
    x0, y0, x1, y1 = ZONE_RECT[zone]
    return rng.uniform(x0 + margin, x1 - margin, n), rng.uniform(y0 + margin, y1 - margin, n)


def build_reference(ctx: Ctx) -> dict:
    rng = ctx.rng("reference")
    zcfg = pd.DataFrame(ctx.cfg["district"]["zones"])
    zcfg["area_km2"] = [round((r[2] - r[0]) * (r[3] - r[1]), 3) for r in (ZONE_RECT[z] for z in zcfg.zone_id)]
    zones = zcfg[["zone_id", "name_en", "name_ar", "zone_type", "area_km2", "population_start"]]

    roads = pd.DataFrame(ROADS, columns=["segment_id", "name_en", "name_ar", "zone_id", "lanes", "speed_limit_kmh", "x0", "y0", "x1", "y1"])

    # buildings
    rows = []
    for z, mix in BUILDING_MIX.items():
        for use, n in mix.items():
            xs, ys = points_in_zone(rng, z, n)
            for x, y in zip(xs, ys):
                if use == "residential":
                    floors = int(rng.integers(4, 11)); units = int(floors * rng.integers(3, 7))
                elif use == "government":
                    floors = int(rng.integers(3, 13)); units = int(rng.integers(4, 30))
                elif use == "commercial":
                    floors = int(rng.integers(2, 16)); units = int(rng.integers(2, 40))
                elif use == "school":
                    floors = int(rng.integers(2, 5)); units = int(rng.integers(20, 45))
                elif use == "clinic":
                    floors = int(rng.integers(2, 5)); units = int(rng.integers(6, 20))
                else:  # mosque
                    floors = 1; units = 1
                rows.append((z, use, floors, units, x, y))
    b = pd.DataFrame(rows, columns=["zone_id", "use_type", "floors", "units", "x", "y"])
    b.insert(0, "building_id", [f"B-{i:04d}" for i in range(1, len(b) + 1)])
    b["lat"], b["lon"] = to_latlon(ctx, b.x, b.y)

    # assets + sensors
    assets, sensors = [], []

    def add_asset(aid, atype, pillar, zone, x, y, crit, install):
        assets.append((aid, atype, pillar, zone, x, y, install, crit))

    def add_sensor(sid, stype, pillar, zone, aid, x, y, unit, install, status="active", seg=""):
        sensors.append((sid, stype, pillar, zone, aid, x, y, unit, install, status, seg))

    def install_date():
        return (pd.Timestamp("2023-06-01") + pd.Timedelta(days=int(rng.integers(0, 520)))).strftime("%Y-%m-%d")

    # traffic detectors on road segments
    i = 0
    for z, n in SENSOR_SPLIT["traffic"].items():
        segs = roads[roads.zone_id == z]
        for k in range(n):
            i += 1
            s = segs.iloc[k % len(segs)]
            t = rng.uniform(0.2, 0.8)
            x, y = s.x0 + t * (s.x1 - s.x0), s.y0 + t * (s.y1 - s.y0)
            inst = install_date()
            add_asset(f"DET-{i:03d}", "traffic_detector", "mobility", z, x, y, "medium", inst)
            add_sensor(f"TRF-{i:03d}", "traffic_counter", "mobility", z, f"DET-{i:03d}", x, y, "vehicles/15min", inst, seg=s.segment_id)
    i = 0
    for z, n in SENSOR_SPLIT["signals"].items():
        xs, ys = points_in_zone(rng, z, n)
        for x, y in zip(xs, ys):
            i += 1
            add_asset(f"TSG-{i:02d}", "traffic_signal", "mobility", z, x, y, "high", install_date())
    i = 0
    for z, n in SENSOR_SPLIT["parking"].items():
        xs, ys = points_in_zone(rng, z, n)
        for x, y in zip(xs, ys):
            i += 1
            inst = install_date()
            add_asset(f"PRK-{i:02d}", "parking_lot", "mobility", z, x, y, "low", inst)
            add_sensor(f"LOT-{i:02d}", "parking_counter", "mobility", z, f"PRK-{i:02d}", x, y, "vehicles", inst)
    i = 0
    for z, n in SENSOR_SPLIT["pressure"].items():
        xs, ys = points_in_zone(rng, z, n)
        for x, y in zip(xs, ys):
            i += 1
            inst = install_date()
            add_asset(f"VLV-{i:02d}", "network_valve", "water", z, x, y, "high", inst)
            add_sensor(f"PRS-{i:02d}", "pressure_flow", "water", z, f"VLV-{i:02d}", x, y, "bar; L/s", inst)
    for i, z in enumerate(["Z01", "Z02", "Z03", "Z04", "Z05", "Z06"], 1):
        (x,), (y,) = points_in_zone(rng, z, 1)
        inst = install_date()
        add_asset(f"WQA-{i:02d}", "water_quality_analyser", "water", z, x, y, "high", inst)
        add_sensor(f"WQ-{i:02d}", "water_quality", "water", z, f"WQA-{i:02d}", x, y, "mg/L; NTU; pH", inst)
        add_asset(f"PMP-{i:02d}", "pump", "water", z, x + 0.03, y, "high", install_date())
    i = 0
    for z, n in SENSOR_SPLIT["bins"].items():
        xs, ys = points_in_zone(rng, z, n)
        for x, y in zip(xs, ys):
            i += 1
            inst = install_date()
            add_asset(f"BIN-{i:03d}", "smart_bin", "waste", z, x, y, "low", inst)
            add_sensor(f"FIL-{i:03d}", "fill_level", "waste", z, f"BIN-{i:03d}", x, y, "%; °C", inst)
    i = 0
    for z, n in SENSOR_SPLIT["cameras"].items():
        xs, ys = points_in_zone(rng, z, n)
        for x, y in zip(xs, ys):
            i += 1
            inst = install_date()
            add_asset(f"CAM-{i:03d}", "cctv_camera", "public_safety", z, x, y, "high", inst)
            add_sensor(f"CAM-{i:03d}", "cctv_camera", "public_safety", z, f"CAM-{i:03d}", x, y, "% uptime", inst)
    for i, z in enumerate(SENSOR_SPLIT["air"], 1):
        (x,), (y,) = points_in_zone(rng, z, 1)
        inst = install_date()
        add_asset(f"AQS-{i:02d}", "air_quality_station", "environment", z, x, y, "medium", inst)
        add_sensor(f"AQ-{i:02d}", "air_quality", "environment", z, f"AQS-{i:02d}", x, y, "µg/m³; ppb; °C; %", inst)
    i = 0
    for z, n in SENSOR_SPLIT["noise"].items():
        xs, ys = points_in_zone(rng, z, n)
        for x, y in zip(xs, ys):
            i += 1
            inst = install_date()
            add_asset(f"NSM-{i:02d}", "noise_monitor", "environment", z, x, y, "low", inst)
            add_sensor(f"NSE-{i:02d}", "noise", "environment", z, f"NSM-{i:02d}", x, y, "dB(A)", inst)
    i = 0
    for z, n in SENSOR_SPLIT["streetlights"].items():
        xs, ys = points_in_zone(rng, z, n, margin=0.02)
        for x, y in zip(xs, ys):
            i += 1
            add_asset(f"SL-{i:04d}", "streetlight", "energy", z, x, y, "low", install_date())

    # public buildings with BMS (25): 12 government, 6 schools, 5 clinics, 2 mosques
    pick = []
    for use, n in [("government", 12), ("school", 6), ("clinic", 5), ("mosque", 2)]:
        cand = b[b.use_type == use]
        pick += list(cand.sample(n, random_state=int(rng.integers(10**9))).building_id)
    pick = sorted(pick)
    for bid in pick:
        r = b[b.building_id == bid].iloc[0]
        inst = install_date()
        add_asset(f"HVAC-{bid[2:]}", "hvac_unit", "buildings", r.zone_id, r.x, r.y, "medium", inst)
        add_sensor(f"BMS-{bid[2:]}", "bms", "buildings", r.zone_id, f"HVAC-{bid[2:]}", r.x, r.y, "°C; %; kW; persons", inst)

    # meter subset (stratified; always includes Z02 residential for the H1 story)
    n_m = int(ctx.ed["meter_buildings"])
    if n_m >= len(b):
        meters = list(b.building_id)
    else:
        quota = [("residential", 50), ("commercial", 12), ("government", 8), ("school", 5), ("clinic", 3), ("mosque", 2)]
        meters = []
        for use, n in quota:
            cand = b[b.use_type == use]
            if use == "residential":
                z2 = cand[cand.zone_id == "Z02"].sample(15, random_state=int(rng.integers(10**9)))
                rest = cand.drop(z2.index).sample(n - 15, random_state=int(rng.integers(10**9)))
                meters += list(z2.building_id) + list(rest.building_id)
            else:
                meters += list(cand.sample(n, random_state=int(rng.integers(10**9))).building_id)
        meters = sorted(meters)
    for bid in meters:
        r = b[b.building_id == bid].iloc[0]
        add_sensor(f"EM-{bid[2:]}", "electricity_meter", "energy", r.zone_id, "", r.x, r.y, "kWh", install_date())
        add_sensor(f"WM-{bid[2:]}", "water_meter", "water", r.zone_id, "", r.x, r.y, "m³", install_date())

    A = pd.DataFrame(assets, columns=["asset_id", "asset_type", "pillar", "zone_id", "x", "y", "install_date", "criticality"])
    A["lat"], A["lon"] = to_latlon(ctx, A.x, A.y)
    S = pd.DataFrame(sensors, columns=["sensor_id", "sensor_type", "pillar", "zone_id", "asset_id", "x", "y", "unit", "install_date", "status", "segment_id"])
    S["lat"], S["lon"] = to_latlon(ctx, S.x, S.y)
    # a few devices flagged in maintenance (registry status — not the same as data outages)
    S.loc[S.sensor_id.isin(["NSE-04", "FIL-077", "CAM-031"]), "status"] = "maintenance"

    ctx.ref = {"zones": zones, "roads": roads, "buildings": b, "assets": A, "sensors": S,
               "bms_buildings": pick, "meter_buildings": meters}
    return ctx.ref


def write_reference(ctx: Ctx) -> None:
    d = ctx.ref_dir
    d.mkdir(parents=True, exist_ok=True)
    r = ctx.ref
    kw = dict(index=False, encoding="utf-8", lineterminator="\n")
    r["zones"].to_csv(d / "zones.csv", **kw)
    r["buildings"][["building_id", "zone_id", "use_type", "floors", "units", "lat", "lon"]].to_csv(d / "buildings.csv", **kw)
    r["assets"][["asset_id", "asset_type", "pillar", "zone_id", "lat", "lon", "install_date", "criticality"]].to_csv(d / "assets.csv", **kw)
    r["sensors"][["sensor_id", "sensor_type", "pillar", "zone_id", "asset_id", "lat", "lon", "unit", "install_date", "status", "segment_id"]].to_csv(d / "sensors.csv", **kw)

    feats = []
    for _, z in r["zones"].iterrows():
        x0, y0, x1, y1 = ZONE_RECT[z.zone_id]
        ring = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        lat, lon = to_latlon(ctx, [p[0] for p in ring], [p[1] for p in ring])
        feats.append({"type": "Feature", "properties": {k: (v.item() if hasattr(v, "item") else v) for k, v in z.items()},
                      "geometry": {"type": "Polygon", "coordinates": [[[float(lo), float(la)] for la, lo in zip(lat, lon)]]}})
    (d / "zones.geojson").write_text(json.dumps({"type": "FeatureCollection", "name": "oasis_zones", "features": feats}, ensure_ascii=False, indent=1), encoding="utf-8")

    feats = []
    for _, s in r["roads"].iterrows():
        lat, lon = to_latlon(ctx, [s.x0, s.x1], [s.y0, s.y1])
        props = {k: (s[k].item() if hasattr(s[k], "item") else s[k]) for k in ["segment_id", "name_en", "name_ar", "zone_id", "lanes", "speed_limit_kmh"]}
        feats.append({"type": "Feature", "properties": props,
                      "geometry": {"type": "LineString", "coordinates": [[float(lo), float(la)] for la, lo in zip(lat, lon)]}})
    (d / "roads.geojson").write_text(json.dumps({"type": "FeatureCollection", "name": "oasis_roads", "features": feats}, ensure_ascii=False, indent=1), encoding="utf-8")
