"""
propose: monthly grid, real inputs (read only) and the extended drivers used by every generator step.
input: app_data/real/*.parquet (R1 outputs), configs/data.yaml.
output: MONTHS grid (2017-01 .. 2026-09), month helpers, `load_real()`, `drivers()`.
"""

import numpy as np
import pandas as pd

from src.pipeline.common import CFG, REAL

GEN = CFG["generator"]
LABEL = GEN["label"]
SIM = REAL.parent / "sim"
MONTHS = pd.period_range(GEN["warmup_start"], GEN["end"], freq="M")
N = len(MONTHS)
M_START = MONTHS.to_timestamp()                      # first day of each month
M_END = MONTHS.to_timestamp(how="end").normalize()   # last day of each month
DAYS = np.asarray(MONTHS.days_in_month)
O0 = int((MONTHS >= pd.Period(GEN["start"], "M")).argmax())   # first written month
N_OUT = N - O0
FLOAT_M = int((pd.Period(GEN["float_month"], "M") - MONTHS[0]).n)


def mi(ts) -> int:
    """month index of a date on the grid (can be negative or >= N)."""
    return int((pd.Period(pd.Timestamp(ts), "M") - MONTHS[0]).n)


def mlabel(m: int) -> str:
    return str(MONTHS[m])


def load_real() -> dict[str, pd.DataFrame]:
    names = ["compounds", "sat_quarterly", "sat_yearly", "statements", "drivers_monthly", "rules", "kpi_values"]
    return {n: pd.read_parquet(REAL / f"{n}.parquet") for n in names}


def _days_in(ranges: list, m: int) -> int:
    a, b = M_START[m], M_END[m]
    return sum(max(0, (min(b, pd.Timestamp(e)) - max(a, pd.Timestamp(s))).days + 1) for s, e in ranges)


def drivers(real_drivers: pd.DataFrame) -> pd.DataFrame:
    """real drivers on the full grid. before 2023-01 the price series are held at their first value; temperature uses the real calendar-month mean."""
    d = real_drivers.assign(m=real_drivers.month.map(lambda s: int((pd.Period(s, "M") - MONTHS[0]).n))).set_index("m")
    out = pd.DataFrame(index=range(N))
    for c in ("usd_egp", "policy_rate_pct", "materials_index"):
        out[c] = d[c].reindex(out.index).bfill().ffill()
    clim = d.groupby(MONTHS[d.index].month).tmax_mean_c.mean()
    out["tmax_c"] = [d.tmax_mean_c.get(m, clim[MONTHS[m].month]) for m in out.index]
    ram = GEN["ramadan_pre2023"] + CFG["drivers"]["ramadan"]
    eid = GEN["eid_pre2023"] + CFG["drivers"]["eid"]
    out["ramadan_share"] = [_days_in(ram, m) / DAYS[m] for m in out.index]
    out["eid_days"] = [_days_in(eid, m) for m in out.index]
    out["month"] = [str(p) for p in MONTHS]
    return out


def seasonal_work(drv: pd.DataFrame) -> np.ndarray:
    """productivity factor per month: Ramadan -20%, Jul/Aug heat -10%, Eid week -30% (weighted by the share of the month)."""
    s = GEN["progress"]["season"]
    heat = np.array([p.month in (7, 8) for p in MONTHS], dtype=float)
    eid = np.minimum(drv.eid_days.values, 7) / DAYS
    return 1 + s["ramadan"] * drv.ramadan_share.values + s["jul_aug"] * heat + s["eid_week"] * eid

