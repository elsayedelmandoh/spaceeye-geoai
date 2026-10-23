"""Mobility · التنقل — traffic_counts, parking_occupancy, transit_ridership."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import defects as D
from . import profiles as P
from .calendar import day_features
from .common import Ctx, fmt_ts, interp_profile, tag, time_grid, write_dataset


def long_frame(grid: pd.DataFrame, ids, col: str) -> pd.DataFrame:
    n, k = len(grid), len(ids)
    return pd.DataFrame({
        col: np.repeat(np.asarray(ids), n),
        "timestamp": np.tile(grid.timestamp.values, k),
        "_phantom": np.tile(grid.dst_phantom.values, k),
        "_repeat": np.tile(grid.dst_repeat.values, k),
    })


def by_daytype(day_type: pd.Series, hours: np.ndarray, table: dict) -> np.ndarray:
    out = np.zeros(len(hours))
    dt = day_type.to_numpy()
    for k, prof in table.items():
        m = dt == k
        if m.any():
            out[m] = interp_profile(prof, hours[m])
    return out


def traffic(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng("traffic")
    cfg = ctx.cfg
    S = ctx.ref["sensors"]
    roads = ctx.ref["roads"].set_index("segment_id")
    sens = S[S.sensor_type == "traffic_counter"][["sensor_id", "zone_id", "segment_id"]].copy()
    orphan = cfg["defects"]["DQ10_orphan_sensor"]
    sens = pd.concat([sens, pd.DataFrame([{"sensor_id": orphan, "zone_id": "Z04", "segment_id": "RD-18"}])], ignore_index=True)
    sens["lanes"] = roads.loc[sens.segment_id, "lanes"].values
    sens["vfree"] = roads.loc[sens.segment_id, "speed_limit_kmh"].values * rng.uniform(0.88, 1.02, len(sens))
    sens["scale"] = rng.uniform(0.75, 1.15, len(sens))
    sens = sens.set_index("sensor_id")

    grid = time_grid(ctx.start, ctx.end, "15min", dst="phantom")
    df = long_frame(grid, sens.index, "sensor_id")
    f = day_features(ctx, df.timestamp)
    hrs = (df.timestamp.dt.hour + df.timestamp.dt.minute / 60 + 0.125).to_numpy()
    shape = by_daytype(f.day_type, hrs, P.TRAFFIC)
    sz = sens.loc[df.sensor_id]
    cap15 = sz.lanes.values * 450.0
    zone = sz.zone_id.values
    mult = sz.scale.values * f.growth.to_numpy() ** 0.6 * (1 - 0.15 * f.dust.to_numpy())
    eid = f.is_eid.to_numpy()
    mult = np.where(eid & (zone == "Z06"), mult * 2.4, mult)          # Eid: park roads busy
    noise = rng.lognormal(0, 0.10, len(df))
    vol = cap15 * 0.55 * shape * mult * noise
    u = np.clip(vol / cap15, 0, 1.2)
    vfree = sz.vfree.values
    speed = vfree * (1 - 0.85 * u ** 2) * (1 - 0.28 * f.dust.to_numpy()) * rng.normal(1, 0.03, len(df))
    df["_story"] = ""

    # H1 — water main break: Z02 roads slow 06:45–10:00 on 2025-05-13
    h1 = cfg["stories"]["H1"]
    d1 = pd.Timestamp(str(h1["date"]))
    m1 = (zone == "Z02") & (df.timestamp >= d1 + pd.Timedelta("06:45:00")).to_numpy() & (df.timestamp < d1 + pd.Timedelta("10:00:00")).to_numpy()
    speed = np.where(m1, speed * 0.58, speed)
    vol = np.where(m1, vol * 0.85, vol)
    tag(df, m1, "H1", "_story")
    m5 = (f.dust_story == "H5").to_numpy()
    tag(df, m5, "H5", "_story")

    occ = np.clip(100 * u * 1.05 + (1 - speed / vfree) * 25 + rng.normal(0, 1.5, len(df)), 0, 100)
    df["vehicle_count"] = np.round(vol).astype(float)
    df["avg_speed_kmh"] = np.round(np.clip(speed, 3, None), 1)
    df["occupancy_pct"] = np.round(occ, 1)
    df["_dq"] = ""

    # DQ12 / H3 — slow drift on TRF-017 (+1 % per week from 1 March)
    q = cfg["defects"]["DQ12"]
    md = (df.sensor_id == q["sensor"]).to_numpy()
    weeks = (df.timestamp - pd.Timestamp(str(q["start"]))).dt.days.to_numpy() / 7.0
    drift = 1 + q["per_week"] * np.clip(weeks, 0, None)
    df.loc[md, "vehicle_count"] = np.round(df.loc[md, "vehicle_count"].to_numpy() * drift[md])
    ctx.note(id="DQ12", dataset="traffic_counts", rows=int(md.sum()), rate=md.mean(),
             detail=f"{q['sensor']}: vehicle_count multiplied by 1 + {q['per_week']}×weeks since {q['start']} (≈ +{q['per_week']*weeks[md].max()*100:.0f}% by 30 June). Also hidden story H3.")

    # DQ6b — stuck traffic sensor (supports the Day 1 dashboard)
    for blk in cfg["defects"]["DQ6b_stuck_traffic"]:
        t0, t1 = pd.Timestamp(blk["start"]), pd.Timestamp(blk["end"])
        ms = (df.sensor_id == blk["sensor"]).to_numpy() & (df.timestamp >= t0).to_numpy() & (df.timestamp < t1).to_numpy()
        first = np.flatnonzero(ms)[0]
        for c in ["vehicle_count", "avg_speed_kmh", "occupancy_pct"]:
            df.loc[ms, c] = df.iloc[first][c]
        tag(df, ms, "DQ6b")
        ctx.note(id="DQ6b", dataset="traffic_counts", rows=int(ms.sum()), rate=ms.mean(),
                 detail=f"{blk['sensor']} repeats the same reading ({int(df.iloc[first].vehicle_count)} veh, {df.iloc[first].avg_speed_kmh} km/h) from {blk['start']} to {blk['end']} — extra stuck block used by the Day 1 dashboard")

    ctx.note(id="DQ10", dataset="traffic_counts", rows=int((df.sensor_id == orphan).sum()), rate=(df.sensor_id == orphan).mean(),
             detail=f"sensor_id {orphan} has data but is not in reference/sensors.csv (orphan key)")

    df = D.dq4_dst(ctx, "traffic_counts", df, "phantom", 4)
    df = D.dq2_outage(ctx, "traffic_counts", df, "sensor_id", cfg["defects"]["DQ2_traffic_sensors"])
    df = D.dq1_missing(ctx, "traffic_counts", df, ["vehicle_count", "avg_speed_kmh", "occupancy_pct"])
    df = df.sort_values(["timestamp", "sensor_id"], kind="stable").reset_index(drop=True)
    df = D.dq3_duplicates(ctx, "traffic_counts", df, ["timestamp", "sensor_id"])
    df["vehicle_count"] = df.vehicle_count.astype("Int64")
    out = df[["sensor_id", "timestamp", "vehicle_count", "avg_speed_kmh", "occupancy_pct", "_dq", "_story"]].copy()
    out["timestamp"] = fmt_ts(out.timestamp)
    write_dataset(ctx, "traffic_counts", out)
    return out


LOT_KIND = {"Z01": "res", "Z02": "res", "Z03": "gov", "Z04": "biz", "Z05": "mixed", "Z06": "park"}


def parking(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng("parking")
    S = ctx.ref["sensors"]
    lots = S[S.sensor_type == "parking_counter"][["sensor_id", "zone_id"]].rename(columns={"sensor_id": "lot_id"}).set_index("lot_id")
    lots["capacity"] = rng.choice([150, 200, 250, 300, 400, 500, 600], len(lots))
    grid = time_grid(ctx.start, ctx.end, "h", dst="aware")
    df = long_frame(grid, lots.index, "lot_id")
    f = day_features(ctx, df.timestamp)
    h = df.timestamp.dt.hour.to_numpy()
    kind = lots.loc[df.lot_id, "zone_id"].map(LOT_KIND).to_numpy()
    work = f.is_workday.to_numpy(); ram = f.is_ramadan.to_numpy(); eid = f.is_eid.to_numpy(); off = ~work
    frac = np.zeros(len(df))
    # residential: full at night, half empty on working days
    night = (h >= 20) | (h < 7)
    frac = np.where(kind == "res", np.where(night, 0.88, np.where(work, 0.48, 0.72)), frac)
    frac = np.where((kind == "res") & ram & (h >= 19), 0.80, frac)
    g_open, g_close = np.where(ram, 10, 8), np.where(ram, 15, 16)
    frac = np.where(kind == "gov", np.where(work & (h >= g_open) & (h < g_close), 0.90, 0.08), frac)
    frac = np.where(kind == "biz", np.where(work & (h >= 9) & (h < 18), 0.86, np.where(off & (h >= 11) & (h < 22), 0.32, 0.12)), frac)
    frac = np.where(kind == "mixed", np.where((h >= 17) & (h < 23), 0.80, np.where((h >= 9) & (h < 17), 0.62, 0.50)), frac)
    park_busy = (h >= 15) & (h < 23)
    frac = np.where(kind == "park", np.where(park_busy, np.where(eid, 0.98, np.where(off, 0.78, 0.42)), 0.10), frac)
    frac = frac * f.growth.to_numpy() ** 0.4 * rng.normal(1, 0.05, len(df))
    cap = lots.loc[df.lot_id, "capacity"].to_numpy()
    df["capacity"] = cap
    df["occupied"] = np.clip(np.round(cap * frac), 0, cap).astype(float)
    df["_dq"] = ""; df["_story"] = ""

    def spike(d, idx, r):
        neg = r.random(len(idx)) < 0.3
        d.loc[idx[~neg], "occupied"] = d.loc[idx[~neg], "capacity"] * 4
        d.loc[idx[neg], "occupied"] = -r.integers(1, 30, neg.sum())
        return f"occupied set to 4× capacity (400% occupancy) in {(~neg).sum()} rows and to a negative count in {neg.sum()} rows"

    df = D.dq4_dst(ctx, "parking_occupancy", df, "aware", 1)
    df = D.dq5_spikes(ctx, "parking_occupancy", df, spike)
    df = D.dq1_missing(ctx, "parking_occupancy", df, ["occupied"])
    df = df.sort_values(["timestamp", "lot_id"], kind="stable").reset_index(drop=True)
    df["occupied"] = df.occupied.astype("Int64")
    out = df[["lot_id", "timestamp", "capacity", "occupied", "_dq", "_story"]].copy()
    out["timestamp"] = fmt_ts(out.timestamp)
    write_dataset(ctx, "parking_occupancy", out)
    return out


LINES = {"Line A": ["Z01", "Z01", "Z01", "Z03", "Z03", "Z03", "Z04", "Z04"],
         "Line B": ["Z02", "Z02", "Z02", "Z04", "Z04", "Z05", "Z05", "Z05"],
         "Line C": ["Z05", "Z05", "Z06", "Z06", "Z03", "Z03"]}


def transit(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng("transit")
    rows = []
    for line, zones in LINES.items():
        for i, z in enumerate(zones, 1):
            rows.append((line, f"{line[-1]}{i:02d}", z, float(rng.uniform(90, 420))))
    stops = pd.DataFrame(rows, columns=["line_id", "stop_id", "zone_id", "base"])
    days = pd.date_range(ctx.start, ctx.end, freq="D")
    df = stops.merge(pd.DataFrame({"date": days}), how="cross")
    f = ctx.cal.loc[df.date]
    work = f.is_workday.to_numpy()
    m = np.where(work, 1.0, 0.55) * np.where(f.is_ramadan, 0.85, 1.0) * f.growth.to_numpy() ** 1.2
    m *= np.where(f.is_school_day & df.line_id.isin(["Line A", "Line B"]).to_numpy(), 1.08, 1.0)
    eid = f.is_eid.to_numpy()
    m *= np.where(eid, np.where(df.line_id == "Line C", 1.35, 0.5), 1.0)
    m *= 1 - 0.2 * f.dust.to_numpy()
    b = np.round(df.base.to_numpy() * m * rng.lognormal(0, 0.07, len(df)))
    df["boardings"] = b.astype(int)
    df["alightings"] = np.round(b * rng.uniform(0.85, 1.15, len(df))).astype(int)
    ot = 94 + rng.normal(0, 1.8, len(df)) - 11 * f.dust.to_numpy() + np.where(eid, 2, 0)
    h1 = pd.Timestamp(str(ctx.cfg["stories"]["H1"]["date"]))
    mh = (df.date == h1).to_numpy() & (df.line_id == "Line B").to_numpy()
    ot = np.where(mh, ot - 9, ot)
    df["on_time_pct"] = np.round(np.clip(ot, 50, 100), 1)
    df["_story"] = ""
    tag(df, mh, "H1", "_story")
    out = df[["date", "line_id", "stop_id", "boardings", "alightings", "on_time_pct", "_story"]].copy()
    out["date"] = out.date.dt.strftime("%Y-%m-%d")
    write_dataset(ctx, "transit_ridership", out)
    return out
