"""
propose: step 6. success criterion of DATA_PLAN_FINAL section 3, computed once on the frozen-clock kpi_values.
pre-registered reading (written into this file before any result): a case counts if it is at level 1-2 in some quarter whose end is
6 or more months before the case's first announced delivery date (the K3 clock origin). thresholds are never changed after the result.
the wording "stays in level 1-2" also allows two stricter readings, computed from the same table and reported next to it:
  point in time: level 1-2 at the last quarter that ends 6 or more months before the first date (the alert is standing at that moment);
  after start:   level 1-2 in such a quarter at or after the first quarter where A showed building (ignores empty-land inactivity before construction).
secondary: the same with the original promise date of the eval table; the other 14 compounds flagged.
input: kpi_values, eval_outcomes. output: backtest/cases.csv, backtest/summary.json.
"""

import json

import numpy as np
import pandas as pd

from src.pipeline import activity, kpis
from src.pipeline.common import APP, CFG, months_between, qend, qindex

B = CFG["backtest"]


def readings(kc: pd.DataFrame, first: pd.Timestamp) -> dict:
    """the three readings of the criterion for one compound (kc sorted by quarter, assessable quarters only)."""
    elig = kc[kc.qi.map(qend) <= first - pd.DateOffset(months=B["months_before"])]
    hit = elig[elig.level.isin(B["levels"])]
    started = kc[kc.active.fillna(False).astype(bool)]
    after = hit[hit.qi >= started.qi.min()] if len(started) else hit.iloc[0:0]

    def lead(d: pd.DataFrame):
        """months between the earliest quarter in d and the first date."""
        return months_between(qend(d.qi.iloc[0]), first) if len(d) else None

    k5 = kc[kc.K5 & (kc.qi.map(qend) <= first)]
    last = elig.iloc[-1] if len(elig) else None
    return {"literal": len(hit) > 0, "literal_months_before": lead(hit), "first_alert_quarter": hit.quarter.iloc[0] if len(hit) else None,
            "driver": ("K2" if hit.K2.iloc[0] >= CFG["levels"]["k2_l2"] else "K3" if hit.K3.iloc[0] >= CFG["levels"]["k3_l2"] else "K5") if len(hit) else None,
            "point_in_time": bool(last is not None and last.level in B["levels"]), "level_at_freeze": None if last is None else int(last.level),
            "after_start": len(after) > 0, "after_start_months_before": lead(after), "k5_first_quarter": k5.quarter.iloc[0] if len(k5) else None,
            "k5_months_before": lead(k5)}


def run(kpi: pd.DataFrame, ev: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows = []
    for e in ev.itertuples():
        kc = kpi[(kpi.code == e.code) & kpi.level.notna()].sort_values("qi")
        main, alt = readings(kc, pd.Timestamp(e.first_deadline)), readings(kc, pd.Timestamp(e.promise_original_end))
        rows.append({"case": e.case, "code": e.code, "first_deadline": e.first_deadline, **main,
                     "alt_deadline": e.promise_original_end, "alt_literal": alt["literal"], "alt_point_in_time": alt["point_in_time"]})
    cases = pd.DataFrame(rows)
    others = kpi[~kpi.code.isin(ev.code) & kpi.level.notna()]
    n = {k: int(cases[k].sum()) for k in ("literal", "point_in_time", "after_start", "alt_literal", "alt_point_in_time")}
    summary = {"criterion": f">= {B['min_cases']} of {len(cases)} cases at level 1-2 at least {B['months_before']} months before the first date",
               "n_cases": len(cases), "pre_registered_literal_reading": {"n": n["literal"], "met": n["literal"] >= B["min_cases"]},
               "point_in_time_reading": {"n": n["point_in_time"], "met": n["point_in_time"] >= B["min_cases"]},
               "after_start_reading": {"n": n["after_start"], "met": n["after_start"] >= B["min_cases"]},
               "alt_dates": {"literal": n["alt_literal"], "point_in_time": n["alt_point_in_time"]},
               "k5_fired_before_first_date": int(cases.k5_first_quarter.notna().sum()),
               "others": {"n": int(others.code.nunique()), "flagged_1_2_at_asof": int(others[(others.quarter == CFG["asof"]) & others.level.isin([1, 2])].code.nunique()),
                          "ever_flagged_1_2": int(others[others.level.isin([1, 2])].code.nunique())}}
    return cases, summary


def frozen_clock_check(model, thr: float, sat_a: pd.DataFrame, full: pd.DataFrame, comp, stm, yearly, run_id: str) -> dict:
    """recompute from data cut at the quarter (no later image, statement or vegetation year) and compare with the full run at that quarter."""
    base = sat_a[["code", "qi", "built_prob_mean", "n_images", "K4"]]
    out = {}
    for q in ("2021Q4", "2023Q2", "2024Q4", "2025Q3"):
        qi = qindex(q)
        cut = base[base.qi <= qi]
        sat_c = cut.merge(activity.score(cut, model, thr, last_qi=qi)[["code", "qi", "activity_prob", "active"]], on=["code", "qi"], how="left")
        part = kpis.kpi_values(sat_c, comp, stm[pd.to_datetime(stm.published_date) <= qend(qi)], yearly[yearly.year <= 2016 + qi // 4], run_id, upto=qi)
        a, b = part[part.qi == qi].set_index("code"), full[full.qi == qi].set_index("code")
        cols = ["activity_prob", "K2", "K3", "K5", "level", "may_be_complete"]
        out[q] = bool(np.allclose(a[cols].astype(float).values, b.loc[a.index, cols].astype(float).values, equal_nan=True))
    return out


def save(cases: pd.DataFrame, summary: dict) -> None:
    d = APP / "backtest"
    d.mkdir(parents=True, exist_ok=True)
    cases.to_csv(d / "cases.csv", index=False)
    (d / "summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
