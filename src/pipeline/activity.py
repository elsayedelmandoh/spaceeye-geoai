"""
propose: step 3. activity score A = probability that a compound is building (GBM, validated in 28_team_ideas_tests/s5_verify).
features per window ending at a quarter: dynamic world trend (slope8, slope12, K1, persistence) and 12-month changes of
sentinel-2 indices and dynamic world class shares. quarter of the year is NOT a feature.
trained on 12-month windows ending EVERY quarter 2019Q1-2023Q4 (not only 30 June): each window takes the open-buildings label of the plot-year whose
30 June falls inside it (windows ending in Q1 of year y -> label y-1, Q2-Q4 -> label y). threshold = out-of-fold balanced-accuracy optimum.
every feature at quarter q uses data up to q only.
if the quarterly A fails any acceptance test (FIXES_PROTOCOL section 1) the fallback is used: A from windows ending in Q2 only, held for the 4 quarters it
covers (Q2, Q3, Q4 and the next Q1). the backtest variant is trained without the plots that cover a compound (leakage), see fit(exclude=...).
input: raw/dw_polygons_quarterly, plot_labels, plot_split, s4 windows (compounds, plots at 30 June, plots at every quarter), plot_compound_overlap, sat_quarterly.
output: model/activity_gbm*.joblib, model/activity_meta*.json, A per compound-quarter.
"""

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold

from src.pipeline.common import CFG, MODEL, N_Q, RAW, qindex

SEED, THR, CAP, ACT = CFG["seed"], CFG["k1_active"], CFG["activity_features_cap"], CFG["activity"]
S4C = ["NDVI", "NDBI", "BSI", "B2", "B3", "B4", "B8", "B11", "B12", "bare", "trees", "grass", "crops", "shrub_and_scrub", "water", "built"]
FE = ["K1", "slope8", "slope12", "persist", "tslc"] + ["d_" + c for c in S4C if c not in ("built",)]
FIRST_A = qindex("2019Q1")  # first quarter with all features (windows from 2018Q1)


def wide(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """quarter x unit table of built_prob_mean (all 43 quarters)."""
    return df.pivot(index="qi", columns=key, values="built_prob_mean").reindex(range(N_Q))


def rolling_delta(w: pd.DataFrame) -> pd.DataFrame:
    """K1: mean of the last 4 quarters minus the mean of the 4 before."""
    m = w.rolling(4).mean()
    return m - m.shift(4)


def _slope(s: pd.Series, n: int) -> float:
    v = s.iloc[-n:].values.astype(float)
    return np.nan if len(v) < n or np.isnan(v).any() else np.polyfit(np.arange(n), v, 1)[0]


def features(W: pd.DataFrame, s4: pd.DataFrame, units: list[tuple[str, int]]) -> pd.DataFrame:
    """one row per (unit, quarter). s4 is indexed by (pid, qi) with the window means."""
    K1 = rolling_delta(W)
    rows = []
    for uid, qi in units:
        f = {"uid": uid, "qi": qi}
        if uid in W:
            s = W[uid].iloc[: qi + 1]
            act = (K1[uid].iloc[qi - CAP + 1 : qi + 1] > THR).values[::-1]  # newest first
            n = 0
            for a in act:
                if not a:
                    break
                n += 1
            f.update(K1=K1.at[qi, uid], slope8=_slope(s, 8), slope12=_slope(s, 12), persist=n, tslc=int(np.argmax(act)) if act.any() else CAP)
        if (uid, qi) in s4.index and (uid, qi - 4) in s4.index:
            d = s4.loc[(uid, qi)] - s4.loc[(uid, qi - 4)]
            f.update({"d_" + c: d[c] for c in S4C})
        rows.append(f)
    return pd.DataFrame(rows)


def load_s4() -> pd.DataFrame:
    """windows of compounds (every quarter), of plots ending 30 June (audit) and of plots ending every quarter (retrospective pull)."""
    names = ("s4_windows_q2.csv", "s4_windows_compounds.csv", "s4_windows_plots_quarterly.csv")
    parts = [pd.read_csv(RAW / n) for n in names if (RAW / n).exists()]
    return pd.concat(parts).drop_duplicates(["pid", "qi"]).set_index(["pid", "qi"]).sort_index()


def label_year(qi: int) -> int:
    """plot-year whose 30 June lies inside the 12-month window ending at quarter qi: Q1 -> previous year, Q2-Q4 -> same year."""
    return 2016 + qi // 4 - (1 if qi % 4 == 0 else 0)


def held_qi(qi: int, mode: str) -> int:
    """window whose A is used at quarter qi: itself (quarterly), or the latest window ending in Q2 (q2hold: Q2 -> Q2, Q3 -> Q2, Q4 -> Q2, Q1 -> previous Q2)."""
    return qi if mode == "quarterly" else qi - (qi - 1) % 4


def labels() -> pd.DataFrame:
    lab = pd.read_csv(RAW / "plot_labels.csv")
    return lab[(lab.area_ha >= 2) & lab.year.between(2018, 2023)]


def training_frame(s4: pd.DataFrame, exclude: frozenset = frozenset(), mode: str = "quarterly") -> pd.DataFrame:
    """one row per (plot, window ending 2019Q1-2023Q4; Q2 windows only in q2hold mode) with a label: growth = 1, stable = 0, others dropped.
    `exclude` = plots left out of training."""
    lab = labels()
    W = wide(pd.read_csv(RAW / "dw_polygons_quarterly.csv"), "osm_id")
    q0, q1 = qindex(ACT["train_first_quarter"]), qindex(ACT["train_last_quarter"])
    qs = [qi for qi in range(q0, q1 + 1) if mode == "quarterly" or qi % 4 == 1]
    units = [(p, qi) for p in sorted(set(lab.osm_id) - set(exclude)) for qi in qs]
    D = features(W, s4, units)
    D["ly"] = D.qi.map(label_year)
    P = D.merge(lab[["osm_id", "year", "growth", "stable"]], left_on=["uid", "ly"], right_on=["osm_id", "year"], how="left")
    P["y"] = np.where(P.growth == True, 1, np.where(P.stable == True, 0, np.nan))
    return P[P.y.notna()].reset_index(drop=True)


def overlapping_plots(share: float | None = None) -> frozenset:
    """training plots that cover `share` or more of the area of any compound (default from the config): the leak of the backtest."""
    ov = pd.read_csv(RAW / "plot_compound_overlap.csv")
    return frozenset(set(ov[ov.share_of_compound >= (ACT["overlap_exclude"] if share is None else share)].osm_id) & set(labels().osm_id))


def gbm() -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=150, min_samples_leaf=20, class_weight="balanced", random_state=SEED)


