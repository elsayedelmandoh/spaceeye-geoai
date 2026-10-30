# ruff: noqa  -- archived experiment script, kept as run
"""Step 3 (PROTOCOL.md, Amendments 1-2): baseline B, model M, arm H on the S0/S1/S2 labels.
Usage: python s3_model.py dev | test | report.
`dev` freezes every choice (dev_results.json); `test` runs once (test.flag, test_results.json); `report` writes RESULTS.md."""
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.dont_write_bytecode = True
ROOT = Path("F:/ACUD AI Data Lab/Project/real_data/37_coarse_stage")
SEED_SPLIT = 2038
SEED_MODEL = 2038
SEED_BOOT = 2039
TEST_FRACTION = 0.30
N_FOLDS = 5
N_BOOT = 2000
CI_LEVEL = 0.90
STAGES = ["S0", "S1", "S2"]
GATE_MACRO, GATE_CLASS, GATE_S2_PRECISION, GATE_2025 = 0.75, 0.60, 0.60, 0.70
LGBM_MIN_GAIN = 0.02
ARM_MIN_GAIN = 0.03
LAST_OBT_YEAR = 2023
DW = ["built", "bare", "grass", "trees", "water"]
SAT_FEATURES = (
    [f"dw_{c}" for c in DW]
    + [f"dw_{c}_chg" for c in DW]
    + ["s2_ndvi", "s2_ndbi", "s2_brightness", "s2_swir_nir", "s2_ndvi_p90"]
    + ["s1_vv", "s1_vh", "s1_vv_minus_vh", "s1_vv_std", "s1_vh_std"]
    + ["ntl", "ntl_chg"]
)
HEIGHT_FEATURES = ["h_presence", "h_mean", "h_p90", "h_share_tall", "h_mean_chg", "height_age_years"]
ARMS = {"B": ["dw_built", "dw_grass_trees"], "M": SAT_FEATURES, "H": SAT_FEATURES + HEIGHT_FEATURES}
ARM_ORDER = ["B", "M", "H"]
THRESHOLD_QUANTILES = np.linspace(0.02, 0.98, 49)


def read_labels() -> pd.DataFrame:
    """Parse line by line: notes may contain unquoted commas."""
    rows = []
    for path in sorted(glob.glob(str(ROOT / "labels" / "labels_pass1_*.csv"))):
        with open(path, encoding="utf-8") as fh:
            for line in list(fh)[1:]:
                if line.strip():
                    parts = line.rstrip("\n").split(",", 3)
                    rows.append((parts[0], parts[1]))
    return pd.DataFrame(rows, columns=["row_id", "stage"])


def build_table() -> tuple[pd.DataFrame, pd.Series]:
    """Return (labelled S0/S1/S2 rows with features, count of every label value)."""
    labels = read_labels()
    feats = pd.read_csv(ROOT / "features" / "ee_window_features.csv")
    obt = pd.read_csv(ROOT / "features" / "obt_features.csv").set_index(["block_id", "obt_year"])
    feats["dw_grass_trees"] = feats.dw_grass + feats.dw_trees
    height_year = feats.target_year.clip(upper=LAST_OBT_YEAR)
    feats["height_age_years"] = feats.target_year - height_year
    now = obt.reindex(pd.MultiIndex.from_arrays([feats.block_id, height_year]))
    prev = obt.reindex(pd.MultiIndex.from_arrays([feats.block_id, height_year - 2]))
    for col in ["h_presence", "h_mean", "h_p90", "h_share_tall"]:
        feats[col] = now[col].to_numpy()
    feats["h_mean_chg"] = now["h_mean"].fillna(0).to_numpy() - prev["h_mean"].fillna(0).to_numpy()
    # No present building pixel: height statistics are undefined and set to 0 (presence share is 0 too).
    feats[["h_mean", "h_p90", "h_share_tall"]] = feats[["h_mean", "h_p90", "h_share_tall"]].fillna(0)
    table = labels.merge(feats, on="row_id", how="left", validate="one_to_one")
    return table[table.stage.isin(STAGES)].reset_index(drop=True), labels.stage.value_counts()


def split_blocks(table: pd.DataFrame) -> tuple[list[str], list[str]]:
    blocks = np.array(sorted(table.block_id.unique()))
    shuffled = np.random.default_rng(SEED_SPLIT).permutation(blocks)
    n_test = round(TEST_FRACTION * len(blocks))
    return sorted(shuffled[n_test:]), sorted(shuffled[:n_test])


