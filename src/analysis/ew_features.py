"""
propose: leak-free feature table for the early-warning experiment (EW_PROTOCOL.md section 2-3): one row per compound x quarterly cut-off.
input: app_data/sim/fin_monthly.parquet, app_data/sim/complaints.parquet, app_data/real/{kpi_values,compounds}.parquet; private/answer_key.parquet (labels only).
output: DataFrame from build_table(); every feature is computed from data dated <= the cut-off (snapshot() filters before it computes).
"""

import numpy as np
import pandas as pd

from src.generator.defects import PHONE
from src.pipeline.common import APP, PRIVATE, REAL, qindex, qlabel
from src.pipeline.privacy import mask_text

SIM = APP / "sim"
CUTOFF_QUARTERS = [qlabel(i) for i in range(qindex("2023Q4"), qindex("2026Q2") + 1)]
LAG_MONTHS = 6          # trend window = two quarters
COVER_CAP = 3.0

# feature groups (protocol section 3)
INTERNAL = [
    "cover_ratio", "cover_req0", "cover_ctc", "land_late", "cmp_rate90", "cmp_pctl", "gap", "report_age",
    "meters", "kwh_per_meter", "kwh_ratio",
]
SAT = ["A", "active", "K2", "K3", "level", "started"]
TREND_BASE = ["cover_ratio", "cover_ctc", "land_late", "cmp_rate90", "gap", "meters", "kwh_ratio"]
TREND_SAT = ["A", "K2"]
INTERNAL_ALL = INTERNAL + [f"d_{c}" for c in TREND_BASE]
SAT_ALL = SAT + [f"d_{c}" for c in TREND_SAT]
FEATURES = INTERNAL_ALL + SAT_ALL


def qend_month(quarter: str) -> pd.Period:
    return pd.Period(f"{quarter[:4]}-{3 * int(quarter[5]):02d}", "M")