def metrics(y: np.ndarray, pred: np.ndarray) -> tuple[float, float, float]:
    """sensitivity, specificity, balanced accuracy (percent)."""
    se = (pred & (y == 1)).sum() / max((y == 1).sum(), 1)
    sp = (~pred & (y == 0)).sum() / max((y == 0).sum(), 1)
    return round(100 * se, 1), round(100 * sp, 1), round(100 * (se + sp) / 2, 1)


def oof_threshold(tr: pd.DataFrame) -> tuple[float, tuple]:
    X, y = tr[FE].values, tr.y.values.astype(int)
    oof = np.zeros(len(tr))
    for a, b in GroupKFold(5).split(X, y, tr.uid.values):
        oof[b] = gbm().fit(X[a], y[a]).predict_proba(X[b])[:, 1]
    grid = np.unique(np.quantile(oof, np.linspace(0.02, 0.98, 97)))
    ba = [metrics(y, oof > t)[2] for t in grid]
    t = float(grid[int(np.argmax(ba))])
    return t, metrics(y, oof > t)


def predict(model, t: float, W: pd.DataFrame, s4: pd.DataFrame, units: list[tuple[str, int]], mode: str) -> pd.DataFrame:
    """A and the active flag for (unit, quarter) pairs; in q2hold mode the value of the latest Q2-ending window. K1 is the one of the quarter itself."""
    need = sorted({(u, held_qi(q, mode)) for u, q in units})
    F = features(W, s4, need)
    ok = F[FE].notna().all(axis=1)
    F["activity_prob"] = np.nan
    F.loc[ok, "activity_prob"] = model.predict_proba(F.loc[ok, FE].values)[:, 1]
    F = F.rename(columns={"qi": "hq"})[["uid", "hq", "activity_prob"]]
    out = pd.DataFrame(units, columns=["uid", "qi"])
    out["hq"] = out.qi.map(lambda q: held_qi(q, mode))
    out = out.merge(F, on=["uid", "hq"], how="left")
    K1 = rolling_delta(W)
    out["K1"] = [K1.at[q, u] if u in K1 else np.nan for u, q in zip(out.uid, out.qi)]
    out["active"] = pd.array(np.where(out.activity_prob.notna(), out.activity_prob > t, pd.NA), dtype="boolean")
    return out.drop(columns="hq")


