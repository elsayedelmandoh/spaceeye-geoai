"""
propose: step 2. the hidden monthly truth of one compound: plan, true progress, handover, occupancy, roads.
input: `Signals` (real anchors and activity state), the extended drivers, one random generator per compound.
output: `Setup` (sampled dates and developer traits) and `Truth` (arrays on the 2017-01 .. 2026-09 grid).

true progress is built in two moves:
  1. knots: announced % (minus the developer's optimism), the real handover events (lower bounds) and the satellite built level (monotone fit) are put on a
     time axis, anchors first, satellite level only where it does not contradict an anchor.
  2. bridge: between two knots the rise is spread over the months with weights = season (Ramadan, heat, Eid) x AR(1) noise x activity gate
     (real smoothed A: inactive months get ~0). so the path passes through every real anchor exactly and never goes down.
"""

from dataclasses import dataclass, field

import numpy as np

from src.generator.inputs import GEN, N, mi
from src.generator.stories import Signals

P, G = GEN["progress"], GEN["stories"]


@dataclass
class Setup:
    launch: int
    cstart: int            # first month of real construction
    plan_start: int
    plan_T: int
    deadline: int          # contractual delivery month (end of the first promise when known)
    phase_share: float
    occ_cap: float
    optimism: float        # points the developer adds in reports and announcements
    style: str
    strength: str
    cost_usd_m2: float
    cover_cancel_pct: float
    cover_pct: float
    shape: float = 2.5


@dataclass
class Truth:
    plan: np.ndarray
    progress: np.ndarray
    knots: list = field(default_factory=list)       # (month, value, kind)
    handed: np.ndarray = None                        # units handed over (cumulative, int)
    batches: np.ndarray = None                       # units handed over this month
    occupied: np.ndarray = None
    roads: np.ndarray = None
    stalled: np.ndarray = None                       # true progress < 0.06 pp in the month, while building


def sample_setup(sig: Signals, rng: np.random.Generator, dev: dict, cost_usd_m2: float) -> Setup:
    pl, lag = GEN["plan"], GEN["plan"]["launch_to_start_months"]
    fa = sig.first_active
    cands = []
    if sig.launch_real is not None:
        cands.append(sig.launch_real)
    if fa is not None:
        cands.append(fa - int(rng.integers(4, 11)))
    if not cands:                                       # no real marketing signal at all, or already active at 2019Q1
        cands.append(int(rng.integers(mi("2021-06-01"), mi("2022-12-01"))) if fa is None and not sig.state[0] else int(rng.integers(0, 24)))
    launch = max(0, min(cands))
    cstart = fa if fa is not None else launch + int(rng.integers(lag[0], lag[1] + 1))
    T = int(rng.integers(pl["duration_months"][0], pl["duration_months"][1] + 1))
    if sig.first_deadline is not None:
        deadline = sig.first_deadline
        new = sig.story == "new_start"
        pstart = cstart - int(rng.integers(0, 3)) if new else max(deadline - T, launch + lag[0])
        T = max(deadline - pstart, 18)
    else:
        pstart = cstart - int(rng.integers(0, 3))
        deadline = pstart + T
    shape = float(rng.uniform(*GEN["plan"]["weibull_shape"]))
    ps = float(rng.uniform(*G["phase_share"]))
    cancel = 30.0 if sig.cover_pct >= 20 else 25.0
    return Setup(launch, cstart, pstart, T, deadline, ps, float(rng.uniform(*GEN["utilities"]["occupancy_cap"])), dev["optimism"], dev["style"], dev["strength"],
                 cost_usd_m2, cancel, sig.cover_pct, shape)


def plan_curve(st: Setup, start: int | None = None, T: int | None = None) -> np.ndarray:
    """Weibull S-curve divided by its value at the end of the duration, so the plan hits 100 % exactly at the contractual date."""
    x = (np.arange(N) - (st.plan_start if start is None else start)) / (st.plan_T if T is None else T)

    def f(v):
        return 1 - np.exp(-(np.clip(v, 0, None) / GEN["plan"]["weibull_scale"]) ** st.shape)

    return 100 * np.minimum(1, f(x) / f(1.0))


def fit_plan(st: Setup, prog: np.ndarray, rng: np.random.Generator) -> None:
    """no published deadline: finished work gets the plan the developer would have written (deadline within -2..+4 months of the month true progress passes
    95 %); unfinished work keeps the drawn duration, so the plan may already be ahead of the work."""
    done = np.nonzero(prog >= 95)[0]
    if len(done):
        st.plan_T = max(18, int(done[0]) - st.plan_start + int(rng.integers(-2, 5)))
        st.deadline = st.plan_start + st.plan_T


def handover_floor(sub: str, scope: str, st: Setup) -> float:
    """true progress at least this high when the real handover event happens."""
    if scope.startswith("phase"):
        return 85 * st.phase_share
    return {"delivery_start": 85.0, "delivery_progress": 70.0, "delivery_complete": 100.0}[sub]


