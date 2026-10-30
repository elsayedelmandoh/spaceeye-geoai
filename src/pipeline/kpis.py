"""
propose: step 4. K2, K3, K5 (real fine-eligible screening months), K6, priority level, "may be complete" flag and the reason sentence, for every compound at every as-of quarter.
every value at quarter q uses only data published by the end of q (clock frozen per quarter).
input: sat_quarterly (with activity_prob/active), compounds, statements, sat_yearly. output: kpi_values.

fixed definitions (written before any backtest):
  started  at quarter q: A showed 4 consecutive active quarters ending at or before q (start = first quarter of the first such run), or a launch / delivery event was
           published by the end of q (start = quarter of the event period, else of the publication). before that the legacy start state is false, not level 1.
  K2  consecutive latest quarters with A inactive, counted only from the quarter construction started (stops at an active or a missing quarter); empty before the start.
  K3  months since the end of the FIRST published delivery promise; 0 if a handover was announced or no date has passed. independent of `started`.
  K5 is cumulative policy-screening exposure (fine-eligible months), not a contractual/legal fine assessment; it never sets the level.
  month arithmetic is KEPT: K3 and K6 use the nearest month (days / 30.44), while K5 uses calendar months; changing it after results exist would shift levels.
  K6 is months since the first known launch without confirmed observed start; null when launch/history is unknown or observation has gaps.
  strict K6 history is KEPT: every quarter from the launch/promise reference to the as-of quarter must be assessable; one gap makes K6 unknown later, and unknown K6 never raises a level.
  K6 now enters priority under the user-approved imported-spec extension (28 Oct); prior evaluation is historical.
  may be complete = handover announced, or vegetation share >= veg_complete (latest year finished by the quarter end). caps the level at 3.
  level = worst of K2 (after the start), K3 and the combined rule; not started with K3 = 0 has no level.
  level labels distinguish "not started" (K6 is known and at most 12 months) from "start unknown" (no construction start and K6 is unknown); neither has a priority level.
  observed_started is separate descriptive evidence: four assessable active quarters or a published delivery event, excluding marketing launch.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.pipeline.build_real import first_promise
from src.pipeline.common import (
    CFG,
    N_Q,
    months_between,
    qend,
    qindex,
    qindex_of,
    qlabel,
    summer_year,
)

L, ST = CFG["levels"], CFG["start"]
FIRST_Q = qindex(CFG["backtest"]["first_quarter"])
START_EVIDENCE_COLUMNS = (
    "observed_started", "observed_start_quarter", "observed_start_source", "start_observation_sufficient",
    "launch_date_asof", "launch_first_published", "K6", "start_reference_date_asof",
    "start_reference_published", "start_reference_source",
)
LEVEL_WORD = {1: "first", 2: "second", 3: "third", 4: "fourth"}
LEVEL_WORD_AR = {1: "الأولى", 2: "الثانية", 3: "الثالثة", 4: "الرابعة"}
KPI_ORIGINS: dict[str, str] = {
    "code": "key",
    "quarter": "key",
    "qi": "key",
    "activity_prob": "derived",
    "active": "derived",
    "started": "derived",
    "start_quarter": "derived",
    "K2": "derived",
    "K3": "derived",
    "K4": "derived",
    "may_be_complete": "derived",
    "observed_started": "derived",
    "observed_start_quarter": "derived",
    "observed_start_source": "derived",
    "start_observation_sufficient": "derived",
    "launch_date_asof": "derived",
    "launch_first_published": "derived",
    "K6": "derived",
    "start_reference_date_asof": "derived",
    "start_reference_published": "derived",
    "start_reference_source": "derived",
    "K5_no_start_months": "derived",
    "K5_post_grace_months": "derived",
    "K5_overlap_months": "derived",
    "K5_months": "derived",
    "K5_basis": "derived",
    "K5_status": "derived",
    "K5_text_ar": "derived",
    "K5_months_assumed": "assumption",
    "K5_assumed_basis": "assumption",
    "K6_status": "derived",
    "K6_text_ar": "derived",
    "level": "derived",
    "level_label": "derived",
    "reason": "derived",
    "reason_ar": "derived",
    "level_word": "derived",
    "level_word_ar": "derived",
    "k3_first_deadline": "derived",
    "cycle_rank": "derived",
    "origin": "derived",
    "run_id": "derived",
    "computed_at": "derived",
}


def level_labels(k4: bool, level: int | None, k6=None) -> tuple[str, str, str]:
    """Priority label and words, including the distinct unknown-start state."""
    if not k4:
        return "not assessable", "not assessable", "غير قابل للتقييم"
    if pd.notna(level):
        level = int(level)
        return str(level), LEVEL_WORD[level], LEVEL_WORD_AR[level]
    if pd.isna(k6):
        return "start unknown", "start unknown", "بداية غير معروفة"
    return "not started", "not started", "بداية غير مؤكدة"


@dataclass(frozen=True)
class _CodeEvidence:
    delivery: pd.DataFrame
    launches: pd.DataFrame
    promises: pd.DataFrame
    first_run: int | None
    history: pd.Series
    run_quarters: int


@dataclass(frozen=True)
class _ReferenceEvidence:
    launch_date: pd.Timestamp
    launch_published: pd.Timestamp
    reference_published: pd.Timestamp
    reference_date: pd.Timestamp
    reference_source: str | None


def inactive(a) -> bool:
    """A is known and below the threshold (a missing value is neither)."""
    return not pd.isna(a) and not bool(a)


def event_starts(stm: pd.DataFrame) -> pd.DataFrame:
    """launch / delivery events: code, date published, quarter the event started (period start or date, never later than the publication)."""
    e = stm[(stm.kind == "event") & stm.subtype.isin(ST["events"])].copy()
    pub = pd.to_datetime(e.published_date)
    start = pd.to_datetime(e.period_start.fillna(e.published_date)).where(lambda d: d <= pub, pub)
    e["pub"], e["start_qi"] = pub, start.map(qindex_of)
    return e[["code", "pub", "start_qi"]]


def _k2_at(g: pd.DataFrame, index: int, start_qi: int) -> int:
    """Consecutive inactive quarters ending at index, counted from the construction start."""
    count = 0
    for quarter_index in range(index, -1, -1):
        if g.qi[quarter_index] < start_qi or not inactive(g.active[quarter_index]):
            break
        count += 1
    return count


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
            k2.append(np.nan if st is None or pd.isna(g.active[i]) else _k2_at(g, i, st))
        out.append(g.assign(K2=k2, started=started, start_quarter=start_q))
    return add_start_evidence(pd.concat(out).sort_values(["code", "qi"]).reset_index(drop=True), stm)


def _start_sources(stm: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Published delivery events, launch events and promise publications used for start evidence."""
    delivery = event_starts(stm[stm.subtype != "launch"])
    launches = stm[(stm.kind == "event") & (stm.subtype == "launch")].copy()
    launches["pub"] = pd.to_datetime(launches.published_date)
    launches["event_date"] = pd.to_datetime(launches.period_start.fillna(launches.published_date)).where(
        lambda d: d <= launches["pub"], launches["pub"])
    launches = launches.sort_values(["pub", "event_date"])
    promises = stm[stm.kind == "promise"].copy()
    promises["pub"] = pd.to_datetime(promises.published_date)
    return delivery, launches, promises