def recall_precision(conf: np.ndarray) -> dict:
    support = conf.sum(axis=1)
    recall = np.divide(np.diag(conf), support, out=np.full(3, np.nan), where=support > 0)
    pred_s2 = conf[:, 2].sum()
    precision_s2 = conf[2, 2] / pred_s2 if pred_s2 > 0 else np.nan
    return {
        "macro_recall": float(np.nanmean(recall)),
        "recall": dict(zip(STAGES, map(float, recall), strict=True)),
        "s2_precision": float(precision_s2),
    }


def to_conf(y_true, y_pred) -> np.ndarray:
    return confusion_matrix(y_true, y_pred, labels=STAGES)


class ThresholdBaseline:
    """S0 if built < t_built; else S2 if grass+trees >= t_green; else S1. Thresholds maximise macro recall on the training rows."""

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        best = -1.0
        for t_built in np.unique(np.quantile(X.dw_built, THRESHOLD_QUANTILES)):
            for t_green in np.unique(np.quantile(X.dw_grass_trees, THRESHOLD_QUANTILES)):
                score = recall_precision(to_conf(y, self._predict(X, t_built, t_green)))["macro_recall"]
                if score > best:
                    best, self.t_built_, self.t_green_ = score, float(t_built), float(t_green)
        return self

    @staticmethod
    def _predict(X: pd.DataFrame, t_built: float, t_green: float) -> np.ndarray:
        return np.where(X.dw_built < t_built, "S0", np.where(X.dw_grass_trees >= t_green, "S2", "S1"))

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self._predict(X, self.t_built_, self.t_green_)


def make_model(arm: str, kind: str):
    if arm == "B":
        return ThresholdBaseline()
    if kind == "logit":
        return make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(class_weight="balanced", max_iter=5000, random_state=SEED_MODEL),
        )
    return LGBMClassifier(
        max_depth=3, num_leaves=7, n_estimators=200, learning_rate=0.05, class_weight="balanced",
        random_state=SEED_MODEL, n_jobs=1, verbose=-1,
    )


def oof_predict(dev: pd.DataFrame, arm: str, kind: str) -> np.ndarray:
    pred = np.empty(len(dev), dtype=object)
    X, y = dev[ARMS[arm]], dev.stage.to_numpy()
    for train_idx, val_idx in GroupKFold(n_splits=N_FOLDS).split(X, y, dev.block_id):
        pred[val_idx] = make_model(arm, kind).fit(X.iloc[train_idx], y[train_idx]).predict(X.iloc[val_idx])
    return pred


def run_dev() -> None:
    if (ROOT / "dev_results.json").exists():
        raise SystemExit("dev_results.json already exists: choices are frozen")
    table, label_counts = build_table()
    dev_blocks, test_blocks = split_blocks(table)
    dev = table[table.block_id.isin(dev_blocks)].reset_index(drop=True)
    results = {
        "label_counts": label_counts.to_dict(),
        "n_labelled_blocks": len(dev_blocks) + len(test_blocks),
        "n_dev_blocks": len(dev_blocks),
        "n_test_blocks": len(test_blocks),
        "test_blocks": test_blocks,
        "dev_class_counts": dev.stage.value_counts().to_dict(),
        "arms": {},
    }
    for arm in ARM_ORDER:
        entry = {}
        if arm == "B":
            entry["model"] = "threshold"
            oof = oof_predict(dev, arm, "logit")
            fitted = ThresholdBaseline().fit(dev[ARMS[arm]], dev.stage.to_numpy())
            entry["thresholds"] = {"dw_built": fitted.t_built_, "dw_grass_trees": fitted.t_green_}
        else:
            oofs = {kind: oof_predict(dev, arm, kind) for kind in ("logit", "lgbm")}
            scores = {k: recall_precision(to_conf(dev.stage, p)) for k, p in oofs.items()}
            gain = scores["lgbm"]["macro_recall"] - scores["logit"]["macro_recall"]
            entry["model"] = "lgbm" if gain >= LGBM_MIN_GAIN else "logit"
            entry["dev_candidates"] = scores
            oof = oofs[entry["model"]]
        entry["dev"] = recall_precision(to_conf(dev.stage, oof))
        entry["dev_confusion"] = to_conf(dev.stage, oof).tolist()
        results["arms"][arm] = entry
        print(arm, entry["model"], round(entry["dev"]["macro_recall"], 4), flush=True)
    (ROOT / "dev_results.json").write_text(json.dumps(results, indent=2))


