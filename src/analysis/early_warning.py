"""
propose: early-warning experiment on the generated data (EW_PROTOCOL.md): compare four methods, apply the product rule, write EW_REPORT.md.
input: app_data/sim, app_data/real, private/answer_key.parquet (labels for evaluation only).
output: app_data/EW_REPORT.md, app_data/ew/*.csv and *.png.
run: uv run --with matplotlib python -m src.analysis.early_warning
"""

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.analysis import ew_eval as E
from src.analysis import ew_features as F
from src.analysis import ew_report as R
from src.pipeline.common import APP, BASE_DIR, CFG, PRIVATE, REAL

OUT = APP / "ew"
METHODS = {
    # key: (label, score column, alert column), {view} is replaced by time / dev / cv
    "sat": ("(1) قاعدة القمر وحده (مستوى R1)", "score_sat", "alert_sat"),
    "k2": ("(1b) K2 وحده", "score_k2", "alert_k2"),
    "b": ("(2b) محفزات B وحدها", "score_b", "alert_b"),
    "rule": ("(2) القاعدة البسيطة (R1 + B)", "score_rule", "alert_rule"),
    "lr": ("(3) لوجستي", "p_lr_both_{view}", "p_lr_both_{view}"),
    "gb": ("(4) Gradient boosting", "p_gb_both_{view}", "p_gb_both_{view}"),
    "lr_sat": ("لوجستي، ميزات القمر بس", "p_lr_sat_{view}", "p_lr_sat_{view}"),
    "lr_int": ("لوجستي، ميزات الداخلي بس", "p_lr_internal_{view}", "p_lr_internal_{view}"),
    "gb_sat": ("GB، ميزات القمر بس", "p_gb_sat_{view}", "p_gb_sat_{view}"),
    "gb_int": ("GB، ميزات الداخلي بس", "p_gb_internal_{view}", "p_gb_internal_{view}"),
}
MODEL_KEYS = {"lr", "gb", "lr_sat", "lr_int", "gb_sat", "gb_int"}


def input_hashes() -> dict:
    """Fingerprint the actual inputs and source code without copying private labels."""
    paths = {
        "real/compounds.parquet": REAL / "compounds.parquet",
        "real/kpi_values.parquet": REAL / "kpi_values.parquet",
        "sim/fin_monthly.parquet": F.SIM / "fin_monthly.parquet",
        "sim/complaints.parquet": F.SIM / "complaints.parquet",
        "private/answer_key.parquet": PRIVATE / "answer_key.parquet",
        "configs/data.yaml": BASE_DIR / "configs" / "data.yaml",
        "src/pipeline/common.py": BASE_DIR / "src" / "pipeline" / "common.py",
    }
    paths.update({f"src/analysis/{name}.py": BASE_DIR / "src" / "analysis" / f"{name}.py"
                  for name in ("early_warning", "ew_features", "ew_eval", "ew_report")})
    for folder in ("pipeline", "generator"):
        paths.update({p.relative_to(BASE_DIR).as_posix(): p for p in sorted((BASE_DIR / "src" / folder).glob("*.py"))})
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in sorted(paths.items())}


def run_provenance(st: dict, hashes: dict) -> dict:
    """Record which data, scope and frozen evaluation settings produced this run."""
    identity = json.dumps(hashes, sort_keys=True).encode()
    return {
        "run_id": "EW-" + hashlib.sha256(identity).hexdigest()[:12],
        "sha256": hashes, "scope_districts": CFG.get("scope_districts", []),
        "codes": sorted(st["table"]["code"].unique()),
        "cutoffs": sorted(st["table"]["quarter"].unique()),
        "train_last": E.TRAIN_LAST, "test_label_quarters": E.TEST_LABEL_Q,
        "test_all_quarters": E.TEST_ALL_Q, "test_onset_from": str(E.TEST_ONSET_FROM),
        "top_n": E.N_DEFAULT, "held_developers": st["held"], "held_seed": st["held_seed"],
    }


TRAINING_KEYS = ["code", "developer_code", "quarter", "month"]
TARGET, CENSOR = "label_distress_next_6m", "label_censored"