def _code_evidence(g: pd.DataFrame, delivery: pd.DataFrame, launches: pd.DataFrame,
                   promises: pd.DataFrame) -> _CodeEvidence:
    """Per-compound start evidence inputs at each observed quarter."""
    quality = g["K4"].fillna(False).astype(bool) if "K4" in g else pd.Series(False, index=g.index)
    known = quality & g.active.notna()
    active = known & g.active.fillna(False).astype(bool)
    run_quarters = ST["run_quarters"]
    first_run = next((i for i in range(len(g) - run_quarters + 1)
                      if active.iloc[i:i + run_quarters].all()
                      and np.all(np.diff(g.qi.iloc[i:i + run_quarters]) == 1)), None)
    code = g.code.iloc[0]
    return _CodeEvidence(
        delivery=delivery[delivery.code == code], launches=launches[launches.code == code],
        promises=promises[promises.code == code], first_run=first_run,
        history=pd.Series(known.to_numpy(), index=g.qi), run_quarters=run_quarters,
    )


def _observed_evidence(g: pd.DataFrame, index: int, asof: pd.Timestamp,
                       context: _CodeEvidence) -> tuple[str | None, str | None]:
    """Observed construction start known by the cutoff, if any."""
    candidates = [(int(quarter), "published_delivery")
                  for quarter in context.delivery.loc[context.delivery.pub <= asof, "start_qi"]]
    if context.first_run is not None and context.first_run + context.run_quarters - 1 <= index:
        candidates.append((int(g.qi.iloc[context.first_run]), "activity_run"))
    if not candidates:
        return None, None
    quarter, source = min(candidates)
    return qlabel(quarter), source


