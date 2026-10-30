# ruff: noqa  -- archived experiment script, kept as run
"""Diagnostic only (no model change): why did the real-case backtest alert in 1 of 6 cases?

Reads the frozen backtest outputs and the saved real tables, rebuilds a quarter-by-quarter timeline per case, and
labels which rule could fire at each quarter. Nothing is refit, retuned or written outside this folder.

usage (repo python env):
  python diagnose_backtest.py [REPO] [PROJECT_APP_DATA]
defaults: F:/ACUD AI Data Lab/spaceeye-v6-fixes and F:/ACUD AI Data Lab/Project/app_data

inputs
  <repo>/releases/ready-data/backtest/{cases,events,kpi_inputs}.csv, <repo>/configs/data.yaml
  <app_data>/backtest/kpi_values_backtest.parquet  (backtest activity variant q2hold; checked equal to kpi_inputs.csv)
  <app_data>/real/{sat_quarterly,sat_yearly,statements,compounds,eval_outcomes}.parquet
outputs (next to this script)
  timelines/<case>_<code>.csv, timelines/compact_tables.md, summary_by_case.csv, k2_firing_all_compounds.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(sys.argv[1] if len(sys.argv) > 1 else "F:/ACUD AI Data Lab/spaceeye-v6-fixes")
APP = Path(sys.argv[2] if len(sys.argv) > 2 else "F:/ACUD AI Data Lab/Project/app_data")
OUT = Path(__file__).parent
CFG = yaml.safe_load((REPO / "configs/data.yaml").read_text(encoding="utf-8"))
L = CFG["levels"]
K1_ACTIVE, N_MIN = CFG["k1_active"], CFG["n_images_min"]
MONTHS_BEFORE = CFG["backtest"]["months_before"]


def qlabel(qi): return f"{2016 + qi // 4}Q{qi % 4 + 1}"
def qindex_of(ts): return (ts.year - 2016) * 4 + (ts.month - 1) // 3
def qend(qi): return pd.Timestamp(2016 + qi // 4, 3 * (qi % 4) + 3, 1) + pd.offsets.MonthEnd(0)
def summer_year(qi): return 2016 + qi // 4 if qi % 4 >= 2 else 2015 + qi // 4


def rule_levels(k2, k3, k6, started):
    """level each K rule alone would give (same thresholds as kpis.level_of; None = rule silent)."""
    k2 = 0 if (pd.isna(k2) or not started) else k2
    k3 = 0 if pd.isna(k3) else k3
    k6 = 0 if pd.isna(k6) else k6
    r2 = 1 if k2 >= L["k2_l1"] else 2 if k2 >= L["k2_l2"] else 3 if k2 >= 1 else None
    r3 = 1 if k3 > L["k3_l1"] else 2 if k3 >= L["k3_l2"] else 3 if k3 >= 1 else None
    r6 = 1 if k6 > L["k6_l1"] else 2 if k6 >= L["k6_l2"] else None
    rc = 1 if (k2 >= L["combo_k2"] and k3 > L["combo_k3"]) else None
    return r2, r3, r6, rc


def md_table(df):
    """plain markdown table (no tabulate dependency)."""
    head = "| " + " | ".join(df.columns) + " |"
    sep = "| " + " | ".join("---" for _ in df.columns) + " |"
    body = ["| " + " | ".join(map(str, r)) + " |" for r in df.values.tolist()]
    return chr(10).join([head, sep] + body)


def missing_text(r):
    """what stopped a level 1-2 alert in this quarter (descriptive)."""
    if not r.K4:
        return f"not assessable: {int(r.n_images)} images < {N_MIN}"
    if pd.notna(r.level) and r.level <= 2:
        return "alert fired"
    if not r.started:
        return "start not yet confirmed (needs 4 consecutive active quarters or a launch/delivery statement); K2 silent"
    if r.active is True:
        return "A active -> K2=0; K3 clock not yet past the deadline"
    if r.active is False and r.K2 < L["k2_l2"]:
        return f"A inactive but K2={int(r.K2)} < {L['k2_l2']}"
    return "A missing"


def main():
    cases = pd.read_csv(REPO / "releases/ready-data/backtest/cases.csv")
    ev = pd.read_csv(REPO / "releases/ready-data/backtest/events.csv")
    kin = pd.read_csv(REPO / "releases/ready-data/backtest/kpi_inputs.csv")
    kb = pd.read_parquet(APP / "backtest/kpi_values_backtest.parquet")
    sat = pd.read_parquet(APP / "real/sat_quarterly.parquet")
    yearly = pd.read_parquet(APP / "real/sat_yearly.parquet")
    stm = pd.read_parquet(APP / "real/statements.parquet")
    comp = pd.read_parquet(APP / "real/compounds.parquet").set_index("code")
    eo = pd.read_parquet(APP / "real/eval_outcomes.parquet").set_index("case")

    # the parquet used here must be the one the published replay used
    chk = kb.merge(kin, on=["code", "quarter"], suffixes=("", "_r"))
    assert len(chk) == len(kin) == len(kb)
    assert (chk.level.fillna(-1).astype(float) == chk.level_r.fillna(-1).astype(float)).all()
    assert (chk.K2.fillna(-1).astype(float) == chk.K2_r.fillna(-1).astype(float)).all()
    assert (chk.started == chk.started_r).all()

    base = sat[["code", "quarter", "qi", "n_images", "built_prob_mean", "K1", "dw12_built"]].merge(
        kb[["code", "qi", "activity_prob", "active", "started", "start_quarter", "K2", "K3", "K4", "K6", "may_be_complete",
            "level", "level_label", "observed_started"]], on=["code", "qi"])
    base["active"] = base.active.map({True: True, False: False})  # <NA> -> NaN
    base["K1_growth"] = base.K1 > K1_ACTIVE
    yearly = yearly.set_index(["code", "year"])
    summ, md = [], ["# Compact timelines (view of the CSVs; pre = quarter ends on or before the 6-month cutoff)"]
    for c in cases.itertuples():
        d = base[base.code == c.code].sort_values("qi").copy()
        dl, alt = pd.Timestamp(c.first_deadline), pd.Timestamp(ev.set_index("case").promise_original_end[c.case])
        cut, cut_alt = dl - pd.DateOffset(months=MONTHS_BEFORE), alt - pd.DateOffset(months=MONTHS_BEFORE)
        d["qend"] = d.qi.map(qend)
        d["months_to_deadline"] = ((dl - d.qend).dt.days / 30.44).round().astype(int)
        d["pre_cutoff"] = d.qend <= cut
        d["pre_cutoff_alt"] = d.qend <= cut_alt
        rl = d.apply(lambda r: rule_levels(r.K2, r.K3, r.K6, r.started), axis=1, result_type="expand")
        d["rule_K2"], d["rule_K3"], d["rule_K6"], d["rule_combo"] = rl[0], rl[1], rl[2], rl[3]
        d["missing"] = d.apply(missing_text, axis=1)
        # independent context, not used by the level rules: OBT yearly structure (latest year already over) and published progress
        sy = d.qi.map(summer_year)
        for col in ("n_built_cells", "height_mean_m", "height_p90_m", "share_built_ge20m"):
            d["obt_" + col] = [yearly[col].get((c.code, y), np.nan) for y in sy]
        prog = stm[(stm.code == c.code) & (stm.kind == "progress")].copy()
        prog["pub"] = pd.to_datetime(prog.published_date)
        d["progress_pct_published"] = [prog[prog.pub <= q].sort_values("pub").value.iloc[-1] if (prog.pub <= q).any() else np.nan for q in d.qend]
        evs = stm[(stm.code == c.code) & (stm.kind == "event")].copy()
        evs["pub"] = pd.to_datetime(evs.published_date)
        d["events_published_in_quarter"] = [";".join(f"{r.subtype}" for r in evs[(evs.pub <= q) & (evs.pub > q - pd.offsets.QuarterEnd(1))].itertuples()) for q in d.qend]

        full = d.copy()
        d = d[(d.qi >= 12) & (d.qend <= dl + pd.offsets.QuarterEnd(0))]  # 2019Q1 .. quarter holding the first deadline
        cols = ["quarter", "months_to_deadline", "pre_cutoff", "pre_cutoff_alt", "n_images", "K4", "built_prob_mean", "dw12_built", "K1", "K1_growth",
                "activity_prob", "active", "started", "start_quarter", "K2", "K3", "K6", "may_be_complete", "level", "level_label", "rule_K2", "rule_K3",
                "rule_K6", "rule_combo", "missing", "obt_n_built_cells", "obt_height_mean_m", "obt_height_p90_m", "obt_share_built_ge20m",
                "progress_pct_published", "events_published_in_quarter"]
        d[cols].round(4).to_csv(OUT / "timelines" / f"{c.case}_{c.code}.csv", index=False)
        v = d[["quarter", "pre_cutoff", "n_images", "built_prob_mean", "K1", "activity_prob", "active", "started", "K2", "K3", "K6", "level_label", "obt_height_mean_m", "obt_share_built_ge20m"]].copy()
        v["pre_cutoff"] = v.pre_cutoff.map({True: "pre", False: ""})
        v["active"] = v.active.map({True: "1", False: "0"}).fillna("")
        v["started"] = v.started.map({True: "1", False: "0"})
        v = v.rename(columns={"pre_cutoff": "cut", "n_images": "imgs", "built_prob_mean": "built", "activity_prob": "A", "active": "act", "started": "st",
                              "level_label": "level", "obt_height_mean_m": "obt_h", "obt_share_built_ge20m": "obt_ge20"})
        md += [chr(10) + f"## {c.case} / {c.code} (first date {dl.date()}, cutoff {cut.date()})" + chr(10), md_table(v.astype(object).round(3).fillna("").astype(str))]

        pre, a = d[d.pre_cutoff], d[d.pre_cutoff & d.level.notna()]
        started_pre = a[a.started]
        first_any = full[full.level.isin([1, 2])]
        first_any_after_start = full[full.level.isin([1, 2]) & full.started]
        summ.append({
            "case": c.case, "code": c.code, "deadline": dl.date(), "cutoff": cut.date(), "alt_deadline": alt.date(),
            "quarters_2019Q1_to_cutoff": len(pre), "quarters_n_images_ge6": int(pre.K4.sum()), "min_images": int(pre.n_images.min()), "median_images": float(pre.n_images.median()),
            "assessable_pre_cutoff": len(a), "started_and_assessable_pre_cutoff": len(started_pre),
            "start_quarter": started_pre.start_quarter.iloc[0] if len(started_pre) else None,
            "first_assessable_quarter": a.quarter.iloc[0] if len(a) else None,
            "A_active_share_started_pre": float(started_pre.active.astype(float).mean()) if len(started_pre) else np.nan,
            "K1_growth_share_started_pre": float(started_pre.K1_growth.mean()) if len(started_pre) else np.nan,
            "max_K2_pre_cutoff": float(started_pre.K2.max()) if len(started_pre) else np.nan,
            "levels_pre_cutoff": "".join(str(x) if pd.notna(x) else "-" for x in a.level),
            "any_L12_pre_cutoff_started": int((started_pre.level <= 2).sum()),
            "any_L12_pre_cutoff_not_started": int((a[~a.started].level <= 2).sum()),
            "first_L12_any_quarter_after_start": first_any_after_start.quarter.iloc[0] if len(first_any_after_start) else None,
            "first_L12_any_quarter_any": first_any.quarter.iloc[0] if len(first_any) else None,
            "level_at_cutoff": a.level_label.iloc[-1] if len(a) else None,
            "K6_at_cutoff": a.K6.iloc[-1] if len(a) else None,
            "built_prob_start": float(pre.built_prob_mean.iloc[0]), "built_prob_at_cutoff": float(pre.built_prob_mean.iloc[-1]),
            "dw12_built_at_cutoff": float(pre.dw12_built.iloc[-1]),
            "obt_height_mean_at_cutoff": float(pre.obt_height_mean_m.iloc[-1]), "obt_share_ge20m_at_cutoff": float(pre.obt_share_built_ge20m.iloc[-1]),
            "progress_pct_at_cutoff": float(pre.progress_pct_published.iloc[-1]) if pre.progress_pct_published.notna().any() else np.nan,
            "outcome_type": eo.outcome_type[c.case], "delay_months_vs_promise": eo.delay_months_vs_promise[c.case],
        })
    (OUT / "timelines" / "compact_tables.md").write_text(chr(10).join(md) + chr(10), encoding="utf-8")
    pd.DataFrame(summ).to_csv(OUT / "summary_by_case.csv", index=False)
    print(pd.DataFrame(summ).T.to_string())

    # how often can K2 fire at all? every compound, started quarters up to 2026Q3 (context for the A-too-sticky question)
    rows = []
    for code, g in base.groupby("code"):
        st = g[g.started & g.level.notna()]
        rows.append({"code": code, "case": cases.set_index("code").case.get(code, "-"), "started_assessable_quarters": len(st),
                     "A_inactive_quarters": int((st.active == False).sum()), "max_K2": float(st.K2.max()) if len(st) else np.nan,
                     "quarters_level12": int(st.level.isin([1, 2]).sum()),
                     "quarters_level12_from_K2": int(((st.K2 >= L["k2_l2"]) & st.level.isin([1, 2])).sum()),
                     "quarters_with_K1_le_threshold": int((~st.K1_growth).sum()),
                     "A_active_while_K1_le_threshold": int(((st.active == True) & ~st.K1_growth).sum())})
    pd.DataFrame(rows).to_csv(OUT / "k2_firing_all_compounds.csv", index=False)
    print(pd.DataFrame(rows).to_string())


if __name__ == "__main__":
    main()
