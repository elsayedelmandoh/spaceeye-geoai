"""Current binary distress evaluation under the team lead's revised scope."""

import hashlib
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.pipeline.common import APP, BASE_DIR, CFG, PRIVATE

CLASSES = ["distressed", "not_distressed"]
VARIANT = CFG.get("candidates", {}).get("variant", "v1")  # v1 = frozen results; any other name writes to its own files
STEM = "CURRENT" if VARIANT == "v1" else VARIANT.upper()
OUT = APP / ("ml_current" if VARIANT == "v1" else f"ml_{VARIANT}")
PROTOCOL = BASE_DIR / ("data/EW_PROTOCOL_CURRENT.md" if VARIANT == "v1" else f"data/EW_PROTOCOL_{STEM}.md")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_protocol_hash():
    """hash of the protocol file; a non-v1 variant must match the hash recorded when the protocol was frozen."""
    current = sha(PROTOCOL)
    if VARIANT != "v1":
        recorded = PROTOCOL.with_suffix(".sha256").read_text(encoding="utf-8").split()[0]
        if recorded != current:
            raise ValueError(f"{PROTOCOL.name} changed after its hash was recorded; freeze a new protocol version")
    return current


def masks(frame):
    usable = ~frame.label_censored & ~frame.already_completed_at_cutoff
    return usable & frame.quarter.le("2024Q4"), usable & frame.quarter.between("2025Q2", "2026Q1")


def estimator(kind):
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    if kind == "logistic":
        return make_pipeline(imputer, StandardScaler(), LogisticRegression(C=0.3, class_weight="balanced", max_iter=2000, random_state=2026))
    return make_pipeline(imputer, HistGradientBoostingClassifier(max_depth=2, max_iter=60, learning_rate=0.05,
        min_samples_leaf=6, l2_regularization=1, class_weight="balanced", random_state=2026))


def probabilities(model, frame):
    if set(model.classes_) != set(CLASSES):
        raise ValueError("Binary training must contain both declared distress classes")
    fitted = model.predict_proba(frame)
    return pd.DataFrame({name: fitted[:, list(model.classes_).index(name)]
                         for name in CLASSES}, index=frame.index)


def top_flags(frame, score, capacity=4):
    order = frame.loc[frame.K4.astype(bool)].assign(_score=score).sort_values(["quarter", "_score", "code"], ascending=[True, False, True])
    selected = order.groupby("quarter", sort=False).head(capacity).index
    return pd.Series(frame.index.isin(selected), index=frame.index)


def rule_columns(frame):
    out = frame.copy()
    public = out.level.astype(float).where(out.level.le(4))
    trigger = ((out.cover_req0.eq(0) & out.cover_ratio.lt(1)) | out.land_late.ge(2) | out.cmp_pctl.ge(0.95) | out.gap.gt(20))
    level = public.where(~trigger, public.clip(upper=2))
    level = level.mask(out.cover_req0.eq(0) & out.cover_ratio.lt(1) & out.K2.ge(2) & public.notna(), 1)
    level = level.where(~out.may_be_complete.astype(bool), level.clip(lower=3)).where(out.K4.astype(bool))
    out["current_rule_level"] = level
    # Lexicographic priority rule; feature ranges are bounded by the dataset contract.
    out["score_public"] = -public.fillna(5) * 1e9 + out.K2.fillna(0) * 1e5 + out.K3.fillna(0) * 10
    out["score_combined_rule"] = -level.fillna(5) * 1e9 + out.K2.fillna(0) * 1e5 + out.K3.fillna(0) * 10
    return out


def random_recalls(test, draws=2000):
    rng = np.random.default_rng(2026)
    positive = test.y_outcome_6m.eq("distressed")
    denominator = int(positive.sum())
    if not denominator:
        return np.full(draws, np.nan)
    groups = [g.index.to_numpy() for _, g in test.loc[test.K4.astype(bool)].groupby("quarter", sort=True)]
    values = []
    for _ in range(draws):
        chosen = np.concatenate([rng.choice(g, size=min(4, len(g)), replace=False) for g in groups])
        values.append(int(positive.loc[chosen].sum()) / denominator)
    return np.array(values)