def _reference_evidence(context: _CodeEvidence, asof: pd.Timestamp) -> _ReferenceEvidence:
    """Earliest published launch or promise publication available by the cutoff."""
    available = context.launches[context.launches.pub <= asof]
    launch = available.iloc[0] if len(available) else None
    launch_date = launch.event_date if launch is not None else pd.NaT
    launch_published = launch.pub if launch is not None else pd.NaT
    refs = [(row.pub, row.event_date, "launch") for row in available.itertuples()]
    promise_rows = context.promises[context.promises.pub <= asof]
    refs += [(row.pub, row.pub, "promise_publication") for row in promise_rows.itertuples()]
    ref_pub, ref_date, ref_source = min(refs) if refs else (pd.NaT, pd.NaT, None)
    return _ReferenceEvidence(launch_date, launch_published, ref_pub, ref_date, ref_source)


def _history_is_complete(history: pd.Series, reference_date: pd.Timestamp, quarter: int) -> bool:
    """Whether every quarter from the reference through the cutoff is assessable."""
    if pd.isna(reference_date):
        return False
    start_qi = qindex_of(reference_date)
    return bool(history.reindex(range(start_qi, int(quarter) + 1), fill_value=False).all())


def _start_evidence_row(g: pd.DataFrame, index: int, context: _CodeEvidence) -> dict:
    """Start-evidence values for one compound-quarter."""
    quarter = g.qi.iloc[index]
    asof = qend(quarter)
    start_quarter, source = _observed_evidence(g, index, asof, context)
    reference = _reference_evidence(context, asof)
    complete_history = _history_is_complete(context.history, reference.reference_date, quarter)
    confirmed = start_quarter is not None
    return {
        "observed_started": confirmed,
        "observed_start_quarter": start_quarter,
        "observed_start_source": source,
        "start_observation_sufficient": confirmed or complete_history,
        "launch_date_asof": reference.launch_date,
        "launch_first_published": reference.launch_published,
        "K6": max(0, months_between(reference.reference_date, asof)) if not confirmed and complete_history else pd.NA,
        "start_reference_date_asof": reference.reference_date,
        "start_reference_published": reference.reference_published,
        "start_reference_source": reference.reference_source,
    }


def _start_evidence_frame(g: pd.DataFrame, context: _CodeEvidence) -> pd.DataFrame:
    """Attach all start-evidence columns to one compound's quarterly frame."""
    evidence = pd.DataFrame([_start_evidence_row(g, index, context) for index in range(len(g))],
                            columns=START_EVIDENCE_COLUMNS)
    for column in ("observed_start_quarter", "observed_start_source", "start_reference_source"):
        evidence[column] = pd.array(evidence[column], dtype="string")
    for column in ("launch_date_asof", "launch_first_published", "start_reference_date_asof",
                   "start_reference_published"):
        evidence[column] = pd.array(evidence[column], dtype="datetime64[ns]")
    evidence["K6"] = pd.array(evidence["K6"], dtype="Int64")
    return g.assign(**{column: evidence[column] for column in START_EVIDENCE_COLUMNS})


def add_start_evidence(sat: pd.DataFrame, stm: pd.DataFrame) -> pd.DataFrame:
    """Separate marketing launch from observed start without altering the existing rule.

    A positive start needs consecutive, assessable active quarters or an already-published delivery event.
    Without positive evidence, K6 needs uninterrupted known observations from launch through the cutoff.
    This strict rule is KEPT: one non-assessable quarter makes K6 unknown for later quarters, and unknown never raises a level.
    K6 means time without a confirmed observed start, not proof that no construction took place.
    """
    delivery, launches, promises = _start_sources(stm)
    output = []
    for _, g in sat.sort_values("qi").groupby("code"):
        g = g.reset_index(drop=True)
        context = _code_evidence(g, delivery, launches, promises)
        output.append(_start_evidence_frame(g, context))
    return pd.concat(output).sort_values(["code", "qi"]).reset_index(drop=True)


def veg_latest(yearly: pd.DataFrame, code: str, qi: int) -> float:
    """vegetation share of the latest summer (Jun-Sep) already over at the end of quarter qi."""
    y = summer_year(qi)
    v = yearly[(yearly.code == code) & (yearly.year <= y) & yearly.veg_share.notna()].sort_values("year")
    return float(v.veg_share.iloc[-1]) if len(v) else np.nan


