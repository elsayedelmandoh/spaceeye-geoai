"""Energy · الطاقة (electricity_meters, streetlights) and Water · المياه (water_meters, network_pressure, water_quality)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import defects as D
from . import profiles as P
from .calendar import day_features
from .common import Ctx, fmt_ts, interp_profile, tag, time_grid, write_dataset
from .mobility import long_frame


def hourly_temp(f: pd.DataFrame, hour: np.ndarray) -> np.ndarray:
    return f.temp_mean.to_numpy() + 6.0 * np.cos(2 * np.pi * (hour - 15) / 24)


def _meter_frame(ctx: Ctx, name: str):
    B = ctx.ref["buildings"].set_index("building_id")
    ids = ctx.ref["meter_buildings"]
    grid = time_grid(ctx.start, ctx.end, "h", dst="aware")
    df = long_frame(grid, ids, "building_id")
    f = day_features(ctx, df.timestamp)
    b = B.loc[df.building_id]
    return df, f, b


def electricity(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng("electricity")
    df, f, b = _meter_frame(ctx, "electricity")
    h = df.timestamp.dt.hour.to_numpy() + 0.5
    use = b.use_type.to_numpy()
    ram = f.is_ramadan.to_numpy(); work = f.is_workday.to_numpy(); school = f.is_school_day.to_numpy()
    fri = (f.weekday == 4).to_numpy(); eid = f.is_eid.to_numpy()
    shape = np.zeros(len(df))
    m = use == "residential"
    shape[m] = np.where(ram[m], interp_profile(P.ELEC_RES["ramadan"], h[m]), interp_profile(P.ELEC_RES["normal"], h[m]))
    day = (h >= 10) & (h < 17)
    shape = np.where(m & ~work & day, shape * 1.15, shape)
    shape = np.where(m & eid & day, shape * 1.10, shape)
    m = use == "government"
    shape[m] = np.where(work[m], np.where(ram[m], interp_profile(P.WORK_OFFICE_RAM, h[m]), interp_profile(P.WORK_OFFICE, h[m])), 0.25)
    m = use == "commercial"
    shape[m] = np.where(ram[m], interp_profile(P.COMMERCIAL_RAM, h[m]), interp_profile(P.COMMERCIAL, h[m])) * np.where(work[m], 1.0, 0.8) * np.where(eid[m], 0.7, 1.0)
    m = use == "school"
    shape[m] = np.where(school[m], interp_profile(P.SCHOOL, h[m]), 0.15)
    m = use == "clinic"
    shape[m] = interp_profile(P.CLINIC, h[m]) * np.where(work[m], 1.0, 0.8)
    m = use == "mosque"
    shape[m] = np.where(ram[m], interp_profile(P.MOSQUE_RAM, h[m]), interp_profile(P.MOSQUE, h[m]))
    shape = np.where((use == "mosque") & fri & (h >= 11) & (h < 14), shape * 1.7, shape)

    units, floors = b.units.to_numpy(), b.floors.to_numpy()
    peak = np.select([use == "residential", use == "government", use == "commercial", use == "school", use == "clinic"],
                     [units * 1.25, floors * 14.0, units * 3.2, 45.0, 70.0], default=18.0)
    T = hourly_temp(f, h)
    cool = 1 + 0.07 * np.clip(T - 22, 0, None)
    g = f.growth.to_numpy()
    grow = np.where(use == "residential", g, g ** 0.3)
    kwh = peak * shape * cool * grow * rng.lognormal(0, 0.08, len(df))
    df["kwh"] = np.round(kwh, 2)
    df["_dq"] = ""; df["_story"] = ""

    # DQ7 — three buildings report Wh instead of kWh for the whole series
    bids = pd.Series(ctx.ref["meter_buildings"])
    btype = ctx.ref["buildings"].set_index("building_id").use_type
    res = bids[btype.loc[bids].values == "residential"].tolist()
    com = bids[btype.loc[bids].values == "commercial"].tolist()
    r = ctx.rng("DQ7.electricity")
    wh = sorted(list(r.choice(res, 2, replace=False)) + list(r.choice(com, 1, replace=False)))
    mw = df.building_id.isin(wh).to_numpy()
    df.loc[mw, "kwh"] = np.round(df.loc[mw, "kwh"] * 1000, 0)
    ctx.note(id="DQ7", dataset="electricity_meters", rows=int(mw.sum()), rate=mw.mean(),
             detail=f"buildings {', '.join(wh)} report Wh (values ×1000) for the whole series", buildings=wh)

    def spike(d, idx, r):
        k = len(idx)
        kind = r.random(k)
        neg, big = kind < 0.45, kind >= 0.45
        d.loc[idx[neg], "kwh"] = -np.round(d.loc[idx[neg], "kwh"].abs() * r.uniform(0.5, 1.5, neg.sum()), 2)
        d.loc[idx[big], "kwh"] = np.round(r.uniform(5000, 60000, big.sum()), 0)
        d.loc[idx[big][0], "kwh"] = 40000.0     # the Day 2 hook: "the meter that used 40,000 kWh in an hour"
        return f"{neg.sum()} negative kWh readings and {big.sum()} impossible spikes 5,000–60,000 kWh (row {idx[big][0]} = exactly 40,000 kWh)"

    df = D.dq4_dst(ctx, "electricity_meters", df, "aware", 1)
    df = D.dq5_spikes(ctx, "electricity_meters", df, spike)
    df = D.dq1_missing(ctx, "electricity_meters", df, ["kwh"])
    df = df.sort_values(["timestamp", "building_id"], kind="stable").reset_index(drop=True)
    out = df[["building_id", "timestamp", "kwh", "_dq", "_story"]].copy()
    out["timestamp"] = fmt_ts(out.timestamp)
    write_dataset(ctx, "electricity_meters", out)
    return out


def streetlights(ctx: Ctx) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Daily status per light. Returns (data, fault_episodes) — episodes feed work_orders."""
    rng = ctx.rng("streetlights")
    A = ctx.ref["assets"]
    sl = A[A.asset_type == "streetlight"][["asset_id", "zone_id"]].reset_index(drop=True)
    days = pd.date_range(ctx.start, ctx.end, freq="D")
    cal = ctx.cal.loc[days]
    doy = days.dayofyear.to_numpy()
    night = 12.0 - 1.55 * np.sin(2 * np.pi * (doy - 80) / 365)
    n, k = len(sl), len(days)
    status = np.full((n, k), "on", dtype=object)
    burn = np.tile(night, (n, 1)) + rng.normal(0, 0.15, (n, k))
    episodes = []
    for i in range(n):
        j = 0
        while j < k:
            p = 0.0011 * (1 + 6 * cal.dust.iloc[j])
            if rng.random() < p:
                dur = int(rng.geometric(1 / 3.5))
                end = min(k, j + dur)
                status[i, j:end] = "fault"
                burn[i, j] = rng.uniform(0, night[j] * 0.6)
                burn[i, j + 1:end] = 0
                episodes.append((sl.asset_id[i], sl.zone_id[i], days[j], days[min(end, k - 1)] if end < k else None))
                j = end
            elif rng.random() < 0.002:
                status[i, j] = "off"; burn[i, j] = 0; j += 1
            else:
                j += 1
    df = pd.DataFrame({"asset_id": np.repeat(sl.asset_id.values, k), "date": np.tile(days.values, n),
                       "status": status.ravel(), "burn_hours": np.round(burn.ravel(), 2)})
    df["_dq"] = ""; df["_story"] = ""
    df = D.dq1_missing(ctx, "streetlights", df, ["burn_hours"])
    df = df.sort_values(["date", "asset_id"], kind="stable").reset_index(drop=True)
    df["date"] = pd.to_datetime(df.date).dt.strftime("%Y-%m-%d")
    write_dataset(ctx, "streetlights", df[["asset_id", "date", "status", "burn_hours", "_dq", "_story"]])
    ep = pd.DataFrame(episodes, columns=["asset_id", "zone_id", "fault_date", "fixed_date"])
    return df, ep


