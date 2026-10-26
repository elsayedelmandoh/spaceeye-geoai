"""
propose: extras (calibration, feature importance, per-quarter lists, lead-time chart) and the EW_REPORT.md writer.
input: the state and results from early_warning.prepare() / evaluate_all().
output: app_data/ew/*.csv, *.png and app_data/EW_REPORT.md.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.inspection import permutation_importance  # noqa: E402

from src.analysis import ew_eval as E  # noqa: E402
from src.analysis import ew_features as F  # noqa: E402
from src.pipeline.common import APP  # noqa: E402

OUT = APP / "ew"
INK, MUTED = "#1f2933", "#6b7280"
COL = {"sat": "#9ca3af", "rule": "#1f5fbf", "b": "#2a9d8f", "lr": "#d9822b", "gb": "#8a4fbf"}
NAMES_EN = {"sat": "(1) satellite-only rule", "rule": "(2) simple rule (R1 + B)", "b": "(2b) B triggers only", "lr": "(3) logistic", "gb": "(4) boosting"}
NAMES = {"sat": "(1) القمر وحده", "rule": "(2) القاعدة البسيطة", "b": "(2b) B وحدها", "lr": "(3) لوجستي", "gb": "(4) GB"}


def pct(x, nd=0):
    return "-" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{100 * x:.{nd}f}%"


def num(x, nd=1):
    return "-" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


def decide(res_time: pd.DataFrame, res_ext: pd.DataFrame) -> dict:
    """protocol section 7: a model is adopted only if it beats the rule on recall@N and median lead in BOTH views; ties go to the rule."""
    out = {}
    for m in ("lr", "gb"):
        wins = {}
        for tag, tab in (("time", res_time), ("ext", res_ext)):
            r, x = tab.set_index("key").loc["rule"], tab.set_index("key").loc[m]
            lead_r = -np.inf if np.isnan(r["lead_median"]) else r["lead_median"]
            lead_m = -np.inf if np.isnan(x["lead_median"]) else x["lead_median"]
            wins[tag] = {"recall": bool(x["recall"] > r["recall"]), "lead": bool(lead_m > lead_r)}
        out[m] = {"wins": wins, "adopt": all(v for w in wins.values() for v in w.values())}
    out["product"] = next((m for m in ("gb", "lr") if out[m]["adopt"]), "rule")
    return out


def reasons(row: pd.Series) -> str:
    parts = []
    lvl = row["rule_level"]
    parts.append("لسه ما بدأش" if row["started"] != 1 and row["level"] == 5 else f"مستوى {int(lvl)}")
    if row["K2"] >= 1:
        parts.append(f"{int(row['K2'])} ربع بدون نشاط")
    if row["K3"] > 0:
        parts.append(f"{int(row['K3'])} شهر بعد الميعاد")
    if row["t_B1"]:
        parts.append(f"غطاء {row['cover_ratio']:.2f}× من المطلوب")
    if row["t_B2"]:
        parts.append(f"أقساط أرض متأخرة {int(row['land_late'])}")
    if row["t_B3"]:
        parts.append("شكاوى في أسوأ 5% من تاريخه")
    if row["t_B5"]:
        parts.append(f"فجوة المخطط والمعلن {row['gap']:.0f} نقطة")
    if row["ntrig"] == 0 and row["K2"] < 1 and row["K3"] <= 0:
        parts.append("من غير محفز (تكملة القائمة)")
    return "، ".join(parts)


def topn_lists(d: pd.DataFrame, score: str, n: int, show_p: str | None = None) -> pd.DataFrame:
    flag = E.topn_flag(d, score, n)
    t = d[flag].copy()
    t["rank"] = t.assign(_s=-t[score]).sort_values(["quarter", "_s", "code"]).groupby("quarter").cumcount().reindex(t.index) + 1
    t["reason"] = t.apply(reasons, axis=1)
    if show_p:
        t["reason"] = t["reason"] + t[show_p].map(lambda p: f" (احتمال {p:.2f})")
    t["hit"] = np.where(t["censored"], "؟", np.where(t["label"], "✓", ""))
    return t.sort_values(["quarter", "rank"])[["quarter", "rank", "code", "reason", "hit"]]


def importances(d: pd.DataFrame) -> dict:
    tr = d[E.train_mask(d)]
    te = d[d["quarter"].isin(E.TEST_LABEL_Q) & ~d["censored"]]
    _, (imp, sc, lr) = E.fit_predict("lr", F.FEATURES, tr, te)
    coef = pd.Series(lr.coef_[0], index=F.FEATURES).sort_values(key=abs, ascending=False)
    _, gb = E.fit_predict("gb", F.FEATURES, tr, te)
    pi = permutation_importance(gb, te[F.FEATURES].astype(float), te["label"].astype(int), scoring="average_precision",
                                n_repeats=20, random_state=E.SEED)
    gbi = pd.Series(pi.importances_mean, index=F.FEATURES).sort_values(ascending=False)
    return {"lr": coef, "gb": gbi}


def calibration(d: pd.DataFrame, kind: str):
    te = d[d["quarter"].isin(E.TEST_LABEL_Q) & ~d["censored"]]
    ext = d[~d["censored"] & d[f"p_{kind}_both_cv"].notna()]
    rt = E.reliability(te["label"].to_numpy(), te[f"p_{kind}_both_time"].to_numpy(), 4)
    rx = E.reliability(ext["label"].to_numpy(), ext[f"p_{kind}_both_cv"].to_numpy(), 5)
    brier = lambda y, p: float(np.mean((p - y.astype(float)) ** 2))  # noqa: E731
    return rt, rx, brier(te["label"].to_numpy(), te[f"p_{kind}_both_time"].to_numpy()), brier(ext["label"].to_numpy(), ext[f"p_{kind}_both_cv"].to_numpy())


def plot_calibration(d: pd.DataFrame):
    fig, axes = plt.subplots(2, 2, figsize=(8, 7), sharex=True, sharey=True)
    stats = {}
    for i, kind in enumerate(("lr", "gb")):
        rt, rx, bt, bx = calibration(d, kind)
        stats[kind] = (bt, bx)
        for j, (r, ttl) in enumerate(((rt, "time test (4 bins)"), (rx, "developer folds, all cut-offs (5 bins)"))):
            ax = axes[i, j]
            ax.plot([0, 1], [0, 1], color=MUTED, lw=1, ls="--")
            ax.plot(r["p"], r["obs"], "o-", color=COL[kind], lw=2)
            for _, row in r.iterrows():
                ax.annotate(f"n={int(row['n'])}", (row["p"], row["obs"]), textcoords="offset points", xytext=(4, -10), fontsize=7, color=MUTED)
            ax.set_title(f"{kind.upper()} - {ttl}", fontsize=9, color=INK)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.grid(alpha=0.2)
            if i == 1:
                ax.set_xlabel("predicted probability", fontsize=8)
            if j == 0:
                ax.set_ylabel("observed rate", fontsize=8)
    fig.suptitle("Calibration (generated data)", fontsize=10, color=INK)
    fig.tight_layout()
    fig.savefig(OUT / "calibration.png", dpi=130)
    plt.close(fig)
    return stats


def event_leads(st: dict, methods: dict) -> pd.DataFrame:
    """lead time per onset event and method on all 11 cut-offs (models: developer-fold predictions)."""
    d = st["table"]
    rows = []
    for key in ("sat", "rule", "b", "lr", "gb"):
        score = methods[key][1].format(view="cv")
        flag = E.topn_flag(d, score, E.N_DEFAULT)
        ev = E.event_table(d, flag, st["ev_all"], F.CUTOFF_QUARTERS)
        ev["method"] = key
        rows.append(ev)
    return pd.concat(rows, ignore_index=True)


def plot_leads(ev: pd.DataFrame):
    events = ev[ev["method"] == "rule"][["code", "onset"]].reset_index(drop=True)
    labels = [f"{r.code}\n{r.onset}" + ("\n(test)" if pd.Period(r.onset, "M") >= E.TEST_ONSET_FROM else "") for r in events.itertuples()]
    keys = ["sat", "rule", "b", "lr", "gb"]
    w = 0.16
    fig, ax = plt.subplots(figsize=(10, 4.6))
    for k, key in enumerate(keys):
        e = ev[ev["method"] == key].reset_index(drop=True)
        x = np.arange(len(e)) + (k - 2) * w
        lead = e["lead"].fillna(0).to_numpy()
        ax.bar(x, lead, w, color=COL[key], label=NAMES_EN[key])
        for xi, c in zip(x, e["caught"]):
            if not c:
                ax.text(xi, 0.2, "x", ha="center", fontsize=9, color="#b91c1c")
    ax.set_xticks(np.arange(len(events)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("lead time (months before onset)")
    ax.set_ylim(0, 13)
    ax.axhline(6, color=MUTED, lw=0.8, ls=":")
    ax.text(-0.45, 6.2, "label horizon = 6 months", fontsize=7, color=MUTED, ha="left")
    ax.set_title("Lead time per distress onset, top-8 list (x = missed). Models: developer-fold predictions", fontsize=10, color=INK)
    ax.legend(fontsize=8, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.18), frameon=False)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUT / "lead_time.png", dpi=130)
    plt.close(fig)


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def comparison_table(res: pd.DataFrame, keys: list[str], rnd: dict | None = None) -> str:
    t = res.set_index("key")
    rows = []
    for k in keys:
        r = t.loc[k]
        rows.append({
            "الطريقة": r["method"],
            "Recall@N (صفوف)": f"{pct(r['recall'])} ({int(r['tp'])}/{int(r['positives'])})",
            "Precision@N": pct(r["precision"]),
            "Recall على الـonset الجديد": pct(r["recall_new"]) + f" (من {int(r['new_positives'])})",
            "Recall الأحداث": f"{int(r['events_caught'])}/{int(r['events'])}",
            "Lead (ميديان، شهور)": num(r["lead_median"]),
            "False-alarm: قصص سليمة": pct(r["fa_healthy"]),
            "False-alarm: ما اتعثرتش أبدًا": pct(r["fa_never"]),
        })
    if rnd:
        rows.append({"الطريقة": "top-N عشوائي (متوسط، 95%)", "Recall@N (صفوف)": f"{pct(rnd['recall'][0])} ({pct(rnd['recall'][1])}-{pct(rnd['recall'][2])})",
                     "Precision@N": pct(rnd["precision"][0]), "Recall على الـonset الجديد": "-", "Recall الأحداث": "-", "Lead (ميديان، شهور)": "-",
                     "False-alarm: قصص سليمة": "-", "False-alarm: ما اتعثرتش أبدًا": "-"})
    return md_table(pd.DataFrame(rows))


def alert_table(res: pd.DataFrame, keys: list[str]) -> str:
    t = res.set_index("key")
    rows = [{"الطريقة": t.loc[k, "method"], "Recall (تنبيه)": pct(t.loc[k, "alert_recall"]), "False-alarm سليمة": pct(t.loc[k, "alert_fa_healthy"]),
             "False-alarm ما اتعثرتش": pct(t.loc[k, "alert_fa_never"]), "تنبيهات/ربع": num(t.loc[k, "alert_alerts_per_q"]),
             "Recall الأحداث": pct(t.loc[k, "alert_event_recall"]), "Lead": num(t.loc[k, "alert_lead_median"])} for k in keys]
    return md_table(pd.DataFrame(rows))
