"""
propose: step 4. K2-K5, priority level, "may be complete" flag and the reason sentence, for every compound at every as-of quarter.
every value at quarter q uses only data published by the end of q (clock frozen per quarter).
input: sat_quarterly (with activity_prob/active), compounds, statements, sat_yearly. output: kpi_values.

fixed definitions (written before any backtest):
  K2  consecutive latest quarters with A inactive (stops at an active or a missing quarter).
  K3  months since the end of the FIRST published delivery promise; 0 if a handover was announced or no date has passed.
  K5  first date still ahead by 0-12 months, no handover announced, and either (a) A inactive and not finished, or
      (b) required rise in built share to reach the "ready" level / remaining quarters > max_rate.
      ready = median built share, in the quarter handover started, of the OTHER compounds whose handover start was published (leave-one-out).
      finished = may be complete, or built share already at the ready level.
  may be complete = handover announced, or vegetation share >= veg_complete (latest year finished by the quarter end). caps the level at 3.
"""

import math

import numpy as np
import pandas as pd

from src.pipeline.build_real import first_promise
from src.pipeline.common import CFG, N_Q, months_between, qend, qindex, qlabel

L, K5C = CFG["levels"], CFG["k5"]
FIRST_Q = qindex(CFG["backtest"]["first_quarter"])


def inactive(a) -> bool:
    """A is known and below the threshold (a missing value is neither)."""
    return not pd.isna(a) and not bool(a)


def add_k2(sat: pd.DataFrame) -> pd.DataFrame:
    """K2 per compound-quarter from the active flag."""
    out = []
    for _, g in sat.sort_values("qi").groupby("code"):
        n, k2 = 0, []
        for a in g.active:
            n = n + 1 if inactive(a) else 0
            k2.append(np.nan if pd.isna(a) else n)
        out.append(g.assign(K2=k2))
    return pd.concat(out).sort_values(["code", "qi"]).reset_index(drop=True)


def delivery_starts(stm: pd.DataFrame) -> pd.DataFrame:
    """handover start events: code, date it was published, quarter it started (period start, else the publish date)."""
    e = stm[(stm.kind == "event") & (stm.subtype == "delivery_start")].copy()
    start = pd.to_datetime(e.period_start.fillna(e.published_date))
    e["pub"], e["start_qi"] = pd.to_datetime(e.published_date), (start.dt.year - 2016) * 4 + (start.dt.month - 1) // 3
    return e[["code", "pub", "start_qi"]]


def ready_level(code: str, asof: pd.Timestamp, starts: pd.DataFrame, built: pd.DataFrame) -> float:
    """median built share at handover start of the other compounds that had announced a start by `asof` (nan if none)."""
    s = starts[(starts.pub <= asof) & (starts.code != code)].drop_duplicates("code")
    vals = [built.at[q, c] for c, q in zip(s.code, s.start_qi) if q in built.index and c in built]
    return float(np.nanmedian(vals)) if len(vals) and not np.all(np.isnan(vals)) else np.nan


def veg_latest(yearly: pd.DataFrame, code: str, qi: int) -> float:
    """vegetation share of the latest summer (Jun-Sep) already over at the end of quarter qi."""
    y = 2016 + qi // 4 if qi % 4 >= 2 else 2015 + qi // 4
    v = yearly[(yearly.code == code) & (yearly.year <= y) & yearly.veg_share.notna()].sort_values("year")
    return float(v.veg_share.iloc[-1]) if len(v) else np.nan


def level_of(k2: float, k3: int, k5: bool, complete: bool) -> int:
    k2 = 0 if pd.isna(k2) else k2
    if k2 >= L["k2_l1"] or k3 > L["k3_l1"] or (k2 >= L["combo_k2"] and k3 > L["combo_k3"]):
        lv = 1
    elif L["k2_l2"] <= k2 < L["k2_l1"] or L["k3_l2"] <= k3 <= L["k3_l1"]:
        lv = 2
    elif k2 == 1 or 1 <= k3 <= L["k3_l2"] - 1:
        lv = 3
    else:
        lv = 4
    if k5:
        lv = min(lv, 2)
    return max(lv, 3) if complete else lv