def stable_plots() -> list[str]:
    """OBT-stable plots as in s5_verify T3: smallest presence fraction in 2022-2023 >= 0.15, no change above 0.005, no growth label."""
    lab = pd.read_csv(RAW / "plot_labels.csv")
    lab = lab[(lab.area_ha >= 2) & lab.year.isin([2022, 2023])]
    st = lab.groupby("osm_id").agg(pres=("presence_fraction", "min"), dmax=("d_presence_fraction", lambda x: x.abs().max()),
                                   grow=("growth", lambda x: bool(x.fillna(False).any())))
    return sorted(st[(st.pres >= 0.15) & (st.dmax < 0.005) & ~st.grow].index)


def share_by_season(E: pd.DataFrame, flag: str) -> dict:
    """percent of windows flagged active, by quarter of the year, and the spread (highest minus lowest)."""
    sh = (E.groupby(E.qi % 4 + 1)[flag].mean() * 100).round(1)
    return {"by_quarter": {f"Q{q}": float(v) for q, v in sh.items()}, "spread_pp": round(float(sh.max() - sh.min()), 1)}


def replay_validation(L: pd.DataFrame, model, t: float, s4: pd.DataFrame, mode: str) -> dict:
    """the tests of the audit on windows of every quarter, plus the seasonality test (FIXES_PROTOCOL section 1).
    T1 (time + plot holdout), T2 (time holdout), T3 (false alarms on stable plots), seasonal spread (active share by quarter of the year on the same stable plots).
    `model`, `t` are the fitted model on all rows. in q2hold mode T3 and the spread use the held A."""
    split = pd.read_csv(RAW / "plot_split.csv").set_index("plot").split
    h = ACT["holdout_label_year"]
    last_tr = qindex(f"{h - 1}Q4")
    L = L.assign(split=L.uid.map(split))
    tr_all = L[(L.ly <= h - 1) & (L.qi <= last_tr)]  # windows ending after 2021Q4 are dropped from both sides
    out = {"mode": mode}
    for name, tr, te in [("T1", tr_all[tr_all.split == "train"], L[(L.split == "test") & (L.ly >= h)]), ("T2", tr_all, L[L.ly >= h])]:
        thr, _ = oof_threshold(tr)
        yt = te.y.values.astype(int)
        k1 = metrics(yt, (te.K1 > THR).values)
        a = metrics(yt, gbm().fit(tr[FE].values, tr.y.values.astype(int)).predict_proba(te[FE].values)[:, 1] > thr)
        out[name] = {"n_train": len(tr), "n_test": len(te), "test_plots": int(te.uid.nunique()), "K1_sens_spec_ba": list(k1), "A_sens_spec_ba": list(a),
                     "gain_ba": round(a[2] - k1[2], 1), "pass": bool(a[2] - k1[2] >= ACT["min_gain_ba"])}
    W = wide(pd.read_csv(RAW / "dw_polygons_quarterly.csv"), "osm_id")
    q0, q1 = qindex(ACT["eval_first_quarter"]), qindex(ACT["eval_last_quarter"])
    stable = stable_plots()

    def frame(ids, a, b):
        F = predict(model, t, W, s4, [(p, qi) for p in ids for qi in range(a, b + 1)], mode)
        F = F[F.activity_prob.notna() & F.K1.notna()].copy()
        F["A"], F["K1_flag"] = F.active.astype(bool), F.K1 > THR
        return F

    E = frame(stable, q0, q1)
    ka, kk = E.A.mean() * 100, E.K1_flag.mean() * 100
    out["T3"] = {"n_plots": int(E.uid.nunique()), "n_windows": len(E), "K1_active_pct": round(kk, 1), "A_active_pct": round(ka, 1),
                 "pass": bool(ka <= kk + ACT["max_false_alarm_extra"])}
    sa, sk = share_by_season(E, "A"), share_by_season(E, "K1_flag")
    out["seasonal"] = {"stable_plots_2024_2025": {"A": sa, "K1": sk}, "pass": bool(sa["spread_pp"] <= ACT["max_seasonal_spread"]),
                       "stable_plots_2026": {"A": share_by_season(frame(stable, qindex("2026Q1"), qindex("2026Q3")), "A")},
                       "all_labelled_plots_2024_2025": {"A": share_by_season(frame(sorted(set(labels().osm_id)), q0, q1), "A")}}
    out["all_pass"] = bool(out["T1"]["pass"] and out["T2"]["pass"] and out["T3"]["pass"] and out["seasonal"]["pass"])
    return out