def developer_diagnostic(frame, train_mask, test_mask, public, features, metrics):
    """Fixed-seed, chronological holdout; never select developers by their labels."""
    available = sorted(frame.loc[test_mask, "developer_code"].unique())
    if len(available) < 3:
        return {"status": "SKIPPED", "reason": "Fewer than three test developers"}
    held = sorted(np.random.default_rng(2026).choice(available, size=3, replace=False).tolist())
    train = frame.loc[train_mask & ~frame.developer_code.isin(held)]
    test = frame.loc[test_mask & frame.developer_code.isin(held)]
    result = {"held_developers": held, "seed": 2026, "train_rows": len(train), "test_rows": len(test)}
    if test.developer_code.nunique() < 3 or set(train.y_outcome_6m) != set(CLASSES):
        return {**result, "status": "SKIPPED", "reason": "Fixed holdout lacks three test developers or both training classes; no outcome-driven reselection"}
    predictions = []
    for kind in ("logistic", "boosting"):
        for group, columns in (("satellite", public), ("combined", features)):
            method = f"{kind}_{group}"
            model = estimator(kind).fit(train[columns].astype(float), train.y_outcome_6m)
            p = probabilities(model, test[columns].astype(float))
            guess = pd.Series(model.predict(test[columns].astype(float)), index=test.index)
            for name in CLASSES:
                actual = test.y_outcome_6m.eq(name)
                hits, total = int((actual & guess.eq(name)).sum()), int(actual.sum())
                metrics.append({"view": "developer_holdout", "method": method, "metric": "class_recall", "class": name,
                                "value": hits / total if total else None, "numerator": hits, "denominator": total})
            metrics.append({"view": "developer_holdout", "method": method, "metric": "macro_f1_binary", "class": "all",
                            "value": float(f1_score(test.y_outcome_6m, guess, labels=CLASSES, average="macro", zero_division=0)), "numerator": None, "denominator": len(test)})
            part = test[["code", "quarter"]].copy()
            part["method"], part["view"] = method, "developer_holdout"
            part["p_distressed"], part["p_not_distressed"] = p.distressed, p.not_distressed
            part["synthetic_label"] = "Synthetic - for training only"
            predictions.append(part)
            joblib.dump(model, OUT / "models" / f"{method}_developer.joblib")
    pd.concat(predictions, ignore_index=True).to_parquet(OUT / "developer_holdout_predictions.parquet", index=False)
    status = "FITTED" if test.y_outcome_6m.eq("distressed").any() else "FITTED_UNINFORMATIVE"  # no distressed test row: recall is undefined
    return {**result, "status": status, "train_classes": train.y_outcome_6m.value_counts().to_dict(), "test_classes": test.y_outcome_6m.value_counts().to_dict()}


def without_height(columns: list[str]) -> list[str]:
    """candidate ablation: drop the stale static height feature (off by default, see configs/data.yaml candidates)."""
    return [c for c in columns if c != "height_mean_m"]