def level_of(k2: float, k3: int, complete: bool, started: bool = True, k6=None) -> int | None:
    """worst of K2 (only after construction started), K3 and the combined rule. None means no level: "not started" when K6 is known, "start unknown" when K6 is unknown."""
    k2 = 0 if (pd.isna(k2) or not started) else k2
    k6 = 0 if pd.isna(k6) else k6
    if k2 >= L["k2_l1"] or k3 > L["k3_l1"] or (k2 >= L["combo_k2"] and k3 > L["combo_k3"]) or k6 > L["k6_l1"]:
        lv = 1
    elif L["k2_l2"] <= k2 < L["k2_l1"] or L["k3_l2"] <= k3 <= L["k3_l1"] or L["k6_l2"] <= k6 <= L["k6_l1"]:
        lv = 2
    elif 1 <= k2 < L["k2_l2"] or 1 <= k3 <= L["k3_l2"] - 1:
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
    K5 keeps calendar-month arithmetic while K3 and K6 use nearest months; the difference is intentional.
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


K6_TEXT_AR = {"known": "{} شهرًا دون بدء مؤكد", "not_applicable_started": "لا ينطبق: الإنشاء بدأ",
              "unknown_history": "غير محدد: انقطاع في رصد الأقمار"}
K5_TEXT_AR = {"computed": "{} شهرًا", "no_published_deadline": "لا يوجد موعد تسليم منشور",
              "not_assessable": "غير محدد: بداية الإنشاء غير مؤكدة"}


def k6_status(k6, observed_started) -> str:
    """Why K6 is empty: it only counts months before a confirmed start."""
    if pd.notna(k6):
        return "known"
    return "not_applicable_started" if bool(observed_started) else "unknown_history"


def k5_status(first_end, k5_months) -> str:
    """Why K5 is empty: it is computed from the first published delivery date."""
    if first_end is None or pd.isna(first_end):
        return "no_published_deadline"
    return "computed" if pd.notna(k5_months) else "not_assessable"


def assumed_k5(first_end, reference_date, asof, observed_start_quarter, sufficient, handover_published=None):
    """Display-only K5 for compounds without a published date: launch + the assumed delivery term. Never sets the level."""
    if first_end is not None or pd.isna(reference_date):
        return pd.NA
    assumed_end = pd.Timestamp(reference_date) + pd.DateOffset(months=CFG["fines"]["assumed_delivery_months"])
    return fine_months(assumed_end, asof, observed_start_quarter, sufficient, handover_published)["K5_months"]


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
    head = f"Level {r['level']}" if pd.notna(r["level"]) else "Start unknown" if pd.isna(r.get("K6")) else "Not started"
    return f"{head}: " + "; ".join(p) + "."


