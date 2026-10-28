"""
propose: step 4. K2, K3, priority level, "may be complete" flag and the reason sentence, for every compound at every as-of quarter.
every value at quarter q uses only data published by the end of q (clock frozen per quarter).
input: sat_quarterly (with activity_prob/active), compounds, statements, sat_yearly. output: kpi_values.

fixed definitions (written before any backtest; K5 was dropped on 26 Oct 2026 because it added nothing, see FIXES_PROTOCOL):
  started  at quarter q: A showed 4 consecutive active quarters ending at or before q (start = first quarter of the first such run), or a launch / delivery event was
           published by the end of q (start = quarter of the event period, else of the publication). before that the state is "not started", not level 1.
  K2  consecutive latest quarters with A inactive, counted only from the quarter construction started (stops at an active or a missing quarter); empty before the start.
  K3  months since the end of the FIRST published delivery promise; 0 if a handover was announced or no date has passed. independent of `started`.
  may be complete = handover announced, or vegetation share >= veg_complete (latest year finished by the quarter end). caps the level at 3.
  level = worst of K2 (after the start), K3 and the combined rule; not started with K3 = 0 has no level.
  observed_started is separate descriptive evidence: four assessable active quarters or a published delivery event, excluding marketing launch.
  K6 is months since the first known launch without confirmed observed start; null when launch/history is unknown or observation has gaps.
  K6 now enters priority under the user-approved imported-spec extension (28 Oct); prior evaluation is historical.
  K5 is cumulative policy-screening exposure, not a contractual/legal fine assessment.
"""

import numpy as np
import pandas as pd

from src.pipeline.build_real import first_promise
from src.pipeline.common import CFG, N_Q, months_between, qend, qindex, qlabel

L, ST = CFG["levels"], CFG["start"]
FIRST_Q = qindex(CFG["backtest"]["first_quarter"])
START_EVIDENCE_COLUMNS = (
    "observed_started", "observed_start_quarter", "observed_start_source", "start_observation_sufficient",
    "launch_date_asof", "launch_first_published", "K6", "start_reference_date_asof",
    "start_reference_published", "start_reference_source",
)


def inactive(a) -> bool:
    """A is known and below the threshold (a missing value is neither)."""
    return not pd.isna(a) and not bool(a)


def event_starts(stm: pd.DataFrame) -> pd.DataFrame:
    """launch / delivery events: code, date published, quarter the event started (period start or date, never later than the publication)."""
    e = stm[(stm.kind == "event") & stm.subtype.isin(ST["events"])].copy()
    pub = pd.to_datetime(e.published_date)
    start = pd.to_datetime(e.period_start.fillna(e.published_date)).where(lambda d: d <= pub, pub)
    e["pub"], e["start_qi"] = pub, (start.dt.year - 2016) * 4 + (start.dt.month - 1) // 3
    return e[["code", "pub", "start_qi"]]


def add_k2(sat: pd.DataFrame, stm: pd.DataFrame) -> pd.DataFrame:
    """K2 and the construction-start state per compound-quarter (frozen clock: only runs and events known at the quarter count)."""
    ev, run = event_starts(stm), ST["run_quarters"]
    out = []
    for code, g in sat.sort_values("qi").groupby("code"):
        g = g.reset_index(drop=True)
        act = g.active.fillna(False).astype(bool).tolist()
        s_run = next((i for i in range(len(act) - run + 1) if all(act[i : i + run])), None)  # first run of `run` active quarters
        mine = ev[ev.code == code]
        k2, started, start_q = [], [], []
        for i, q in enumerate(g.qi):
            cands = [int(x) for x in mine[mine.pub <= qend(q)].start_qi]
            if s_run is not None and s_run + run - 1 <= i:
                cands.append(int(g.qi[s_run]))
            st = min(cands) if cands else None
            started.append(st is not None)
            start_q.append(qlabel(st) if st is not None else None)
            if st is None or pd.isna(g.active[i]):
                k2.append(np.nan)
                continue
            n = 0
            for j in range(i, -1, -1):
                if g.qi[j] < st or not inactive(g.active[j]):
                    break
                n += 1
            k2.append(n)
        out.append(g.assign(K2=k2, started=started, start_quarter=start_q))
    return add_start_evidence(pd.concat(out).sort_values(["code", "qi"]).reset_index(drop=True), stm)