def reason(r: dict) -> str:
    """fixed template filled by code. codes only, no names."""
    if not r["K4"]:
        return f"Not assessable: {r['n_images']} images in the quarter (minimum {CFG['n_images_min']})."
    p = []
    a = r["activity_prob"]
    p.append(f"no building activity for {int(r['K2'])} quarter(s) (activity score {a:.2f})" if r["K2"] >= 1 else f"building activity detected (activity score {a:.2f})")
    if r["handover"]:
        p.append("handover announced")
    elif r["first_end"] is None:
        p.append("no announced handover date")
    elif r["K3"] > 0:
        p.append(f"first announced handover date ({r['first_end']:%b %Y}) passed by {r['K3']} months")
    else:
        p.append(f"first announced handover date ({r['first_end']:%b %Y}) is still ahead")
    if r["K5"]:
        if pd.notna(r["k5_rate_needed"]) and r["k5_rate_needed"] > K5C["max_rate"]:
            p.append(f"at risk of missing it: built share must rise {r['k5_rate_needed']:.2f} per quarter (fastest observed {K5C['max_rate']:.2f})")
        else:
            p.append(f"at risk of missing it: no activity and not finished with {r['months_left']} months left")
    if r["may_be_complete"]:
        p.append("may be complete (" + ("handover announced" if r["handover"] else f"vegetation share {r['veg']:.2f}") + "): confirm on site")
    p.append(f"observation complete ({r['n_images']} images in the quarter)")
    return f"Level {r['level']}: " + "; ".join(p) + "."


def kpi_values(sat: pd.DataFrame, comp: pd.DataFrame, stm: pd.DataFrame, yearly: pd.DataFrame, run_id: str, upto: int = N_Q - 1) -> pd.DataFrame:
    sat = add_k2(sat[sat.qi <= upto])
    built = sat.pivot(index="qi", columns="code", values="built_prob_mean")
    starts = delivery_starts(stm)
    prom = stm[stm.kind == "promise"]
    hand = comp.set_index("code").handover_first_published
    rows = []
    for r in sat[sat.qi.between(FIRST_Q, upto)].itertuples():
        asof = qend(r.qi)
        fp = first_promise(prom[pd.to_datetime(prom.published_date) <= asof])
        first_end = pd.Timestamp(fp.period_end[r.code]) if r.code in fp.index else None
        h = hand.get(r.code)
        handover = bool(pd.notna(h) and pd.Timestamp(h) <= asof)
        veg = veg_latest(yearly, r.code, r.qi)
        complete = handover or (pd.notna(veg) and veg >= CFG["veg_complete"])
        months_left = months_between(asof, first_end) if first_end is not None else None
        k3 = max(0, -months_left) if first_end is not None and not handover else 0
        ready, rate, k5 = np.nan, np.nan, False
        if first_end is not None and not handover and 0 <= months_left <= K5C["horizon_months"] and pd.notna(r.built_prob_mean):
            ready = ready_level(r.code, asof, starts, built)
            rq = max(1, math.ceil(months_left / 3))
            finished = complete or (pd.notna(ready) and r.built_prob_mean >= ready)
            if pd.notna(ready):
                rate = max(0.0, ready - r.built_prob_mean) / rq
            k5 = bool((inactive(r.active) and not finished) or (pd.notna(rate) and rate > K5C["max_rate"]))
        row = {"code": r.code, "quarter": qlabel(r.qi), "qi": r.qi, "activity_prob": r.activity_prob, "active": r.active, "K2": r.K2, "K3": k3, "K4": bool(r.K4),
               "K5": k5, "k5_rate_needed": rate, "may_be_complete": bool(complete), "n_images": r.n_images}
        row["level"] = level_of(r.K2, k3, k5, complete) if r.K4 else pd.NA
        row["level_label"] = "not assessable" if not r.K4 else str(row["level"])
        row["reason"] = reason({**row, "handover": handover, "first_end": first_end, "months_left": months_left, "veg": veg})
        row["k3_first_deadline"] = first_end
        rows.append(row)
    out = pd.DataFrame(rows)
    out["level"] = out.level.astype("Int64")
    out = rank_cycle(out)
    out["origin"], out["run_id"], out["computed_at"] = "derived", run_id, CFG["computed_on"]
    return out.drop(columns="n_images").sort_values(["qi", "code"]).reset_index(drop=True)


def rank_cycle(kpi: pd.DataFrame) -> pd.DataFrame:
    """inspection order inside each quarter: level, then K2 descending, then K3 descending. the top N with level 1-3 form the cycle list."""
    kpi = kpi.copy()
    kpi["cycle_rank"] = pd.array([pd.NA] * len(kpi), dtype="Int64")
    for q, g in kpi[kpi.level.notna() & (kpi.level <= 3)].groupby("qi"):
        order = g.assign(k2=g.K2.fillna(0)).sort_values(["level", "k2", "K3", "code"], ascending=[True, False, False, True])
        kpi.loc[order.index[: CFG["cycle_capacity"]], "cycle_rank"] = range(1, min(len(order), CFG["cycle_capacity"]) + 1)
    return kpi


def cycle_list(kpi: pd.DataFrame, quarter: str) -> pd.DataFrame:
    c = kpi[(kpi.quarter == quarter) & kpi.cycle_rank.notna()].sort_values("cycle_rank")
    return c[["cycle_rank", "code", "level", "K2", "K3", "K5", "may_be_complete"]]
