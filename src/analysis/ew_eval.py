"""
propose: the four early-warning methods, the split, and the metrics from EW_PROTOCOL.md (sections 4-6).
input: the feature table from ew_features.build_table().
output: score / alert columns per method, metric dicts. no file output here (see early_warning.py).
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src.analysis.ew_features import FEATURES, INTERNAL_ALL, SAT_ALL

SEED = 2026
SPLIT_SEED = 20261026
N_DEFAULT = 8
TRAIN_LAST = "2024Q4"
TEST_LABEL_Q = ["2025Q2", "2025Q3", "2025Q4", "2026Q1"]
TEST_ALL_Q = TEST_LABEL_Q + ["2026Q2"]
TEST_ONSET_FROM = pd.Period("2025-07", "M")
LOG_COLS = ["land_late", "cmp_rate90", "kwh_per_meter", "meters", "report_age"]
GB_PARAMS = dict(max_depth=2, max_iter=60, learning_rate=0.05, min_samples_leaf=6, l2_regularization=1.0,
                 class_weight="balanced", random_state=SEED)

# ---------------------------------------------------------------- rules


def add_rule_columns(df: pd.DataFrame) -> pd.DataFrame:
    """B triggers (project-plan section 3), the rule level and the score of every rule variant (higher = more urgent)."""
    d = df.copy()
    k2 = d["K2"].fillna(0)
    k3 = d["K3"].fillna(0)
    d["t_B1"] = (d["cover_req0"] == 0) & (d["cover_ratio"] < 1)
    d["t_B2"] = d["land_late"] >= 2
    d["t_B3"] = (d["cmp_pctl"] >= 0.95) & (d["cmp_hist_n"] >= 12)
    d["t_B5"] = d["gap"] > 20
    tcols = ["t_B1", "t_B2", "t_B3", "t_B5"]
    d["ntrig"] = d[tcols].sum(axis=1)
    lvl = d["level"].astype(float)
    rule_level = lvl.copy()
    rule_level[(d["ntrig"] > 0)] = np.minimum(rule_level[(d["ntrig"] > 0)], 2)
    rule_level[d["t_B1"] & (k2 >= 2)] = 1
    d["rule_level"] = rule_level
    # K2-only level
    k2lvl = np.select([d["started"] != 1, k2 >= 4, k2 >= 2, k2 >= 1], [5, 1, 2, 3], default=4).astype(float)
    d["k2_level"] = k2lvl
    d["score_rule"] = -d["rule_level"] * 1e6 + d["ntrig"] * 1e5 + k2 * 1e3 + k3
    d["score_sat"] = -lvl * 1e6 + k2 * 1e3 + k3
    d["score_k2"] = -d["k2_level"] * 1e6 + k2 * 1e3 + k3
    d["score_b"] = d["ntrig"].astype(float)
    d["alert_rule"] = d["rule_level"] <= 2
    d["alert_sat"] = lvl <= 2
    d["alert_k2"] = d["k2_level"] <= 2
    d["alert_b"] = d["ntrig"] >= 1
    return d


# ---------------------------------------------------------------- models


def _matrix(df: pd.DataFrame, feats: list[str]) -> pd.DataFrame:
    x = df[feats].astype(float).copy()
    for c in LOG_COLS:
        if c in x:
            x[c] = np.log1p(x[c].clip(lower=0))
    return x


def fit_predict(kind: str, feats: list[str], train: pd.DataFrame, pred: pd.DataFrame):
    """returns (probabilities for pred, fitted artefacts)."""
    y = train["label"].astype(int).to_numpy()
    if kind == "lr":
        imp = SimpleImputer(strategy="median", keep_empty_features=True).fit(_matrix(train, feats))
        sc = StandardScaler().fit(imp.transform(_matrix(train, feats)))
        model = LogisticRegression(C=0.3, class_weight="balanced", max_iter=2000).fit(sc.transform(imp.transform(_matrix(train, feats))), y)
        p = model.predict_proba(sc.transform(imp.transform(_matrix(pred, feats))))[:, 1]
        return p, (imp, sc, model)
    model = HistGradientBoostingClassifier(**GB_PARAMS).fit(train[feats].astype(float), y)
    return model.predict_proba(pred[feats].astype(float))[:, 1], model


FEATSETS = {"both": FEATURES, "sat": SAT_ALL, "internal": INTERNAL_ALL}


# ---------------------------------------------------------------- split


def holdout_developers(tab: pd.DataFrame, share: float = 0.2, seed: int = SPLIT_SEED):
    """20% of developers; the seed moves up by one until a held-out developer owns a compound with a positive test-window row."""
    devs = sorted(tab["developer"].unique())
    k = round(share * len(devs))
    pos_devs = set(tab.loc[tab["quarter"].isin(TEST_LABEL_Q) & tab["label"] & ~tab["censored"], "developer"])
    s = seed
    while True:
        held = sorted(np.random.default_rng(s).permutation(devs)[:k])
        if pos_devs & set(held):
            return held, s
        s += 1


def cv_folds(tab: pd.DataFrame, n_folds: int = 5, seed: int = SPLIT_SEED) -> dict:
    devs = sorted(tab["developer"].unique())
    perm = np.random.default_rng(seed).permutation(devs)
    return {d: i % n_folds for i, d in enumerate(perm)}


def train_mask(tab: pd.DataFrame) -> pd.Series:
    return (tab["quarter"] <= TRAIN_LAST) & ~tab["censored"]


def add_models(tab: pd.DataFrame, held: list[str]) -> pd.DataFrame:
    """adds p_<kind>_<featset>_<view> columns. views: time (all developers, time split), dev (trained without held-out developers),
    cv (developer folds, all cut-offs)."""
    d = tab.copy()
    tr = d[train_mask(d)]
    tr_dev = tr[~tr["developer"].isin(held)]
    fold = d["developer"].map(cv_folds(d))
    cv_ok = ~d["censored"]
    for kind in ("lr", "gb"):
        for fs, feats in FEATSETS.items():
            d[f"p_{kind}_{fs}_time"], _ = fit_predict(kind, feats, tr, d)
            d[f"p_{kind}_{fs}_dev"], _ = fit_predict(kind, feats, tr_dev, d)
            oof = pd.Series(np.nan, index=d.index)
            for f in sorted(fold.unique()):
                te = fold == f
                p, _ = fit_predict(kind, feats, d[cv_ok & ~te], d[te])
                oof[te] = p
            d[f"p_{kind}_{fs}_cv"] = oof
    return d


# ---------------------------------------------------------------- metrics


def topn_flag(df: pd.DataFrame, score: str, n: int) -> pd.Series:
    """top-n per quarter by score (ties broken by code, as in the protocol)."""
    d = df[["quarter", "code", score]].copy()
    d["_neg"] = -d[score]
    d = d.sort_values(["quarter", "_neg", "code"])
    d["_rank"] = d.groupby("quarter").cumcount() + 1
    return (d["_rank"] <= n).reindex(df.index)


def event_table(df: pd.DataFrame, flag: pd.Series, events: pd.DataFrame, quarters: list[str]) -> pd.DataFrame:
    """per onset event: caught (flagged at a cut-off 1-6 months before onset) and lead (earliest flagged cut-off within 12 months)."""
    out = []
    f = df.assign(_flag=flag.to_numpy())
    f = f[f["quarter"].isin(quarters)]
    for _, e in events.iterrows():
        g = f[(f["code"] == e["code"]) & f["_flag"]]
        gaps = [(e["onset"] - m).n for m in g["month"]]
        near = [x for x in gaps if 1 <= x <= 6]
        lead = max([x for x in gaps if 1 <= x <= 12]) if near else np.nan
        out.append({"code": e["code"], "onset": str(e["onset"]), "caught": bool(near), "lead": lead})
    return pd.DataFrame(out)


def metrics(df: pd.DataFrame, flag: pd.Series, events: pd.DataFrame, label_q: list[str], all_q: list[str], never: set) -> dict:
    """row-level and event-level metrics for one flag column over the given cut-offs."""
    rows = df[df["quarter"].isin(label_q) & ~df["censored"]]
    fl = flag.reindex(rows.index)
    pos = rows["label"]
    tp = int((fl & pos).sum())
    new = pos & ~rows["distress_now"]
    allr = df[df["quarter"].isin(all_q)]
    fa_all = flag.reindex(allr.index)
    healthy = allr["story"] == "healthy"
    nev = allr["code"].isin(never)
    ev = event_table(df, flag, events, all_q)
    return {
        "recall": tp / pos.sum() if pos.sum() else np.nan,
        "precision": tp / fl.sum() if fl.sum() else np.nan,
        "tp": tp, "positives": int(pos.sum()), "flagged": int(fl.sum()),
        "recall_new": int((fl & new).sum()) / new.sum() if new.sum() else np.nan,
        "new_positives": int(new.sum()),
        "fa_healthy": float(fa_all[healthy].mean()) if healthy.any() else np.nan,
        "fa_never": float(fa_all[nev].mean()) if nev.any() else np.nan,
        "events": len(ev), "events_caught": int(ev["caught"].sum()) if len(ev) else 0,
        "event_recall": float(ev["caught"].mean()) if len(ev) else np.nan,
        "lead_median": float(ev["lead"].median()) if len(ev) and ev["lead"].notna().any() else np.nan,
        "alerts_per_q": float(fa_all.sum() / max(len(all_q), 1)),
    }


def random_baseline(df: pd.DataFrame, label_q: list[str], n: int, sims: int = 2000, seed: int = SEED) -> dict:
    """recall and precision of a random top-n list (same quarters, same pool)."""
    rng = np.random.default_rng(seed)
    rows = df[df["quarter"].isin(label_q) & ~df["censored"]]
    rec, prec = [], []
    groups = [g["label"].to_numpy() for _, g in rows.groupby("quarter")]
    for _ in range(sims):
        tp = sum(int(g[rng.permutation(len(g))[: min(n, len(g))]].sum()) for g in groups)
        rec.append(tp / max(sum(g.sum() for g in groups), 1))
        prec.append(tp / sum(min(n, len(g)) for g in groups))
    q = lambda a: (float(np.mean(a)), float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5)))  # noqa: E731
    return {"recall": q(rec), "precision": q(prec)}


def reliability(y: np.ndarray, p: np.ndarray, bins: int) -> pd.DataFrame:
    """equal-count bins: mean predicted vs observed rate."""
    d = pd.DataFrame({"y": y.astype(float), "p": p}).sort_values("p").reset_index(drop=True)
    d["bin"] = np.concatenate([[i] * len(a) for i, a in enumerate(np.array_split(np.arange(len(d)), bins))])
    return d.groupby("bin").agg(p=("p", "mean"), obs=("y", "mean"), n=("y", "size")).reset_index()