def clean_fin(fin: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    """Unique monthly rows, unit corrections, and valid report events; never invent a report date."""
    fin = fin.copy()
    fin["month"] = pd.PeriodIndex(fin["month"], freq="M")
    mon = fin.sort_values(["code", "month"], kind="stable").drop_duplicates(["code", "month"], keep="first").reset_index(drop=True)
    mon["report_date"] = pd.to_datetime(mon["report_date"], errors="coerce")
    invalid = mon.reported_pct.notna() & (mon.report_date.isna() | mon.report_date.dt.to_period("M").ne(mon.month))
    mon.loc[invalid, ["reported_pct", "report_date"]] = [np.nan, pd.NaT]
    rep = mon.loc[mon.reported_pct.notna() & mon.report_date.notna(), ["code", "report_date", "reported_pct"]]
    rep = rep.sort_values(["code", "report_date"]).reset_index(drop=True)
    fixed = 0
    for idx in mon.groupby("code").groups.values():
        bal = mon.loc[idx, "cover_balance_egp"].to_numpy(dtype=float).copy()
        for i in range(1, len(bal)):
            prev = bal[i - 1]
            if prev > 0 and bal[i] < 0.005 * prev and 0.2 * prev <= bal[i] * 1000 <= 5 * prev:
                bal[i] *= 1000
                fixed += 1
        mon.loc[idx, "cover_balance_egp"] = bal
    return mon, rep, fixed


def clean_complaints(cmp_: pd.DataFrame, codes, start, end, names=()) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    """Use observable keys/time bounds; mask phones in accepted and quarantined text. No answer-key repairs."""
    out = cmp_.copy()
    out["created_at"] = pd.to_datetime(out["created_at"], errors="coerce")
    masked = 0
    if "text_ar" in out:
        has_phone = out.text_ar.fillna("").str.contains(PHONE)
        masked = int(has_phone.sum())
        out.loc[out.text_ar.notna(), "text_ar"] = out.loc[out.text_ar.notna(), "text_ar"].map(lambda value: mask_text(value, names))
    bad_code = ~out.code.isin(codes)
    bad_date = out.created_at.isna() | (out.created_at < pd.Timestamp(start)) | (out.created_at >= pd.Timestamp(end))
    reason = np.where(bad_code & bad_date, "unknown_code;invalid_date", np.where(bad_code, "unknown_code", "invalid_date"))
    bad = bad_code | bad_date
    return out.loc[~bad].copy(), out.loc[bad].assign(dq_reason=reason[bad]), masked


def complaint_rates(cmp_: pd.DataFrame, units: pd.Series, months: pd.PeriodIndex) -> pd.DataFrame:
    """90-day complaint rate per 1000 units at every month end; row = month, column = code. uses only complaints up to that month end."""
    cmp_ = cmp_[cmp_["code"].isin(units.index)]
    out = {}
    for code, u in units.items():
        ts = np.sort(cmp_.loc[cmp_["code"] == code, "created_at"].to_numpy(dtype="datetime64[ns]"))
        vals = []
        for m in months:
            end = np.datetime64(m.end_time.normalize() + pd.Timedelta(days=1), "ns")      # exclusive end
            start = end - np.timedelta64(90, "D")
            n = np.searchsorted(ts, end) - np.searchsorted(ts, start)
            vals.append(1000.0 * n / u)
        out[code] = vals
    return pd.DataFrame(out, index=months)


class Source:
    """all inputs, loaded once."""

    def __init__(self, sat_lag_q: int = 0):
        fin = pd.read_parquet(SIM / "fin_monthly.parquet")
        self.mon, self.rep, self.n_balance_fixed = clean_fin(fin)
        self.compounds = pd.read_parquet(REAL / "compounds.parquet")[["code", "developer_code", "units"]].set_index("code")
        self.cmp = pd.read_parquet(SIM / "complaints.parquet")[["code", "created_at"]]
        self.kpi = pd.read_parquet(REAL / "kpi_values.parquet").set_index(["code", "quarter"])
        self.sat_lag_q = sat_lag_q
        self.months = pd.period_range("2023-01", "2026-09", freq="M")
        self.cmp, _, _ = clean_complaints(self.cmp, self.compounds.index, self.months[0].start_time, (self.months[-1] + 1).start_time)
        self.rates = complaint_rates(self.cmp, self.compounds["units"], self.months)
        self.codes = sorted(self.compounds.index)


def _reported_asof(rep: pd.DataFrame, code: str, date: pd.Timestamp):
    r = rep[(rep["code"] == code) & (rep["report_date"] <= date)]
    return (r["reported_pct"].iloc[-1], r["report_date"].iloc[-1]) if len(r) else (np.nan, pd.NaT)


def snapshot(src: Source, month: pd.Period) -> pd.DataFrame:
    """level features for every compound as of the end of `month`. nothing dated after it is read."""
    date = month.end_time.normalize()
    mon = src.mon[src.mon["month"] <= month]
    rows = []
    for code in src.codes:
        g = mon[mon["code"] == code].set_index("month")
        cur = g.loc[month] if month in g.index else None
        r = {"code": code}
        if cur is not None:
            req, bal, ctc = cur["cover_required_egp"], cur["cover_balance_egp"], cur["cost_to_complete_egp"]
            r["cover_req0"] = float(req <= 0)
            r["cover_ratio"] = COVER_CAP if req <= 0 else min(bal / req, COVER_CAP)
            r["cover_ctc"] = min(bal / ctc, COVER_CAP) if ctc > 0 else COVER_CAP
            r["land_late"] = float(cur["land_months_late"])
            r["meters"] = float(cur["meters_active"])
            k3 = g["kwh"].iloc[-3:].mean()
            r["kwh_per_meter"] = k3 / cur["meters_active"] if cur["meters_active"] > 0 else np.nan
            prior = g["kwh"].loc[month - 9: month - 4]
            r["kwh_ratio"] = k3 / prior.mean() if len(prior) >= 3 and prior.mean() > 0 else np.nan
            planned = cur["planned_pct"]
        else:
            planned = np.nan
        rep, rep_date = _reported_asof(src.rep, code, date)
        r["gap"] = planned - rep if pd.notna(rep) else np.nan
        r["report_age"] = (month - rep_date.to_period("M")).n if pd.notna(rep_date) else 12.0
        hist = src.rates.loc[src.rates.index < month, code]
        hist = hist[hist.index >= pd.Period("2023-03", "M")]             # 90-day window needs 3 months of data
        now = src.rates.loc[month, code] if month >= pd.Period("2023-03", "M") else np.nan
        r["cmp_rate90"] = now
        r["cmp_hist_n"] = len(hist)
        r["cmp_pctl"] = 0.5 if len(hist) < 6 or pd.isna(now) else ((hist < now).sum() + 0.5 * (hist == now).sum()) / len(hist)
        rows.append(r)
    return pd.DataFrame(rows).set_index("code").reindex(columns=INTERNAL + ["cmp_hist_n"])


def sat_features(src: Source, quarter: str) -> pd.DataFrame:
    """satellite features at `quarter` (shifted back by sat_lag_q) and the 2-quarter trend."""
    q = qindex(quarter) - src.sat_lag_q

    def at(qi):
        idx = [(c, qlabel(qi)) for c in src.codes]
        k = src.kpi.reindex(idx)
        out = pd.DataFrame(index=src.codes)
        out["A"] = k["activity_prob"].to_numpy(dtype=float)
        out["active"] = k["active"].astype(float).to_numpy()
        out["K2"] = k["K2"].to_numpy(dtype=float)
        out["K3"] = k["K3"].to_numpy(dtype=float)
        out["level"] = k["level"].astype("float").fillna(5).to_numpy()
        out["started"] = k["started"].astype(float).to_numpy()
        return out

    now, before = at(q), at(q - 2)
    for c in TREND_SAT:
        now[f"d_{c}"] = now[c] - before[c]
    now.index.name = "code"
    return now


def build_table(sat_lag_q: int = 0, src: Source | None = None, quarters=None) -> pd.DataFrame:
    src = src or Source(sat_lag_q)
    ak = pd.read_parquet(PRIVATE / "answer_key.parquet")[["code", "month", "story", "true_distress", "label_distress_next_6m", "label_censored"]]
    ak["month"] = pd.PeriodIndex(ak["month"], freq="M")
    ak = ak.set_index(["code", "month"])
    frames = []
    for quarter in CUTOFF_QUARTERS if quarters is None else quarters:
        m = qend_month(quarter)
        now, then = snapshot(src, m), snapshot(src, m - LAG_MONTHS)
        f = now.copy()
        for c in TREND_BASE:
            f[f"d_{c}"] = now[c] - then[c]
        f = f.join(sat_features(src, quarter))
        f["quarter"], f["month"] = quarter, m
        f["developer"] = src.compounds["developer_code"]
        lab = ak.reindex(list(zip(f.index, [m] * len(f))))
        f["story"] = lab["story"].to_numpy()
        f["distress_now"] = lab["true_distress"].to_numpy(dtype=bool)
        f["label"] = lab["label_distress_next_6m"].to_numpy(dtype=bool)
        f["censored"] = lab["label_censored"].to_numpy(dtype=bool)
        frames.append(f.reset_index())
    return pd.concat(frames, ignore_index=True)


def onset_events(first_month: str = "2023-02") -> pd.DataFrame:
    """first month of every contiguous true_distress run that starts after the data start (evaluation only)."""
    ak = pd.read_parquet(PRIVATE / "answer_key.parquet").sort_values(["code", "month"])
    out = []
    for code, g in ak.groupby("code"):
        d, m = g["true_distress"].to_numpy(), g["month"].to_numpy()
        for i in range(len(d)):
            if d[i] and (i == 0 or not d[i - 1]) and m[i] >= first_month:
                out.append({"code": code, "onset": pd.Period(m[i], "M")})
    return pd.DataFrame(out)


def a_acceleration(frame: pd.DataFrame, col: str = "A") -> pd.Series:
    """candidate feature: year-over-year second difference (A(t)-A(t-4)) - (A(t-4)-A(t-8)) per code, quarterly index qi.
    Uses only past quarters; a missing quarter or fewer than 8 earlier quarters gives NaN, never 0.
    Not wired into the dataset: a v2 build needs the external data and a protocol hashed before fitting."""
    values = frame.set_index(["code", "qi"])[col]

    def lagged(k: int) -> np.ndarray:
        return values.reindex(pd.MultiIndex.from_arrays([frame.code, frame.qi - k])).to_numpy(dtype=float)

    now = frame[col].to_numpy(dtype=float)
    return pd.Series((now - lagged(4)) - (lagged(4) - lagged(8)), index=frame.index)