def bootstrap(block_conf: np.ndarray, rng: np.random.Generator) -> dict:
    """block_conf: (n_blocks, 3, 3) per-block confusion counts; percentile interval over block resamples."""
    draws = {"macro_recall": [], "s2_precision": [], **{f"recall_{s}": [] for s in STAGES}}
    for _ in range(N_BOOT):
        m = recall_precision(block_conf[rng.integers(0, len(block_conf), len(block_conf))].sum(axis=0))
        draws["macro_recall"].append(m["macro_recall"])
        draws["s2_precision"].append(m["s2_precision"])
        for stage in STAGES:
            draws[f"recall_{stage}"].append(m["recall"][stage])
    lo, hi = (1 - CI_LEVEL) / 2 * 100, (1 + CI_LEVEL) / 2 * 100
    return {k: [float(np.nanpercentile(v, lo)), float(np.nanpercentile(v, hi))] for k, v in draws.items()}


def block_confusions(df: pd.DataFrame, pred: np.ndarray, blocks: list[str]) -> np.ndarray:
    df = df.assign(pred=pred)
    out = np.zeros((len(blocks), 3, 3))
    for i, block in enumerate(blocks):
        sub = df[df.block_id == block]
        if len(sub):
            out[i] = to_conf(sub.stage, sub.pred)
    return out


def gates(metrics: dict, metrics_2025: dict) -> dict:
    checks = {
        "macro_recall": metrics["macro_recall"] >= GATE_MACRO,
        "class_recall": all(r >= GATE_CLASS for r in metrics["recall"].values()),
        "s2_precision": metrics["s2_precision"] >= GATE_S2_PRECISION,
        "macro_recall_2025": metrics_2025["macro_recall"] >= GATE_2025,
    }
    checks["step3_pass"] = checks["macro_recall"] and checks["class_recall"] and checks["s2_precision"]
    checks["pass"] = checks["step3_pass"] and checks["macro_recall_2025"]
    return checks


def choose_arm(results: dict) -> str | None:
    """Simplest passing arm; a more complex passing arm only with +ARM_MIN_GAIN dev macro recall."""
    passing = [a for a in ARM_ORDER if results["arms"][a]["gates"]["pass"]]
    if not passing:
        return None
    chosen = passing[0]
    for arm in passing[1:]:
        if results["arms"][arm]["dev"]["macro_recall"] - results["arms"][chosen]["dev"]["macro_recall"] >= ARM_MIN_GAIN:
            chosen = arm
    return chosen


def run_test() -> None:
    flag = ROOT / "test.flag"
    if flag.exists():
        raise SystemExit("test.flag exists: the test was already run once")
    results = json.loads((ROOT / "dev_results.json").read_text())
    flag.write_text("test evaluated once; see test_results.json\n")
    table, _ = build_table()
    test_blocks = results["test_blocks"]
    dev = table[~table.block_id.isin(test_blocks)].reset_index(drop=True)
    test = table[table.block_id.isin(test_blocks)].reset_index(drop=True)
    is_2025 = (test.target_year == 2025).to_numpy()
    rng = np.random.default_rng(SEED_BOOT)
    results["test_class_counts"] = test.stage.value_counts().to_dict()
    results["test_rows_2025"] = int(is_2025.sum())
    results["test_class_counts_2025"] = test[is_2025].stage.value_counts().to_dict()
    for arm in ARM_ORDER:
        entry = results["arms"][arm]
        kind = "logit" if entry["model"] == "threshold" else entry["model"]
        pred = make_model(arm, kind).fit(dev[ARMS[arm]], dev.stage.to_numpy()).predict(test[ARMS[arm]])
        metrics = recall_precision(to_conf(test.stage, pred))
        metrics_2025 = recall_precision(to_conf(test.stage[is_2025], pred[is_2025]))
        entry.update(
            test=metrics,
            test_ci=bootstrap(block_confusions(test, pred, test_blocks), rng),
            test_2025=metrics_2025,
            test_2025_ci=bootstrap(block_confusions(test[is_2025], pred[is_2025], test_blocks), rng),
            test_confusion=to_conf(test.stage, pred).tolist(),
            gates=gates(metrics, metrics_2025),
        )
    results["chosen_arm"] = choose_arm(results)
    (ROOT / "test_results.json").write_text(json.dumps(results, indent=2))
    print("chosen:", results["chosen_arm"])


