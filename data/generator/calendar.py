"""calendar.csv and the internal day-feature table every generator uses."""
from __future__ import annotations

import numpy as np
import pandas as pd
from hijridate import Hijri

from .common import Ctx

WD_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WD_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
SEASON = {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
          6: "summer", 7: "summer", 8: "summer", 9: "autumn", 10: "autumn", 11: "autumn"}


def _h(y, m, d) -> pd.Timestamp:
    return pd.Timestamp(Hijri(y, m, d).to_gregorian())


def holidays_2025() -> dict:
    """Synthetic approximation of Egyptian public holidays in 2025.
    Islamic dates come from the Umm al-Qura Hijri calendar (hijridate); observed dates may differ."""
    hol = {
        "2025-01-07": ("Coptic Christmas", "عيد الميلاد المجيد", None),
        "2025-01-25": ("Police Day and January Revolution", "عيد الشرطة وثورة يناير", None),
        "2025-04-21": ("Sham El-Nessim", "شم النسيم", None),
        "2025-04-25": ("Sinai Liberation Day", "عيد تحرير سيناء", None),
        "2025-05-01": ("Labour Day", "عيد العمال", None),
        "2025-06-30": ("June 30 Revolution", "ثورة ٣٠ يونيو", None),
        "2025-07-23": ("July 23 Revolution", "ثورة ٢٣ يوليو", None),
        "2025-10-06": ("Armed Forces Day", "عيد القوات المسلحة", None),
    }
    for i in range(3):
        d = _h(1446, 10, 1) + pd.Timedelta(days=i)
        hol[d.strftime("%Y-%m-%d")] = ("Eid al-Fitr", "عيد الفطر", "fitr")
    hol[_h(1446, 12, 9).strftime("%Y-%m-%d")] = ("Arafat Day", "وقفة عرفات", None)
    for i in range(4):
        d = _h(1446, 12, 10) + pd.Timedelta(days=i)
        hol[d.strftime("%Y-%m-%d")] = ("Eid al-Adha", "عيد الأضحى", "adha")
    hol[_h(1447, 1, 1).strftime("%Y-%m-%d")] = ("Islamic New Year", "رأس السنة الهجرية", None)
    hol[_h(1447, 3, 12).strftime("%Y-%m-%d")] = ("Prophet's Birthday", "المولد النبوي الشريف", None)
    return hol


def ramadan_range() -> tuple[pd.Timestamp, pd.Timestamp]:
    return _h(1446, 9, 1), _h(1446, 10, 1) - pd.Timedelta(days=1)


def build_calendar(ctx: Ctx) -> pd.DataFrame:
    cfg = ctx.cfg
    rng = ctx.rng("calendar.temperature")
    days = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    hol = holidays_2025()
    r0, r1 = ramadan_range()
    se = pd.Timestamp(str(cfg["events"]["school_year_end"]))
    ss = pd.Timestamp(str(cfg["events"]["school_year_start"]))
    c = pd.DataFrame({"date": days})
    c["weekday"] = c.date.dt.weekday
    c["weekday_en"] = [WD_EN[w] for w in c.weekday]
    c["weekday_ar"] = [WD_AR[w] for w in c.weekday]
    c["is_weekend"] = c.weekday.isin([4, 5])
    key = c.date.dt.strftime("%Y-%m-%d")
    c["is_holiday"] = key.isin(hol.keys())
    c["holiday_en"] = [hol.get(k, ("", "", None))[0] for k in key]
    c["holiday_ar"] = [hol.get(k, ("", "", None))[1] for k in key]
    c["eid"] = [hol.get(k, ("", "", None))[2] or "" for k in key]
    c["is_ramadan"] = (c.date >= r0) & (c.date <= r1)
    mid_year_break = (c.date >= "2025-01-24") & (c.date <= "2025-02-06")
    in_year = (c.date <= se) | (c.date >= ss)
    c["is_school_day"] = in_year & ~mid_year_break & ~c.is_weekend & ~c.is_holiday
    c["season"] = c.date.dt.month.map(SEASON)
    # internal features (not written to calendar.csv)
    doy = c.date.dt.dayofyear.to_numpy()
    noise = np.zeros(len(c))
    for i in range(1, len(c)):
        noise[i] = 0.75 * noise[i - 1] + rng.normal(0, 1.0)
    c["temp_mean"] = 21.5 - 7.5 * np.cos(2 * np.pi * (doy - 18) / 365) + noise
    c["dust"] = 0.0
    c["dust_story"] = ""
    for ev in cfg["events"]["dust_storms"]:
        m = c.date == pd.Timestamp(str(ev["date"]))
        c.loc[m, "dust"] = ev["intensity"]
        c.loc[m, "dust_story"] = ev.get("story", "")
    months = (c.date - pd.Timestamp("2025-01-01")).dt.days / 30.44
    g = (1 + cfg["district"]["growth_per_month"]) ** months
    c["growth"] = g
    c["population"] = (cfg["district"]["population_start"] * g).round().astype(int)
    c["is_eid"] = c.eid != ""
    eid_dates = set(c.date[c.is_eid])
    c["day_after_eid"] = [(d - pd.Timedelta(days=1)) in eid_dates and d not in eid_dates for d in c.date]
    # working-day flag: gov offices closed on weekend and holidays
    c["is_workday"] = ~c.is_weekend & ~c.is_holiday
    off = c.is_weekend | c.is_holiday
    c["day_type"] = np.select(
        [c.is_eid, c.is_ramadan & ~off, c.is_ramadan & off, off, c.is_school_day],
        ["eid", "ram_wd", "ram_we", "we", "wd_school"], default="wd_noschool")
    ctx.cal = c.set_index("date")
    return c


def write_calendar(ctx: Ctx) -> pd.DataFrame:
    c = ctx.cal.reset_index()
    out = c[["date", "weekday_en", "weekday_ar", "is_weekend", "is_holiday", "holiday_en", "holiday_ar",
             "is_ramadan", "is_school_day", "season"]].copy()
    out["date"] = out.date.dt.strftime("%Y-%m-%d")
    for b in ["is_weekend", "is_holiday", "is_ramadan", "is_school_day"]:
        out[b] = out[b].astype(int)
    ctx.ref_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(ctx.ref_dir / "calendar.csv", index=False, encoding="utf-8", lineterminator="\n")
    return out


def day_features(ctx: Ctx, ts: pd.Series) -> pd.DataFrame:
    """Join day features onto a timestamp series (fast, via date codes)."""
    d = ts.dt.normalize()
    f = ctx.cal.reindex(d.values)
    f.index = ts.index
    return f