def reason_ar(r: dict) -> str:
    """Committee-facing Arabic data, using the same evidence and template order as the English reason."""
    if not r["K4"]:
        return f"غير قابل للتقييم: عدد الصور {r['n_images']} خلال الربع؛ الحد الأدنى {CFG['n_images_min']}."
    parts = []
    activity_prob = r.get("activity_prob")
    score = f" (درجة النشاط {activity_prob:.2f})" if pd.notna(activity_prob) else ""
    if not r["started"]:
        parts.append("بداية التنفيذ غير مؤكدة وفق قاعدة البداية المستخدمة" + score)
    elif pd.notna(r["K2"]) and r["K2"] >= 1:
        parts.append(f"لم يرصد نشاط بناء منذ {int(r['K2'])} ربع" + score)
    else:
        parts.append("رصد نشاط بناء" + score)
    if r["handover"]:
        parts.append("يوجد إعلان تسليم منشور")
    elif r["first_end"] is None:
        parts.append("لا يوجد موعد تسليم معلن متاح")
    elif r["K3"] > 0:
        parts.append(f"تجاوز أول موعد تسليم معلن ({r['first_end']:%Y-%m-%d}) بمقدار {r['K3']} شهر")
    else:
        parts.append(f"أول موعد تسليم معلن ({r['first_end']:%Y-%m-%d}) لم يحن بعد")
    if r["may_be_complete"]:
        parts.append("قد يكون مكتملًا وفق إعلان التسليم أو الغطاء النباتي؛ يلزم تحقق ميداني")
    if pd.notna(r.get("K6")):
        parts.append(f"لم تتأكد بداية مرصودة منذ {int(r['K6'])} شهر من أول إعلان إطلاق أو وعد متاح")
    parts.append(f"عدد الصور خلال الربع {r['n_images']}")
    level = r.get("level")
    head = f"المستوى {int(level)}: " if pd.notna(level) else "بداية غير معروفة: " if pd.isna(r.get("K6")) else "بداية غير مؤكدة: "
    return head + "؛ ".join(parts) + "."


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
        row["K5_status"] = k5_status(first_end, row["K5_months"])
        row["K5_text_ar"] = K5_TEXT_AR[row["K5_status"]].format(row["K5_months"])
        # assumed term runs from the published launch, else from the observed construction start
        launch_known = pd.notna(r.start_reference_date_asof)
        reference = r.start_reference_date_asof if launch_known else (
            pd.Period(r.observed_start_quarter, "Q").start_time if pd.notna(r.observed_start_quarter) else pd.NaT)
        row["K5_months_assumed"] = assumed_k5(first_end, reference, asof, r.observed_start_quarter,
                                              r.start_observation_sufficient, h if handover else None)
        row["K5_assumed_basis"] = ("not used: published date exists" if first_end is not None else
                                   f"assumption: {'launch' if launch_known else 'observed construction start'} + "
                                   f"{CFG['fines']['assumed_delivery_months']} months; no published date")
        row["K6_status"] = k6_status(r.K6, r.observed_started)
        row["K6_text_ar"] = K6_TEXT_AR[row["K6_status"]].format(r.K6)
        lv = level_of(r.K2, k3, complete, bool(r.started), r.K6) if r.K4 else None
        row["level"] = pd.NA if lv is None else lv
        labels = level_labels(r.K4, lv, r.K6)
        row["level_label"] = labels[0]
        row["reason"] = reason({**row, "handover": handover, "first_end": first_end, "veg": veg})
        row["reason_ar"] = reason_ar({**row, "handover": handover, "first_end": first_end, "veg": veg})
        row["level_word"] = labels[1]
        row["level_word_ar"] = labels[2]
        row["k3_first_deadline"] = first_end
        rows.append(row)
    out = pd.DataFrame(rows)
    out["active"] = pd.array(out["active"], dtype="boolean")
    out["K6"] = pd.array(out["K6"], dtype="Int64")
    for col in ("K5_no_start_months", "K5_post_grace_months", "K5_overlap_months", "K5_months", "K5_months_assumed"):
        out[col] = pd.array(out[col], dtype="Int64")
    for col in ("observed_start_quarter", "observed_start_source"):
        out[col] = out[col].astype("string")
    for col in ("launch_date_asof", "launch_first_published"):
        out[col] = out[col].astype("datetime64[ns]")
    out["level"] = out.level.astype("Int64")
    out = rank_cycle(out)
    out["origin"], out["run_id"], out["computed_at"] = "derived", run_id, CFG["computed_on"]
    return out.drop(columns="n_images").sort_values(["qi", "code"]).reset_index(drop=True)


def eligible_order(group: pd.DataFrame) -> pd.DataFrame:
    """Eligible rows ordered by level, K2 and K3 descending, then code."""
    return (group[group.level.notna() & group.level.le(3)]
            .assign(k2=lambda frame: frame.K2.fillna(0))
            .sort_values(["level", "k2", "K3", "code"], ascending=[True, False, False, True]))


def rank_cycle(kpi: pd.DataFrame) -> pd.DataFrame:
    """inspection order inside each quarter: level, then K2 descending, then K3 descending. the top N with level 1-3 form the cycle list; compounds with no priority level are not ranked."""
    kpi = kpi.copy()
    kpi["cycle_rank"] = pd.array([pd.NA] * len(kpi), dtype="Int64")
    for _, group in kpi.groupby("qi"):
        order = eligible_order(group)
        if order.empty:
            continue
        kpi.loc[order.index[: CFG["cycle_capacity"]], "cycle_rank"] = range(1, min(len(order), CFG["cycle_capacity"]) + 1)
    return kpi


def cycle_list(kpi: pd.DataFrame, quarter: str) -> pd.DataFrame:
    c = kpi[(kpi.quarter == quarter) & kpi.cycle_rank.notna()].sort_values("cycle_rank")
    return c[["cycle_rank", "code", "quarter", "level", "level_word", "level_word_ar", "K2", "K3", "K5_months", "K6", "may_be_complete", "reason", "reason_ar", "origin", "run_id", "computed_at"]]