def training_dataset(table: pd.DataFrame) -> pd.DataFrame:
    """Persist only the declared X, keys and evaluation-only y; never hidden truth or fitted predictions."""
    forbidden = {*TRAINING_KEYS, "developer", "story", "distress_now", "warning_issued", "status_level", "label", "censored", TARGET, CENSOR}
    if any(c in forbidden or c.startswith(("true_", "label_", "p_", "score_", "alert_")) for c in F.FEATURES):
        raise ValueError("An evaluation-only or fitted column was declared as a training feature")
    out = table[["code", "developer", "quarter", "month", *F.FEATURES, "label", "censored"]].rename(
        columns={"developer": "developer_code", "label": TARGET, "censored": CENSOR}).copy()
    if out.duplicated(["code", "quarter"]).any():
        raise ValueError("Training dataset has duplicate compound-quarter keys")
    out[TARGET] = pd.array(out[TARGET], dtype="boolean")
    if (out[TARGET].isna() & ~out[CENSOR]).any():
        raise ValueError("An uncensored training row has no target")
    out.loc[out[CENSOR], TARGET] = pd.NA
    out["month"] = out["month"].astype(str)
    return out.sort_values(["quarter", "code"]).reset_index(drop=True)


def training_metadata(data: pd.DataFrame, hashes: dict) -> dict:
    """The frozen time split, censoring and binary class counts are auditable independently of model scores."""
    masks = {
        "train": (data["quarter"] <= E.TRAIN_LAST) & ~data[CENSOR],
        "time_test": data["quarter"].isin(E.TEST_LABEL_Q) & ~data[CENSOR],
        "censored": data[CENSOR],
    }
    counts = {name: {"rows": int(mask.sum()), "positive": int(data.loc[mask, TARGET].sum()),
                     "negative": int((~data.loc[mask, TARGET]).sum()), "unlabelled": int(data.loc[mask, TARGET].isna().sum())}
              for name, mask in masks.items()}
    return {
        "synthetic_label": CFG["generator"]["label"],
        "purpose": "Historical reconstruction / mechanism experiment, not measured operational accuracy",
        "keys": TRAINING_KEYS, "features": list(F.FEATURES), "target": TARGET, "censor_column": CENSOR,
        "feature_groups": {"public_observation_derived": list(F.SAT_ALL), "generated_operations_derived": list(F.INTERNAL_ALL)},
        "target_definition": "true distress in any of the next six months; excludes the cutoff month",
        "horizon_months": 6, "classes": {"false": "no future distress", "true": "future distress"},
        "censoring_rule": "Target is null when the complete next-six-month horizon is unavailable; these rows never enter fitting or row metrics.",
        "rows": len(data), "compounds": int(data.code.nunique()), "cutoffs": sorted(data.quarter.unique()),
        "train_last": E.TRAIN_LAST, "test_label_quarters": E.TEST_LABEL_Q, "split_counts": counts,
        "excluded_uncensored_quarters": sorted(data.loc[~(masks["train"] | masks["time_test"] | masks["censored"]), "quarter"].unique()),
        "features_only_rule": "X is exactly features; keys, target and censor flag never enter X. Fit imputation/scaling on training only.",
        "feature_preparation": "src/analysis/ew_features.py: deduplicate monthly financial keys, validate report dates against recorded month, repair detected thousand-EGP balance entries, and use only records available at each cutoff. Exact implementation is source-hashed.",
        "feature_missing_values": {c: int(data[c].isna().sum()) for c in F.FEATURES},
        "dtypes": {c: str(data[c].dtype) for c in data.columns}, "input_and_source_sha256": hashes,
    }