def add_start_evidence(sat: pd.DataFrame, stm: pd.DataFrame) -> pd.DataFrame:
    """Separate marketing launch from observed start without altering the existing rule.

    A positive start needs consecutive, assessable active quarters or an already-published delivery event.
    Without positive evidence, K6 needs uninterrupted known observations from launch through the cutoff.
    K6 means time without a confirmed observed start, not proof that no construction took place.
    """
    delivery = event_starts(stm[stm.subtype != "launch"])
    launches = stm[(stm.kind == "event") & (stm.subtype == "launch")].copy()
    launches["pub"] = pd.to_datetime(launches.published_date)
    launches["event_date"] = pd.to_datetime(launches.period_start.fillna(launches.published_date)).where(
        lambda d: d <= launches["pub"], launches["pub"])
    launches = launches.sort_values(["pub", "event_date"])
    promises = stm[stm.kind == "promise"].copy()
    promises["pub"] = pd.to_datetime(promises.published_date)
    output = []
    for code, g in sat.sort_values("qi").groupby("code"):
        g = g.reset_index(drop=True)
        quality = g["K4"].fillna(False).astype(bool) if "K4" in g else pd.Series(False, index=g.index)
        known = quality & g.active.notna()
        active = known & g.active.fillna(False).astype(bool)
        n = ST["run_quarters"]
        first_run = next((i for i in range(len(g) - n + 1)
                          if active.iloc[i:i + n].all() and np.all(np.diff(g.qi.iloc[i:i + n]) == 1)), None)
        mine = delivery[delivery.code == code]
        my_launches = launches[launches.code == code]
        observed, start_q, source, sufficient, dates, published, k6 = [], [], [], [], [], [], []
        ref_dates, ref_pubs, ref_sources = [], [], []
        history = pd.Series(known.to_numpy(), index=g.qi)
        for i, qi in enumerate(g.qi):
            asof = qend(qi)
            candidates = [(int(q), "published_delivery") for q in mine.loc[mine.pub <= asof, "start_qi"]]
            if first_run is not None and first_run + n - 1 <= i:
                candidates.append((int(g.qi.iloc[first_run]), "activity_run"))
            evidence = min(candidates) if candidates else None
            available = my_launches[my_launches.pub <= asof]
            launch = available.iloc[0] if len(available) else None
            launch_date = launch.event_date if launch is not None else pd.NaT
            launch_pub = launch.pub if launch is not None else pd.NaT
            refs = [(x.pub, x.event_date, "launch") for x in available.itertuples()]
            refs += [(x.pub, x.pub, "promise_publication") for x in promises[(promises.code == code) & (promises.pub <= asof)].itertuples()]
            ref_pub, ref_date, ref_source = min(refs) if refs else (pd.NaT, pd.NaT, None)
            complete_history = False
            if pd.notna(ref_date):
                start_qi = qindex(f"{ref_date.year}Q{ref_date.quarter}")
                complete_history = bool(history.reindex(range(start_qi, int(qi) + 1), fill_value=False).all())
            confirmed = evidence is not None
            observed.append(confirmed)
            start_q.append(qlabel(evidence[0]) if confirmed else None)
            source.append(evidence[1] if confirmed else None)
            sufficient.append(confirmed or complete_history)
            dates.append(launch_date)
            published.append(launch_pub)
            ref_dates.append(ref_date)
            ref_pubs.append(ref_pub)
            ref_sources.append(ref_source)
            k6.append(max(0, months_between(ref_date, asof)) if not confirmed and complete_history else pd.NA)
        output.append(g.assign(
            observed_started=observed, observed_start_quarter=pd.array(start_q, dtype="string"),
            observed_start_source=pd.array(source, dtype="string"), start_observation_sufficient=sufficient,
            launch_date_asof=pd.array(dates, dtype="datetime64[ns]"),
            launch_first_published=pd.array(published, dtype="datetime64[ns]"), K6=pd.array(k6, dtype="Int64"),
            start_reference_date_asof=pd.array(ref_dates, dtype="datetime64[ns]"),
            start_reference_published=pd.array(ref_pubs, dtype="datetime64[ns]"),
            start_reference_source=pd.array(ref_sources, dtype="string")))
    return pd.concat(output).sort_values(["code", "qi"]).reset_index(drop=True)


