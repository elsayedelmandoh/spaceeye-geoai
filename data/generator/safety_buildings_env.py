"""Public safety (incidents, camera_status), Buildings (bms_readings, work_orders), Environment (air_quality, noise)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import defects as D
from . import profiles as P
from .calendar import day_features
from .common import Ctx, fmt_ts, interp_profile, real_local, tag, time_grid, write_dataset
from .energy_water import hourly_temp
from .mobility import by_daytype, long_frame

ZONE_INC = {"Z01": 9, "Z02": 8, "Z03": 4, "Z04": 10, "Z05": 24, "Z06": 6}   # incidents per day (base)
INC_TYPES = {  # type: (weight, {source: p}, severity probs [1,2,3,4])
    "traffic_accident":   (0.20, {"CCTV": .45, "call": .35, "patrol": .15, "sensor": .05}, [.03, .30, .55, .12]),
    "illegal_parking":    (0.22, {"CCTV": .62, "patrol": .33, "call": .05}, [0, 0, .10, .90]),
    "vandalism":          (0.08, {"CCTV": .55, "patrol": .25, "call": .20}, [0, .05, .45, .50]),
    "suspicious_activity": (0.10, {"CCTV": .62, "patrol": .23, "call": .15}, [0, .10, .70, .20]),
    "fire_alarm":         (0.04, {"sensor": .62, "call": .38}, [.25, .55, .20, 0]),
    "medical_emergency":  (0.08, {"call": .85, "patrol": .15}, [.10, .70, .20, 0]),
    "road_hazard":        (0.12, {"patrol": .40, "CCTV": .30, "call": .30}, [0, .15, .60, .25]),
    "crowd_gathering":    (0.06, {"CCTV": .70, "patrol": .30}, [0, .05, .60, .35]),
    "utility_failure":    (0.10, {"sensor": .60, "call": .40}, [.05, .35, .45, .15]),
}
SEV_RESP = {1: 8, 2: 12, 3: 20, 4: 45}
ACTIVITY = np.array([.25, .18, .12, .10, .10, .15, .35, .70, .95, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.05, 1.1, 1.15, 1.15, 1.1, 1.0, .85, .6, .4])


def incidents(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng("incidents")
    cfg = ctx.cfg
    types = list(INC_TYPES)
    tw = np.array([INC_TYPES[t][0] for t in types]); tw = tw / tw.sum()
    h8 = cfg["stories"]["H8"]; h8s, h8e = pd.Timestamp(str(h8["start"])), pd.Timestamp(str(h8["end"]))
    rows = []
    for d, c in ctx.cal.loc[ctx.start:ctx.end].iterrows():
        for z, base in ZONE_INC.items():
            lam = base * c.growth ** 0.7
            if c.is_weekend or c.is_holiday:
                lam *= {"Z06": 1.5, "Z03": 0.4, "Z04": 0.6}.get(z, 1.0)
            if c.is_eid and z == "Z06":
                lam *= 1.4
            n = rng.poisson(lam)
            for _ in range(n):
                t = types[rng.choice(len(types), p=tw)]
                srcs = dict(INC_TYPES[t][1])
                if z == "Z05" and "CCTV" in srcs:          # Z05 is the most densely covered zone
                    srcs["CCTV"] *= 1.6
                pv = np.array(list(srcs.values())); pv = pv / pv.sum()
                src = rng.choice(list(srcs), p=pv)
                if z == "Z05" and h8s <= d <= h8e and src == "CCTV" and rng.random() < 0.62:
                    continue                                        # H8: cameras down — these are never seen
                hour = rng.choice(24, p=ACTIVITY / ACTIVITY.sum())
                rows.append((d + pd.Timedelta(hours=int(hour), minutes=int(rng.integers(0, 60))), z, t, src, "", ""))
            # dust storms: extra road incidents
            if c.dust > 0:
                for _ in range(rng.poisson(base * 0.25 * c.dust * 4)):
                    t = rng.choice(["traffic_accident", "road_hazard"])
                    srcs = INC_TYPES[t][1]
                    src = rng.choice(list(srcs), p=list(srcs.values()))
                    hour = int(rng.integers(8, 19))
                    rows.append((d + pd.Timedelta(hours=hour, minutes=int(rng.integers(0, 60))), z, t, src, "", c.dust_story))
    df = pd.DataFrame(rows, columns=["timestamp", "zone_id", "type", "source", "_dq", "_story"])
    sev = [rng.choice([1, 2, 3, 4], p=INC_TYPES[t][2]) for t in df.type]
    df["severity"] = sev
    # H5 story rows: every incident on the dust-storm dates
    h5d = [pd.Timestamp(str(x)) for x in cfg["stories"]["H5"]["dates"]]
    df.loc[df.timestamp.dt.normalize().isin(h5d) & (df._story == ""), "_story"] = "H5"
    df.loc[(df.zone_id == "Z05") & df.timestamp.dt.normalize().between(h8s, h8e) & (df._story == ""), "_story"] = "H8"
    # H1: the water main break and its knock-on road hazard
    d1 = pd.Timestamp(str(cfg["stories"]["H1"]["date"]))
    h1rows = pd.DataFrame([
        {"timestamp": d1 + pd.Timedelta("06:44:00"), "zone_id": "Z02", "type": "utility_failure", "source": "sensor", "severity": 1, "_dq": "", "_story": "H1"},
        {"timestamp": d1 + pd.Timedelta("07:05:00"), "zone_id": "Z02", "type": "road_hazard", "source": "CCTV", "severity": 2, "_dq": "", "_story": "H1"},
    ])
    df = pd.concat([df, h1rows], ignore_index=True)
    df["timestamp"] = real_local(df.timestamp)
    df = df.sort_values("timestamp", kind="stable").reset_index(drop=True)
    med = df.severity.map(SEV_RESP).to_numpy() * np.where(df.zone_id == "Z05", 1.35, 1.0)
    df["response_min"] = np.round(med * rng.lognormal(0, 0.45, len(df)), 1)
    df.loc[df._story == "H1", "response_min"] = [9.0, 14.0]
    age = (ctx.end + pd.Timedelta(days=1) - df.timestamp).dt.total_seconds() / 86400
    st = np.where(age > 2, "closed", np.where(rng.random(len(df)) < 0.5, "in_progress", "open"))
    df["status"] = st
    df.insert(0, "incident_id", [f"INC-{i:06d}" for i in range(1, len(df) + 1)])
    ing = df.timestamp + pd.to_timedelta(rng.uniform(1, 10, len(df)), unit="min")
    # DQ11 — 2 % arrive 1–3 days late
    ok = np.flatnonzero((df._story == "").to_numpy())
    late = rng.choice(ok, size=int(round(cfg["defects"]["DQ11_late_rate"] * len(df))), replace=False)
    ing.iloc[late] = df.timestamp.iloc[late] + pd.to_timedelta(rng.uniform(24, 72, len(late)), unit="h")
    df["ingested_at"] = real_local(ing.dt.floor("min"))
    m = np.zeros(len(df), bool); m[late] = True
    tag(df, m, "DQ11")
    ctx.note(id="DQ11", dataset="incidents", rows=int(m.sum()), rate=m.mean(),
             detail="ingested_at is 24–72 h after the event; the file is in arrival order, so these rows appear out of time order (late-arriving)")
    df = df.sort_values(["ingested_at", "timestamp"], kind="stable").reset_index(drop=True)
    df["timestamp"] = fmt_ts(df.timestamp); df["ingested_at"] = fmt_ts(df.ingested_at)
    out = df[["incident_id", "timestamp", "zone_id", "type", "severity", "source", "response_min", "status", "ingested_at", "_dq", "_story"]]
    write_dataset(ctx, "incidents", out)
    return out


def camera_status(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng("camera_status")
    S = ctx.ref["sensors"]
    cams = S[S.sensor_type == "cctv_camera"][["sensor_id", "zone_id"]].rename(columns={"sensor_id": "camera_id"})
    days = pd.date_range(ctx.start, ctx.end, freq="D")
    df = cams.merge(pd.DataFrame({"date": days}), how="cross")
    target = df.zone_id.map({"Z01": 98.25, "Z02": 98.4, "Z03": 98.8, "Z04": 98.5, "Z05": 98.55, "Z06": 97.8}).to_numpy()
    up = 100 - rng.exponential(100 - target)
    bad = rng.random(len(df)) < 0.004
    up = np.where(bad, rng.uniform(20, 70, len(df)), up)
    up = np.where(df.camera_id == "CAM-031", np.minimum(up, 99), up)
    h8 = ctx.cfg["stories"]["H8"]
    mh = (df.zone_id == h8["zone"]).to_numpy() & df.date.between(pd.Timestamp(str(h8["start"])), pd.Timestamp(str(h8["end"]))).to_numpy()
    up = np.where(mh, h8["outage_uptime"] + rng.normal(0, 5, len(df)), up)
    df["uptime_pct"] = np.round(np.clip(up, 0, 100), 1)
    df["_dq"] = ""; df["_story"] = ""
    tag(df, mh, "H8", "_story")
    df = D.dq1_missing(ctx, "camera_status", df, ["uptime_pct"])
    df = df.sort_values(["date", "camera_id"], kind="stable").reset_index(drop=True)
    df["date"] = df.date.dt.strftime("%Y-%m-%d")
    write_dataset(ctx, "camera_status", df[["camera_id", "date", "uptime_pct", "_dq", "_story"]])
    return df


# ------------------------------------------------------------------ buildings
def bms(ctx: Ctx):
    rng = ctx.rng("bms")
    B = ctx.ref["buildings"].set_index("building_id")
    ids = ctx.ref["bms_buildings"]
    grid = time_grid(ctx.start, ctx.end, "h", dst="aware")
    df = long_frame(grid, ids, "building_id")
    f = day_features(ctx, df.timestamp)
    h = df.timestamp.dt.hour.to_numpy() + 0.5
    b = B.loc[df.building_id]
    use = b.use_type.to_numpy(); units = b.units.to_numpy(); floors = b.floors.to_numpy()
    work = f.is_workday.to_numpy(); ram = f.is_ramadan.to_numpy(); school = f.is_school_day.to_numpy(); fri = (f.weekday == 4).to_numpy()
    occ_shape = np.select(
        [use == "government", use == "school", use == "clinic"],
        [np.where(work, np.where(ram, interp_profile(P.WORK_OFFICE_RAM, h), interp_profile(P.WORK_OFFICE, h)), 0.0),
         np.where(school, interp_profile(P.SCHOOL, h), 0.0),
         interp_profile(P.CLINIC, h) * np.where(work, 1.0, 0.6)],
        default=np.where(ram, interp_profile(P.MOSQUE_RAM, h), interp_profile(P.MOSQUE, h)) * np.where(fri & (h > 11) & (h < 14), 2.2, 1.0))
    occ_shape = np.clip(occ_shape - 0.25, 0, None) / 0.75
    cap = np.select([use == "government", use == "school", use == "clinic"], [units * 22, units * 28, units * 9], default=350)
    occ = np.round(cap * occ_shape * rng.lognormal(0, 0.12, len(df)))
    on = occ > 0
    T = hourly_temp(f, h)
    indoor = np.where(on, 23.6 + 0.07 * (T - 23) + rng.normal(0, 0.35, len(df)), 0.55 * T + 0.45 * 25 + rng.normal(0, 0.5, len(df)))
    kw_cap = np.select([use == "government", use == "school", use == "clinic"], [floors * 9.0, 40.0, 55.0], default=30.0)
    hvac = np.where(on, kw_cap * np.clip((T - 18) / 16, 0.12, 1.3), kw_cap * 0.03) * rng.lognormal(0, 0.06, len(df))
    hum = np.clip(46 - 0.9 * (T - 22) + rng.normal(0, 4, len(df)) - 6 * f.dust.to_numpy(), 12, 85)
    df["indoor_temp_c"] = indoor; df["humidity_pct"] = hum; df["hvac_kw"] = hvac; df["occupancy_count"] = occ
    df["_dq"] = ""; df["_story"] = ""
    # HVAC failures (feed work orders): 5 episodes in May–June
    fails = []
    fr = ctx.rng("bms.failures")
    cand = [i for i in ids if B.loc[i, "use_type"] in ("government", "school", "clinic")]
    for _ in range(5):
        bid = cand[fr.integers(len(cand))]
        day = pd.Timestamp("2025-05-05") + pd.Timedelta(days=int(fr.integers(0, 50)))
        while not ctx.cal.loc[day, "is_workday"]:
            day += pd.Timedelta(days=1)
        t0 = day + pd.Timedelta(hours=int(fr.integers(9, 12)))
        dur = int(fr.integers(5, 30))
        m = (df.building_id == bid).to_numpy() & (df.timestamp >= t0).to_numpy() & (df.timestamp < t0 + pd.Timedelta(hours=dur)).to_numpy()
        df.loc[m, "hvac_kw"] = 0.4
        df.loc[m, "indoor_temp_c"] = (0.75 * T[m] + 0.25 * 25) + 1.5
        fails.append((f"HVAC-{bid[2:]}", t0, t0 + pd.Timedelta(hours=dur)))
    # DQ7 — one building's BMS reports °F
    fb = sorted(ids)[int(ctx.rng("DQ7.bms").integers(len(ids)))]
    mf = (df.building_id == fb).to_numpy()
    df.loc[mf, "indoor_temp_c"] = df.loc[mf, "indoor_temp_c"] * 9 / 5 + 32
    ctx.note(id="DQ7", dataset="bms_readings", rows=int(mf.sum()), rate=mf.mean(),
             detail=f"building {fb} reports indoor temperature in °F (column still named indoor_temp_c) for the whole series", buildings=[fb])
    for c, nd in [("indoor_temp_c", 1), ("humidity_pct", 0), ("hvac_kw", 1)]:
        df[c] = np.round(df[c], nd)
    df = D.dq4_dst(ctx, "bms_readings", df, "aware", 1)
    df = D.dq1_missing(ctx, "bms_readings", df, ["indoor_temp_c", "humidity_pct", "hvac_kw", "occupancy_count"])
    df = df.sort_values(["timestamp", "building_id"], kind="stable").reset_index(drop=True)
    df["occupancy_count"] = df.occupancy_count.astype("Int64")
    out = df[["building_id", "timestamp", "indoor_temp_c", "humidity_pct", "hvac_kw", "occupancy_count", "_dq", "_story"]].copy()
    out["timestamp"] = fmt_ts(out.timestamp)
    write_dataset(ctx, "bms_readings", out)
    return out, fails


WO_CAT = {"Streetlight": ["streetlight", "Street light", "إنارة", "Streetlights"],
          "HVAC": ["hvac", "AC", "تكييف", "H.V.A.C"],
          "CCTV": ["cctv", "Camera", "كاميرات", "C.C.T.V"],
          "Water network": ["water network", "Water", "شبكة المياه", "Water Network "],
          "Waste bin": ["waste bin", "Bin", "حاويات", "Waste-bin"],
          "Traffic signal": ["traffic signal", "Signals", "إشارات المرور", "Traffic Signal"],
          "Sensor": ["sensor", "Sensors", "حساسات", "SENSOR"]}
PRIO_SLA = {"P1": 4, "P2": 24, "P3": 72, "P4": 168}


def work_orders(ctx: Ctx, sl_episodes: pd.DataFrame, hvac_fails, outage_blocks) -> pd.DataFrame:
    rng = ctx.rng("work_orders")
    A = ctx.ref["assets"]
    rows = []

    def add(asset, opened, cat, prio, closed=None, story=""):
        sla = PRIO_SLA[prio]
        if closed is None:
            dur = sla * rng.lognormal(np.log(0.55), 0.5)
            closed = opened + pd.Timedelta(hours=float(dur))
        if closed is not None and closed > ctx.end + pd.Timedelta(days=1):
            closed = None
        rows.append((asset, opened, closed, cat, prio, sla, story))

    for _, e in sl_episodes.iterrows():
        opened = e.fault_date + pd.Timedelta(hours=float(rng.uniform(7, 11)))
        closed = (e.fixed_date + pd.Timedelta(hours=float(rng.uniform(8, 14)))) if e.fixed_date is not None and not pd.isna(e.fixed_date) else None
        add(e.asset_id, opened, "Streetlight", rng.choice(["P3", "P4"], p=[.6, .4]), closed)
    for asset, t0, t1 in hvac_fails:
        add(asset, t0 + pd.Timedelta(minutes=40), "HVAC", "P2", t1 + pd.Timedelta(minutes=float(rng.uniform(5, 30))))
    for blk in outage_blocks:
        dev = blk["sensor"]
        aid = ctx.ref["sensors"].set_index("sensor_id").asset_id.get(dev, "")
        t0 = pd.Timestamp(blk["start"]) + pd.Timedelta(hours=1)
        add(aid, t0, "Sensor", "P3", pd.Timestamp(blk["end"]) + pd.Timedelta(minutes=30))
    # H8: camera outage cluster in Z05
    h8 = ctx.cfg["stories"]["H8"]
    s8 = pd.Timestamp(str(h8["start"]))
    z5cams = A[(A.asset_type == "cctv_camera") & (A.zone_id == "Z05")].asset_id
    for i, cam in enumerate(z5cams):
        add(cam, s8 + pd.Timedelta(hours=7, minutes=10 + i), "CCTV", "P1", s8 + pd.Timedelta(days=3, hours=6, minutes=int(rng.integers(0, 90))), story="H8")
    # H1: valve / network repair
    d1 = pd.Timestamp(str(ctx.cfg["stories"]["H1"]["date"]))
    add("VLV-07", d1 + pd.Timedelta("06:52:00"), "Water network", "P1", d1 + pd.Timedelta("09:35:00"), story="H1")
    add("PMP-02", d1 + pd.Timedelta("07:20:00"), "Water network", "P2", d1 + pd.Timedelta("12:10:00"), story="H1")
    # background maintenance
    pool = {"CCTV": "cctv_camera", "Water network": "network_valve", "Waste bin": "smart_bin", "Traffic signal": "traffic_signal", "HVAC": "hvac_unit"}
    days = (ctx.end - ctx.start).days + 1
    for cat, atype in pool.items():
        cands = A[A.asset_type == atype].asset_id.to_numpy()
        n = rng.poisson({"CCTV": 0.6, "Water network": 0.5, "Waste bin": 0.9, "Traffic signal": 0.4, "HVAC": 0.3}[cat] * days)
        for _ in range(n):
            opened = ctx.start + pd.Timedelta(minutes=int(rng.integers(0, days * 1440)))
            add(rng.choice(cands), opened, cat, rng.choice(["P1", "P2", "P3", "P4"], p=[.08, .32, .40, .20]))
    df = pd.DataFrame(rows, columns=["asset_id", "opened_at", "closed_at", "category", "priority", "sla_hours", "_story"])
    df["opened_at"] = real_local(df.opened_at.dt.floor("min"))
    df["closed_at"] = real_local(df.closed_at.dt.floor("min"))
    df = df.sort_values("opened_at", kind="stable").reset_index(drop=True)
    df.insert(0, "work_order_id", [f"WO-{i:05d}" for i in range(1, len(df) + 1)])
    df["status"] = np.where(df.closed_at.notna(), "closed", np.where(rng.random(len(df)) < 0.6, "in_progress", "open"))
    df["_dq"] = ""
    df = dq9_variants(ctx, "work_orders", df, "category", WO_CAT)
    df["opened_at"] = fmt_ts(df.opened_at)
    df["closed_at"] = df.closed_at.dt.strftime("%Y-%m-%d %H:%M")
    write_dataset(ctx, "work_orders", df[["work_order_id", "asset_id", "opened_at", "closed_at", "category", "priority", "sla_hours", "status", "_dq", "_story"]])
    return df


def dq9_variants(ctx: Ctx, name: str, df: pd.DataFrame, col: str, variants: dict) -> pd.DataFrame:
    rng = ctx.rng(f"DQ9.{name}")
    rate = ctx.cfg["defects"]["DQ9_rate"]
    ok = np.flatnonzero((df._story == "").to_numpy())
    pick = rng.choice(ok, size=int(round(rate * len(df))), replace=False)
    for i in pick:
        canon = df.at[df.index[i], col]
        df.at[df.index[i], col] = variants[canon][rng.integers(len(variants[canon]))]
    m = np.zeros(len(df), bool); m[pick] = True
    tag(df, m, "DQ9")
    ctx.note(id="DQ9", dataset=name, rows=len(pick), rate=len(pick) / len(df),
             detail=f"{col} written with a spelling / language variant instead of the canonical value", variants=variants)
    return df


# ------------------------------------------------------------------ environment
def air_quality(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng("air_quality")
    S = ctx.ref["sensors"]
    st = S[S.sensor_type == "air_quality"][["sensor_id", "zone_id"]].rename(columns={"sensor_id": "station_id"}).set_index("station_id")
    st["pm10_base"] = rng.uniform(65, 95, len(st))
    grid = time_grid(ctx.start, ctx.end, "h", dst="aware")
    df = long_frame(grid, st.index, "station_id")
    f = day_features(ctx, df.timestamp)
    h = df.timestamp.dt.hour.to_numpy() + 0.5
    tr = by_daytype(f.day_type, h, P.TRAFFIC)
    T = hourly_temp(f, h)
    base = st.loc[df.station_id, "pm10_base"].to_numpy()
    dust = f.dust.to_numpy()
    dust_shape = np.clip(np.sin(np.pi * (h - 7) / 14), 0, None) ** 1.5      # builds through the day
    pm10_dust = dust * 1150 * (0.25 + 0.75 * dust_shape)
    pm10 = base * (0.72 + 0.55 * tr) * rng.lognormal(0, 0.15, len(df)) + pm10_dust * rng.lognormal(0, 0.12, len(df))
    pm25 = 0.45 * base * (0.72 + 0.55 * tr) * rng.lognormal(0, 0.15, len(df)) + 0.22 * pm10_dust
    no2 = (14 + 32 * tr) * rng.lognormal(0, 0.15, len(df))
    sun = np.clip(np.sin(np.pi * (h - 6) / 13), 0, None)
    o3 = (22 + 38 * sun * (1 + 0.035 * (T - 20))) * rng.lognormal(0, 0.1, len(df)) - 0.15 * no2
    hum = np.clip(52 - 1.3 * (T - 20) + rng.normal(0, 5, len(df)) - 12 * dust, 8, 92)
    df["pm25"] = np.round(pm25, 1); df["pm10"] = np.round(pm10, 1); df["no2"] = np.round(no2, 1); df["o3"] = np.round(np.clip(o3, 2, None), 1)
    df["temp_c"] = np.round(T + rng.normal(0, 0.4, len(df)), 1); df["humidity_pct"] = np.round(hum, 0)
    df["_dq"] = ""; df["_story"] = ""
    tag(df, (f.dust_story == "H5").to_numpy(), "H5", "_story")
    cols = ["pm25", "pm10", "no2", "o3", "temp_c", "humidity_pct"]
    for blk in ctx.cfg["defects"]["DQ6_stuck"]:
        t0, t1 = pd.Timestamp(blk["start"]), pd.Timestamp(blk["end"])
        m = (df.station_id == blk["sensor"]).to_numpy() & (df.timestamp >= t0).to_numpy() & (df.timestamp < t1).to_numpy()
        first = np.flatnonzero(m)[0]
        for c in cols:
            df.loc[m, c] = df.iloc[first][c]
        tag(df, m, "DQ6")
        ctx.note(id="DQ6", dataset="air_quality", rows=int(m.sum()), rate=m.mean(),
                 detail=f"{blk['sensor']} stuck: every column repeats its {blk['start']} value until {blk['end']} (PM10 = {df.iloc[first].pm10})")
    df = D.dq4_dst(ctx, "air_quality", df, "aware", 1)
    df = D.dq1_missing(ctx, "air_quality", df, cols)
    df = df.sort_values(["timestamp", "station_id"], kind="stable").reset_index(drop=True)
    out = df[["station_id", "timestamp"] + cols + ["_dq", "_story"]].copy()
    out["timestamp"] = fmt_ts(out.timestamp)
    write_dataset(ctx, "air_quality", out)
    return out


def noise(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng("noise")
    S = ctx.ref["sensors"]
    st = S[S.sensor_type == "noise"][["sensor_id", "zone_id"]].set_index("sensor_id")
    grid = time_grid(ctx.start, ctx.end, "h", dst="aware")
    df = long_frame(grid, st.index, "sensor_id")
    f = day_features(ctx, df.timestamp)
    h = df.timestamp.dt.hour.to_numpy() + 0.5
    tr = by_daytype(f.day_type, h, P.TRAFFIC)
    zone = st.loc[df.sensor_id, "zone_id"].to_numpy()
    zf = np.select([zone == "Z04", zone == "Z05", zone == "Z06", zone == "Z03"], [1.15, 1.1, 0.8, 0.95], default=0.9)
    la = 47 + 17 * tr * zf + rng.normal(0, 1.6, len(df))
    eve = (h >= 17) & (h < 24)
    off = ~f.is_workday.to_numpy()
    la += np.where((zone == "Z06") & eve & off, 4.5, 0) + np.where((zone == "Z06") & f.is_eid.to_numpy() & ((h >= 10) | (h < 1)), 7.5, 0)
    la += np.where(f.is_eid.to_numpy() & (zone != "Z06") & eve, 2.0, 0)
    la += np.where(f.is_ramadan.to_numpy() & ((h >= 19) | (h < 2)), 3.0, 0)
    df["laeq_db"] = np.round(la, 1)
    df["_dq"] = ""; df["_story"] = ""
    df = D.dq4_dst(ctx, "noise", df, "aware", 1)
    df = D.dq1_missing(ctx, "noise", df, ["laeq_db"])
    df = df.sort_values(["timestamp", "sensor_id"], kind="stable").reset_index(drop=True)
    out = df[["sensor_id", "timestamp", "laeq_db", "_dq", "_story"]].copy()
    out["timestamp"] = fmt_ts(out.timestamp)
    write_dataset(ctx, "noise", out)
    return out
