"""
propose: step 3. the hidden money of one compound: sales, collections, escrow (decree 2184), developer cash, land installments.
input: Signals, Setup, Truth, drivers, the supervisor reports (they trigger the escrow releases), one random generator.
output: `Economy` arrays on the grid. no double counting: buyer payments go into escrow, and reach the developer only as releases after a quarterly report.

  sales        hazard (launch spike, slow tail) x demand (policy rate, Ramadan, post-float boom 2-4 months after the float); price list jumps 15-40 % after the float
  collections  8.5 % at sale + equal monthly installments over 7-12 years, x payment rate (late share, higher after the float, weaker before a stall)
  escrow       all collections in. release at a report month = min(balance - 5 % refund reserve (art. 3(6)), certified cost so far x 1.05 - already released).
               the financial cover (cover % x cost to complete, until certified progress passes the art. 4 threshold 30 % / 25 %) is a posted guarantee, not cash;
               cover_balance = escrow cash + the cover the developer still keeps posted (shrinks when it is in arrears)
  cash         releases + equity at launch + bank line - construction spending - overhead - interest - land. contractor arrears pile up when cash is short
  land         16 quarterly installments, paid when cash covers the instalment and a month of spending, arrears pay a monthly penalty, cleared in one payment
"""

from dataclasses import dataclass

import numpy as np

from src.generator.inputs import FLOAT_M, GEN, N
from src.generator.stories import Signals
from src.generator.truth import Setup, Truth

S, E, F, L = GEN["sales"], GEN["escrow"], GEN["funding"], GEN["land"]


@dataclass
class Economy:
    total_cost: np.ndarray
    sold: np.ndarray
    price: np.ndarray            # average price of the units sold in the month (nan if none)
    value_sold: np.ndarray       # contract value sold in the month
    collections: np.ndarray
    balance: np.ndarray          # escrow cash balance (buyers' money), end of month
    cover_balance: np.ndarray    # escrow cash + the financial cover the developer keeps posted (a guarantee, not cash)
    released: np.ndarray
    required: np.ndarray         # cover required by the decree on the certified numbers
    ctc_cert: np.ndarray         # cost to complete on certified progress
    ctc_true: np.ndarray
    cash: np.ndarray             # developer cash, end of month
    arrears: np.ndarray          # unpaid contractor dues
    debt: np.ndarray
    spend: np.ndarray
    land_due: np.ndarray
    land_paid: np.ndarray
    land_late: np.ndarray        # months the oldest unpaid instalment is late
    land_arrears: np.ndarray
    stress: np.ndarray           # collection weakness used by the story (0 = none)
    events: list                 # (month, kind) that complaints react to


def cost_path(sig: Signals, st: Setup, drv) -> np.ndarray:
    """total build cost at each month: 40 % follows the dollar, 60 % follows the real rebar and cement index."""
    imp = GEN["cost"]["imported_share"]
    fx, mat = drv.usd_egp.values, drv.materials_index.values
    return sig.bua_m2 * st.cost_usd_m2 * (imp * fx + (1 - imp) * fx[0] * mat / mat[0])


def stress_path(sig: Signals, st: Setup, rng: np.random.Generator) -> tuple[np.ndarray, int | None]:
    """buyers pay less 3-6 months before a stall and during it; back to normal two months after a recovery."""
    s = np.zeros(N)
    if sig.story not in ("gradual_stall", "stall_recovery"):
        return s, None
    onset = sig.onset if sig.onset is not None else st.launch + 14
    ramp = int(rng.integers(3, 7))
    peak = float(rng.uniform(0.35, 0.5))
    end = (sig.recovery + 2) if sig.recovery is not None else N
    for t in range(max(onset - ramp, 0), min(end, N)):
        s[t] = peak * min(1.0, (t - (onset - ramp)) / ramp)
    return s, onset