def veg_latest(yearly: pd.DataFrame, code: str, qi: int) -> float:
    """vegetation share of the latest summer (Jun-Sep) already over at the end of quarter qi."""
    y = 2016 + qi // 4 if qi % 4 >= 2 else 2015 + qi // 4
    v = yearly[(yearly.code == code) & (yearly.year <= y) & yearly.veg_share.notna()].sort_values("year")
    return float(v.veg_share.iloc[-1]) if len(v) else np.nan


def level_of(k2: float, k3: int, complete: bool, started: bool = True, k6=None) -> int | None:
    """worst of K2 (only after construction started), K3 and the combined rule. None = "not started" (and no K3 date has passed either)."""
    k2 = 0 if (pd.isna(k2) or not started) else k2
    k6 = 0 if pd.isna(k6) else k6
    if k2 >= L["k2_l1"] or k3 > L["k3_l1"] or (k2 >= L["combo_k2"] and k3 > L["combo_k3"]) or k6 > L["k6_l1"]:
        lv = 1
    elif L["k2_l2"] <= k2 < L["k2_l1"] or L["k3_l2"] <= k3 <= L["k3_l1"] or L["k6_l2"] <= k6 <= L["k6_l1"]:
        lv = 2
    elif k2 == 1 or 1 <= k3 <= L["k3_l2"] - 1:
        lv = 3
    elif started:
        lv = 4
    else:
        return None
    return max(lv, 3) if complete else lv


def fine_months(first_end, asof, observed_start_quarter, sufficient, handover_published=None) -> dict:
    """Union of calendar months under the requested screening policy. Unknown never means zero.

    Post-deadline/no-observed-start and post-grace months overlap; count once.
    Accrual stops at the first published handover. Previous exposure is retained.
    This is a research policy proxy, not evidence that a contract fine is due.
    """
    if first_end is None or pd.isna(first_end):
        return {"K5_no_start_months": pd.NA, "K5_post_grace_months": pd.NA, "K5_overlap_months": pd.NA, "K5_months": pd.NA}
    end = min(asof, pd.Timestamp(handover_published)) if pd.notna(handover_published) else asof
    due, until = pd.Period(first_end, "M"), pd.Period(end, "M")
    elapsed = max(0, until.ordinal - due.ordinal)
    grace = max(0, elapsed - CFG["fines"]["grace_months"])
    if pd.notna(observed_start_quarter):
        started = pd.Period(observed_start_quarter, "Q").start_time.to_period("M")
        no_start = max(0, min(elapsed, started.ordinal - due.ordinal - 1))
    else:
        no_start = elapsed if sufficient or elapsed == 0 else pd.NA
    overlap = max(0, no_start - CFG["fines"]["grace_months"]) if pd.notna(no_start) else pd.NA
    return {"K5_no_start_months": no_start, "K5_post_grace_months": grace, "K5_overlap_months": overlap,
            "K5_months": no_start + grace - overlap if pd.notna(no_start) else pd.NA}