def export_training_dataset(st: dict, hashes: dict, folder: Path = PRIVATE, public_folder: Path = OUT) -> dict:
    data = training_dataset(st["table"])
    meta = training_metadata(data, hashes)
    meta["run_id"] = run_provenance(st, hashes)["run_id"]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "ml_dataset.parquet"
    tab = pa.Table.from_pandas(data, preserve_index=False)
    tab = tab.replace_schema_metadata({**(tab.schema.metadata or {}), b"synthetic_label": meta["synthetic_label"].encode(),
                                      b"features": json.dumps(meta["features"]).encode(), b"target": TARGET.encode(), b"censor_column": CENSOR.encode()})
    pq.write_table(tab, path)
    meta["dataset_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    metadata_path = folder / "ml_dataset_metadata.json"
    metadata_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    dictionary = folder / "dictionaries" / "ml_dataset.md"
    dictionary.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Binary training dataset (private)", "", meta["synthetic_label"], "",
             "One row per compound and quarterly cutoff. X is exactly the feature list below. Hidden truth and fitted predictions are excluded.",
             "The target uses the next six months and is null for censored rows; exclude those rows from supervised fitting and row metrics. See ml_dataset_metadata.json for the frozen split and hashes.", "",
             "| column | role | type |", "| --- | --- | --- |"]
    lines += [f"| `{c}` | {'feature X' if c in F.FEATURES else 'key (not X)' if c in TRAINING_KEYS else 'target y' if c == TARGET else 'censor flag (not X)'} | {data[c].dtype} |" for c in data]
    dictionary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    public_folder.mkdir(parents=True, exist_ok=True)
    public = {k: meta[k] for k in ("synthetic_label", "purpose", "run_id", "rows", "compounds", "cutoffs", "features", "feature_groups", "target", "censor_column", "split_counts")}
    public["private_dataset"] = "private/ml_dataset.parquet"
    (public_folder / "dataset_summary.json").write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"private/" + p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (path, metadata_path, dictionary)}


def never_distressed() -> set:
    ak = pd.read_parquet(PRIVATE / "answer_key.parquet")
    return set(ak.groupby("code")["true_distress"].any().loc[lambda s: ~s].index)


def method_flags(d: pd.DataFrame, key: str, view: str, n: int):
    _, score, alert = METHODS[key]
    score = score.format(view=view)
    alert = alert.format(view=view)
    top = E.topn_flag(d, score, n)
    al = d[alert] >= 0.5 if key in MODEL_KEYS else d[alert]
    return top, al


def evaluate_view(d: pd.DataFrame, view: str, n: int, label_q, all_q, events, never) -> pd.DataFrame:
    rows = []
    for key, (name, *_rest) in METHODS.items():
        if view == "rule_all" and key in MODEL_KEYS:
            continue
        v = "cv" if view == "rule_all" else view
        top, al = method_flags(d, key, v, n)
        m = E.metrics(d, top, events, label_q, all_q, never)
        a = E.metrics(d, al, events, label_q, all_q, never)
        rows.append({"key": key, "method": name, **m, **{f"alert_{k}": a[k] for k in ("recall", "fa_healthy", "fa_never", "alerts_per_q", "event_recall", "lead_median")}})
    return pd.DataFrame(rows)


def prepare(sat_lag_q: int = 0) -> dict:
    """feature table + rule columns + model probabilities (all views)."""
    src = F.Source(sat_lag_q)
    tab = F.build_table(src=src)
    held, held_seed = E.holdout_developers(tab)
    d = E.add_models(E.add_rule_columns(tab), held)
    ev_all = F.onset_events()
    return {"table": d, "held": held, "held_seed": held_seed, "never": never_distressed(), "ev_all": ev_all,
            "ev_test": ev_all[ev_all["onset"] >= E.TEST_ONSET_FROM], "lag": sat_lag_q, "fixed": src.n_balance_fixed}


def evaluate_all(st: dict, n: int = E.N_DEFAULT) -> dict:
    d, held, never = st["table"], st["held"], st["never"]
    all_label_q = [q for q in F.CUTOFF_QUARTERS if q != "2026Q2"]
    res = {"n": n}
    res["time"] = evaluate_view(d, "time", n, E.TEST_LABEL_Q, E.TEST_ALL_Q, st["ev_test"], never)
    # developer hold-out: the pool is the held-out developers' compounds only, so the list size is scaled with the pool
    dh = d[d["developer"].isin(held)]
    n_h = max(1, round(n * dh["code"].nunique() / d["code"].nunique()))
    res["dev"] = evaluate_view(dh, "dev", n_h, E.TEST_LABEL_Q, E.TEST_ALL_Q, st["ev_test"][st["ev_test"]["code"].isin(dh["code"])], never)
    res["n_dev"] = n_h
    res["ext"] = evaluate_view(d, "cv", n, all_label_q, F.CUTOFF_QUARTERS, st["ev_all"], never)
    res["rules_all"] = evaluate_view(d, "rule_all", n, all_label_q, F.CUTOFF_QUARTERS, st["ev_all"], never)
    res["random_time"] = E.random_baseline(d, E.TEST_LABEL_Q, n)
    res["random_ext"] = E.random_baseline(d, all_label_q, n)
    return res


