"""
propose: step 7. realism checks. `hard` checks decide whether the output may be used (fail -> exit code 1); `calibration` rows are reported with numbers but do not fail the run.
input: the simulated units (hidden truth), the clean fin_monthly and complaints (before the defects), the defective copies and the defects log.
output: a DataFrame (check, kind, value, rule, ok) and a list of out-of-tolerance satellite points for the report.

hard   balance >= 0 | collections <= value sold | true progress never falls | anchors within +-10 (announced, handover, satellite level) | BUA / land <= 1.8 |
       same seed -> same files | 25-40 % of reports are multiples of 5 | warning for every compound with K3 > 12 and none for an active compound with K3 <= 0 |
       reports equal the real announced values exactly in the statement months | the 6 defects are present with the logged counts
"""

import numpy as np
import pandas as pd

from src.generator.defects import PHONE
from src.generator.inputs import GEN, MONTHS, M_END, N, O0, mi
from src.generator.observe import season_kwh
from src.generator.truth import handover_floor

TOL = 10.0


def _r(check, kind, value, rule, ok) -> dict:
    return {"check": check, "kind": kind, "value": value, "rule": rule, "ok": bool(ok)}


def anchors(units) -> tuple[list, list]:
    """announced + handover + satellite-level differences between true progress and each real anchor; returns (rows, misses)."""
    rows, miss = [], []
    for u in units:
        s, p = u.sig, u.tr.progress
        for (m, v, rid) in s.anchors:
            mm = min(m, N - 1)
            rows.append((s.code, "announced", str(MONTHS[mm]), v, float(p[mm]), v - float(p[mm])))
        for m, sub, scope in s.handovers:
            fl = handover_floor(sub, scope, u.st)
            rows.append((s.code, "handover_floor", str(MONTHS[m]), fl, float(p[m]), fl - float(p[m])))
        for m, lvl in sorted(s.dw_p.items()):                 # the monotone fit of the real built level: a built footprint does not un-build
            if m < O0 or m >= N:
                continue
            d = lvl - float(p[m])
            rows.append((s.code, "satellite", str(MONTHS[m]), lvl, float(p[m]), d))
            if abs(d) > TOL:
                near = [a for a in s.anchors if abs(min(a[0], N - 1) - m) <= 24] + [h for h in s.handovers if abs(h[0] - m) <= 24]
                why = "announced/handover anchor within 24 months" if near else ("before the first sustained activity" if m < u.st.cstart else "UNEXPLAINED")
                miss.append((s.code, str(MONTHS[m]), round(lvl, 1), round(float(p[m]), 1), why))
    return rows, miss


