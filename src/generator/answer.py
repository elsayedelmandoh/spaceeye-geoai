"""
propose: the private side of the data: true distress per month, the answer key (compound x month) and the complaint truth.
input: the simulated units and the complaints with their private helper columns.
output: `distress(u)` (bool per month), `answer_key(units, devs)`, `complaint_truth(complaints)`. these files live in Project/private and are joined only at training time.

true distress (hidden) in a month: work really stalled for 6 months in a row before handover (and below 85 %), or (3 months in a row) contractor arrears above two months of burn,
or land arrears of 3+ months while the cover held is below the decree minimum.
label_distress_next_6m = true distress in any of the next 6 months (`label_censored` where fewer than 6 months are left in the horizon).
"""

import numpy as np
import pandas as pd

from src.generator.inputs import GEN, MONTHS, N, O0


def distress(u) -> np.ndarray:
    tr, e, s = u.tr, u.eco, u.sig
    started = np.arange(N) >= u.st.plan_start + 3
    run, stalled = 0, np.zeros(N, bool)
    handed = np.arange(N) >= min([m for m, _, _ in s.handovers], default=N)
    for t in range(N):
        run = run + 1 if (tr.stalled[t] and started[t] and tr.progress[t] < 85 and not handed[t]) else 0
        stalled[t] = run >= 6
    burn = np.maximum(pd.Series(e.spend).rolling(3, min_periods=1).mean().values, e.total_cost / 36)
    money = (e.arrears > 2 * burn) | ((e.land_late >= 3) & (e.cover_balance < e.required))
    persistent = pd.Series(money).rolling(3, min_periods=3).sum().fillna(0).values >= 3        # money trouble must last 3 months in a row
    return stalled | persistent


def answer_key(units, devs: dict) -> pd.DataFrame:
    rows = []
    for u in units:
        d = u.distress
        nxt = np.array([d[t + 1:t + 7].any() if t + 1 < N else False for t in range(N)])
        cens = np.arange(N) + 6 > N - 1
        sl = slice(O0, N)
        rows.append(pd.DataFrame({
            "code": u.sig.code, "month": [str(p) for p in MONTHS[sl]], "story": u.sig.story, "story_reason": u.sig.why,
            "developer_strength": devs[u.sig.developer]["strength"], "reporting_style": devs[u.sig.developer]["style"],
            "true_progress_pct": u.tr.progress[sl].round(2), "true_cash_egp": u.eco.cash[sl].round(0), "contractor_arrears_egp": u.eco.arrears[sl].round(0),
            "bank_debt_egp": u.eco.debt[sl].round(0), "true_cost_to_complete_egp": u.eco.ctc_true[sl].round(0), "escrow_cash_egp": u.eco.balance[sl].round(0),
            "handed_over_units": u.tr.handed[sl], "true_occupied_units": u.tr.occupied[sl].round(1),
            "true_distress": d[sl], "label_distress_next_6m": nxt[sl], "label_censored": cens[sl], "synthetic_label": GEN["label"],
        }))
    return pd.concat(rows, ignore_index=True)


def complaint_truth(cmp_: pd.DataFrame) -> pd.DataFrame:
    t = cmp_[["complaint_id", "_true_code", "_true_cat", "_cause", "_dup_of", "_wrong"]].rename(
        columns={"_true_code": "true_code", "_true_cat": "true_category", "_cause": "true_cause", "_dup_of": "duplicate_of", "_wrong": "desk_category_wrong"})
    t["has_text"] = cmp_.text_ar.notna().values
    t["synthetic_label"] = GEN["label"]
    return t