DEVIATIONS = """\
- **Gates read on point estimates.** The protocol lists 90 % block intervals next to the gates without saying whether the point value or the lower bound must clear them. Pass/fail uses the point estimate; every interval is shown.
- **The 2025 regime check is applied to every arm, including B** (Amendment 1 says "each arm"). B also passes the original Step 3 gates alone; the table shows both.
- **Dynamic World:** mean over all DW scenes in the window (no join to Sentinel-2 L1C cloud < 20 % as in Step 1a). Change = window mean minus the mean of the 12 months before the window start.
- **Sentinel-2:** SR harmonized, scenes with CLOUDY_PIXEL_PERCENTAGE < 60 and SCL masked (cloud, shadow, cirrus, snow, no-data, saturated); median bands give NDVI, NDBI, brightness, SWIR1/NIR. NDVI p90 = per-pixel temporal 90th percentile of scene NDVI, then block mean.
- **Sentinel-1:** GRD IW, ascending pass only (one geometry, all relative orbits), VV and VH in dB as stored in Earth Engine; temporal std per pixel, then block mean.
- **Night lights:** VNP46A2 Gap_Filled_DNB_BRDF_Corrected_NTL, daily mean over the window; change vs the 12 months before the window start. Raw Earth Engine units (not rescaled).
- **Windows** are capture date -6 / +6 months. All block values are means over the 500 m block at 10 m (UTM 36N); block cell = block_id.
- **Open Buildings Temporal:** one image per year (2017, 2019, 2021, 2023), presence >= 0.5, read at 4 m. Height statistics are over present pixels; a block with no present pixel gets height mean / p90 / tall share = 0 (presence share 0). Change of mean height = mean height at the height year minus the year two earlier (2017 for 2019 rows; 2021 for 2025 rows, where the height year is 2023).
- **Model details not fixed by the protocol:** logistic C = 1 (default, not tuned); LightGBM depth 3, 7 leaves, 200 trees, learning rate 0.05, class-balanced; B thresholds from a 49-quantile grid maximising macro recall; GroupKFold(5) without shuffling; bootstrap 2,000 block resamples, seed 2039. LightGBM was compared with the logistic inside each feature arm (M and H) with the +0.02 dev rule.
- **Arm H2:** pending: server inference not yet available. Not run.
- **PROTOCOL.md hash:** sha256 equals the value in PROTOCOL.sha256 (166255658c4f81731c6a3c2d12bba75bdee439ae059effce535fc5c71d8af8b0), including the Amendment 2 text; no mismatch.
- Earth Engine reported "restricted mode" (noncommercial quota) as a warning; all requests still completed.
"""


def fmt_ci(value: float, ci: list[float]) -> str:
    return f"{value:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]"


def conf_table(conf: list[list[int]]) -> str:
    lines = ["| true / predicted | S0 | S1 | S2 |", "| --- | --- | --- | --- |"]
    lines += [f"| {s} | " + " | ".join(str(int(v)) for v in row) + " |" for s, row in zip(STAGES, conf, strict=True)]
    return "\n".join(lines)


