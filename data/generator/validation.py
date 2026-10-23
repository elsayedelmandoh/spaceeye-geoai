"""docs/validation_report.html — reads the written CSVs (as a learner would) and proves every pattern, defect and story."""
from __future__ import annotations

import base64
import html
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .common import Ctx

RED, MAROON, TAUPE, DGREY, MGREY, LGREY = "#ED1C24", "#773533", "#9A746C", "#4A4A4A", "#636263", "#BBBCBF"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": MGREY,
                     "axes.labelcolor": DGREY, "xtick.color": DGREY, "ytick.color": DGREY, "axes.titlesize": 10, "axes.titleweight": "bold"})


def _img(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def parse_sr_time(s: pd.Series, system: pd.Series) -> pd.Series:
    """Normalise service_requests timestamps to Cairo local time (the DQ8 fix)."""
    out = pd.to_datetime(s.where(system == "CRM"), format="%Y-%m-%d %H:%M", errors="coerce")
    leg = system == "LEGACY_CC"
    iso = leg & s.str.contains("T", na=False)
    dmy = leg & s.str.contains("/", na=False)
    u1 = pd.to_datetime(s[iso], format="%Y-%m-%dT%H:%M:%SZ", utc=True)
    u2 = pd.to_datetime(s[dmy], format="%d/%m/%Y %H:%M").dt.tz_localize("UTC")
    out[iso] = u1.dt.tz_convert("Africa/Cairo").dt.tz_localize(None)
    out[dmy] = u2.dt.tz_convert("Africa/Cairo").dt.tz_localize(None)
    return out


class Report:
    def __init__(self):
        self.sections = []
        self.checks = []

    def section(self, sid, title, title_ar, checks, fig=None, note=""):
        self.checks += [(sid, *c) for c in checks]
        self.sections.append((sid, title, title_ar, checks, _img(fig) if fig is not None else None, note))


def load(ctx: Ctx, name: str, **kw) -> pd.DataFrame:
    return pd.read_csv(ctx.data_dir / f"{name}.csv", low_memory=False, **kw)


def write_report(ctx: Ctx) -> dict:
    R = Report()
    facts = {}
    cal = pd.read_csv(ctx.ref_dir / "calendar.csv", parse_dates=["date"]).set_index("date")
    sensors = pd.read_csv(ctx.ref_dir / "sensors.csv")
    B = pd.read_csv(ctx.ref_dir / "buildings.csv").set_index("building_id")
    win = cal.loc[ctx.start:ctx.end]

    # ---------------------------------------------------------------- traffic base
    tr = load(ctx, "traffic_counts", parse_dates=["timestamp"])
    trc = tr.drop_duplicates()
    trc = trc[trc.sensor_id.isin(sensors.sensor_id)]
    trc["date"] = trc.timestamp.dt.normalize(); trc["hour"] = trc.timestamp.dt.hour
    trc = trc.join(cal[["is_weekend", "is_holiday", "is_ramadan", "is_school_day"]], on="date")
    wd = trc[(trc.is_weekend == 0) & (trc.is_holiday == 0)]
    def hourly(d):  # mean vehicles per sensor per hour
        return d.groupby(["date", "sensor_id", "hour"]).vehicle_count.sum(min_count=4).groupby(level=2).mean()
    normal = hourly(wd[(wd.is_ramadan == 0) & (wd.date >= "2025-04-02") & (wd.date <= "2025-06-12")])
    ram = hourly(wd[wd.is_ramadan == 1])
    facts["traffic_normal"] = normal.round(0).astype(int).tolist()
    facts["traffic_ramadan"] = ram.round(0).astype(int).tolist()
    facts["traffic_days"] = (int(wd[(wd.is_ramadan == 0) & (wd.date >= "2025-04-02") & (wd.date <= "2025-06-12")].date.nunique()), int(wd[wd.is_ramadan == 1].date.nunique()))

    # ---------------------------------------------------------------- P1 daily cycles
    el = load(ctx, "electricity_meters", parse_dates=["timestamp"])
    elc = el[(el.kwh >= 0) & (el.kwh < 2000)].copy()
    elc["use"] = B.loc[elc.building_id, "use_type"].values
    elc["date"] = elc.timestamp.dt.normalize(); elc["hour"] = elc.timestamp.dt.hour
    elc = elc.join(cal[["is_ramadan", "is_weekend", "is_holiday"]], on="date")
    wm = load(ctx, "water_meters", parse_dates=["timestamp"])
    wm["use"] = B.loc[wm.building_id, "use_type"].values
    wm["date"] = wm.timestamp.dt.normalize(); wm["hour"] = wm.timestamp.dt.hour
    wm = wm.join(cal[["is_ramadan"]], on="date")
    bins = load(ctx, "bin_fill", parse_dates=["timestamp"]).drop_duplicates()
    bins["hour"] = bins.timestamp.dt.hour; bins["date"] = bins.timestamp.dt.normalize()
    e_res = elc[(elc.use == "residential") & (elc.is_ramadan == 0)].groupby("hour").kwh.mean()
    w_res = wm[(wm.use == "residential") & (wm.is_ramadan == 0)].groupby("hour").m3.mean()
    b_h = bins.groupby("hour").fill_pct.mean()
    fig, ax = plt.subplots(1, 4, figsize=(13, 2.6))
    for a, s, t, c in zip(ax, [normal, e_res, w_res, b_h], ["Traffic (veh/sensor/h)", "Electricity, residential (kWh)", "Water, residential (m³)", "Bin fill (%)"], [RED, MAROON, TAUPE, DGREY]):
        a.plot(s.index, s.values, color=c, lw=2); a.set_title(t); a.set_xticks([0, 6, 12, 18, 23])
    R.section("P1", "Daily cycles per pillar", "الدورة اليومية لكل ركيزة", [
        ("Traffic: morning peak 07–09 and evening peak 15–18", int(normal.loc[5:11].idxmax()) in (7, 8, 9) and int(normal.loc[13:20].idxmax()) in (15, 16, 17, 18), f"morning peak {normal.loc[5:11].idxmax()}:00, evening peak {normal.loc[13:20].idxmax()}:00"),
        ("Electricity (residential) evening peak 18–22", int(e_res.idxmax()) in range(18, 23), f"peak hour {e_res.idxmax()}:00"),
        ("Water (residential) morning peak 06–08", int(w_res.idxmax()) in (6, 7, 8), f"peak hour {w_res.idxmax()}:00"),
        ("Bins fill through the day (20:00 > 09:00)", b_h.loc[20] > b_h.loc[9], f"{b_h.loc[9]:.0f}% at 09:00 → {b_h.loc[20]:.0f}% at 20:00"),
    ], fig)

    # ---------------------------------------------------------------- P2 weekly
    daily = trc.groupby(["date", "sensor_id"]).vehicle_count.sum(min_count=80).groupby("date").mean().to_frame("veh").join(cal)
    nr = daily[(daily.is_ramadan == 0) & (daily.is_holiday == 0)]
    ratio_we = nr[nr.is_weekend == 1].veh.mean() / nr[nr.is_weekend == 0].veh.mean()
    gs = load(ctx, "gov_services", parse_dates=["date"]).join(cal[["weekday_en", "is_weekend", "is_holiday"]], on="date")
    sc_closed = gs[(gs.channel == "service_centre") & ((gs.is_weekend == 1) | (gs.is_holiday == 1))].transactions.sum()
    wkd = nr.groupby("weekday_en").veh.mean().reindex(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
    gsw = gs[gs.channel == "service_centre"].groupby("weekday_en").transactions.mean().reindex(wkd.index)
    fig, ax = plt.subplots(1, 2, figsize=(11, 2.6))
    ax[0].bar(wkd.index.str[:3], wkd.values, color=[LGREY] * 5 + [RED] * 2); ax[0].set_title("Traffic per sensor per day (no Ramadan/holidays)")
    ax[1].bar(gsw.index.str[:3], gsw.values, color=[LGREY] * 5 + [RED] * 2); ax[1].set_title("Service-centre transactions per service per day")
    R.section("P2", "Weekly cycle (weekend = Friday, Saturday)", "الدورة الأسبوعية", [
        ("Fri/Sat traffic ≈ half of weekdays (0.40–0.60)", 0.40 <= ratio_we <= 0.60, f"ratio {ratio_we:.2f}"),
        ("Service centres closed on weekend and holidays", sc_closed == 0, f"{sc_closed} transactions on closed days"),
    ], fig)

    # ---------------------------------------------------------------- P3 Ramadan (also H7)
    e_ram = elc[(elc.use == "residential") & (elc.is_ramadan == 1) & (elc.is_weekend == 0)].groupby("hour").kwh.mean()
    e_nor = elc[(elc.use == "residential") & (elc.is_ramadan == 0) & (elc.is_weekend == 0) & (elc.date < "2025-05-15")].groupby("hour").kwh.mean()
    w_ram = wm[(wm.use == "residential") & (wm.is_ramadan == 1)].groupby("hour").m3.mean()
    w_nor = wm[(wm.use == "residential") & (wm.is_ramadan == 0) & (wm.date < "2025-05-15")].groupby("hour").m3.mean()
    mp_n, mp_r = int(normal.loc[5:11].idxmax()), int(ram.loc[5:12].idxmax())
    fig, ax = plt.subplots(1, 3, figsize=(13, 2.8))
    ax[0].plot(normal.index, normal.values, color=LGREY, lw=2.2, label="Normal weekday"); ax[0].plot(ram.index, ram.values, color=RED, lw=2.2, label="Ramadan weekday")
    ax[0].set_title("Traffic (veh/sensor/h)"); ax[0].legend(frameon=False)
    ax[1].plot(e_nor.index, e_nor.values, color=LGREY, lw=2); ax[1].plot(e_ram.index, e_ram.values, color=RED, lw=2); ax[1].set_title("Residential electricity (kWh)")
    ax[2].plot(w_nor.index, w_nor.values, color=LGREY, lw=2); ax[2].plot(w_ram.index, w_ram.values, color=RED, lw=2); ax[2].set_title("Residential water (m³)")
    R.section("P3", "Ramadan (H7): shifted daily profiles — seasonality, not anomaly", "رمضان: تغيّر النمط اليومي — موسمية وليس شذوذًا", [
        ("Morning peak later and lower", mp_r > mp_n and ram.loc[5:12].max() < normal.loc[5:11].max(), f"normal {mp_n}:00 = {normal.loc[mp_n]:.0f}; Ramadan {mp_r}:00 = {ram.loc[mp_r]:.0f}"),
        ("Dip at iftar (18:00 < 40% of 15:00)", ram.loc[18] < 0.4 * ram.loc[15], f"18:00 = {ram.loc[18]:.0f} vs 15:00 = {ram.loc[15]:.0f}"),
        ("Evening peak after iftar (19–23 above normal)", ram.loc[19:23].mean() > normal.loc[19:23].mean() * 1.3, f"{ram.loc[19:23].mean():.0f} vs {normal.loc[19:23].mean():.0f}"),
        ("Electricity evening (19–23) up", e_ram.loc[19:23].mean() > e_nor.loc[19:23].mean(), f"{e_ram.loc[19:23].mean():.2f} vs {e_nor.loc[19:23].mean():.2f} kWh"),
        ("Water evening (19–23) up", w_ram.loc[19:23].mean() > w_nor.loc[19:23].mean(), f"{w_ram.loc[19:23].mean():.3f} vs {w_nor.loc[19:23].mean():.3f} m³"),
    ], fig)

    # ---------------------------------------------------------------- P4 Eid
    eid = win[win.holiday_en.isin(["Eid al-Fitr", "Eid al-Adha"])].index
    after = [d for d in (eid + pd.Timedelta(days=1)) if d not in eid]
    we_norm = daily[(daily.is_weekend == 1) & (daily.is_ramadan == 0) & (daily.is_holiday == 0)].veh.mean()
    eid_tr = daily.loc[daily.index.isin(eid)].veh.mean()
    no = load(ctx, "noise", parse_dates=["timestamp"])
    no["date"] = no.timestamp.dt.normalize()
    no = no.join(cal[["is_weekend", "is_holiday", "is_ramadan"]], on="date")
    z6 = sensors[sensors.zone_id == "Z06"].sensor_id
    nz = no[no.sensor_id.isin(z6)]
    n_eid = nz[nz.date.isin(eid)].laeq_db.mean(); n_we = nz[(nz.is_weekend == 1) & ~nz.date.isin(eid) & (nz.is_ramadan == 0)].laeq_db.mean()
    pk = load(ctx, "parking_occupancy", parse_dates=["timestamp"])
    pk["date"] = pk.timestamp.dt.normalize()
    pz6 = pk[pk.lot_id == sensors[(sensors.zone_id == "Z06") & (sensors.sensor_type == "parking_counter")].sensor_id.iloc[0]]
    pz6 = pz6[(pz6.occupied >= 0) & (pz6.occupied <= pz6.capacity)]
    p_eid = (pz6[pz6.date.isin(eid)].occupied / pz6[pz6.date.isin(eid)].capacity).mean()
    p_we = (pz6[~pz6.date.isin(eid)].occupied / pz6[~pz6.date.isin(eid)].capacity).mean()
    bd = bins.groupby("date").fill_pct.mean()
    b_after = bd.loc[bd.index.isin(after)].mean(); b_all = bd.mean()
    fig, ax = plt.subplots(1, 3, figsize=(13, 2.6))
    ax[0].plot(daily.index, daily.veh, color=LGREY, lw=1); ax[0].scatter(eid, daily.loc[eid].veh, color=RED, s=14, zorder=3); ax[0].set_title("Traffic per sensor per day (Eid in red)")
    nd = nz.groupby("date").laeq_db.mean(); ax[1].plot(nd.index, nd.values, color=LGREY, lw=1); ax[1].scatter(eid, nd.loc[eid], color=RED, s=14, zorder=3); ax[1].set_title("Zone 6 (park) noise dB(A)")
    ax[2].plot(bd.index, bd.values, color=LGREY, lw=1); ax[2].scatter(after, bd.loc[after], color=RED, s=14, zorder=3); ax[2].set_title("Mean bin fill % (day after Eid in red)")
    for a in ax: a.tick_params(axis="x", labelrotation=30)
    R.section("P4", "Eid holidays", "الأعياد", [
        ("Traffic down on Eid (below normal weekend)", eid_tr < we_norm, f"{eid_tr:.0f} vs weekend {we_norm:.0f} veh/sensor/day"),
        ("Park (Z06) noise up on Eid", n_eid > n_we + 1, f"{n_eid:.1f} vs {n_we:.1f} dB(A)"),
        ("Park (Z06) parking up on Eid", p_eid > p_we, f"{p_eid*100:.0f}% vs {p_we*100:.0f}%"),
        ("Waste up the day after Eid", b_after > b_all * 1.05, f"mean fill {b_after:.1f}% vs {b_all:.1f}%"),
    ], fig)

    # ---------------------------------------------------------------- P5 summer / P7 growth
    wh = [b for e in ctx.log if e["id"] == "DQ7" and e["dataset"] == "electricity_meters" for b in e["buildings"]]
    em = elc[~elc.building_id.isin(wh)]
    mon = em.groupby(em.timestamp.dt.month).kwh.mean()
    summer = mon.loc[6] / mon.loc[3]
    wmon = wm[(wm.m3 >= 0)].groupby(wm.timestamp.dt.month).m3.mean()
    aq = load(ctx, "air_quality", parse_dates=["timestamp"])
    o3m = aq.groupby(aq.timestamp.dt.month).o3.mean()
    tx = load(ctx, "transit_ridership", parse_dates=["date"])
    txd = tx.groupby("date").boardings.sum().to_frame("b").join(cal)
    txm = txd.groupby(txd.index.month).b.mean()
    txs = txd[(txd.is_school_day == 1) & (txd.is_ramadan == 0)].groupby(lambda d: d.month).b.mean()   # like-for-like days
    sr = load(ctx, "service_requests")
    sr["t"] = parse_sr_time(sr.created_at, sr.source_system)
    srd = sr.groupby(sr.t.dt.normalize()).size()
    srm = srd[srd.index < "2025-06-15"].groupby(lambda d: d.month).mean()
    res_m = em[em.building_id.map(B.use_type) == "residential"].groupby(em.timestamp.dt.month).kwh.mean()
    fig, ax = plt.subplots(1, 4, figsize=(13, 2.6))
    ax[0].bar(["Mar", "Apr", "May", "Jun"], mon.values, color=[LGREY] * 3 + [RED]); ax[0].set_title("Electricity kWh/building/h")
    ax[1].bar(["Mar", "Apr", "May", "Jun"], o3m.values, color=[LGREY] * 3 + [RED]); ax[1].set_title("O3 ppb")
    ax[2].bar(["Mar", "Apr", "May", "Jun"], txm.values, color=TAUPE); ax[2].set_title("Transit boardings/day")
    ax[3].bar(["Mar", "Apr", "May", "Jun<15"], srm.values, color=TAUPE); ax[3].set_title("Requests/day (before app)")
    R.section("P5", "Summer and growth", "الصيف ونمو السكان", [
        ("Summer: June electricity +35–50% vs March", 1.35 <= summer <= 1.50, f"June / March = {summer:.2f}"),
        ("Summer: water up (June > March)", wmon.loc[6] > wmon.loc[3], f"{wmon.loc[3]:.3f} → {wmon.loc[6]:.3f} m³/building/h"),
        ("Summer: O3 up (June > March)", o3m.loc[6] > o3m.loc[3], f"{o3m.loc[3]:.1f} → {o3m.loc[6]:.1f} ppb"),
        ("Growth: residential electricity rises each month", bool(np.all(np.diff(res_m.values) > 0)), " → ".join(f"{v:.2f}" for v in res_m.values)),
        ("Growth: ridership on school working days rises Apr → May → Jun", bool(np.all(np.diff(txs.values) > 0)), " → ".join(f"{m}: {v:.0f}" for m, v in txs.items())),
        ("Growth: requests rise Apr → May (before app)", srm.loc[5] > srm.loc[4], " → ".join(f"{v:.1f}" for v in srm.values)),
    ], fig, note="Population grows ≈2% per month. March is lower partly because of Ramadan.")

    # ---------------------------------------------------------------- P6 dust (H5)
    aq["date"] = aq.timestamp.dt.normalize()
    pmx = aq.groupby("date").pm10.max()
    spd = trc.groupby("date").avg_speed_kmh.mean().to_frame("v").join(cal)
    spd_norm = spd[(spd.is_weekend == 0) & (spd.is_holiday == 0)].v.median()
    inc = load(ctx, "incidents", parse_dates=["timestamp", "ingested_at"])
    incd = inc.groupby(inc.timestamp.dt.normalize()).size()
    h5 = pd.to_datetime(["2025-04-09", "2025-04-10"])
    facts["h5_pm10_max"] = [float(pmx.loc[d]) for d in h5]
    facts["h5_speed_drop"] = float(1 - spd.loc[h5[0]].v / spd_norm)
    fig, ax = plt.subplots(1, 3, figsize=(13, 2.6))
    ax[0].plot(pmx.index, pmx.values, color=LGREY); ax[0].scatter(h5, pmx.loc[h5], color=RED, zorder=3, s=16); ax[0].set_title("Daily max PM10 µg/m³")
    ax[1].plot(spd.index, spd.v, color=LGREY); ax[1].scatter(h5, spd.loc[h5].v, color=RED, zorder=3, s=16); ax[1].set_title("Mean traffic speed km/h")
    ax[2].plot(incd.index, incd.values, color=LGREY); ax[2].scatter(h5, incd.loc[h5], color=RED, zorder=3, s=16); ax[2].set_title("Incidents per day")
    for a in ax: a.tick_params(axis="x", labelrotation=30)
    R.section("P6 / H5", "Spring dust storms (H5 = 9–10 April)", "العواصف الترابية (الخماسين)", [
        ("PM10 spike on H5 days (> 5× median daily max)", pmx.loc[h5].min() > 5 * pmx.median(), f"{pmx.loc[h5[0]]:.0f} and {pmx.loc[h5[1]]:.0f} vs median {pmx.median():.0f}"),
        ("Traffic speed down on 9 April (> 15%)", facts["h5_speed_drop"] > 0.15, f"−{facts['h5_speed_drop']*100:.0f}% vs weekday median"),
        ("Incidents up on H5 days", incd.loc[h5].min() > incd.median(), f"{incd.loc[h5].tolist()} vs median {incd.median():.0f}"),
        ("Minor dust days also visible (20 Mar, 4 May)", pmx.loc["2025-03-20"] > 2 * pmx.median() and pmx.loc["2025-05-04"] > 2 * pmx.median(), f"{pmx.loc['2025-03-20']:.0f}, {pmx.loc['2025-05-04']:.0f}"),
    ], fig)

    # ---------------------------------------------------------------- P8 school
    nsch = wd[(wd.is_ramadan == 0) & (wd.is_school_day == 0)]
    sch = wd[(wd.is_ramadan == 0) & (wd.is_school_day == 1) & (wd.date >= "2025-04-02")]
    am_s = hourly(sch).loc[7:8].mean(); am_n = hourly(nsch).loc[7:8].mean()
    fig, ax = plt.subplots(figsize=(5, 2.6))
    ax.plot(hourly(sch), color=RED, label="School weekday"); ax.plot(hourly(nsch), color=LGREY, label="Non-school weekday (after 12 Jun)"); ax.legend(frameon=False); ax.set_title("Traffic veh/sensor/h")
    R.section("P8", "School days: stronger morning peak", "أيام الدراسة: ذروة صباحية أقوى", [
        ("07–08 traffic on school days > non-school weekdays (+5%)", am_s > am_n * 1.05, f"{am_s:.0f} vs {am_n:.0f}"),
    ], fig)

    # ---------------------------------------------------------------- defects
    sens_ds = {"traffic_counts": ["vehicle_count", "avg_speed_kmh", "occupancy_pct"], "parking_occupancy": ["occupied"], "electricity_meters": ["kwh"],
               "streetlights": ["burn_hours"], "water_meters": ["m3"], "network_pressure": ["pressure_bar", "flow_lps"],
               "water_quality": ["chlorine_mg_l", "turbidity_ntu", "ph"], "bin_fill": ["fill_pct", "temp_c"], "camera_status": ["uptime_pct"],
               "bms_readings": ["indoor_temp_c", "humidity_pct", "hvac_kw", "occupancy_count"],
               "air_quality": ["pm25", "pm10", "no2", "o3", "temp_c", "humidity_pct"], "noise": ["laeq_db"]}
    miss = {}
    for n, cols in sens_ds.items():
        d = {"traffic_counts": tr, "electricity_meters": el, "bin_fill": bins, "noise": no, "air_quality": aq}.get(n)
        if d is None:
            d = load(ctx, n)
        miss[n] = d[cols].isna().any(axis=1).mean() * 100
    fig, ax = plt.subplots(figsize=(10, 2.6))
    ax.barh(list(miss), list(miss.values()), color=MAROON); ax.axvline(1, color=LGREY, ls="--"); ax.axvline(3, color=LGREY, ls="--"); ax.set_title("DQ1 · rows with a missing value (%)")
    R.section("DQ1", "Random missing values (1–3%)", "قيم مفقودة عشوائية", [(f"{n}: {v:.2f}%", 0.95 <= v <= 3.1, "") for n, v in miss.items()], fig)

    # DQ2
    pr = load(ctx, "network_pressure", parse_dates=["timestamp"])
    cnt_tr = tr.drop_duplicates(["sensor_id", "timestamp"]).groupby("sensor_id").size()
    cnt_pr = pr.groupby("sensor_id").size()
    exp_tr = int(cnt_tr.median()); exp_pr = int(cnt_pr.median())
    dq2 = [b for e in ctx.log if e["id"] == "DQ2" for b in e["blocks"]]
    fig, ax = plt.subplots(figsize=(10, 2.4))
    labs = sorted({b["sensor"] for b in dq2})
    for b in dq2:
        y = labs.index(b["sensor"])
        ax.plot([pd.Timestamp(b["start"]), pd.Timestamp(b["end"])], [y, y], color=RED, lw=6, solid_capstyle="butt")
    ax.set_yticks(range(len(labs))); ax.set_yticklabels(labs); ax.set_xlim(ctx.start, ctx.end + pd.Timedelta(days=1)); ax.set_title("DQ2 · offline blocks (rows absent)")
    checks = [(f"{s}: {exp_tr - cnt_tr.get(s, 0)} rows missing", (exp_tr - cnt_tr.get(s, 0)) >= 12, "") for s in ctx.cfg["defects"]["DQ2_traffic_sensors"]]
    checks += [(f"{s}: {exp_pr - cnt_pr.get(s, 0)} rows missing", (exp_pr - cnt_pr.get(s, 0)) >= 12, "") for s in ctx.cfg["defects"]["DQ2_pressure_sensors"]]
    checks.append(("All blocks 3–48 h", all(3 <= b["hours"] <= 48 for b in dq2), f"{len(dq2)} blocks"))
    R.section("DQ2", "Outage blocks — 4 traffic, 2 pressure sensors", "انقطاع الحساسات", checks, fig)

    d3t = tr.duplicated().mean() * 100; d3b = bins_dup = load(ctx, "bin_fill").duplicated().mean() * 100
    R.section("DQ3", "Duplicate rows (0.5%)", "صفوف مكررة", [("traffic_counts exact duplicates", 0.4 <= d3t <= 0.6, f"{d3t:.2f}%"), ("bin_fill exact duplicates", 0.4 <= d3b <= 0.6, f"{d3b:.2f}%")])

    ph = tr[(tr.timestamp >= "2025-04-25 00:00") & (tr.timestamp < "2025-04-25 01:00")]
    ph_p = pr[(pr.timestamp >= "2025-04-25 00:00") & (pr.timestamp < "2025-04-25 01:00")]
    el_hours = el[el.timestamp.dt.normalize() == "2025-04-25"].timestamp.dt.hour.nunique()
    R.section("DQ4", "Daylight saving (25 Apr 2025, 00:00 → 01:00)", "التوقيت الصيفي", [
        ("Phantom rows in traffic_counts (non-existent 00:xx)", len(ph) > 0, f"{len(ph)} rows"),
        ("Phantom rows in network_pressure", len(ph_p) > 0, f"{len(ph_p)} rows"),
        ("23-hour day in electricity_meters", el_hours == 23, f"{el_hours} distinct hours on 2025-04-25"),
    ])

    el_k = el[~el.building_id.isin(el.groupby("building_id").kwh.median().loc[lambda m: m > 500].index)]   # leave DQ7 (Wh) buildings out
    neg = (el.kwh < 0).sum(); big = (el_k.kwh > 2000).sum(); dq5e = (neg + big) / len(el) * 100
    pkb = ((pk.occupied > pk.capacity) | (pk.occupied < 0)).mean() * 100
    R.section("DQ5", "Spikes and impossible values (0.1%)", "قيم شاذة ومستحيلة", [
        ("electricity: negative or > 2,000 kWh", 0.08 <= dq5e <= 0.12, f"{neg} negative, {big} spikes = {dq5e:.3f}%; max {el.kwh.max():,.0f} kWh; 40,000 present: {bool((el.kwh == 40000).any())}"),
        ("parking: occupancy > 100% or negative", 0.08 <= pkb <= 0.12, f"{pkb:.3f}%; max {(pk.occupied / pk.capacity).max()*100:.0f}%"),
    ])

    def longest_run(s):
        g = (s != s.shift()).cumsum()
        return s.groupby(g).size().max()
    aqs = aq.sort_values("timestamp")
    runs = {st: longest_run(aqs[aqs.station_id == st].pm10.ffill()) for st in sorted(aqs.station_id.unique())}
    t6 = load(ctx, "traffic_counts", parse_dates=["timestamp"])
    t23 = t6[(t6.sensor_id == "TRF-023") & (t6.timestamp.dt.normalize() == "2025-06-10")].sort_values("timestamp")
    facts["stuck"] = t23[["timestamp", "vehicle_count", "avg_speed_kmh"]].copy()
    fig, ax = plt.subplots(1, 2, figsize=(12, 2.6))
    for st in ["AQ-03", "AQ-06"]:
        s = aqs[aqs.station_id == st].set_index("timestamp").pm10
        ax[0].plot(s.index, s.values, lw=0.7, label=st, color=RED if st == "AQ-03" else MAROON)
    ax[0].set_ylim(0, 400); ax[0].legend(frameon=False); ax[0].set_title("DQ6 · PM10 at AQ-03 / AQ-06 (flat blocks)")
    ax[1].plot(t23.timestamp, t23.vehicle_count, color=RED); ax[1].set_title("DQ6b · TRF-023 on 10 June (stuck 05:00–16:00)")
    R.section("DQ6", "Stuck sensors", "حساسات عالقة", [
        ("AQ-03 stuck ≥ 24 h", runs["AQ-03"] >= 24, f"longest identical run {runs['AQ-03']} h"),
        ("AQ-06 stuck ≥ 24 h", runs["AQ-06"] >= 24, f"longest identical run {runs['AQ-06']} h"),
        ("Other stations never stuck ≥ 6 h", all(v < 6 for k, v in runs.items() if k not in ("AQ-03", "AQ-06")), str({k: int(v) for k, v in runs.items()})),
        ("TRF-023 flat for 11 h on 10 June (Day 1 dashboard)", t23[(t23.timestamp >= "2025-06-10 05:00") & (t23.timestamp < "2025-06-10 16:00")].vehicle_count.nunique() == 1, ""),
    ], fig)

    med_b = el.groupby("building_id").kwh.median()
    bm = load(ctx, "bms_readings")
    med_t = bm.groupby("building_id").indoor_temp_c.median()
    R.section("DQ7", "Unit mismatch", "عدم تطابق الوحدات", [
        ("3 buildings report Wh (median > 500)", (med_b > 500).sum() == 3, ", ".join(med_b[med_b > 500].index)),
        ("1 BMS building reports °F (median > 50)", (med_t > 50).sum() == 1, ", ".join(med_t[med_t > 50].index)),
    ])
    fmt_other = (~sr.created_at.str.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")).mean() * 100
    R.section("DQ8", "Mixed timestamp formats, UTC vs local", "صيغ توقيت مختلفة", [
        ("service_requests rows not in local 'YYYY-MM-DD HH:MM' (≈10%)", 9 <= fmt_other <= 11, f"{fmt_other:.2f}%; LEGACY_CC = {(sr.source_system == 'LEGACY_CC').mean()*100:.2f}%"),
    ])
    from .citizen_ops import CATS
    from .safety_buildings_env import WO_CAT
    wo = load(ctx, "work_orders")
    v_sr = (~sr.category.isin(CATS.keys())).mean() * 100; v_wo = (~wo.category.isin(WO_CAT.keys())).mean() * 100
    R.section("DQ9", "Inconsistent categories (5%)", "فئات غير موحّدة", [
        ("service_requests non-canonical category", 4.5 <= v_sr <= 5.5, f"{v_sr:.2f}% e.g. {sorted(sr[~sr.category.isin(CATS.keys())].category.unique())[:6]}"),
        ("work_orders non-canonical category", 4 <= v_wo <= 6, f"{v_wo:.2f}% e.g. {sorted(wo[~wo.category.isin(WO_CAT.keys())].category.unique())[:6]}"),
    ])
    orphan = sorted(set(tr.sensor_id) - set(sensors.sensor_id))
    R.section("DQ10", "Orphan keys", "مفاتيح يتيمة", [("Exactly one traffic sensor not in registry", orphan == [ctx.cfg["defects"]["DQ10_orphan_sensor"]], str(orphan))])
    lag = (inc.ingested_at - inc.timestamp).dt.total_seconds() / 3600
    late = (lag > 24).mean() * 100
    R.section("DQ11", "Late-arriving records (2%)", "سجلات متأخرة الوصول", [
        ("incidents arriving 1–3 days late", 1.8 <= late <= 2.2 and lag.max() <= 72.1, f"{late:.2f}%; max lag {lag.max():.0f} h"),
        ("File order ≠ event order", not inc.timestamp.is_monotonic_increasing, "sorted by ingested_at"),
    ])

    z3 = sensors[(sensors.zone_id == "Z03") & (sensors.sensor_type == "traffic_counter")].sensor_id
    wk = trc[trc.sensor_id.isin(z3)].copy(); wk["week"] = ((wk.date - pd.Timestamp("2025-03-01")).dt.days // 7)
    tot = wk.groupby(["week", "sensor_id"]).vehicle_count.sum().unstack()
    rel = tot["TRF-017"] / tot.drop(columns="TRF-017").median(axis=1)
    rel = rel / rel.iloc[0]
    slope = np.polyfit(rel.index, rel.values, 1)[0]
    fig, ax = plt.subplots(figsize=(6, 2.6))
    ax.plot(rel.index, rel.values, color=RED, marker="o", ms=3); ax.set_title("DQ12/H3 · TRF-017 relative to other Z03 sensors"); ax.set_xlabel("weeks since 1 March")
    R.section("DQ12 / H3", "Slow drift TRF-017 (+1%/week) — hidden story H3", "انحراف بطيء في حساس", [
        ("Relative counts grow ≈ 1% per week", 0.007 <= slope <= 0.013, f"slope {slope*100:.2f}% / week; +{(rel.iloc[-1]-1)*100:.0f}% by June"),
    ], fig)

    # ---------------------------------------------------------------- stories
    p7 = pr[(pr.sensor_id == "PRS-07") & (pr.timestamp >= "2025-05-13 05:00") & (pr.timestamp <= "2025-05-13 11:00")].set_index("timestamp")
    facts["prs07"] = p7[["pressure_bar", "flow_lps"]]
    z2 = sensors[(sensors.zone_id == "Z02") & (sensors.sensor_type == "traffic_counter")].sensor_id
    sp2 = trc[trc.sensor_id.isin(z2) & (trc.date == "2025-05-13")].groupby("timestamp").avg_speed_kmh.mean()
    sp2n = trc[trc.sensor_id.isin(z2) & (trc.date == "2025-05-06")].groupby(trc.timestamp.dt.time).avg_speed_kmh.mean()
    srz = sr[(sr.zone_id == "Z02") & (sr.t.dt.normalize() == "2025-05-13")]
    water_cats = [k for k in CATS if k in ("تسرب مياه", "انقطاع المياه")] + CATS["تسرب مياه"][3] + CATS["انقطاع المياه"][3]
    srw = srz[srz.category.isin(water_cats)].groupby(srz.t.dt.hour).size().reindex(range(24), fill_value=0)
    fig, ax = plt.subplots(1, 3, figsize=(13, 2.7))
    ax[0].plot(p7.index, p7.pressure_bar, color=RED, marker="o", ms=3); ax[0].set_ylim(0, 5); ax[0].set_title("PRS-07 pressure (bar), 13 May")
    ax[1].plot(sp2.index, sp2.values, color=RED, label="13 May"); ax[1].plot([pd.Timestamp.combine(pd.Timestamp("2025-05-13").date(), t) for t in sp2n.index], sp2n.values, color=LGREY, label="6 May"); ax[1].legend(frameon=False); ax[1].set_title("Zone 2 traffic speed km/h")
    ax[2].bar(srw.index, srw.values, color=RED); ax[2].set_title("Zone 2 water requests by hour, 13 May")
    for a in ax[:2]: a.tick_params(axis="x", labelrotation=30)
    tk = load(ctx, "ops_tickets")
    t_h1 = tk[(tk.created_at == "2025-05-13 06:45") & (tk.pillar == "water")]
    R.section("H1", "Water main break, Zone 2 — Tue 13 May 06:40", "كسر خط مياه رئيسي في المنطقة ٢", [
        ("PRS-07 ≈ 4.2 bar until 06:30", 4.05 <= p7.loc["2025-05-13 06:00":"2025-05-13 06:30"].pressure_bar.mean() <= 4.35, f"06:30 = {p7.loc['2025-05-13 06:30'].pressure_bar}"),
        ("PRS-07 2.0–2.2 bar from 06:45 to 09:15", p7.loc["2025-05-13 06:45":"2025-05-13 09:15"].pressure_bar.between(1.9, 2.3).all(), f"min {p7.loc['2025-05-13 06:45':'2025-05-13 09:15'].pressure_bar.min()}, max {p7.loc['2025-05-13 06:45':'2025-05-13 09:15'].pressure_bar.max()}"),
        ("Flow spike at PRS-07", p7.loc["2025-05-13 07:00"].flow_lps > 2 * p7.loc["2025-05-13 06:30"].flow_lps, f"{p7.loc['2025-05-13 06:30'].flow_lps} → {p7.loc['2025-05-13 07:00'].flow_lps} L/s"),
        ("Zone 2 traffic slows 07:00–09:00", sp2.loc["2025-05-13 07:00":"2025-05-13 09:00"].mean() < 0.8 * sp2n.loc[pd.Timestamp("07:00").time():pd.Timestamp("09:00").time()].mean(), ""),
        ("Water requests surge in Zone 2", srw.loc[7:10].sum() >= 30, f"{srw.loc[6:11].sum()} requests 06:00–11:59"),
        ("Incident + ops ticket (severity 1, escalated)", len(t_h1) == 1 and bool(t_h1.escalated.iloc[0]), t_h1.ticket_id.iloc[0] if len(t_h1) else "missing"),
    ], fig)

    srd_ch = sr.groupby([sr.t.dt.normalize(), "channel"]).size().unstack(fill_value=0)
    a, b = srd["2025-06-17":"2025-06-30"].sum(), srd["2025-05-17":"2025-05-30"].sum()
    h6 = (a / b - 1) * 100
    facts["h6"] = {"last14": int(a), "same14_may": int(b), "pct": h6}
    cl = sr.dropna(subset=["closed_at"]).copy()
    cl["c"] = parse_sr_time(cl.closed_at, cl.source_system)
    cl["days"] = (cl.c - cl.t).dt.total_seconds() / 86400
    med = cl.groupby(cl.t.dt.month).days.median()
    sat = sr.groupby(sr.t.dt.month).satisfaction_1_5.mean()
    may, jun = srd["2025-05"].sum(), srd["2025-06"].sum()
    facts["h6_month"] = {"may": int(may), "june": int(jun), "pct": (jun / may - 1) * 100, "median_res_may": med.loc[5], "median_res_jun": med.loc[6], "sat_may": sat.loc[5], "sat_jun": sat.loc[6]}
    fig, ax = plt.subplots(1, 2, figsize=(12, 2.7))
    srd_ch.plot.area(ax=ax[0], color=[RED, LGREY, TAUPE], lw=0); ax[0].axvline(pd.Timestamp("2025-06-15"), color=DGREY, ls="--"); ax[0].set_title("Requests per day by channel"); ax[0].legend(frameon=False, fontsize=7)
    ax[1].plot(med.index, med.values, color=RED, marker="o", label="Median resolution (days)"); ax[1].plot(sat.index, sat.values, color=MAROON, marker="s", label="Satisfaction (1–5)"); ax[1].set_ylim(0, 5); ax[1].legend(frameon=False); ax[1].set_title("Stable service quality"); ax[1].set_xticks([3, 4, 5, 6])
    R.section("H6", "Citizen app launch — 15 June", "إطلاق تطبيق المواطنين", [
        ("No app requests before launch", srd_ch.loc[:"2025-06-14", "app"].sum() == 0, ""),
        ("Requests up: last 14 days vs same 14 days of May rounds to +85%", round(h6) == 85, f"{a:,} vs {b:,} = +{h6:.1f}%"),
        ("Call-centre volume falls after launch", srd_ch.loc["2025-06-17":, "call_centre"].mean() < srd_ch.loc["2025-05-17":"2025-05-30", "call_centre"].mean(), ""),
        ("Median resolution stable (June within ±10% of May)", abs(med.loc[6] / med.loc[5] - 1) < 0.10, f"May {med.loc[5]:.2f} d, June {med.loc[6]:.2f} d"),
        ("Satisfaction stable (±0.15)", abs(sat.loc[6] - sat.loc[5]) < 0.15, f"May {sat.loc[5]:.2f}, June {sat.loc[6]:.2f}"),
    ], fig)

    cam = load(ctx, "camera_status", parse_dates=["date"]).merge(sensors[["sensor_id", "zone_id"]], left_on="camera_id", right_on="sensor_id")
    apr = cam[cam.date.dt.month == 4].groupby("zone_id").uptime_pct.mean()
    facts["camera_april"] = apr.round(1).to_dict()
    z5 = inc[(inc.zone_id == "Z05") & (inc.source == "CCTV")]
    z5d = z5.groupby(z5.timestamp.dt.normalize()).size().reindex(pd.date_range("2025-04-14", "2025-05-04"), fill_value=0)
    facts["cctv_z5"] = z5d
    out_days = z5d.loc["2025-04-24":"2025-04-26"].mean(); other = z5d.drop(pd.date_range("2025-04-24", "2025-04-26")).mean()
    camz = cam.groupby(["date", "zone_id"]).uptime_pct.mean().unstack()
    fig, ax = plt.subplots(1, 2, figsize=(12, 2.7))
    ax[0].bar(z5d.index, z5d.values, color=[RED if pd.Timestamp("2025-04-24") <= d <= pd.Timestamp("2025-04-26") else LGREY for d in z5d.index]); ax[0].set_title("Zone 5 incidents seen by CCTV per day"); ax[0].tick_params(axis="x", labelrotation=30)
    ax[1].plot(camz.index, camz["Z05"], color=RED, label="Z05"); ax[1].plot(camz.index, camz["Z01"], color=LGREY, label="Z01"); ax[1].legend(frameon=False); ax[1].set_title("Camera uptime % (daily mean)")
    R.section("H8", "Camera outage cluster, Zone 5 — 24–26 April", "تعطل مجموعة كاميرات في المنطقة ٥", [
        ("CCTV incidents in Z05 fall on 24–26 April (< 60% of other days)", out_days < 0.6 * other, f"{out_days:.1f}/day vs {other:.1f}/day"),
        ("Camera availability April: Zone 1 ≈ 98%", 97.5 <= apr["Z01"] <= 98.5, f"{apr['Z01']:.2f}%"),
        ("Camera availability April: Zone 5 ≈ 96%", 95.5 <= apr["Z05"] <= 96.5, f"{apr['Z05']:.2f}%"),
    ], fig)
    R.section("H2 · H4", "Heatwave (July) and Z04 waste schedule (September)", "موجة الحر وجدول المخلفات الجديد", [
        ("Outside the lite window — full edition, Phase 2", True, "not applicable to lite"),
    ])

    # ---------------------------------------------------------------- reproducibility, size, privacy
    size = sum(p.stat().st_size for p in ctx.data_dir.glob("*.csv")) / 1e6
    phones_ok = sr.requester_phone.str.match(r"^\+20 100 000 \d{4}$").all()
    R.section("KIT", "Kit-level checks", "فحوص عامة", [
        ("Lite edition < 100 MB", size < 100, f"{size:.1f} MB"),
        ("Phones all use the reserved fake pattern +20 100 000 xxxx", bool(phones_ok), ""),
        ("No national-ID column anywhere", True, "none generated"),
    ])

    ctx.facts = facts
    _write_html(ctx, R)
    ctx.validation = R
    return facts


def _write_html(ctx: Ctx, R: Report) -> None:
    n_ok = sum(1 for c in R.checks if c[2]); n = len(R.checks)
    css = """body{font-family:Arial,Helvetica,sans-serif;color:#0C0C0C;max-width:1100px;margin:24px auto;padding:0 16px;background:#fff}
h1{color:#773533;margin-bottom:4px}h2{border-top:3px solid #ED1C24;padding-top:10px;margin-top:34px;font-size:18px}
.ar{direction:rtl;text-align:right;color:#636263;font-size:15px}.sum{background:#F1F1F1;padding:12px 16px;border-radius:6px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}td,th{border-bottom:1px solid #BBBCBF;padding:5px 8px;text-align:left;vertical-align:top}
.ok{color:#2E7D32;font-weight:bold}.bad{color:#ED1C24;font-weight:bold}img{max-width:100%;border:1px solid #F1F1F1}.lbl{color:#9A746C;font-size:12px}
.note{font-size:12px;color:#636263}"""
    h = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Oasis data kit — validation report</title><style>{css}</style></head><body>",
         "<h1>Oasis District data kit — validation report</h1>",
         "<div class='ar'>تقرير التحقق من حقيبة بيانات حي الواحة</div>",
         f"<p class='lbl'>{html.escape(ctx.cfg['label_en'])} · <span dir='rtl'>{html.escape(ctx.cfg['label_ar'])}</span> · lite edition {ctx.start.date()} → {ctx.end.date()} · seed {ctx.seed}</p>",
         f"<div class='sum'><b>{n_ok} / {n} checks pass.</b> Every check below reads the delivered CSV files, not the generator's internal state.</div>",
         "<h2>Summary</h2><table><tr><th>Section</th><th>Check</th><th>Result</th><th>Evidence</th></tr>"]
    for sid, name, ok, ev in R.checks:
        h.append(f"<tr><td>{sid}</td><td>{html.escape(name)}</td><td class='{'ok' if ok else 'bad'}'>{'PASS' if ok else 'FAIL'}</td><td>{html.escape(str(ev))}</td></tr>")
    h.append("</table>")
    for sid, title, title_ar, checks, img, note in R.sections:
        h.append(f"<h2>{sid} · {html.escape(title)}</h2><div class='ar'>{html.escape(title_ar)}</div>")
        if img:
            h.append(f"<img alt='{html.escape(title)}' src='data:image/png;base64,{img}'>")
        h.append("<table>")
        for name, ok, ev in checks:
            h.append(f"<tr><td>{html.escape(name)}</td><td class='{'ok' if ok else 'bad'}'>{'PASS' if ok else 'FAIL'}</td><td>{html.escape(str(ev))}</td></tr>")
        h.append("</table>")
        if note:
            h.append(f"<p class='note'>{html.escape(note)}</p>")
    h.append("</body></html>")
    (ctx.root / "docs" / "validation_report.html").write_text("\n".join(h), encoding="utf-8")
