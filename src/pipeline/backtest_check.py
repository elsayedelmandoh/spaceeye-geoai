"""
propose: step 6. success criterion of DATA_PLAN_FINAL section 3, computed once on the frozen-clock kpi_values (built with the backtest variant of A, without the leaking plots).
reading used after the 26 Oct corrections (FIXES_PROTOCOL section 5): a case counts if, in some quarter whose end is 6 or more months before the case's first announced
delivery date (the K3 clock origin), construction had already started (4 active quarters of A, or a published launch / delivery event) and the level is 1-2.
the same table also gives the other readings of "stays in level 1-2":
  point in time: level 1-2 at the last quarter that ends 6 or more months before the first date (the alert is standing at that moment);
  literal:       level 1-2 in any such quarter (after the "not started" fix a quarter before construction has no level, so it equals the after-start reading).
the results before the corrections (literal 8, point in time 0, after start 0 of 8) are kept in before_corrections/. thresholds are never changed after a result.
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
    """the readings of the criterion for one compound (kc sorted by quarter, assessable quarters only)."""
    elig = kc[kc.qi.map(qend) <= first - pd.DateOffset(months=B["months_before"])]
    hit = elig[elig.level.isin(B["levels"])]
    after = hit[hit.started]

    def lead(d: pd.DataFrame):
        """months between the earliest quarter in d and the first date."""
        return months_between(qend(d.qi.iloc[0]), first) if len(d) else None

    last = elig.iloc[-1] if len(elig) else None
    return {"after_start": len(after) > 0, "after_start_months_before": lead(after), "first_alert_quarter": after.quarter.iloc[0] if len(after) else None,
            "driver": ("K2" if after.K2.iloc[0] >= CFG["levels"]["k2_l2"] else "K3") if len(after) else None,
            "point_in_time": bool(last is not None and last.level in B["levels"]), "level_at_freeze": None if last is None else last.level_label,
            "literal": len(hit) > 0, "started_by_cutoff": bool(last is not None and last.started),
            "start_quarter": None if last is None or not last.started else last.start_quarter}


def run(kpi: pd.DataFrame, ev: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows = []
    for e in ev.itertuples():
        kc = kpi[(kpi.code == e.code) & kpi.level.notna()].sort_values("qi")
        main, alt = readings(kc, pd.Timestamp(e.first_deadline)), readings(kc, pd.Timestamp(e.promise_original_end))
        rows.append({"case": e.case, "code": e.code, "first_deadline": e.first_deadline, **main,
                     "alt_deadline": e.promise_original_end, "alt_after_start": alt["after_start"], "alt_point_in_time": alt["point_in_time"]})
    cases = pd.DataFrame(rows)
    others = kpi[~kpi.code.isin(ev.code) & kpi.level.notna()]
    n = {k: int(cases[k].sum()) for k in ("literal", "point_in_time", "after_start", "alt_after_start", "alt_point_in_time", "started_by_cutoff")}
    summary = {"criterion": f">= {B['min_cases']} of {len(cases)} cases at level 1-2 at least {B['months_before']} months before the first date",
               "n_cases": len(cases), "primary_reading": "after_start",
               "after_start_reading": {"n": n["after_start"], "met": n["after_start"] >= B["min_cases"]},
               "point_in_time_reading": {"n": n["point_in_time"], "met": n["point_in_time"] >= B["min_cases"]},
               "literal_reading": {"n": n["literal"], "met": n["literal"] >= B["min_cases"]},
               "alt_dates": {"after_start": n["alt_after_start"], "point_in_time": n["alt_point_in_time"]},
               "cases_already_started_at_cutoff": n["started_by_cutoff"],
               "others": {"n": int(others.code.nunique()), "flagged_1_2_at_asof": int(others[(others.quarter == CFG["asof"]) & others.level.isin([1, 2])].code.nunique()),
                          "ever_flagged_1_2": int(others[others.level.isin([1, 2])].code.nunique())}}
    return cases, summary


def frozen_clock_check(model, thr: float, mode: str, sat_a: pd.DataFrame, full: pd.DataFrame, comp, stm, yearly, run_id: str) -> dict:
    """recompute from data cut at the quarter (no later image, statement or vegetation year) and compare with the full run at that quarter."""
    base = sat_a[["code", "qi", "built_prob_mean", "n_images", "K4"]]
    out = {}
    for q in ("2021Q4", "2023Q2", "2024Q4", "2025Q3"):
        qi = qindex(q)
        cut = base[base.qi <= qi]
        sat_c = cut.merge(activity.score(cut, model, thr, last_qi=qi, mode=mode)[["code", "qi", "activity_prob", "active"]], on=["code", "qi"], how="left")
        part = kpis.kpi_values(sat_c, comp, stm[pd.to_datetime(stm.published_date) <= qend(qi)], yearly[yearly.year <= 2016 + qi // 4], run_id, upto=qi)
        a, b = part[part.qi == qi].set_index("code"), full[full.qi == qi].set_index("code")
        cols = ["activity_prob", "K2", "K3", "level", "may_be_complete", "started"]
        out[q] = bool(np.allclose(a[cols].astype(float).values, b.loc[a.index, cols].astype(float).values, equal_nan=True))
    return out


def save(cases: pd.DataFrame, summary: dict) -> None:
    d = APP / "backtest"
    d.mkdir(parents=True, exist_ok=True)
    cases.to_csv(d / "cases.csv", index=False)
    (d / "summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