def run_report() -> None:
    r = json.loads((ROOT / "test_results.json").read_text())
    arms = r["arms"]
    passing = [a for a in ARM_ORDER if arms[a]["gates"]["pass"]]
    chosen = r["chosen_arm"]
    names = {"B": "B (two DW thresholds)", "M": "M (satellite features)", "H": "H (M + OBT heights)"}
    dev_gain = arms["H"]["dev"]["macro_recall"] - arms["B"]["dev"]["macro_recall"]
    lgbm_gain = {a: arms[a]["dev_candidates"]["lgbm"]["macro_recall"] - arms[a]["dev_candidates"]["logit"]["macro_recall"] for a in ("M", "H")}
    out = ["# Coarse construction stage (S0 / S1 / S2): Step 2-3 results", ""]
    out.append(
        f"**Verdict: PASS. Arms passing all gates: {', '.join(passing)}. Rule outcome: arm {chosen}** "
        f"(B passes, but H beats B on development macro recall by {dev_gain:.3f} >= {ARM_MIN_GAIN}; "
        f"M fails the 2025 regime check by {GATE_2025 - arms['M']['test_2025']['macro_recall']:.3f}). "
        "Not applied to R7 yet. Arm H2 is pending: server inference not yet available."
    )
    out += [
        "",
        "Test = 66 held-out blocks (seed 2038), evaluated once (`test.flag`). Intervals are 90 % block bootstrap. "
        "Gates: macro recall >= 0.75, each class recall >= 0.60, S2 precision >= 0.60, 2025-rows macro recall >= 0.70.",
        "",
        "## Results per arm",
        "",
        "| arm | model | dev macro recall | test macro recall [90 % CI] | recall S0 | recall S1 | recall S2 | S2 precision | 2025 rows macro recall [90 % CI] | Step 3 gates | 2025 check | pass |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for a in ARM_ORDER:
        e = arms[a]
        t, ci, g = e["test"], e["test_ci"], e["gates"]
        out.append(
            f"| {names[a]} | {e['model']} | {e['dev']['macro_recall']:.3f} | {fmt_ci(t['macro_recall'], ci['macro_recall'])} | "
            + " | ".join(fmt_ci(t["recall"][s], ci[f"recall_{s}"]) for s in STAGES)
            + f" | {fmt_ci(t['s2_precision'], ci['s2_precision'])} | {fmt_ci(e['test_2025']['macro_recall'], e['test_2025_ci']['macro_recall'])} | "
            f"{'pass' if g['step3_pass'] else 'fail'} | {'pass' if g['macro_recall_2025'] else 'fail'} | **{'PASS' if g['pass'] else 'FAIL'}** |"
        )
    out.append("| H2 (server model heights) | pending: server inference not yet available | | | | | | | | | | not run |")
    c25 = r["test_class_counts_2025"]
    out += [
        "",
        "Notes:",
        "- Several interval lower bounds sit below their thresholds (B macro recall, B S2 recall, S1 recall of M and H, the 2025 macro recall of every arm). "
        "With 66 test blocks the gates are not decided with margin by these intervals.",
        f"- 2025 test rows: {r['test_rows_2025']} (S0 {c25['S0']}, S1 {c25['S1']}, S2 {c25['S2']}); only {c25['S1']} are S1, so the 2025 S1 recall is very noisy.",
        "- H uses OBT 2023 carried forward for 2025 rows (`height_age_years` = 2).",
        f"- Dev macro recall, LightGBM minus logistic: M {lgbm_gain['M']:+.3f} (kept LightGBM, rule +{LGBM_MIN_GAIN}), H {lgbm_gain['H']:+.3f} (kept logistic).",
        f"- B thresholds (fitted on development): built < {arms['B']['thresholds']['dw_built']:.4f} -> S0; else grass+trees >= {arms['B']['thresholds']['dw_grass_trees']:.4f} -> S2; else S1.",
        "",
        "## Choice rule",
        "",
        f"- Passing arms in order of simplicity: {', '.join(passing)}. M does not pass (2025 macro recall {arms['M']['test_2025']['macro_recall']:.3f} < {GATE_2025}).",
        f"- Dev macro recall: B {arms['B']['dev']['macro_recall']:.3f}, M {arms['M']['dev']['macro_recall']:.3f}, H {arms['H']['dev']['macro_recall']:.3f}.",
        f"- H beats B by {dev_gain:.3f} (>= {ARM_MIN_GAIN}), so **{chosen}** is chosen.",
        "",
        "## Confusion matrices (test, rows = true)",
        "",
    ]
    for a in ARM_ORDER:
        out += [f"**{names[a]}**", "", conf_table(arms[a]["test_confusion"]), ""]
    out += ["## Confusion matrices (development, 5-fold GroupKFold out-of-fold)", ""]
    for a in ARM_ORDER:
        out += [f"**{names[a]}**", "", conf_table(arms[a]["dev_confusion"]), ""]
    lc = r["label_counts"]
    out += [
        "## Counts",
        "",
        f"- Pass-1 labels: S0 {lc['S0']}, S1 {lc['S1']}, S2 {lc['S2']}, mixed {lc['mixed']}, unusable {lc['unusable']} (866 usable image rows; 14 more block-years were unusable at sampling, 880 in total).",
        f"- Used for fitting and gates (S0/S1/S2): {sum(r['dev_class_counts'].values()) + sum(r['test_class_counts'].values())} rows in {r['n_labelled_blocks']} blocks.",
        f"- Development: {r['n_dev_blocks']} blocks, {sum(r['dev_class_counts'].values())} rows {r['dev_class_counts']}.",
        f"- Test: {r['n_test_blocks']} blocks, {sum(r['test_class_counts'].values())} rows {r['test_class_counts']}.",
        "- Step 1 kappa: 0.784 (pass), see `AGREEMENT.md`.",
        "",
        "## Deviations and interpretations",
        "",
        DEVIATIONS,
        "## Files",
        "",
        "- `scripts/s2_features.py`, `scripts/s3_model.py`; `features/ee_window_features.csv`, `features/obt_features.csv`; "
        "`dev_results.json` (frozen before the test), `test_results.json`, `test.flag`.",
        "",
    ]
    (ROOT / "RESULTS.md").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    {"dev": run_dev, "test": run_test, "report": run_report}[sys.argv[1]]()
