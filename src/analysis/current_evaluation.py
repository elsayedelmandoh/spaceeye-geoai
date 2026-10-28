"""Current-schema, fixed-time evaluation; never modify labels to create missing classes."""

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

CLASSES = ["distressed", "completed", "ongoing"]
OUT = APP / "ml_current"
PROTOCOL = BASE_DIR / "docs/data/EW_PROTOCOL_CURRENT.md"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    fitted = model.predict_proba(frame)
    return pd.DataFrame({name: fitted[:, list(model.classes_).index(name)] if name in model.classes_ else np.nan
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


def run():
    protocol_hash = sha(PROTOCOL)  # Existing frozen protocol must exist before fitting.
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
    if train.y_outcome_6m.nunique() < 2:
        raise ValueError("Fewer than two observed training classes")
    unsupported = sorted(set(CLASSES) - set(train.y_outcome_6m))
    public = [c for c in features if meta["column_origins"][c] == "derived_public_observation"]
    if not public or "K5_egp" in public:
        raise ValueError("Invalid public feature set")
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
            part["probability_scope"] = "conditional on observed training classes" if unsupported else "three classes"
            part["synthetic_label"] = "Synthetic - for training only"
            predictions.append(part)
            scores[method] = p.distressed
            actual, guess = test.y_outcome_6m, pd.Series(pred, index=frame.index).loc[test_mask]
            recalls = recall_score(actual, guess, labels=CLASSES, average=None, zero_division=0)
            for name, recall in zip(CLASSES, recalls):
                support = int(actual.eq(name).sum())
                metrics.append({"method": method, "metric": "class_recall", "class": name, "value": float(recall) if support else None,
                                "numerator": int((actual.eq(name) & guess.eq(name)).sum()), "denominator": support})
            metrics.append({"method": method, "metric": "macro_f1_three_declared_classes", "class": "all",
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
    result = {"scope": "Synthetic - for training only", "protocol_sha256_before_fit": protocol_hash,
              "train_rows": len(train), "test_rows": len(test), "train_classes": train.y_outcome_6m.value_counts().to_dict(),
              "test_classes": test.y_outcome_6m.value_counts().to_dict(), "unsupported_training_classes": unsupported,
              "three_class_acceptance": not unsupported and set(CLASSES).issubset(set(test.y_outcome_6m)),
              "classes": CLASSES, "confusion_matrices": confusions, "random_at_4": random_summary,
              "public_features": public, "combined_features": features,
              "developer_holdout": "Not fitted: completed has no training support before any additional developer exclusion.",
              "input_sha256": {"dataset": sha(path), "metadata": sha(PRIVATE / "ml_dataset_extended_metadata.json"),
                               "protocol": protocol_hash, "source": sha(BASE_DIR / "src/analysis/current_evaluation.py")},
              "limits": ["No completed training example; its probability is null, not zero.", "Per-row synthetic labels are not independent real events.", "Real-case check set is not used for fitting or tuning."]}
    if sha(PROTOCOL) != protocol_hash:
        raise RuntimeError("Protocol changed during fitting")
    pd.concat(predictions, ignore_index=True).to_parquet(OUT / "predictions.parquet", index=False)
    pd.DataFrame(metrics).to_csv(OUT / "metrics.csv", index=False)
    (OUT / "metadata.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    pd.DataFrame({"draw": range(2000), "recall_at_4": random_values}).to_csv(OUT / "random_draws.csv", index=False)
    docs = BASE_DIR / "docs/data"
    (docs / "CURRENT_MODEL_METADATA.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    pd.DataFrame(metrics).to_csv(docs / "CURRENT_MODEL_METRICS.csv", index=False)
    ranking = pd.DataFrame(metrics).query("metric == 'distressed_recall_at_4'")
    lines = ["# Current early-warning evaluation", "", "Synthetic - for training only. See [frozen protocol](EW_PROTOCOL_CURRENT.md).", "",
             f"Training: {len(train)} rows. Time test: {len(test)} rows. Capacity: 4. Unsupported training classes: {', '.join(unsupported) or 'none'}.", "",
             "**Three-class acceptance: " + ("PASS" if result["three_class_acceptance"] else "NOT MET") + ".** Missing-class probabilities remain null; fitted probabilities are conditional on the observed classes.", "",
             "| Method | Distressed cases selected | Recall@4 |", "| --- | --- | --- |"]
    lines += [f"| {r.method} | {r.numerator:g} of {r.denominator:g} | {r.value:.3f} |" for r in ranking.itertuples()]
    lines += ["", f"Random: 2,000 draws, mean {random_summary['mean']:.3f}, 95% interval [{random_summary['low']:.3f}, {random_summary['high']:.3f}].",
              "", "Class support, per-class recall and macro-F1: [metrics](CURRENT_MODEL_METRICS.csv). Exact split, feature sets and confusion counts: [metadata](CURRENT_MODEL_METADATA.json).",
              "", "This updates the schema/capacity experiment; historical N=8 results remain separate. A completed test case can count as a miss even though its training class is absent. Scores do not establish real-world predictive accuracy or fairness."]
    (docs / "EW_REPORT_CURRENT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Current evaluation fitted four diagnostics; train={len(train)}, test={len(test)}, unsupported={unsupported}")
    return result


if __name__ == "__main__":
    run()