def sens_row(tag: str, res: dict) -> dict:
    """one line of the sensitivity table: does any model beat the rule on both views?"""
    dec = R.decide(res["time"], res["ext"])
    t, x = res["time"].set_index("key"), res["ext"].set_index("key")

    def cell(tab, k):
        return f"{R.pct(tab.loc[k, 'recall'])} / {R.num(tab.loc[k, 'lead_median'])}"

    return {"الحالة": tag, "قاعدة (2) زمني": cell(t, "rule"), "لوجستي زمني": cell(t, "lr"), "GB زمني": cell(t, "gb"),
            "قاعدة (2) مكمّل": cell(x, "rule"), "لوجستي مكمّل": cell(x, "lr"), "GB مكمّل": cell(x, "gb"),
            "المنتج": {"rule": "القاعدة", "lr": "لوجستي", "gb": "GB"}[dec["product"]]}


def ablation_table(res_time: pd.DataFrame, res_ext: pd.DataFrame) -> str:
    t, x = res_time.set_index("key"), res_ext.set_index("key")
    rows = []
    for key, name in (("lr_sat", "لوجستي: قمر بس"), ("lr_int", "لوجستي: داخلي بس"), ("lr", "لوجستي: الاتنين"),
                      ("gb_sat", "GB: قمر بس"), ("gb_int", "GB: داخلي بس"), ("gb", "GB: الاتنين"),
                      ("sat", "قاعدة القمر (1)"), ("b", "قاعدة B وحدها (2b)"), ("rule", "قاعدة (2)")):
        rows.append({"الميزات/الطريقة": name, "Recall@8 زمني": R.pct(t.loc[key, "recall"]), "Lead زمني": R.num(t.loc[key, "lead_median"]),
                     "Recall@8 مكمّل": R.pct(x.loc[key, "recall"]), "Lead مكمّل": R.num(x.loc[key, "lead_median"]),
                     "False-alarm سليمة (زمني)": R.pct(t.loc[key, "fa_healthy"])})
    return R.md_table(pd.DataFrame(rows))


def lists_md(d: pd.DataFrame, score: str, n: int, p_col: str | None) -> str:
    lst = R.topn_lists(d, score, n, p_col)
    out = []
    for q, g in lst.groupby("quarter"):
        tag = "قائمة حية، الليبل مقطوع" if q == "2026Q2" else ("فترة اختبار" if q in E.TEST_LABEL_Q else "embargo" if q == "2025Q1" else "فترة تدريب")
        out.append(f"\n**{q}** ({tag})\n")
        t = g.rename(columns={"rank": "الترتيب", "code": "الكمبوند", "reason": "السبب", "hit": "إيجابي؟"})
        out.append(R.md_table(t[["الترتيب", "الكمبوند", "السبب", "إيجابي؟"]]))
    return "\n".join(out)