# ------------------------------------------------------------------ water
def water_meters(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng("water_meters")
    df, f, b = _meter_frame(ctx, "water")
    h = df.timestamp.dt.hour.to_numpy() + 0.5
    use = b.use_type.to_numpy()
    ram = f.is_ramadan.to_numpy(); work = f.is_workday.to_numpy(); school = f.is_school_day.to_numpy()
    res_shape = np.where(ram, interp_profile(P.WATER_RES["ramadan"], h), interp_profile(P.WATER_RES["normal"], h))
    shape = np.select([use == "residential", use == "government", use == "commercial", use == "school", use == "clinic", use == "mosque"],
                      [res_shape,
                       np.where(work, interp_profile(P.WORK_OFFICE, h), 0.1),
                       interp_profile(P.COMMERCIAL, h),
                       np.where(school, interp_profile(P.SCHOOL, h), 0.05),
                       interp_profile(P.CLINIC, h),
                       np.where(ram, interp_profile(P.MOSQUE_RAM, h), interp_profile(P.MOSQUE, h))])
    units, floors = b.units.to_numpy(), b.floors.to_numpy()
    peak = np.select([use == "residential", use == "government", use == "commercial", use == "school", use == "clinic"],
                     [units * 0.055, floors * 0.16, units * 0.08, 1.6, 1.3], default=1.1)
    summer = 1 + 0.025 * np.clip(f.temp_mean.to_numpy() - 20, 0, None)
    g = f.growth.to_numpy()
    m3 = peak * shape * summer * np.where(use == "residential", g, g ** 0.3) * rng.lognormal(0, 0.10, len(df))
    df["_dq"] = ""; df["_story"] = ""
    # H1 — supply lost in Z02 06:45–09:30, rebound to 10:30
    h1 = ctx.cfg["stories"]["H1"]
    d1 = pd.Timestamp(str(h1["date"]))
    z2 = (b.zone_id == "Z02").to_numpy()
    t = df.timestamp
    # hour starting 06:00: normal until 06:40; 07:00–08:59 almost nothing; 09:30 restored; 10:00 rebound
    hourly_mult = {"06:00": 40 / 60 + 20 / 60 * 0.08, "07:00": 0.08, "08:00": 0.08, "09:00": 0.5 * 0.08 + 0.5 * 1.45, "10:00": 1.45}
    hit = np.zeros(len(df), bool)
    for hhmm, k in hourly_mult.items():
        mm = z2 & (t == d1 + pd.Timedelta(hhmm + ":00")).to_numpy()
        m3 = np.where(mm, m3 * k, m3)
        hit |= mm
    tag(df, hit, "H1", "_story")
    df["m3"] = np.round(m3, 3)
    df = D.dq4_dst(ctx, "water_meters", df, "aware", 1)
    df = D.dq1_missing(ctx, "water_meters", df, ["m3"])
    df = df.sort_values(["timestamp", "building_id"], kind="stable").reset_index(drop=True)
    out = df[["building_id", "timestamp", "m3", "_dq", "_story"]].copy()
    out["timestamp"] = fmt_ts(out.timestamp)
    write_dataset(ctx, "water_meters", out)
    return out


def network_pressure(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng("network_pressure")
    S = ctx.ref["sensors"]
    sens = S[S.sensor_type == "pressure_flow"][["sensor_id", "zone_id"]].set_index("sensor_id")
    sens["base"] = rng.uniform(4.15, 4.45, len(sens))
    sens.loc["PRS-07", "base"] = 4.37
    sens["flow0"] = rng.uniform(18, 55, len(sens))
    grid = time_grid(ctx.start, ctx.end, "15min", dst="phantom")
    df = long_frame(grid, sens.index, "sensor_id")
    f = day_features(ctx, df.timestamp)
    h = (df.timestamp.dt.hour + df.timestamp.dt.minute / 60).to_numpy() + 0.125
    ram = f.is_ramadan.to_numpy()
    demand = np.where(ram, interp_profile(P.WATER_RES["ramadan"], h), interp_profile(P.WATER_RES["normal"], h))
    s = sens.loc[df.sensor_id]
    summer = 1 + 0.025 * np.clip(f.temp_mean.to_numpy() - 20, 0, None)
    p = s.base.to_numpy() - 0.20 * demand * summer + rng.normal(0, 0.035, len(df))
    q = s.flow0.to_numpy() * (0.25 + demand) * summer * f.growth.to_numpy() * rng.lognormal(0, 0.05, len(df))
    df["_dq"] = ""; df["_story"] = ""
    h1 = ctx.cfg["stories"]["H1"]
    d1 = pd.Timestamp(str(h1["date"]))
    t = df.timestamp
    sid = df.sensor_id.to_numpy()
    win = (t >= d1 + pd.Timedelta("06:45:00")).to_numpy() & (t < d1 + pd.Timedelta("09:30:00")).to_numpy()
    rec = {"09:30": 2.7, "09:45": 3.4, "10:00": 3.95}
    main = sid == h1["sensor"]
    p = np.where(main & win, h1["low_bar"] + rng.normal(0, 0.05, len(df)), p)
    q = np.where(main & win, q * 2.6, q)
    for hhmm, val in rec.items():
        mm = main & (t == d1 + pd.Timedelta(hhmm + ":00")).to_numpy()
        p = np.where(mm, val, p)
        q = np.where(mm, q * (1 + (4.2 - val) / 2.1 * 1.6), q)
    nb = np.isin(sid, ["PRS-05", "PRS-06", "PRS-08"]) & win
    p = np.where(nb, p - 0.55, p)
    q = np.where(nb, q * 1.3, q)
    story = (main | np.isin(sid, ["PRS-05", "PRS-06", "PRS-08"])) & (t >= d1 + pd.Timedelta("06:00:00")).to_numpy() & (t < d1 + pd.Timedelta("10:30:00")).to_numpy()
    tag(df, story, "H1", "_story")
    df["pressure_bar"] = np.round(p, 2)
    df["flow_lps"] = np.round(q, 1)
    df = D.dq4_dst(ctx, "network_pressure", df, "phantom", 4)
    df = D.dq2_outage(ctx, "network_pressure", df, "sensor_id", ctx.cfg["defects"]["DQ2_pressure_sensors"])
    df = D.dq1_missing(ctx, "network_pressure", df, ["pressure_bar", "flow_lps"])
    df = df.sort_values(["timestamp", "sensor_id"], kind="stable").reset_index(drop=True)
    out = df[["sensor_id", "timestamp", "pressure_bar", "flow_lps", "_dq", "_story"]].copy()
    out["timestamp"] = fmt_ts(out.timestamp)
    write_dataset(ctx, "network_pressure", out)
    return out


def water_quality(ctx: Ctx) -> pd.DataFrame:
    rng = ctx.rng("water_quality")
    S = ctx.ref["sensors"]
    st = S[S.sensor_type == "water_quality"].sensor_id.tolist()
    days = pd.date_range(ctx.start, ctx.end, freq="D")
    df = pd.DataFrame({"station_id": np.repeat(st, len(days)), "date": np.tile(days, len(st))})
    f = ctx.cal.loc[df.date]
    temp = f.temp_mean.to_numpy()
    df["chlorine_mg_l"] = np.round(0.68 - 0.008 * np.clip(temp - 18, 0, None) + rng.normal(0, 0.06, len(df)), 2)
    df["turbidity_ntu"] = np.round(np.clip(0.32 + 0.45 * f.dust.to_numpy() + rng.normal(0, 0.07, len(df)), 0.05, None), 2)
    df["ph"] = np.round(7.5 + rng.normal(0, 0.1, len(df)), 2)
    df["_dq"] = ""; df["_story"] = ""
    d1 = pd.Timestamp(str(ctx.cfg["stories"]["H1"]["date"]))
    m0 = (df.station_id == "WQ-02").to_numpy() & (df.date == d1).to_numpy()
    m1 = (df.station_id == "WQ-02").to_numpy() & (df.date == d1 + pd.Timedelta(days=1)).to_numpy()
    df.loc[m0, ["chlorine_mg_l", "turbidity_ntu"]] = [0.34, 2.8]
    df.loc[m1, ["chlorine_mg_l", "turbidity_ntu"]] = [0.48, 1.2]
    tag(df, m0 | m1, "H1", "_story")
    df = D.dq1_missing(ctx, "water_quality", df, ["chlorine_mg_l", "turbidity_ntu", "ph"])
    df = df.sort_values(["date", "station_id"], kind="stable").reset_index(drop=True)
    df["date"] = df.date.dt.strftime("%Y-%m-%d")
    write_dataset(ctx, "water_quality", df[["station_id", "date", "chlorine_mg_l", "turbidity_ntu", "ph", "_dq", "_story"]])
    return df
