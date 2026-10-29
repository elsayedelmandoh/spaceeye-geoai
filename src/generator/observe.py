"""
propose: step 4. observation models: how each data owner records the hidden truth.
input: Signals, Setup, Truth, Economy, drivers, random generators.
output: supervisor reports (`reports`), utility meters and kWh (`meters`), ACUD warnings and status (`acud`), and `fin_rows` = the 45 written months of one compound.

  supervisor report  quarterly, dated 15-45 days after the quarter end (row sits in the month of the date), whole 5s in 30 % of the reports and one decimal
                     otherwise, optimistic developers add 2-8 points, 5 % missing (35 % while stalled). In every month where the real source announced a progress value,
                     the report IS that value (exact) and carries the published date.
  utilities          occupied units x 153 kWh x real temperature seasonality + standby per empty meter; before handover a site meter that follows the work done
  ACUD               grace expiry (decree art. 5, 12 months after the first promised date) -> warning; 3 months with no reported progress -> warning at the next
                     quarterly review (every 6 months while it lasts); a warning needs a stalled or late compound; status is recorded at each review
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.generator.economy import Economy
from src.generator.inputs import GEN, M_END, MONTHS, N, O0, mi
from src.generator.stories import Signals
from src.generator.truth import Setup, Truth

R, U, W = GEN["reports"], GEN["utilities"], GEN["warnings"]


@dataclass
class Reports:
    val: np.ndarray            # reported % in the month of the report, nan elsewhere
    date: np.ndarray           # report date (NaT elsewhere)
    announced: np.ndarray      # True where the value is a real announced value
    regular: np.ndarray        # True for the quarterly reports
    covers: np.ndarray         # month index of the quarter end a quarterly report describes (-1 elsewhere)
    due: int = 0               # quarterly reports that were due (their date falls inside the horizon)
    missing: int = 0           # of those, how many never arrived
    stalled_due: int = 0       # due reports of quarters in which work was stalled
    stalled_missing: int = 0


def reports(sig: Signals, st: Setup, tr: Truth, rng: np.random.Generator) -> Reports:
    val, date = np.full(N, np.nan), np.full(N, np.datetime64("NaT"), dtype="datetime64[ns]")
    ann, reg, cov = np.zeros(N, bool), np.zeros(N, bool), np.full(N, -1)
    n_due = n_miss = s_due = s_miss = 0
    for qm in range(N):
        if MONTHS[qm].month % 3 or qm < st.cstart:
            continue
        lag = int(rng.integers(R["lag_days"][0], R["lag_days"][1] + 1)) + (int(rng.integers(*R["late_extra_days"], endpoint=True)) if st.style == "late" else 0)
        d = M_END[qm] + pd.Timedelta(days=lag)
        rm = mi(d)
        stalled = tr.progress[qm] - tr.progress[max(qm - 3, 0)] < 0.5 and tr.progress[qm] < 99
        missing = rng.random() < (R["missing_stall"] if stalled else R["missing_normal"]) + (0.03 if st.style == "late" else 0)
        bias = (st.optimism + (R["optimism_stall_extra"] if stalled else 0.0)) if st.style == "optimistic" else rng.normal(0.0, R["accurate_sd"])
        v = float(np.clip(tr.progress[qm] + bias, 0, 100))
        v = float(round(v / 5) * 5) if rng.random() < R["round5_share"] else round(v, 1)
        if rm < N:
            n_due, n_miss, s_due, s_miss = n_due + 1, n_miss + missing, s_due + stalled, s_miss + (missing and stalled)
        if rm < N and not missing:
            val[rm], date[rm], reg[rm], cov[rm] = v, np.datetime64(d), True, qm
    announced = {}
    for (m, v, _), d in zip(sig.anchors, sig.anchor_dates):
        if m < N:
            announced[m] = (v, d)
    nxt = np.full(N, 100.0)                                 # the next announced value caps the regular reports before it
    for m in sorted(announced, reverse=True):
        nxt[:m + 1] = announced[m][0]
    last = 0.0
    for m in range(N):
        if m in announced:
            val[m], date[m], ann[m], reg[m], cov[m] = announced[m][0], np.datetime64(announced[m][1]), True, False, -1
        elif not np.isnan(val[m]):
            val[m] = round(min(max(val[m], last), nxt[m]), 1)
        if not np.isnan(val[m]):
            last = val[m]
    return Reports(val, date, ann, reg, cov, n_due, int(n_miss), int(s_due), int(s_miss))


def season_kwh(drv) -> np.ndarray:
    """seasonal factor of household electricity from the real monthly max temperature, normalised to a mean of 1 over the calendar."""
    raw = 1 + U["seasonal_slope"] * (drv.tmax_c.values - 19.5) / 18.5
    return raw / pd.Series(raw).groupby(MONTHS.month).mean().mean()


def meters(sig: Signals, st: Setup, tr: Truth, drv, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """meters_active (handed-over units with a contract), kwh per month as the utility records it, and the occupied-homes part of the true kWh."""
    t = np.arange(N)
    act = np.zeros(N)
    for m in np.nonzero(tr.batches)[0]:
        act += tr.batches[m] * (0.5 + 0.42 * np.clip((t - m) / 12.0, 0, 1)) * (t >= m)
    act = np.minimum(np.maximum.accumulate(np.round(act)), tr.handed)
    dprog = np.diff(tr.progress, prepend=0.0)
    site = np.where(t >= st.cstart, float(rng.uniform(*U["site_base_kwh"])) + U["site_kwh_per_m2"] * sig.bua_m2 * dprog / 100 * rng.lognormal(0, 0.15, N), 0.0)
    site = np.where(tr.progress < 99.5, site, 0.0)
    home_occ = tr.occupied * U["kwh_per_unit"] * season_kwh(drv) * rng.lognormal(0, U["kwh_sd"], N)
    kwh = site + home_occ + (act - np.minimum(tr.occupied, act)) * U["standby_kwh"]
    est = rng.random(N) < U["estimated_share"]                # estimated read: a copy of last month, the next read is actual
    for m in np.nonzero(est)[0]:
        if m:
            kwh[m] = kwh[m - 1]
    return act.astype(int), kwh, home_occ


def acud(sig: Signals, st: Setup, tr: Truth, eco: Economy, rep: Reports, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, list]:
    """warning_issued per month, status level per month, and the warning events (month, kind). ACUD only sees the reports, the meters, the ledgers and the dates."""
    warn, level, events = np.zeros(N, bool), np.array(["on_plan"] * N, dtype=object), []
    t_all = np.arange(N)
    cert = np.maximum.accumulate(np.nan_to_num(rep.val, nan=0.0))

    def gain(k: int) -> np.ndarray:
        return cert - np.concatenate([np.zeros(k), cert[:-k]])

    first_rep = int(np.argmax(~np.isnan(rep.val))) if (~np.isnan(rep.val)).any() else N
    handed = t_all >= min([m for m, _, _ in sig.handovers], default=N)
    seen = (t_all >= max(st.plan_start, first_rep) + W["stall_months"]) & (cert < 90) & ~handed
    stalled3 = seen & (gain(W["stall_months"]) < 0.5)           # no reported progress for a review cycle
    stalled6 = seen & (gain(2 * W["stall_months"]) < 1.0)       # six months in a row
    grace = next((t for t in range(N) if sig.k3[t] > W["complaint_grace_months"]), None)
    last_warn, cur = None, "on_plan"
    for t in range(N):
        review = MONTHS[t].month in W["review_months"]
        allowed = (not sig.state[t]) or sig.k3[t] > 0
        if grace is not None and t == grace:
            warn[t], last_warn = True, t
            events.append((t, "grace_expiry"))
        elif review and allowed and stalled3[t] and (last_warn is None or t - last_warn >= W["repeat_months"]):
            warn[t], last_warn = True, t
            events.append((t, "stall_review"))
        if review or t == grace or t == 0:
            if sig.k3[t] > 24 or stalled6[t] or (eco.land_late[t] >= 3 and eco.cover_balance[t] < eco.required[t]):
                cur = "distressed"
            elif sig.k3[t] > 0:
                cur = "late"
            elif cert[t] < tr.plan[t] - 10 and t >= st.plan_start:
                cur = "behind"
            else:
                cur = "on_plan"
        level[t] = cur
    return warn, level, events


def fin_rows(sig: Signals, st: Setup, tr: Truth, eco: Economy, rep: Reports, mt, kwh, warn, level, rng: np.random.Generator) -> pd.DataFrame:
    s = slice(O0, N)
    roads = np.clip(tr.roads + rng.normal(0, 0.02, N), 0, 1)
    return pd.DataFrame({
        "code": sig.code, "month": [str(p) for p in MONTHS[s]],
        "planned_pct": tr.plan[s].round(1), "reported_pct": rep.val[s], "report_date": pd.to_datetime(rep.date[s]),
        "units_sold": eco.sold[s], "avg_price_egp": eco.price[s].round(0), "collections_egp": eco.collections[s].round(0),
        "cover_required_egp": eco.required[s].round(0), "cover_balance_egp": eco.cover_balance[s].round(0), "cost_to_complete_egp": eco.ctc_cert[s].round(0),
        "land_due_egp": eco.land_due[s].round(0), "land_paid_egp": eco.land_paid[s].round(0), "land_months_late": eco.land_late[s].astype(int),
        "roads_paved_share": roads[s].round(2), "meters_active": mt[s], "kwh": kwh[s].round(0),
        "status_level": level[s], "warning_issued": warn[s],
    })