def reason(r: dict) -> str:
    """fixed template filled by code. codes only, no names."""
    if not r["K4"]:
        return f"Not assessable: {r['n_images']} images in the quarter (minimum {CFG['n_images_min']})."
    p = []
    a = r["activity_prob"]
    score = f"activity score {a:.2f}" if pd.notna(a) else "no activity score yet"
    if not r["started"]:
        p.append(f"construction not started: no {ST['run_quarters']}-quarter run of building activity and no published launch or construction event ({score})")
    elif pd.notna(r["K2"]) and r["K2"] >= 1:
        p.append(f"no building activity for {int(r['K2'])} quarter(s) ({score})")
    else:
        p.append(f"building activity detected ({score})")
    if r["handover"]:
        p.append("handover announced")
    elif r["first_end"] is None:
        p.append("no announced handover date")
    elif r["K3"] > 0:
        p.append(f"first announced handover date ({r['first_end']:%b %Y}) passed by {r['K3']} months")
    else:
        p.append(f"first announced handover date ({r['first_end']:%b %Y}) is still ahead")
    if r["may_be_complete"]:
        p.append("may be complete (" + ("handover announced" if r["handover"] else f"vegetation share {r['veg']:.2f}") + "): confirm on site")
    if pd.notna(r.get("K6")):
        p.append(f"no confirmed observed start for {r['K6']} months since the first known launch/promise")
    p.append(f"observation complete ({r['n_images']} images in the quarter)")
    head = f"Level {r['level']}" if pd.notna(r["level"]) else "Not started"
    return f"{head}: " + "; ".join(p) + "."


def kpi_values(sat: pd.DataFrame, comp: pd.DataFrame, stm: pd.DataFrame, yearly: pd.DataFrame, run_id: str, upto: int = N_Q - 1) -> pd.DataFrame:
    sat = add_k2(sat[sat.qi <= upto], stm)
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
        row = {"code": r.code, "quarter": qlabel(r.qi), "qi": r.qi, "activity_prob": r.activity_prob, "active": r.active, "started": bool(r.started), "start_quarter": r.start_quarter,
               "K2": r.K2, "K3": k3, "K4": bool(r.K4), "may_be_complete": bool(complete), "n_images": r.n_images}
        row.update({name: getattr(r, name) for name in START_EVIDENCE_COLUMNS})
        row.update(fine_months(first_end, asof, r.observed_start_quarter, r.start_observation_sufficient, h if handover else None))
        row["K5_basis"] = "policy proxy; contract eligibility unverified"
        lv = level_of(r.K2, k3, complete, bool(r.started), r.K6) if r.K4 else None
        row["level"] = pd.NA if lv is None else lv
        row["level_label"] = "not assessable" if not r.K4 else "not started" if lv is None else str(lv)
        row["reason"] = reason({**row, "handover": handover, "first_end": first_end, "veg": veg})
        row["k3_first_deadline"] = first_end
        rows.append(row)
    out = pd.DataFrame(rows)
    out["active"] = pd.array(out["active"], dtype="boolean")
    out["K6"] = pd.array(out["K6"], dtype="Int64")
    for col in ("K5_no_start_months", "K5_post_grace_months", "K5_overlap_months", "K5_months"):
        out[col] = pd.array(out[col], dtype="Int64")
    for col in ("observed_start_quarter", "observed_start_source"):
        out[col] = out[col].astype("string")
    for col in ("launch_date_asof", "launch_first_published"):
        out[col] = out[col].astype("datetime64[ns]")
    out["level"] = out.level.astype("Int64")
    out = rank_cycle(out)
    out["origin"], out["run_id"], out["computed_at"] = "derived", run_id, CFG["computed_on"]
    return out.drop(columns="n_images").sort_values(["qi", "code"]).reset_index(drop=True)


def rank_cycle(kpi: pd.DataFrame) -> pd.DataFrame:
    """inspection order inside each quarter: level, then K2 descending, then K3 descending. the top N with level 1-3 form the cycle list (not started compounds have no level)."""
    kpi = kpi.copy()
    kpi["cycle_rank"] = pd.array([pd.NA] * len(kpi), dtype="Int64")
    for q, g in kpi[kpi.level.notna() & (kpi.level <= 3)].groupby("qi"):
        order = g.assign(k2=g.K2.fillna(0)).sort_values(["level", "k2", "K3", "code"], ascending=[True, False, False, True])
        kpi.loc[order.index[: CFG["cycle_capacity"]], "cycle_rank"] = range(1, min(len(order), CFG["cycle_capacity"]) + 1)
    return kpi


def cycle_list(kpi: pd.DataFrame, quarter: str) -> pd.DataFrame:
    c = kpi[(kpi.quarter == quarter) & kpi.cycle_rank.notna()].sort_values("cycle_rank")
    return c[["cycle_rank", "code", "level", "K2", "K3", "K5_months", "K6", "may_be_complete"]]
