"""
propose: step 1 of the generator. read each compound's REAL signals and derive its story (no random draw).
input: the R1 tables (sat_quarterly with activity A, statements, compounds, sat_yearly, kpi_values).
output: `derive(real)` -> list[Signals], one per compound code, with the story, the reason (which real signal), the smoothed monthly activity state,
        the real anchors (announced progress, handover events, satellite built level) and K3 per month.

story table (data plan section 4.2), plus "healthy" for the compounds that match none (checked in this order):
  partly_delivered  a handover was announced (delivery start / progress / complete)
  gradual_stall     A inactive for the last 4+ quarters, no handover
  stall_recovery    A stopped for 3+ quarters then came back (and stayed back)
  new_start         first sustained activity at or after 2024Q3, nothing before: a new project
  slow_late         A active and K3 > 0 (first promised date passed)
  healthy           everything else
the satellite flag A flickers by one quarter (R1 report, issue 3), so a 3-quarter majority vote is used before any rule.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.generator.inputs import GEN, M_END, MONTHS, N, mi
from src.pipeline.common import CFG, months_between, qindex

G = GEN["stories"]
HANDOVER = ("delivery_start", "delivery_progress", "delivery_complete")
FIRST_Q = qindex("2019Q1")
DW_K = [0.0]   # fitted slope of the built-level -> progress map, set by derive()


@dataclass
class Signals:
    code: str
    developer: str
    district: str
    units: int
    bua_m2: float
    land_area_m2: float
    cover_pct: float
    story: str = ""
    why: str = ""
    state: np.ndarray = field(default_factory=lambda: np.zeros(N, dtype=bool))
    k3: np.ndarray = field(default_factory=lambda: np.zeros(N, dtype=int))
    launch_real: int | None = None            # month of the earliest real marketing signal
    first_active: int | None = None            # first month of the first sustained activity (None = already active at 2019Q1)
    first_deadline: int | None = None          # month of the end of the first published promise
    handover_pub: int | None = None            # month the first handover was published
    handovers: list = field(default_factory=list)      # (month, subtype, scope)
    anchors: list = field(default_factory=list)        # (month, announced %, record_id); month >= N means "after the horizon"
    anchor_dates: list = field(default_factory=list)   # published date of each anchor
    postponements: list = field(default_factory=list)
    dw_year: dict = field(default_factory=dict)        # year -> mean built share
    dw_p: dict = field(default_factory=dict)           # month -> implied progress (isotonic)
    dw_raw: dict = field(default_factory=dict)         # month -> implied progress (raw)
    onset: int | None = None                   # first month of the trailing stall
    recovery: int | None = None                # month activity returns after a stall


def smooth(a: np.ndarray, w: int) -> np.ndarray:
    """majority vote over a centred window (edges replicated), on a 0/1 array."""
    pad = w // 2
    x = np.pad(a.astype(float), pad, mode="edge")
    return np.array([x[i:i + w].mean() >= 0.5 for i in range(len(a))])


def runs(state: np.ndarray, value: bool) -> list[tuple[int, int]]:
    """(start, length) of consecutive runs of `value`."""
    out, i = [], 0
    while i < len(state):
        if state[i] == value:
            j = i
            while j < len(state) and state[j] == value:
                j += 1
            out.append((i, j - i))
            i = j
        else:
            i += 1
    return out


def q_month(k: int) -> int:
    """month index of the first month of the quarter at position k of the quarterly arrays (0 = 2019Q1)."""
    q = k + FIRST_Q
    return mi(pd.Timestamp(2016 + q // 4, 3 * (q % 4) + 1, 1))


def monthly_state(q_state: np.ndarray) -> np.ndarray:
    """quarterly state (position 0 = 2019Q1) onto the month grid; months before 2019Q1 hold the first value."""
    out = np.zeros(N, dtype=bool)
    for m, p in enumerate(MONTHS):
        qi = (p.year - 2016) * 4 + (p.month - 1) // 3
        out[m] = q_state[max(qi - FIRST_Q, 0)]
    return out


def k3_series(first_end, published, handover_pub) -> np.ndarray:
    """K3 per month as R1 defines it: months since the end of the first published promise, 0 once a handover is published or before the promise exists."""
    k = np.zeros(N, dtype=int)
    if first_end is None:
        return k
    for m in range(N):
        e = M_END[m]
        if (handover_pub is not None and e >= handover_pub) or (published is not None and e < published):
            continue
        k[m] = max(0, -months_between(e, first_end))
    return k


def isotonic(y: list[float]) -> list[float]:
    """pool-adjacent-violators, non-decreasing fit."""
    blocks = [[v, 1] for v in y]
    i = 0
    while i < len(blocks) - 1:
        if blocks[i][0] > blocks[i + 1][0]:
            tot = blocks[i][1] + blocks[i + 1][1]
            blocks[i] = [(blocks[i][0] * blocks[i][1] + blocks[i + 1][0] * blocks[i + 1][1]) / tot, tot]
            del blocks[i + 1]
            i = max(i - 1, 0)
        else:
            i += 1
    return [b[0] for b in blocks for _ in range(b[1])]


def derive(real: dict) -> list[Signals]:
    comp, sat, stm, kpi = real["compounds"], real["sat_quarterly"], real["statements"], real["kpi_values"]
    out = []
    for r in comp.sort_values("code").itertuples():
        s = Signals(r.code, r.developer_code, r.district, int(r.units), float(r.bua_m2), float(r.land_area_m2), float(r.cover_pct))
        sq = sat[(sat.code == r.code) & (sat.qi >= FIRST_Q)].sort_values("qi")
        qs = smooth(sq.active.fillna(False).astype(bool).to_numpy(), G["state_window"])
        s.state = monthly_state(qs)
        st = stm[stm.code == r.code]
        for e in st[(st.kind == "event") & st.subtype.isin(HANDOVER)].itertuples():
            start = e.period_start if (e.subtype == "delivery_start" and pd.notna(e.period_start)) else e.published_date
            s.handovers.append((min(mi(start), mi(e.published_date)), e.subtype, e.scope if isinstance(e.scope, str) else ""))
        s.handovers.sort()
        pr = st[st.kind == "progress"].sort_values(["published_date", "statement_id"])
        s.anchors = [(mi(e.published_date), float(e.value), e.record_id) for e in pr.itertuples()]
        s.anchor_dates = [pd.Timestamp(e.published_date) for e in pr.itertuples()]
        s.postponements = sorted(mi(e.published_date) for e in st[st.subtype == "postponement"].itertuples())
        marks = [mi(e.published_date) for e in st[(st.subtype == "launch") | (st.kind == "promise")].itertuples()] + [a[0] for a in s.anchors]
        s.launch_real = min(marks) if marks else None
        if pd.notna(r.first_deadline):
            s.first_deadline = mi(r.first_deadline)
        if pd.notna(r.handover_first_published):
            s.handover_pub = mi(r.handover_first_published)
        s.k3 = k3_series(pd.Timestamp(r.first_deadline) if pd.notna(r.first_deadline) else None,
                         pd.Timestamp(r.first_deadline_published) if pd.notna(r.first_deadline_published) else None,
                         pd.Timestamp(r.handover_first_published) if pd.notna(r.handover_first_published) else None)
        s.dw_year = {int(y): float(v) for y, v in sq.assign(y=sq.qi // 4 + 2016).groupby("y").built_prob_mean.mean().items()}
        s.story, s.why = classify(s, qs, kpi[(kpi.code == r.code) & (kpi.quarter == CFG["asof"])].iloc[0])
        out.append(s)
    DW_K[0] = dw_progress(out, sat)
    return out


def classify(s: Signals, qs: np.ndarray, k_now) -> tuple[str, str]:
    act_runs = [(a, n) for a, n in runs(qs, True) if n >= 2]
    s.first_active = q_month(act_runs[0][0]) if act_runs and act_runs[0][0] > 0 else None
    if s.handovers:
        kinds = ", ".join(sorted({h[1] for h in s.handovers}))
        return "partly_delivered", f"handover announced ({kinds}); first published {MONTHS[s.handover_pub]}"
    trailing = 0
    for v in qs[::-1]:
        if v:
            break
        trailing += 1
    if trailing >= G["stall_quarters"]:
        s.onset = q_month(len(qs) - trailing) if trailing < len(qs) else None
        return "gradual_stall", f"A inactive for the last {trailing} quarters (raw K2 = {int(k_now.K2)}), no handover announced"
    for a, n in runs(qs, False):
        after = qs[a + n:]
        if n >= G["recovery_gap_quarters"] and any(qs[:a]) and len(after) >= 2 and after[:2].all():
            s.onset, s.recovery = q_month(a), q_month(a + n)
            return "stall_recovery", f"A stopped for {n} quarters (from {MONTHS[s.onset]}) and came back from {MONTHS[s.recovery]}"
    if act_runs and act_runs[0][0] > 0 and act_runs[0][0] + FIRST_Q >= qindex(G["new_start_from"]):
        return "new_start", f"first sustained activity starts {MONTHS[s.first_active]}, nothing active before"
    if int(k_now.K3) > 0 and np.mean(qs[-4:]) >= 0.5:
        return "slow_late", f"A active in {int(np.sum(qs[-4:]))} of the last 4 quarters and K3 = {int(k_now.K3)} months past the first promised date"
    return "healthy", f"A active in {int(np.sum(qs[-4:]))} of the last 4 quarters, K3 = {int(k_now.K3)}, no handover announced"


def dw_progress(sigs: list[Signals], sat: pd.DataFrame) -> float:
    """fill `dw_p` / `dw_raw` (month index -> progress implied by the built-share level, yearly mean placed at mid-year; dw_p is the monotone fit).
    mapping: progress = k * (level - bare), capped. bare = lowest yearly level of any compound; k is the least-squares slope through the bare level on the
    18 announced progress values (level = trailing 4-quarter mean at the announcement quarter). returns k."""
    built = sat.pivot(index="qi", columns="code", values="built_prob_mean").rolling(4, min_periods=3).mean()
    l0 = min(v for s in sigs for v in s.dw_year.values())
    pts = [(v, built.at[(MONTHS[min(m, N - 1)].year - 2016) * 4 + (MONTHS[min(m, N - 1)].month - 1) // 3, s.code] - l0) for s in sigs for m, v, _ in s.anchors]
    k = sum(a * x for a, x in pts) / sum(x * x for _, x in pts)
    for s in sigs:
        ys = sorted(s.dw_year)
        raw = [float(np.clip(k * (s.dw_year[y] - l0), 0, G["dw_cap"])) for y in ys]
        s.dw_raw = {mi(pd.Timestamp(y, 6, 15)): v for y, v in zip(ys, raw)}
        s.dw_p = {mi(pd.Timestamp(y, 6, 15)): v for y, v in zip(ys, isotonic(raw))}
    return k