def build_knots(sig: Signals, st: Setup, rng: np.random.Generator) -> list:
    """monotone list of (month, value, kind): start, announced (hard), satellite level (soft), handover floors, end.
    announced values bind both ways. the satellite level only enters where it fits between two announced values. handover events are floors (a lower bound
    from that month on). where the built footprint stops growing while the compound is active, true progress keeps rising up to 9 points above it: finishing
    work is invisible to the satellite, and 9 stays inside the +-10 tolerance."""
    hard = [(st.cstart, 0.0, "start")] + [(min(m, N - 1), max(0.0, v - st.optimism), "announced") for m, v, _ in sig.anchors]
    hard.sort(key=lambda k: (k[0], -k[1]))
    knots, top = [], 0.0
    for m, v, kind in hard:
        top = max(top, v)
        if knots and knots[-1][0] == m:
            knots[-1] = (m, top, knots[-1][2] if knots[-1][1] >= v else kind)
        else:
            knots.append((m, top, kind))
    first, last = knots[0][0], knots[-1]
    out, flat = list(knots), 0
    prev_raw = None
    for m, v in sorted(sig.dw_p.items()):
        raw = sig.dw_raw[m]
        active_year = sig.state[max(m - 6, 0):m + 6].mean() >= 0.5
        flat = flat + 1 if (prev_raw is not None and raw - prev_raw < 2 and active_year and raw < G["dw_cap"] + 1) else 0
        prev_raw = raw
        if m <= first or m >= N - 1:
            continue
        v = float(np.clip(v + min(9.0, 3.0 * flat) + rng.normal(0, 2.0), 0, 100))
        before = max([k[1] for k in knots if k[0] <= m], default=0.0)
        after = min([k[1] for k in knots if k[0] >= m], default=None)
        if m > last[0]:
            out.append((m, max(v, last[1]), "satellite"))
        elif after is not None and before <= v <= after and all(k[0] != m for k in knots):
            out.append((m, v, "satellite"))
    out.sort(key=lambda k: k[0])
    if out[-1][0] < N - 1:
        out.append((N - 1, out[-1][1], "end"))
    for m, sub, scope in sig.handovers:                    # floors
        floor = handover_floor(sub, scope, st)
        at = float(np.interp(m, [k[0] for k in out], [k[1] for k in out]))
        if at < floor:
            out.append((m, floor, "handover"))
            out.sort(key=lambda k: (k[0], k[1]))
    mono, top = [], 0.0
    for m, v, kind in out:
        top = min(100.0, max(top, v))
        mono.append((m, top, kind))
    return mono


def weights(sig: Signals, st: Setup, season: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    eps = np.zeros(N)
    for t in range(1, N):
        eps[t] = P["ar1"]["rho"] * eps[t - 1] + rng.normal(0, P["ar1"]["sigma"])
    gate = np.where(sig.state, 1.0, P["inactive_weight"])
    if sig.story == "stall_recovery" and sig.onset is not None and sig.recovery is not None:
        gap = slice(sig.onset, sig.recovery)               # the real gap in activity: slow work, with a full stop of 4-5 months inside it
        gate[gap] = 0.25
        stop = int(rng.integers(4, 6))
        gate[sig.onset + 1:sig.onset + 1 + stop] = 0.0
    return season * np.exp(eps) * gate


def bridge(knots: list, w: np.ndarray) -> np.ndarray:
    prog = np.zeros(N)
    for (m0, v0, _), (m1, v1, _) in zip(knots, knots[1:]):
        prog[m0] = v0
        if m1 == m0:
            continue
        seg = w[m0 + 1:m1 + 1]
        c = np.cumsum(seg) / seg.sum() if seg.sum() > 0 else np.linspace(1 / len(seg), 1, len(seg))
        prog[m0 + 1:m1 + 1] = v0 + (v1 - v0) * c
    prog[knots[-1][0]:] = knots[-1][1]
    return prog


def handover_path(sig: Signals, st: Setup) -> tuple[np.ndarray, np.ndarray]:
    """units handed over (cumulative) and per month. steps at the real events, then a slow creep of further batches."""
    share = np.zeros(N)
    for m, sub, scope in sig.handovers:
        ph = scope.startswith("phase")
        if sub == "delivery_complete":
            target, creep = (st.phase_share if ph else 1.0), 0.0
        elif sub == "delivery_start":
            target, creep = (st.phase_share * 0.6 if ph else 0.5), 0.35 * (st.phase_share if ph else 0.5)
        else:
            target, creep = (st.phase_share * 0.9 if ph else 0.75), 0.15
        t = np.arange(N)
        path = np.where(t >= m, target + creep * np.clip((t - m) / 12.0, 0, 1), 0.0)
        share = np.maximum(share, np.minimum(path, 1.0))
    handed = np.maximum.accumulate(np.round(share * sig.units)).astype(int)
    return handed, np.diff(handed, prepend=0)


def occupancy(batches: np.ndarray, st: Setup, rng: np.random.Generator) -> np.ndarray:
    """each handed-over batch fills like a slow logistic curve that starts 2-6 months after handover and ends at the occupancy cap."""
    d0 = float(rng.integers(*GEN["utilities"]["occupancy_delay"], endpoint=True))
    sc = GEN["utilities"]["occupancy_scale_months"] / 2
    occ = np.zeros(N)
    t = np.arange(N)
    for m in np.nonzero(batches)[0]:
        occ += batches[m] * st.occ_cap / (1 + np.exp(-(t - m - d0) / sc)) * (t >= m)
    return occ


def run(sig: Signals, st: Setup, season: np.ndarray, rng: np.random.Generator) -> Truth:
    knots = build_knots(sig, st, rng)
    w = weights(sig, st, season, rng)
    prog = bridge(knots, w)
    handed, batches = handover_path(sig, st)
    occ = np.minimum(occupancy(batches, st, rng), handed)
    roads = np.clip((prog - 35) / 55, 0, 1)
    roads = np.concatenate([np.zeros(2), roads[:-2]])        # paving trails structure by two months
    d = np.diff(prog, prepend=0)
    if sig.first_deadline is None:
        fit_plan(st, prog, rng)
    return Truth(plan_curve(st), prog, knots, handed, batches, occ, roads, (d < 0.06) & (np.arange(N) >= st.cstart) & (prog < 99.5))