def run():
    protocol_hash = checked_protocol_hash()  # Existing frozen protocol must exist before fitting.
    path = PRIVATE / "ml_dataset_extended.parquet"
    frame = pd.read_parquet(path)
    meta = json.loads((PRIVATE / "ml_dataset_extended_metadata.json").read_text(encoding="utf-8"))
    features = meta["features"]
    forbidden = set(meta["keys"] + meta["targets"] + ["label_censored", "already_completed_at_cutoff"])
    if forbidden.intersection(features) or len(features) != 40 or frame.duplicated(["code", "quarter"]).any():
        raise ValueError("Invalid features or duplicate keys")
    if sha(path) != meta["dataset_sha256"]:
        raise ValueError("Training table does not match its metadata")
    train_mask, test_mask = masks(frame)
    train, test = frame.loc[train_mask], frame.loc[test_mask]
    if set(train.y_outcome_6m) != set(CLASSES) or set(test.y_outcome_6m) != set(CLASSES):
        raise ValueError("Both binary classes are required in primary train and test")
    known = frame.loc[~frame.label_censored]
    if not known.y_outcome_6m.eq(np.where(known.label_distress_next_6m.astype(bool), "distressed", "not_distressed")).all():
        raise ValueError("Categorical and boolean distress targets disagree")
    public = [c for c in features if meta["column_origins"][c] == "derived_public_observation"]
    if not public or "K5_egp" in public:
        raise ValueError("Invalid public feature set")
    if CFG.get("candidates", {}).get("no_height_ablation", False):
        features, public = without_height(features), without_height(public)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "models").mkdir(exist_ok=True)
    predictions, metrics, confusions = [], [], {}
    ruled = rule_columns(frame)
    scores = {"public_rule": ruled.score_public, "combined_rule": ruled.score_combined_rule}
    for kind in ("logistic", "boosting"):
        for group, columns in (("satellite", public), ("combined", features)):
            method = f"{kind}_{group}"
            model = estimator(kind).fit(train[columns].astype(float), train.y_outcome_6m)
            p = probabilities(model, frame[columns].astype(float))
            pred = model.predict(frame[columns].astype(float))
            part = frame[["code", "quarter", "label_censored", "already_completed_at_cutoff"]].copy()
            part["method"] = method
            part["split"] = np.select([train_mask, test_mask, frame.quarter.eq("2025Q1")], ["train", "time_test", "embargo"], default="not_evaluated")
            part["predicted_class"] = pred
            for name in CLASSES:
                part["p_" + name] = p[name]
            part["probability_scope"] = "binary future distress"
            part["synthetic_label"] = "Synthetic - for training only"
            predictions.append(part)
            scores[method] = p.distressed
            actual, guess = test.y_outcome_6m, pd.Series(pred, index=frame.index).loc[test_mask]
            recalls = recall_score(actual, guess, labels=CLASSES, average=None, zero_division=0)
            for name, recall in zip(CLASSES, recalls):
                support = int(actual.eq(name).sum())
                metrics.append({"method": method, "metric": "class_recall", "class": name, "value": float(recall) if support else None,
                                "numerator": int((actual.eq(name) & guess.eq(name)).sum()), "denominator": support})
            metrics.append({"method": method, "metric": "macro_f1_binary", "class": "all",
                            "value": float(f1_score(actual, guess, labels=CLASSES, average="macro", zero_division=0)), "numerator": None, "denominator": len(test)})
            confusions[method] = confusion_matrix(actual, guess, labels=CLASSES).tolist()
            joblib.dump(model, OUT / "models" / f"{method}.joblib")
    positive = test.y_outcome_6m.eq("distressed")
    for method, score in scores.items():
        chosen = top_flags(test, score.loc[test.index], CFG["cycle_capacity"])
        hits, total = int((chosen & positive).sum()), int(positive.sum())
        metrics.append({"method": method, "metric": "distressed_recall_at_4", "class": "distressed",
                        "value": hits / total if total else None, "numerator": hits, "denominator": total})
    random_values = random_recalls(test)
    random_summary = {"draws": 2000, "mean": float(np.nanmean(random_values)), "low": float(np.nanquantile(random_values, .025)), "high": float(np.nanquantile(random_values, .975))}
    for metric in metrics:
        metric["view"] = "time_test"
    developer_holdout = developer_diagnostic(frame, train_mask, test_mask, public, features, metrics)
    result = {"scope": "Synthetic - for training only", "protocol_sha256_before_fit": protocol_hash,
              "train_rows": len(train), "test_rows": len(test), "train_classes": train.y_outcome_6m.value_counts().to_dict(),
              "test_classes": test.y_outcome_6m.value_counts().to_dict(), "target": "distressed / not_distressed in next six months",
              "binary_implementation_acceptance": True,
              "classes": CLASSES, "confusion_matrices": confusions, "random_at_4": random_summary,
              "public_features": public, "combined_features": features,
              "developer_holdout": developer_holdout,
              "input_sha256": {"dataset": sha(path), "metadata": sha(PRIVATE / "ml_dataset_extended_metadata.json"),
                               "protocol": protocol_hash, "source": sha(BASE_DIR / "src/analysis/current_evaluation.py")},
              "limits": ["Completion prediction removed by the team lead; handover observations remain context.", "Per-row synthetic labels are not independent real events.", "Real-case check set is not used for fitting or tuning."]}
    if sha(PROTOCOL) != protocol_hash:
        raise RuntimeError("Protocol changed during fitting")
    combined = pd.concat(predictions, ignore_index=True)
    probabilities_sum = combined[["p_distressed", "p_not_distressed"]].sum(axis=1)
    binary = combined[["p_distressed", "p_not_distressed"]]
    if not np.allclose(probabilities_sum, 1) or not binary.notna().all().all() or not ((binary >= 0) & (binary <= 1)).all().all():
        raise RuntimeError("Invalid binary probabilities")
    combined.to_parquet(OUT / "predictions.parquet", index=False)
    pd.DataFrame(metrics).to_csv(OUT / "metrics.csv", index=False)
    (OUT / "metadata.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    pd.DataFrame({"draw": range(2000), "recall_at_4": random_values}).to_csv(OUT / "random_draws.csv", index=False)
    docs = BASE_DIR / "data"
    (docs / f"{STEM}_MODEL_METADATA.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    pd.DataFrame(metrics).to_csv(docs / f"{STEM}_MODEL_METRICS.csv", index=False)
    ranking = pd.DataFrame(metrics).query("metric == 'distressed_recall_at_4' and view == 'time_test'")
    lines = ["# Current early-warning evaluation", "", f"Synthetic - for training only. See [frozen protocol]({PROTOCOL.name}).", "",
             f"Training: {len(train)} rows. Time test: {len(test)} rows. Capacity: 4. Target: distressed / not_distressed.", "",
             "**Binary implementation acceptance: PASS** (implementation checks only: both classes are represented and the two probabilities sum to one; it says nothing about predictive power). Completion prediction is outside the approved scope.", "",
             f"Statistical power is very low: the time test holds {int(test.y_outcome_6m.eq('distressed').sum())} distressed rows, and rows of a compound that is already distressed count as well (persistence, not only new onsets).", "",
             "| Method | Distressed cases selected | Recall@4 |", "| --- | --- | --- |"]
    lines += [f"| {r.method} | {r.numerator:g} of {r.denominator:g} | {r.value:.3f} |" for r in ranking.itertuples()]
    lines += ["", f"Random: 2,000 draws, mean {random_summary['mean']:.3f}, 95% interval [{random_summary['low']:.3f}, {random_summary['high']:.3f}].",
              "", f"Class support, per-class recall and macro-F1: [metrics]({STEM}_MODEL_METRICS.csv). Exact split, feature sets and confusion counts: [metadata]({STEM}_MODEL_METADATA.json).",
              "", f"Secondary developer holdout: {developer_holdout['status']}" + (" (its test rows hold no distressed case, so recall is undefined and the view is uninformative)" if developer_holdout["status"] == "FITTED_UNINFORMATIVE" else "") + "; see metadata and the metrics view column.",
              "", "This is the current binary scope; historical N=8 and v4 three-class-scope results remain separate. Scores do not establish real-world predictive accuracy or fairness."]
    (docs / f"EW_REPORT_{STEM}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Binary evaluation PASS; train={len(train)}, test={len(test)}, developer_holdout={developer_holdout['status']}")
    return result


if __name__ == "__main__":
    run()
