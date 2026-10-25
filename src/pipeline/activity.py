"""
propose: step 3. activity score A = probability that a compound is building (GBM, validated in 28_team_ideas_tests/s5_verify).
features per window ending at a quarter: dynamic world trend (slope8, slope12, K1, persistence) and 12-month changes of
sentinel-2 indices and dynamic world class shares. trained on all 2019-2023 plot-years with the open-buildings labels;
threshold = out-of-fold balanced-accuracy optimum. every feature at quarter q uses data up to q only.
input: raw/dw_polygons_quarterly, plot_labels, plot_split, s4 windows, sat_quarterly (compounds).
output: model/activity_gbm.joblib, model/activity_meta.json, A per compound-quarter.
"""

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold

from src.pipeline.common import CFG, MODEL, N_Q, RAW, qindex

SEED, THR, CAP = CFG["seed"], CFG["k1_active"], CFG["activity_features_cap"]
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
    parts = [pd.read_csv(RAW / n) for n in ("s4_windows_q2.csv", "s4_windows_compounds.csv") if (RAW / n).exists()]
    return pd.concat(parts).drop_duplicates(["pid", "qi"]).set_index(["pid", "qi"]).sort_index()


def training_frame(s4: pd.DataFrame) -> pd.DataFrame:
    """plot-years 2019-2023 with a label: growth = 1, stable = 0, others dropped."""
    lab = pd.read_csv(RAW / "plot_labels.csv")
    lab = lab[(lab.area_ha >= 2) & lab.year.between(2018, 2023)]
    W = wide(pd.read_csv(RAW / "dw_polygons_quarterly.csv"), "osm_id")
    units = [(p, (y - 2016) * 4 + 1) for p in sorted(set(lab.osm_id)) for y in range(2018, 2024)]
    D = features(W, s4, units)
    D["year"] = 2016 + D.qi // 4
    P = D.merge(lab[["osm_id", "year", "growth", "stable"]], left_on=["uid", "year"], right_on=["osm_id", "year"], how="left")
    P["y"] = np.where(P.growth == True, 1, np.where(P.stable == True, 0, np.nan))
    return P[P.y.notna() & P.year.between(2019, 2023)].reset_index(drop=True)


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


def replay_validation(L: pd.DataFrame) -> dict:
    """T1 (time + plot holdout) and T2 (time holdout) of the audit, to confirm this code reproduces the validated gain over K1."""
    split = pd.read_csv(RAW / "plot_split.csv").set_index("plot").split
    L = L.assign(split=L.uid.map(split))
    out = {}
    for name, tr, te in [("T1", L[(L.split == "train") & (L.year <= 2021)], L[(L.split == "test") & (L.year >= 2022)]),
                         ("T2", L[L.year <= 2021], L[L.year >= 2022])]:
        t, _ = oof_threshold(tr)
        yt = te.y.values.astype(int)
        k1 = metrics(yt, (te.K1 > THR).values)
        a = metrics(yt, gbm().fit(tr[FE].values, tr.y.values.astype(int)).predict_proba(te[FE].values)[:, 1] > t)
        out[name] = {"n_train": len(tr), "n_test": len(te), "K1_ba": k1[2], "A_sens_spec_ba": list(a), "gain_ba": round(a[2] - k1[2], 1)}
    return out


def fit() -> tuple[HistGradientBoostingClassifier, float, dict]:
    L = training_frame(load_s4())
    t, oof = oof_threshold(L)
    model = gbm().fit(L[FE].values, L.y.values.astype(int))
    meta = {"threshold": t, "features": FE, "seed": SEED, "n_train": len(L), "n_plots": int(L.uid.nunique()), "n_growth": int(L.y.sum()),
            "oof_sens_spec_ba": list(oof), "k1_ba_same_rows": metrics(L.y.values.astype(int), (L.K1 > THR).values)[2],
            "train_fit_ba": metrics(L.y.values.astype(int), model.predict_proba(L[FE].values)[:, 1] > t)[2],
            "replay": replay_validation(L), "audit_reference": {"T1_gain": 3.0, "T2_gain": 5.1}}
    meta["fingerprint"] = float(round(model.predict_proba(L[FE].values)[:, 1].sum(), 6))
    return model, t, meta


def score(sat_q: pd.DataFrame, model, t: float, last_qi: int = N_Q - 1) -> pd.DataFrame:
    """A for every compound quarter from 2019Q1 to last_qi. uses sat_q rows up to last_qi only."""
    s4 = load_s4()
    sq = sat_q[sat_q.qi <= last_qi]
    W = wide(sq, "code")
    units = [(c, qi) for c in sorted(W.columns) for qi in range(FIRST_A, last_qi + 1)]
    F = features(W, s4, units)
    ok = F[FE].notna().all(axis=1)
    F["activity_prob"] = np.nan
    F.loc[ok, "activity_prob"] = model.predict_proba(F.loc[ok, FE].values)[:, 1]
    F["active"] = pd.array(np.where(ok, F.activity_prob > t, pd.NA), dtype="boolean")
    return F.rename(columns={"uid": "code"})[["code", "qi", "K1", "activity_prob", "active"]]


def save(model, meta: dict) -> None:
    MODEL.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL / "activity_gbm.joblib")
    (MODEL / "activity_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")


def load() -> tuple[HistGradientBoostingClassifier, float, dict]:
    meta = json.loads((MODEL / "activity_meta.json").read_text(encoding="utf-8"))
    return joblib.load(MODEL / "activity_gbm.joblib"), meta["threshold"], meta