def sales_and_collections(sig, st, drv, rng, stress, onset, bulk_month):
    t = np.arange(N)
    fx0 = drv.usd_egp.values[0]
    cost_m2 = st.cost_usd_m2 * (GEN["cost"]["imported_share"] * drv.usd_egp.values + (1 - GEN["cost"]["imported_share"]) * fx0 * drv.materials_index.values / drv.materials_index.values[0])
    margin = float(rng.uniform(*S["margin"]))
    jump, lag = float(rng.uniform(*S["price_jump"])), int(rng.integers(S["price_jump_lag"][0], S["price_jump_lag"][1] + 1))
    ramp = np.clip((t - (FLOAT_M + lag)) / 2.0, 0, 1)
    k = np.clip(t - st.launch, 0, None)
    price_m2 = cost_m2[st.launch] * margin * (1 + S["price_drift_month"]) ** k * (1 + jump * ramp)
    area = sig.bua_m2 / sig.units
    boom = float(rng.uniform(*S["boom_factor"]))
    b0, b1 = S["boom_months"]
    boom_t = np.where((t >= FLOAT_M + b0) & (t <= FLOAT_M + b1), boom, 1.0)
    rate_t = np.exp(-S["rate_sensitivity"] * (drv.policy_rate_pct.values - 16.25))
    ram_t = 1 - 0.5 * drv.ramadan_share.values
    story = np.ones(N)
    if sig.story == "new_start":
        story[st.launch:st.launch + 4] = 1.5
    if sig.story in ("gradual_stall", "stall_recovery") and onset is not None:
        story[onset - 4:] *= 0.45
        story[onset:] *= 0.4
        if sig.recovery is not None:
            story[sig.recovery:] = 1.0
    for m, _, _ in sig.handovers:
        story[m:m + 3] *= 1.4
    saleable = float(rng.uniform(*S["saleable_share"])) * sig.units
    sold, value, dp = np.zeros(N, int), np.zeros(N), np.full(N, S["down_payment"])
    cum = 0
    for m in range(st.launch, N):
        h = (S["hazard_launch"] * np.exp(-(m - st.launch) / S["hazard_decay_months"]) + S["hazard_tail"]) * rate_t[m] * ram_t[m] * boom_t[m] * story[m]
        lam = h * max(saleable - cum, 0)
        n = int(rng.poisson(rng.gamma(6.0, lam / 6.0))) if lam > 0 else 0
        price = price_m2[m] * area * rng.uniform(0.97, 1.03)
        if m == bulk_month:                                  # one investor buys a block, pays 35 % up front
            n_b = min(int(0.05 * sig.units), sig.units - cum - n)
            n += max(n_b, 0)
            dp[m] = (S["down_payment"] * (n - n_b) + 0.35 * n_b) / max(n, 1)
            price *= 0.96
        n = min(n, sig.units - cum)
        sold[m], value[m], cum = n, n * price, cum + n
    years = float(rng.uniform(*S["installment_years"]))
    nm = int(round(12 * years))
    late = np.where((t >= FLOAT_M) & (t < FLOAT_M + 6), S["late_rate_after_float"], S["late_rate"])
    pay = np.clip(1 - late - stress, 0.1, 1.0)
    coll = np.zeros(N)
    for m in np.nonzero(sold)[0]:
        coll[m] += value[m] * dp[m]
        end = min(N, m + nm + 1)
        coll[m + 1:end] += value[m] * (1 - dp[m]) / nm * pay[m + 1:end]
    avg = np.where(sold > 0, value / np.maximum(sold, 1), np.nan)
    return sold, avg, value, coll


