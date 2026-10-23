"""Waste · المخلفات — bin_fill (hourly × 150 bins) and collection_trips."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import defects as D
from . import profiles as P
from .common import Ctx, fmt_ts, interp_profile, tag, time_grid, write_dataset
from .energy_water import hourly_temp

# route -> (zone, truck, start hour, collection days rule)
ROUTES = {
    "R01": ("Z01", "TRK-01", 6, "odd"), "R02": ("Z01", "TRK-02", 6, "even"),
    "R03": ("Z02", "TRK-03", 6, "odd"), "R04": ("Z02", "TRK-04", 6, "even"),
    "R05": ("Z03", "TRK-05", 7, "every3"), "R06": ("Z04", "TRK-05", 5, "workday"),
    "R07": ("Z05", "TRK-06", 6, "daily"), "R08": ("Z06", "TRK-07", 7, "even"),
    "R09": ("Z05", "TRK-08", 16, "daily_pm"),
}
DAILY_FILL = {"Z01": 44, "Z02": 46, "Z03": 30, "Z04": 62, "Z05": 58, "Z06": 36}   # % per day, typical
BIN_TONNES = 0.11


def bins_and_trips(ctx: Ctx):
    rng = ctx.rng("waste")
    A = ctx.ref["assets"]
    bins = A[A.asset_type == "smart_bin"][["asset_id", "zone_id"]].rename(columns={"asset_id": "bin_id"}).reset_index(drop=True)
    nb = len(bins)
    # route membership: Z01/Z02 split by bin parity across two routes; Z05 bins in both R07 and R09 (twice daily)
    member = {r: [] for r in ROUTES}
    for i, (bid, z) in bins.iterrows():
        for r, (rz, *_x) in ROUTES.items():
            if rz != z:
                continue
            if z in ("Z01", "Z02"):
                if (i % 2 == 0) == (r in ("R01", "R03")):
                    member[r].append(i)
            else:
                member[r].append(i)
    bin_factor = rng.uniform(0.7, 1.35, nb)
    grid = time_grid(ctx.start, ctx.end, "h", dst="phantom")
    ts = grid.timestamp
    cal = ctx.cal
    T = len(grid)
    fill = rng.uniform(5, 40, nb)
    out_fill = np.zeros((T, nb)); out_temp = np.zeros((T, nb))
    trips = []
    trip_no = 0
    zone = bins.zone_id.to_numpy()
    base = np.array([DAILY_FILL[z] for z in zone]) / 24.0 * bin_factor
    dates = ts.dt.normalize()
    eid_days = cal.index[cal.is_eid]
    first_eid = {d for d in eid_days if (d - pd.Timedelta(days=1)) not in set(eid_days)}
    cal_rows = {d: cal.loc[d] for d in dates.unique()}
    for k in range(T):
        t = ts.iloc[k]; d = cal_rows[dates.iloc[k]]
        h = t.hour + 0.5
        prof = interp_profile(P.BIN_RATE["ramadan" if d.is_ramadan else "normal"], np.array([h]))[0]
        mult = d.growth ** 0.8 * (1.6 if d.day_after_eid else 1.0)
        zm = np.ones(nb)
        if d.is_eid:
            zm = np.where(zone == "Z06", 2.6, np.where(np.isin(zone, ["Z01", "Z02", "Z05"]), 1.3, 0.6))
        elif d.is_weekend or d.is_holiday:
            zm = np.where(zone == "Z06", 2.0, np.where(np.isin(zone, ["Z03", "Z04"]), 0.4, 1.1))
        fill = fill + base * prof * mult * zm * rng.lognormal(0, 0.15, nb)
        fill = np.minimum(fill, 100.0)
        out_fill[k] = fill
        out_temp[k] = hourly_temp(pd.DataFrame({"temp_mean": [d.temp_mean]}), np.array([h]))[0] + 2.5 + rng.normal(0, 0.8, nb)
        # collections happen during this hour
        dom = t.day
        for r, (rz, truck, start_h, rule) in ROUTES.items():
            if t.hour != start_h or grid.dst_phantom.iloc[k]:
                continue
            if dates.iloc[k] in first_eid:
                continue                        # first day of each Eid: crews off
            ok = {"odd": dom % 2 == 1, "even": dom % 2 == 0, "every3": dom % 3 == 0, "workday": bool(d.is_workday),
                  "daily": True, "daily_pm": not (d.is_weekend or d.is_holiday)}[rule]
            if not ok or not member[r]:
                continue
            idx = np.array(member[r])
            pre = fill[idx].copy()
            fill[idx] = rng.uniform(1, 5, len(idx))
            tonnes = pre / 100 * BIN_TONNES * rng.uniform(0.9, 1.1, len(idx))
            # split into truck loads of ≤ 7.5 t
            start = t + pd.Timedelta(minutes=int(rng.integers(0, 20)))
            chunk = []
            acc = 0.0
            for j, tn in enumerate(tonnes):
                chunk.append(tn); acc += tn
                if acc >= 7.5 or j == len(tonnes) - 1:
                    trip_no += 1
                    dur = len(chunk) * rng.uniform(3, 5) + rng.uniform(25, 40)
                    end = start + pd.Timedelta(minutes=float(dur))
                    trips.append((f"TRP-{trip_no:05d}", truck, r, start, end, len(chunk), round(acc, 2)))
                    start = end + pd.Timedelta(minutes=int(rng.integers(20, 45)))
                    chunk, acc = [], 0.0
    df = pd.DataFrame({"bin_id": np.repeat(bins.bin_id.values, T), "timestamp": np.tile(ts.values, nb),
                       "fill_pct": np.round(out_fill.T.ravel(), 1), "temp_c": np.round(out_temp.T.ravel(), 1),
                       "_phantom": np.tile(grid.dst_phantom.values, nb)})
    df["_dq"] = ""; df["_story"] = ""
    df = D.dq4_dst(ctx, "bin_fill", df, "phantom", 1)
    df = D.dq1_missing(ctx, "bin_fill", df, ["fill_pct", "temp_c"])
    df = df.sort_values(["timestamp", "bin_id"], kind="stable").reset_index(drop=True)
    df = D.dq3_duplicates(ctx, "bin_fill", df, ["timestamp", "bin_id"])
    out = df[["bin_id", "timestamp", "fill_pct", "temp_c", "_dq", "_story"]].copy()
    out["timestamp"] = fmt_ts(out.timestamp)
    write_dataset(ctx, "bin_fill", out)

    tr = pd.DataFrame(trips, columns=["trip_id", "truck_id", "route_id", "start_time", "end_time", "bins_collected", "tonnes"])
    tr["start_time"] = fmt_ts(tr.start_time); tr["end_time"] = fmt_ts(tr.end_time)
    write_dataset(ctx, "collection_trips", tr)
    return out, tr