def run(units, drv, fin, cmp_, fin_def, cmp_def, defects, real, same_hash: bool, hash_note: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    out = []
    # 1 balance >= 0
    mn = min(fin.cover_balance_egp.min(), min(u.eco.cash.min() for u in units), min(u.eco.balance.min() for u in units))
    out.append(_r("balance_non_negative", "hard", f"min {mn:,.0f}", "cover balance, escrow cash and developer cash >= 0", mn >= 0))
    # 2 collections <= value of sales
    worst = max((np.cumsum(u.eco.collections) - np.cumsum(u.eco.value_sold)).max() for u in units)
    out.append(_r("collections_le_sales", "hard", f"max excess {worst:,.0f} EGP", "cumulative collections <= cumulative contract value of units sold", worst <= 1e-3))
    # 3 truth never decreases, handed <= units, occupied <= handed
    dmin = min(np.diff(u.tr.progress).min() for u in units)
    hmin = min(np.diff(u.tr.handed).min() for u in units)
    bad_occ = sum(int(((u.tr.occupied > u.tr.handed + 1e-6) | (u.tr.handed > u.sig.units)).sum()) for u in units)
    out.append(_r("truth_non_decreasing", "hard", f"min step {dmin:.4f}; handed min step {hmin}; occupancy violations {bad_occ}", "true progress and handed-over units never fall; occupied <= handed <= units",
                  dmin >= -1e-9 and hmin >= 0 and bad_occ == 0))
    # 4 anchors
    rows, miss = anchors(units)
    a = pd.DataFrame(rows, columns=["code", "anchor", "month", "anchor_value", "truth", "diff"])
    ann, han, sat = (a[a.anchor == k] for k in ("announced", "handover_floor", "satellite"))
    out.append(_r("anchor_announced", "hard", f"max |diff| {ann['diff'].abs().max():.1f} over {len(ann)} announced values", f"truth within +-{TOL:.0f} points of every announced value", ann["diff"].abs().max() <= TOL))
    out.append(_r("anchor_handover", "hard", f"worst shortfall {max(han['diff'].max(), 0):.1f} over {len(han)} events", "truth at least the handover floor in every event month", han["diff"].max() <= 0.5))
    within = float((sat["diff"].abs() <= TOL).mean())
    unexpl = [m for m in miss if m[4] == "UNEXPLAINED"]
    out.append(_r("anchor_satellite_level", "hard", f"{within:.0%} of {len(sat)} compound-years within +-{TOL:.0f}; {len(miss)} misses, {len(unexpl)} unexplained",
                  "built-share level (progress implied by the satellite, monotone) within +-10; every miss has a real announced or handover anchor within 24 months", within >= 0.75 and not unexpl))
    # 5 BUA / land
    ratio = max(u.sig.bua_m2 / u.sig.land_area_m2 for u in units)
    per_unit = [u.sig.bua_m2 / u.sig.units for u in units]
    out.append(_r("bua_over_land", "hard", f"max {ratio:.2f}; BUA per unit {min(per_unit):.0f}-{max(per_unit):.0f} m2", "BUA / land <= 1.8 (decree 483/2023 cap)", ratio <= 1.8 + 1e-3))
    # 6 reproducibility
    out.append(_r("same_seed_same_files", "hard", hash_note, "two independent builds from the same seed give identical tables", same_hash))
    # 7 multiples of 5
    rep = fin.reported_pct.dropna()
    share = float((np.isclose(rep % 5, 0) | np.isclose(rep % 5, 5)).mean())
    out.append(_r("reports_multiples_of_5", "hard", f"{share:.1%} of {len(rep)} reports", "25-40 % of reports are multiples of 5", 0.25 <= share <= 0.40))
    # 8 warnings
    k3 = {u.sig.code: u.sig.k3 for u in units}
    miss_w = [u.sig.code for u in units if (k3[u.sig.code][O0:] > 12).any() and not (u.warn[O0:][np.argmax(k3[u.sig.code][O0:] > 12):]).any()]
    n_k3 = sum(1 for u in units if (k3[u.sig.code][O0:] > 12).any())
    bad_w = sum(int((u.warn[O0:] & u.sig.state[O0:] & (u.sig.k3[O0:] <= 0)).sum()) for u in units)
    out.append(_r("warning_rules", "hard", f"{n_k3 - len(miss_w)}/{n_k3} compounds with K3 > 12 warned; {bad_w} warnings on active compounds with K3 <= 0",
                  "a warning for every compound with K3 > 12, none for an active compound with K3 <= 0", not miss_w and bad_w == 0))
    # 9 reports equal the real announced values
    st = real["statements"]
    ann_rows = st[(st.kind == "progress") & (pd.to_datetime(st.published_date) >= pd.Timestamp("2023-01-01")) & (pd.to_datetime(st.published_date) <= pd.Timestamp("2026-09-30"))]
    ok_a, n_a = 0, len(ann_rows)
    for r in ann_rows.itertuples():
        row = fin[(fin.code == r.code) & (fin.month == str(pd.Period(r.published_date, "M")))]
        ok_a += int(len(row) == 1 and row.reported_pct.iloc[0] == r.value and row.report_date.iloc[0] == pd.Timestamp(r.published_date))
    out.append(_r("reports_equal_announced", "hard", f"{ok_a}/{n_a} statement months", "reported_pct equals the real announced value exactly (value and date) in every statement month", ok_a == n_a))
    # 10 defects present with the logged counts
    d = defects.set_index("defect_id").rows_affected
    dup = int(fin_def.duplicated(["code", "month"]).sum())
    unk = int((~cmp_def.code.isin(real["compounds"].code)).sum())
    ph = int(cmp_def.text_ar.dropna().map(lambda t: bool(PHONE.search(t))).sum())
    chg = int((fin_def.drop_duplicates(["code", "month"], keep="first").set_index(["code", "month"]).cover_balance_egp.reindex(fin.set_index(["code", "month"]).index).values
               != fin.cover_balance_egp.values).sum())
    ok = dup == d[2] and unk == d[4] and ph == d[6] and chg == d[1] and len(defects) == 6
    out.append(_r("defects_planted", "hard", f"dup {dup}/{d[2]}, unknown code {unk}/{d[4]}, phones {ph}/{d[6]}, balance rows {chg}/{d[1]}", "the 6 defects exist and match defects_log row counts", ok))
    # calibration (reported, not failing)
    cal = []
    n = len(cmp_)
    cal.append(_r("complaints_total", "calibration", f"{n}", "about 2,500 (2,000-3,000)", 2000 <= n <= 3000))
    wrong = float((cmp_.category != cmp_._true_cat).mean())
    cal.append(_r("complaints_wrong_category", "calibration", f"{wrong:.1%}", "10-15 % filed under the wrong category", 0.10 <= wrong <= 0.15))
    cal.append(_r("complaint_texts", "calibration", f"{int(cmp_.text_ar.notna().sum())}", "about 100 texts", int(cmp_.text_ar.notna().sum()) == GEN["complaints"]["n_texts"]))
    reg_rows = [(u.sig.code, str(MONTHS[m]), (u.rep.date[m] - np.datetime64(M_END[int(u.rep.covers[m])])).astype("timedelta64[D]").astype(int)) for u in units for m in range(O0, N) if u.rep.regular[m]]
    lags = np.array([r[2] for r in reg_rows])
    cal.append(_r("report_lag_days", "calibration", f"{lags.min()}-{lags.max()} (median {np.median(lags):.0f})", "15-45 days after quarter end (late-style developers up to 75)", lags.min() >= 15 and lags.max() <= 75))
    due, miss_n = sum(u.rep.due for u in units), sum(u.rep.missing for u in units)
    sd, sm = sum(u.rep.stalled_due for u in units), sum(u.rep.stalled_missing for u in units)
    cal.append(_r("report_missing_share", "calibration", f"{miss_n / due:.1%} of {due} quarterly reports; {sm / max(sd, 1):.0%} of {sd} while stalled", "about 5 % missing normally, 35 % while stalled (late-style developers +3 points)",
                  0.03 <= miss_n / due <= 0.15 and 0.2 <= sm / max(sd, 1) <= 0.5))
    # sales boom and price jump after the float
    f = np.array([u.eco.sold for u in units]).sum(0)
    fm = mi(GEN["float_month"] + "-01")
    boom = f[fm + 2:fm + 5].mean() / f[fm - 6:fm].mean()
    cal.append(_r("post_float_sales_boom", "calibration", f"x{boom:.2f}", "sales 2-4 months after the float above the 6 months before (>= 1.15)", boom >= 1.15))
    pr = np.array([np.nanmean(u.eco.price[fm + 6:fm + 12]) / np.nanmean(u.eco.price[fm - 6:fm]) for u in units if np.isfinite(u.eco.price[fm + 6:fm + 12]).any() and np.isfinite(u.eco.price[fm - 6:fm]).any()])
    cal.append(_r("post_float_price_jump", "calibration", f"median +{(np.median(pr) - 1):.0%}", "list price +15-40 % after the float (incl. drift)", 1.15 <= np.median(pr) <= 1.55))
    # electricity
    seas = season_kwh(drv)
    aug_jan = np.mean([seas[mi(f"{y}-08-01")] / seas[mi(f"{y}-01-01")] for y in (2024, 2025)])
    cal.append(_r("kwh_aug_over_jan", "calibration", f"{aug_jan:.2f}", "1.3-1.8 from the real temperature", 1.3 <= aug_jan <= 1.8))
    occ_u = [u for u in units if u.tr.occupied[O0:].max() > 50]
    kwh_per = np.mean([np.mean(u.home_occ[O0:][u.tr.occupied[O0:] > 50] / u.tr.occupied[O0:][u.tr.occupied[O0:] > 50]) for u in occ_u]) if occ_u else float("nan")
    cal.append(_r("kwh_per_occupied_unit", "calibration", f"{kwh_per:.0f} kWh/month (mean over {len(occ_u)} compounds)", "yearly mean 140-170", 140 <= kwh_per <= 170))
    # stories vs distress
    dist = sum(1 for u in units if u.distress[O0:].sum() >= 3)
    cal.append(_r("compounds_ever_distressed", "calibration", f"{dist} of {len(units)} (true, hidden, 3+ months)", "1-7 of 22 (ACUD says ~8 % of developers are seriously late; real signals here show more stalled-looking compounds)", 1 <= dist <= 7))
    late_any = sum(1 for u in units if (u.sig.k3[O0:] > 0).any())
    cal.append(_r("compounds_late_at_some_point", "calibration", f"{late_any} of {len(units)} (K3 > 0, from the real promises)", "informational (real signal)", True))
    return pd.DataFrame(out + cal), a, pd.DataFrame(miss, columns=["code", "month", "satellite_implied", "truth", "explained_by"])