def run(sig: Signals, st: Setup, tr: Truth, drv, rep_val, rep_flag, rng, drain: np.ndarray, bulk_month: int | None) -> Economy:
    total = cost_path(sig, st, drv)
    stress, onset = stress_path(sig, st, rng)
    sold, avg, value, coll = sales_and_collections(sig, st, drv, rng, stress, onset, bulk_month)
    cert = np.maximum.accumulate(np.nan_to_num(np.where(rep_flag, rep_val, np.nan), nan=0.0))
    dprog = np.diff(tr.progress, prepend=0.0)
    spend = dprog / 100 * total
    ctc_cert, ctc_true = total * (1 - cert / 100), total * (1 - tr.progress / 100)
    fund = F[st.strength]
    rate = drv.policy_rate_pct.values + F["credit_spread_pct"]
    land_total = float(rng.uniform(*L["price_m2"])) * sig.land_area_m2
    inst = land_total / L["installments"]
    first_due = st.launch + int(rng.integers(L["handover_after_launch_months"][0], L["handover_after_launch_months"][1] + 1))
    due_months = {first_due + 3 * i for i in range(L["installments"])}
    eq_month = st.launch
    land_first = F["story_adequacy"][sig.story] >= 1.0          # healthy, slow, delivered and new compounds pay the land before anything else is late

    def cash_loop(cap: float, freeze: bool) -> dict:
        bal = cash = debt = arrears = land_arr = 0.0
        oldest = None
        cs = released_cum = cert_prev = coll_cum = 0.0
        o = {k: np.zeros(N) for k in ("balance", "cover_balance", "released", "required", "cash", "arrears", "debt", "land_due", "land_paid", "land_late", "land_arrears")}
        for t in range(N):
            coll_cum += coll[t]
            rel = 0.0
            req = st.cover_pct / 100 * ctc_cert[t] if cert[t] < st.cover_cancel_pct else 0.0
            reserve = E["refund_reserve"] * coll_cum
            if rep_flag[t]:
                cs += max(0.0, cert[t] - cert_prev) / 100 * total[t]
                eligible = float("inf") if cert[t] >= 99.5 else cs * (1 + E["release_advance"]) - released_cum
                rel = max(0.0, min(bal + coll[t] - reserve, eligible))
            cert_prev = cert[t]
            bal += coll[t] - rel
            released_cum += rel
            diverted = min(rel * drain[t], rel)
            inflow = rel - diverted
            if t == eq_month:
                cash += fund["equity"] * total[t]
            if sig.recovery is not None and t == sig.recovery:             # financing arrives the month work restarts
                inflow += arrears + land_arr + 3 * max(spend[max(t - 12, 0):t].mean() if t else 0.0, 0.0) + 0.1 * ctc_true[t]
            overhead = total[t] * F["overhead_year"] / 12 if st.launch <= t and tr.progress[t] < 99.5 else 0.0
            interest = debt * rate[t] / 1200
            due = inst if t in due_months else 0.0
            if land_arr > 0:
                land_arr *= 1 + L["penalty_month"]
            if due:
                land_arr += due
                oldest = t if oldest is None else oldest
            payable_c = spend[t] + overhead + interest + arrears
            payable = payable_c + (land_arr if land_first else 0.0)
            avail = cash + inflow
            stalled_credit = freeze and onset is not None and t >= onset - 3 and (sig.recovery is None or t < sig.recovery)
            limit = 0.0 if stalled_credit else cap
            draw = max(0.0, min(payable - avail, limit - debt)) if t >= st.launch else 0.0
            debt += draw
            paid = min(payable, avail + draw)
            c_paid = min(payable_c, paid)
            arrears, cash = payable_c - c_paid, avail + draw - paid
            lp = 0.0
            if land_first:
                lp = paid - c_paid
                land_arr -= lp
            elif land_arr > 0 and arrears <= 1e-6 and cash >= land_arr + max(spend[max(t - 2, 0):t + 1].mean(), 0):
                lp, cash, land_arr = land_arr, cash - land_arr, 0.0
            if land_arr < 1.0:
                land_arr, oldest = 0.0, None
            if arrears <= 1e-6 and debt > 0:
                rep = min(debt, max(0.0, cash - 2 * max(spend[max(t - 3, 0):t + 1].mean(), 0)) * 0.5)
                debt, cash = debt - rep, cash - rep
            burn = max(spend[max(t - 2, 0):t + 1].mean(), total[t] / 36)
            gap = float(np.clip(arrears / (2 * burn), 0, 0.7))          # a developer in arrears cannot keep the full cover posted
            for k, v in (("balance", bal), ("cover_balance", bal + req * (1 - gap)), ("released", rel), ("required", req), ("cash", cash), ("arrears", arrears), ("debt", debt), ("land_due", due), ("land_paid", lp),
                         ("land_late", (t - oldest) if oldest is not None else 0), ("land_arrears", land_arr)):
                o[k][t] = v
        return o

    peak = cash_loop(float("inf"), False)["debt"].max()
    o = cash_loop(F["story_adequacy"][sig.story] * fund["adequacy"] * peak, True)
    events = [(m, "postponement") for m in sig.postponements] + [(m, "handover") for m, _, _ in sig.handovers]
    events += [(FLOAT_M + lag_, "price") for lag_ in range(1, 3)]
    if onset is not None:
        events.append((onset, "stall"))
    return Economy(total, sold, avg, value, coll, o["balance"], o["cover_balance"], o["released"], o["required"], ctc_cert, ctc_true, o["cash"], o["arrears"], o["debt"], spend,
                   o["land_due"], o["land_paid"], o["land_late"], o["land_arrears"], stress, events)