def run() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    hashes = input_hashes()
    st = prepare()
    d = st["table"]
    res = evaluate_all(st)
    res5 = evaluate_all(st, 5)
    res_lag = evaluate_all(prepare(1))
    dec = R.decide(res["time"], res["ext"])
    imp = R.importances(d)
    cal = R.plot_calibration(d)
    ev = R.event_leads(st, METHODS)
    R.plot_leads(ev)
    prod = dec["product"]
    score = {"rule": "score_rule", "lr": "p_lr_both_time", "gb": "p_gb_both_time"}[prod]
    p_col = None if prod == "rule" else score
    R.topn_lists(d, score, E.N_DEFAULT, p_col).to_csv(OUT / "topn_lists.csv", index=False, encoding="utf-8-sig")
    for name, r in (("time", res["time"]), ("dev", res["dev"]), ("ext", res["ext"]), ("time_n5", res5["time"]), ("ext_n5", res5["ext"]),
                    ("time_lag1", res_lag["time"]), ("ext_lag1", res_lag["ext"])):
        r.to_csv(OUT / f"comparison_{name}.csv", index=False, encoding="utf-8-sig")
    ev.to_csv(OUT / "event_leads.csv", index=False, encoding="utf-8-sig")
    pd.concat([imp["lr"].rename("lr_coef"), imp["gb"].rename("gb_perm_importance")], axis=1).to_csv(OUT / "feature_importance.csv", encoding="utf-8-sig")

    keys = ["sat", "k2", "b", "rule", "lr", "gb"]
    t, x = res["time"].set_index("key"), res["ext"].set_index("key")
    facts = R.report_facts(st, res["n"])
    pos_t, ev_t = int(t.loc["rule", "positives"]), int(t.loc["rule", "events"])
    ceiling = facts["precision_ceiling"]
    piv = ev.pivot(index=["code", "onset"], columns="method", values="lead").reset_index()
    cau = ev.pivot(index=["code", "onset"], columns="method", values="caught").reset_index()
    pv = piv[["code", "onset"]].copy()
    for k in ("sat", "rule", "b", "lr", "gb"):
        pv[R.NAMES[k]] = ["فاتته" if not c else R.num(v, 0) for v, c in zip(piv[k], cau[k])]
    pv["فترة"] = ["اختبار" if pd.Period(o, "M") >= E.TEST_ONSET_FROM else "مكمّل" for o in pv["onset"]]
    imp_lr = R.md_table(pd.DataFrame({"الميزة": imp["lr"].head(8).index, "معامل (standardized)": [f"{v:+.2f}" for v in imp["lr"].head(8)]}))
    imp_gb = R.md_table(pd.DataFrame({"الميزة": imp["gb"].head(8).index, "permutation (average precision)": [f"{v:.3f}" for v in imp["gb"].head(8)]}))
    held = "، ".join(st["held"])
    n_held, held_codes = facts["held_count"], facts["held_codes"]
    seed_note = (f"البذرة الأصلية `{E.SPLIT_SEED}` حققت شرط وجود صف إيجابي في المجموعة المحجوزة."
                 if st["held_seed"] == E.SPLIT_SEED else
                 f"البذرة اتحرّكت من `{E.SPLIT_SEED}` إلى `{st['held_seed']}` لوجود صف إيجابي في المجموعة المحجوزة (حسب الشرط المكتوب).")
    names = {"rule": "القاعدة البسيطة (2)", "lr": "اللوجستي", "gb": "الـGB"}
    if prod == "rule":
        adopt_txt = "الموديلات ما كسبتش القاعدة في recall@8 والـlead في الرؤيتين معًا (والتعادل بيروح للقاعدة)، فـ**القاعدة البسيطة (2) هي المنتج**."
    else:
        adopt_txt = f"**{names[prod]}** كسب القاعدة في recall@8 والـlead في الرؤيتين، فهو المنتج."
    sens = R.md_table(pd.DataFrame([sens_row("الرئيسي: N=8، القمر من غير تأخير", res), sens_row("N=5", res5),
                                    sens_row("تأخير ربع في إشارات القمر (N=8)", res_lag)]))
    dec_rows = []
    for m, nm in (("lr", "لوجستي"), ("gb", "GB")):
        w = dec[m]["wins"]
        yn = lambda b: "كسب" if b else "ما كسبش"
        dec_rows.append({"الموديل": nm, "recall@8 زمني": yn(w["time"]["recall"]), "lead زمني": yn(w["time"]["lead"]),
                         "recall@8 مكمّل": yn(w["ext"]["recall"]), "lead مكمّل": yn(w["ext"]["lead"]), "القرار": "معتمد" if dec[m]["adopt"] else "مش معتمد"})
    rnd_t, rnd_x = res["random_time"]["recall"][0], res["random_ext"]["recall"][0]
    md = f"""# تقرير الإنذار المبكر (EW_REPORT): {facts['n_compounds']} كمبوند، حتى {facts['last_cutoff']}

> **Synthetic - for training only. النتايج دي على داتا مولّدة إحنا كتبنا آلياتها (R2).** بتثبت **الآلية** (إشارات داخلية + قمر ← تنبيه قبل التعثر بشهور) و**قيمة الداتا**، ومش دقة في العالم الحقيقي، وما تتقالش كأن "الموديل بيتنبأ بالتعثر بدقة X". أكواد بس، مفيش أي اسم كمبوند أو مطوّر. البروتوكول اتكتب قبل أي نتيجة: `EW_PROTOCOL.md`.

## 1. الخلاصة
- {adopt_txt} القاعدة = الأسوأ بين مستوى R1 ومحفزات B (غطاء 2184، أقساط الأرض، الشكاوى، فجوة المخطط والمعلن).
- **الاختبار الزمني** ({facts['test_period']}، {pos_t} صف إيجابي، {ev_t} حدث بداية تعثر): القاعدة (2) جابت **{R.pct(t.loc['rule', 'recall'])}** recall@{res['n']} ({int(t.loc['rule', 'tp'])} من {pos_t}) وprecision {R.pct(t.loc['rule', 'precision'])} (السقف الممكن {R.pct(ceiling)} من عدد الإيجابيات وسعة القوائم الفعلية)، مقابل **{R.pct(t.loc['sat', 'recall'])}** لقاعدة القمر وحده و{R.pct(rnd_t)} لـtop-{res['n']} عشوائي.
- **الرؤية المكمّلة** ({facts['n_cutoffs']} تاريخ حساب، {facts['all_events']} أحداث): قاعدة القمر وحده {R.pct(x.loc['sat', 'recall'])} (العشوائي {R.pct(rnd_x)}) وفاتها {int(x.loc['sat', 'events'] - x.loc['sat', 'events_caught'])} من {int(x.loc['sat', 'events'])} أحداث، والقاعدة (2) {R.pct(x.loc['rule', 'recall'])}، والـGB {R.pct(x.loc['gb', 'recall'])}، واللوجستي {R.pct(x.loc['lr', 'recall'])}.
- **قيمة الإشارات الداخلية والقمر** تتقارن في جدول ablation، بالاسترجاع وزمن الإنذار والإنذارات الكاذبة. أي مكسب هنا يخص آليات البيانات المولّدة في النطاق الحالي.
- **القرار على عينة صغيرة:** جدول الحساسية (القسم 8) يعرض أثر تغيير N وتأخير القمر. في الاختبار {ev_t} حدث بداية تعثر فقط، فلا نعتبر فروق الأداء إثباتًا لدقة تشغيلية.

## 2. الإعداد (مختصر، التفاصيل في البروتوكول)
- {facts['n_compounds']} كمبوند × {facts['n_cutoffs']} تاريخ حساب (نهاية كل ربع {facts['first_cutoff']}–{facts['last_cutoff']}). الهدف `label_distress_next_6m`. الميزات من داتا ≤ تاريخ الحساب (اختبار وحدة بيبوّظ الداتا بعد التاريخ ويتأكد إن الميزات ما اتغيّرتش)، و`reported_pct` بعد `report_date` بس. الرصيد بالألف (العيب 1) اتصلّح من الداتا نفسها: {st['fixed']} صف.
- تدريب ≤ {E.TRAIN_LAST}، **embargo 2025Q1**، اختبار {facts['test_period']} ({facts['test_rows']} صف غير مقطوع)، {facts['last_cutoff']} للقائمة الحية والأحداث (الليبل مقطوع).
- فصل المطوّرين: {held} ({held_codes}).

### سجل الانحرافات عن البروتوكول (اتحدّدوا في الكود قبل أول تشغيل)
1. **embargo 2025Q1** (مذكور في البروتوكول): التدريب ≤ 2024Q4 بدل ≤ 2025Q1.
2. **seed فصل المطوّرين:** {seed_note}
3. **حجم القائمة في فصل المطوّرين:** المجموعة {n_held} كمبوندات بس، فالـN اتقاس بالنسبة ({res['n']} × {n_held}/{facts['n_compounds']}) = **{res['n_dev']}** (البروتوكول ما حددش التقريب).
4. **lead time** بيتحسب لأبكر تاريخ حساب في آخر 12 شهر كان فيه الكمبوند في القائمة، فاستمرار كمبوند في القائمة بعد تعثر سابق ممكن يضخّم زمن الإنذار لحدث لاحق.

## 3. المقارنة الرئيسية: اختبار زمني ({facts['test_period']})، قائمة {res['n']} من {facts['n_compounds']}
{R.comparison_table(res['time'], keys, res['random_time'])}

أحداث الاختبار: {facts['test_events_text']}. فيه {facts['test_positives']} صف إيجابي، منهم {facts['test_current_rows']} صف متعثر بالفعل عند تاريخ الحساب (الأكواد: {facts['test_current_codes']}). الاسترجاع على الصفوف بيشمل المتعثر الحالي؛ الاسترجاع على صفوف الـonset الجديد ({facts['test_new_rows']}) وأحداث البداية أقرب لسؤال الإنذار المبكر.

### نمط التنبيه (القاعدة: مستوى ≤ 2، المحفز B: أي محفز، الموديل: احتمال ≥ 0.5)
{R.alert_table(res['time'], ['sat', 'b', 'rule', 'lr', 'gb'])}

في نمط التنبيه القاعدة (2) بتلتقط {R.pct(t.loc['rule', 'alert_event_recall'])} من الأحداث وبتنبّه على {R.num(t.loc['rule', 'alert_alerts_per_q'])} كمبوند من {facts['n_compounds']} في الربع في المتوسط. نقارن عدد التنبيهات بسعة التفتيش {res['n']}؛ القائمة المحدودة (top-N) هي المقارنة عند ميزانية ثابتة.

## 4. فصل المطوّرين (موديل متدرّب من غير {held}، متقيّم عليهم)
المجموعة {n_held} كمبوندات ({held_codes})، قائمة {res['n_dev']}، {facts['held_positives']} صف إيجابي و{facts['held_events']} حدث بداية. الأعداد محدودة؛ **الجدول لا يكفي لاستنتاج أداء قابل للتعميم**.
{R.comparison_table(res['dev'], keys)}

## 5. الرؤية المكمّلة: طيّات المطوّرين على كل التواريخ ({facts['all_events']} أحداث)
الزمن مش محترم هنا (التدريب على تواريخ أحدث لمطوّرين تانيين)، فالأرقام قد تكون أكتر تفاؤلًا للموديلات من الاختبار الزمني. القواعد من غير تدريب فأرقامها محسوبة على {facts['n_cutoffs']} تاريخ.
{R.comparison_table(res['ext'], keys, res['random_ext'])}

## 6. Lead time
![lead time](ew/lead_time.png)

{R.md_table(pv)}

(الأرقام = شهور قبل بداية التعثر، بحد أقصى 12. الموديلات بتتضخم لما الكمبوند بيفضل في القائمة بعد تعثر سابق.)

## 7. المعايرة
![calibration](ew/calibration.png)

Brier: لوجستي {cal['lr'][0]:.3f} (زمني) / {cal['lr'][1]:.3f} (مكمّل)، GB {cal['gb'][0]:.3f} / {cal['gb'][1]:.3f}. للمقارنة الوصفية، توقّع ثابت بنسبة الإيجابيات المرصودة في الاختبار ({R.pct(facts['test_rate'], 1)}) يعطي Brier {R.num(facts['constant_brier'], 3)}؛ النسبة دي محسوبة بعد الاختبار وليست baseline متاحًا مسبقًا. الاحتمالات مش معايرة (`class_weight` متوازن بيرفعها) وعدد الصفوف في كل شريحة صغير، فبتتستخدم للترتيب مش كاحتمال حقيقي. القاعدة مش احتمال فمالهاش معايرة.

## 8. قاعدة المنتج والحساسية
{R.md_table(pd.DataFrame(dec_rows))}

{adopt_txt}

{sens}

(كل خلية = recall@N / ميديان lead بالشهور.) الحساسية تعرض تغييرات N وتأخير ربع في القمر، على {facts['n_compounds']} كمبوند و{facts['all_events']} أحداث. **القرار المعتمد هو الرئيسي (أول صف)** لأنه المكتوب في البروتوكول قبل النتايج؛ جداول الحساسية لا تستخدم لاختيار إعداد بعد النتيجة.

## 9. أنهي ميزات مهمة؟
**لوجستي (معاملات standardized، تدريب ≤ 2024Q4):**
{imp_lr}

**GB (permutation importance على صفوف الاختبار):**
{imp_gb}

- ترتيب الميزات الفعلي ومعاملاتها في الجدولين أعلاه. حجم التدريب {facts['train_positives']} صف إيجابي من {facts['train_positive_codes']} كمبوندات؛ إشارة معامل وحدها لا تثبت علاقة سببية.
- **تنبيه:** `land_late` عداد تراكمي بيطلع عالي في الكمبوندات اللي المولّد بيوقّفها، فأهميته جزء منها من تصميم المولّد.

### أثر مجموعات الميزات (ablation)
{ablation_table(res['time'], res['ext'])}

نقارن القمر وحده والداخلي وحده والدمج من الجدول، لكل موديل ورؤية. التعادل في الاسترجاع لا يعني أن الدمج أضاف دقة، وأهمية البيانات الداخلية هنا تخص آليات المولّد.

## 10. قوايم الدورة: أعلى {res['n']} في كل تاريخ حساب (المنتج: {names[prod]})
"✓" = صف إيجابي (هيتعثر في 6 شهور أو متعثر)، "؟" = ليبل مقطوع. ترتيب القاعدة: المستوى ثم عدد محفزات B ثم K2 ثم K3، والموديل بترتيب احتماله؛ التعادل بالكود. القائمة قد تضم غير المتعثرين لاستكمال السعة، وجملة السبب توضح المحفزات.
{lists_md(d, score, E.N_DEFAULT, p_col)}

## 11. حدود
1. **داتا مولّدة بآليات إحنا كتبناها:** القصص طالعة من إشارات القمر الحقيقية، والتحصيل والفجوة والأقساط مولّدة. التجربة تثبت اتساق الآلية، مش إن الإنذار هيشتغل على داتا الشركة.
2. **حجم صغير جدًا:** {facts['n_compounds']} كمبوند، {facts['all_positive_codes']} فيهم صف إيجابي؛ {facts['train_positives']} صف إيجابي في التدريب (من {facts['train_positive_codes']} كمبوندات)، و{pos_t} في الاختبار، و{ev_t} حدث بداية في الاختبار و{facts['all_events']} في المكمّل. إصابة صف إيجابي واحدة تغيّر الاسترجاع {R.num(facts['one_hit_points'])} نقطة مئوية. مفيش فواصل ثقة ولا اختبار دلالة غير المقارنة بالعشوائي.
3. **الليبل بيفضل 1 طول التعثر،** فالاسترجاع على الصفوف بيكافئ مسك المتعثر الحالي. صفوف الـonset الجديد ({facts['test_new_rows']}) أقرب للإنذار المبكر.
4. **فصل المطوّرين** اتقيّم على {n_held} كمبوندات و{facts['held_positives']} صف إيجابي و{facts['held_events']} حدث؛ الحجم لا يكفي لاستنتاج أداء عام.
5. **افتراضات توقيت:** بيانات الشهر متاحة آخره، وربع القمر متاح عند نهايته (حساسية تأخير ربع موجودة).
6. **ربط القمر بالتعثر جزء منه بتصميم المولّد** (القصة بتتبني من A و K2 الحقيقيين)، فالنتيجة بتدل على الآلية مش على قيمة القمر الحقيقية.
7. **الرؤية المكمّلة غير زمنية** (تسرّب بين مطوّرين على مستوى الزمن)، فهي دليل مساند مش رقم رئيسي.

## 12. الملفات
`app_data/ew/`: `comparison_*.csv` (كل الأنماط والحساسيات)، `topn_lists.csv`، `event_leads.csv`، `feature_importance.csv`، `lead_time.png`، `calibration.png`. الكود: `src/analysis/early_warning.py` (+ `ew_features.py` و`ew_eval.py` و`ew_report.py`)، واختباراته `tests/test_early_warning.py`. الأمر: `uv run --with matplotlib python -m src.analysis.early_warning`.
`run_provenance.json` يسجل بصمات ملفات المدخلات والكود ونطاق التشغيل؛ بيانات الإجابة الخاصة لا تنسخ فيه، بل بصمتها فقط. `app_data/manifest.csv` يتحدّث بعد اكتمال التشغيل بنجاح.
جدول التدريب الثنائي محفوظ في `private/ml_dataset.parquet`، ومعه قائمة X والهدف والتقسيم والبصمات في `private/ml_dataset_metadata.json`. `app_data/ew/dataset_summary.json` يعرض المجاميع فقط. المتغيرات الخاصة وحالة الإنذار والتنبؤات ليست ضمن X.
"""
    (APP / "EW_REPORT.md").write_text(md, encoding="utf-8")
    if input_hashes() != hashes:
        raise RuntimeError("EW inputs changed during evaluation; outputs must be regenerated")
    provenance = run_provenance(st, hashes)
    provenance["training_output_sha256"] = export_training_dataset(st, hashes)
    (OUT / "run_provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    from src.pipeline.run_all import manifest
    manifest()
    print("report written; product:", prod)


if __name__ == "__main__":
    run()