def fit(exclude: frozenset = frozenset(), mode: str = "quarterly") -> tuple[HistGradientBoostingClassifier, float, dict]:
    """production model: all labelled plots. backtest variant: pass `exclude` = plots covering a compound."""
    s4 = load_s4()
    L = training_frame(s4, exclude, mode)
    t, oof = oof_threshold(L)
    model = gbm().fit(L[FE].values, L.y.values.astype(int))
    desc = {"quarterly": f"ending every quarter {ACT['train_first_quarter']}-{ACT['train_last_quarter']}",
            "q2hold": f"ending in Q2 only {ACT['train_first_quarter'][:4]}-{ACT['train_last_quarter'][:4]}, A held for the 4 quarters it covers"}[mode]
    meta = {"mode": mode, "threshold": t, "features": FE, "seed": SEED, "n_train": len(L), "n_plots": int(L.uid.nunique()), "n_growth": int(L.y.sum()),
            "n_excluded_plots": len(exclude), "windows": desc + "; label = OBT label of the plot-year whose 30 June is in the window",
            "oof_sens_spec_ba": list(oof), "k1_ba_same_rows": metrics(L.y.values.astype(int), (L.K1 > THR).values)[2],
            "train_fit_ba": metrics(L.y.values.astype(int), model.predict_proba(L[FE].values)[:, 1] > t)[2],
            "validation": replay_validation(L, model, t, s4, mode),
            "audit_reference_before_corrections": {"T1_gain": 3.0, "T2_gain": 5.1, "windows": "ending 30 June only"}}
    meta["fingerprint"] = float(round(model.predict_proba(L[FE].values)[:, 1].sum(), 6))
    return model, t, meta


def fit_final() -> tuple[HistGradientBoostingClassifier, float, dict]:
    """the quarterly A if it passes T1, T2, T3 and the seasonal spread; otherwise the Q2-hold fallback (the rejected result is kept in the meta)."""
    model, t, meta = fit(mode="quarterly")
    if meta["validation"]["all_pass"]:
        return model, t, meta
    model2, t2, meta2 = fit(mode="q2hold")
    meta2["rejected_quarterly"] = {k: meta[k] for k in ("threshold", "n_train", "n_plots", "n_growth", "oof_sens_spec_ba", "k1_ba_same_rows", "validation", "fingerprint")}
    return model2, t2, meta2


def score(sat_q: pd.DataFrame, model, t: float, last_qi: int = N_Q - 1, mode: str = "quarterly") -> pd.DataFrame:
    """A for every compound quarter from 2019Q1 to last_qi (q2hold: A of the latest Q2-ending window, missing before 2019Q2). uses sat_q rows up to last_qi only."""
    s4 = load_s4()
    W = wide(sat_q[sat_q.qi <= last_qi], "code")
    out = predict(model, t, W, s4, [(c, qi) for c in sorted(W.columns) for qi in range(FIRST_A, last_qi + 1)], mode)
    return apply_source(out.rename(columns={"uid": "code"})[["code", "qi", "K1", "activity_prob", "active"]])


def apply_source(out: pd.DataFrame, source: str | None = None) -> pd.DataFrame:
    """spec section 13 fallback: with `activity.source: k1` the active flag is K1 > k1_active and A is left empty (a narrower claim:
    Dynamic World change only). the default `model` keeps A. the switch is a recorded decision, never chosen after seeing a result."""
    source = source or ACT.get("source", "model")
    if source == "model":
        return out
    if source != "k1":
        raise ValueError(f"activity.source must be 'model' or 'k1', not {source!r}")
    out = out.copy()
    out["activity_prob"] = np.nan
    out["active"] = pd.array(np.where(out.K1.notna(), out.K1 > THR, pd.NA), dtype="boolean")
    return out


def save(model, meta: dict, suffix: str = "") -> None:
    MODEL.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL / f"activity_gbm{suffix}.joblib")
    (MODEL / f"activity_meta{suffix}.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")


def load(suffix: str = "") -> tuple[HistGradientBoostingClassifier, float, dict]:
    meta = json.loads((MODEL / f"activity_meta{suffix}.json").read_text(encoding="utf-8"))
    return joblib.load(MODEL / f"activity_gbm{suffix}.joblib"), meta["threshold"], meta
