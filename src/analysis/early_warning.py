"""
propose: early-warning experiment on the generated data (EW_PROTOCOL.md): compare four methods, apply the product rule, write EW_REPORT.md.
input: app_data/sim, app_data/real, private/answer_key.parquet (labels for evaluation only).
output: app_data/EW_REPORT.md, app_data/ew/*.csv and *.png.
run: uv run --with matplotlib python -m src.analysis.early_warning
"""

import pandas as pd

from src.analysis import ew_eval as E
from src.analysis import ew_features as F
from src.analysis import ew_report as R
from src.pipeline.common import APP, PRIVATE

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
    pos_t, ev_t = int(t.loc["rule", "positives"]), int(t.loc["rule", "events"])
    ceiling = pos_t / (E.N_DEFAULT * len(E.TEST_LABEL_Q))
    piv = ev.pivot(index=["code", "onset"], columns="method", values="lead").reset_index()
    cau = ev.pivot(index=["code", "onset"], columns="method", values="caught").reset_index()
    pv = piv[["code", "onset"]].copy()
    for k in ("sat", "rule", "b", "lr", "gb"):
        pv[R.NAMES[k]] = ["فاتته" if not c else R.num(v, 0) for v, c in zip(piv[k], cau[k])]
    pv["فترة"] = ["اختبار" if pd.Period(o, "M") >= E.TEST_ONSET_FROM else "مكمّل" for o in pv["onset"]]
    imp_lr = R.md_table(pd.DataFrame({"الميزة": imp["lr"].head(8).index, "معامل (standardized)": [f"{v:+.2f}" for v in imp["lr"].head(8)]}))
    imp_gb = R.md_table(pd.DataFrame({"الميزة": imp["gb"].head(8).index, "permutation (average precision)": [f"{v:.3f}" for v in imp["gb"].head(8)]}))
    held = "، ".join(st["held"])
    n_held = d[d["developer"].isin(st["held"])]["code"].nunique()
    held_codes = "، ".join(sorted(d[d["developer"].isin(st["held"])]["code"].unique()))
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
        yn = lambda b: "كسب" if b else "ما كسبش"  # noqa: E731
        dec_rows.append({"الموديل": nm, "recall@8 زمني": yn(w["time"]["recall"]), "lead زمني": yn(w["time"]["lead"]),
                         "recall@8 مكمّل": yn(w["ext"]["recall"]), "lead مكمّل": yn(w["ext"]["lead"]), "القرار": "معتمد" if dec[m]["adopt"] else "مش معتمد"})
    rnd_t, rnd_x = res["random_time"]["recall"][0], res["random_ext"]["recall"][0]
    md = f"""# تقرير الإنذار المبكر (EW_REPORT): 26 أكتوبر 2026

> **Synthetic - for training only. النتايج دي على داتا مولّدة إحنا كتبنا آلياتها (R2).** بتثبت **الآلية** (إشارات داخلية + قمر ← تنبيه قبل التعثر بشهور) و**قيمة الداتا**، ومش دقة في العالم الحقيقي، وما تتقالش كأن "الموديل بيتنبأ بالتعثر بدقة X". أكواد بس، مفيش أي اسم كمبوند أو مطوّر. البروتوكول اتكتب قبل أي نتيجة: `EW_PROTOCOL.md`.

## 1. الخلاصة
- {adopt_txt} القاعدة = الأسوأ بين مستوى R1 ومحفزات B (غطاء 2184، أقساط الأرض، الشكاوى، فجوة المخطط والمعلن).
- **الاختبار الزمني** (2025Q2–2026Q1، {pos_t} صف إيجابي، {ev_t} حدث بداية تعثر): القاعدة (2) جابت **{R.pct(t.loc['rule', 'recall'])}** recall@8 ({int(t.loc['rule', 'tp'])} من {pos_t}) وprecision {R.pct(t.loc['rule', 'precision'])} (السقف الممكن {R.pct(ceiling)} لأن كل ربع فيه 3–4 إيجابيات بس)، مقابل **{R.pct(t.loc['sat', 'recall'])}** لقاعدة القمر وحده و{R.pct(rnd_t)} لـtop-8 عشوائي.
- **الرؤية المكمّلة** (11 تاريخ حساب، 6 أحداث): قاعدة القمر وحده {R.pct(x.loc['sat', 'recall'])} (العشوائي {R.pct(rnd_x)}) وفاتها {int(x.loc['sat', 'events'] - x.loc['sat', 'events_caught'])} من {int(x.loc['sat', 'events'])} أحداث، والقاعدة (2) {R.pct(x.loc['rule', 'recall'])}، والـGB {R.pct(x.loc['gb', 'recall'])}، واللوجستي {R.pct(x.loc['lr', 'recall'])}.
- **القمر وحده بيتأخر، والإشارات الداخلية هي اللي بتقود الإنذار المبكر** (أقساط الأرض والفجوة). ده متسق مع رسالة المشروع: القمر بيكشف "بيبني ولا لأ"، والإنذار المبكر بالتعثر محتاج داتا الشركة.
- **القرار مش مستقر:** الموديلات بتكسب في الرؤية المكمّلة وبتتعادل أو تخسر في الزمني، والنتيجة بتتقلب مع N وتأخير القمر (القسم 8). الفرق بين القاعدة والموديل جوه الضوضاء (حدثين وإصابة أو اتنين).

## 2. الإعداد (مختصر، التفاصيل في البروتوكول)
- 22 كمبوند × 11 تاريخ حساب (نهاية كل ربع 2023Q4–2026Q2). الهدف `label_distress_next_6m`. الميزات من داتا ≤ تاريخ الحساب (اختبار وحدة بيبوّظ الداتا بعد التاريخ ويتأكد إن الميزات ما اتغيّرتش)، و`reported_pct` بعد `report_date` بس. الرصيد بالألف (العيب 1) اتصلّح من الداتا نفسها: {st['fixed']} صف.
- تدريب ≤ 2024Q4، **embargo 2025Q1**، اختبار 2025Q2–2026Q1 (88 صف)، 2026Q2 للقائمة الحية والأحداث (الليبل مقطوع).
- فصل المطوّرين: {held} ({held_codes}).

### سجل الانحرافات عن البروتوكول (اتحدّدوا في الكود قبل أول تشغيل)
1. **embargo 2025Q1** (مذكور في البروتوكول): التدريب ≤ 2024Q4 بدل ≤ 2025Q1.
2. **seed فصل المطوّرين:** `20261026` ما طلّعش مطوّر معاه صف إيجابي في الاختبار، فاتحرّك لـ`{st['held_seed']}` (حسب الشرط المكتوب).
3. **حجم القائمة في فصل المطوّرين:** المجموعة {n_held} كمبوندات بس، فالـN اتقاس بالنسبة (8 × {n_held}/22) = **{res['n_dev']}** (البروتوكول ما حددش التقريب).
4. **lead time** بيتحسب لأبكر تاريخ حساب في آخر 12 شهر كان فيه الكمبوند في القائمة، فكمبوند فاضل في القائمة بسبب تعثر قديم (زي C07 بعد تعافيه) بيطلع له lead كبير. تضخيم معروف.

## 3. المقارنة الرئيسية: اختبار زمني (2025Q2–2026Q1)، قائمة 8 من 22
{R.comparison_table(res['time'], keys, res['random_time'])}

أحداث الاختبار: C07 (2026-09) و C14 (2026-08). 13 صف إيجابي منهم 3 كمبوندات كانت متعثرة قبل الاختبار (C01 و C09 و C20)، فالاسترجاع على الصفوف بيعكس "هل القائمة بتمسك المتعثرين فعلًا"، وrecall على الـonset الجديد (صفين) هو الاختبار الحقيقي للإنذار المبكر.

### نمط التنبيه (القاعدة: مستوى ≤ 2، المحفز B: أي محفز، الموديل: احتمال ≥ 0.5)
{R.alert_table(res['time'], ['sat', 'b', 'rule', 'lr', 'gb'])}

في نمط التنبيه القاعدة (2) بتمسك كل الأحداث لكن بتنبّه على {R.num(t.loc['rule', 'alert_alerts_per_q'], 0)} كمبوند من 22 كل ربع، وده أكتر من سعة التفتيش. فالقائمة المحدودة (top-N) هي الاستخدام العملي، والتنبيه من غير حد مش.

## 4. فصل المطوّرين (موديل متدرّب من غير {held}، متقيّم عليهم)
المجموعة {n_held} كمبوندات ({held_codes})، قائمة {res['n_dev']}، صف إيجابي واحد (C07 في 2026Q1) وحدث واحد. **مفيش استنتاج ممكن من الرقم ده**؛ بيتعرض لأن البروتوكول طلبه.
{R.comparison_table(res['dev'], keys)}

## 5. الرؤية المكمّلة: طيّات المطوّرين على كل التواريخ (6 أحداث)
الزمن مش محترم هنا (التدريب على تواريخ أحدث لمطوّرين تانيين)، فالأرقام أكتر تفاؤلًا للموديلات من الاختبار الزمني. القواعد من غير تدريب فأرقامها هي نفسها على الـ11 تاريخ.
{R.comparison_table(res['ext'], keys, res['random_ext'])}

## 6. Lead time
![lead time](ew/lead_time.png)

{R.md_table(pv)}

(الأرقام = شهور قبل بداية التعثر، بحد أقصى 12. الموديلات بتتضخم لما الكمبوند بيفضل في القائمة بعد تعثر سابق.)

## 7. المعايرة
![calibration](ew/calibration.png)

Brier: لوجستي {cal['lr'][0]:.3f} (زمني) / {cal['lr'][1]:.3f} (مكمّل)، GB {cal['gb'][0]:.3f} / {cal['gb'][1]:.3f}. للمرجع، توقّع ثابت بنسبة الإيجابيات في الاختبار (15%) Brier ≈ 0.126. الاحتمالات مش معايرة (`class_weight` متوازن بيرفعها) وعدد الصفوف في كل شريحة صغير، فبتتستخدم للترتيب مش كاحتمال حقيقي. القاعدة مش احتمال فمالهاش معايرة.

## 8. قاعدة المنتج والحساسية
{R.md_table(pd.DataFrame(dec_rows))}

{adopt_txt}

{sens}

(كل خلية = recall@N / ميديان lead بالشهور.) النتيجة بتتقلب مع اختيارات صغيرة (N=5 أو تأخير ربع في القمر)، وده تأكيد إن الفرق بين الموديل والقاعدة مش مستقر على داتا بالصغر ده (22 كمبوند، 6 أحداث). **القرار المعتمد هو الرئيسي (أول صف)** لأنه المكتوب في البروتوكول قبل النتايج.

## 9. أنهي ميزات مهمة؟
**لوجستي (معاملات standardized، تدريب ≤ 2024Q4):**
{imp_lr}

**GB (permutation importance على صفوف الاختبار):**
{imp_gb}

- أقساط الأرض المتأخرة (`land_late`) وفجوة المخطط والمعلن (`gap`) من أهم الميزات، وهي إشارات داخلية (ACUD-type) مش قمر. القمر (A و K2) وزنه قليل في GB، ومعامل اتجاه K2 في اللوجستي سالب (ضوضاء على 4 كمبوندات إيجابية في التدريب، مش تفسير).
- **تنبيه:** `land_late` عداد تراكمي بيطلع عالي في الكمبوندات اللي المولّد بيوقّفها، فأهميته جزء منها من تصميم المولّد.

### أثر مجموعات الميزات (ablation)
{ablation_table(res['time'], res['ext'])}

القمر وحده (قاعدة أو موديل) أضعف بوضوح من الداخلي وحده، والداخلي وحده بيوصل لمستوى الاتنين مع بعض أو أعلى. يعني **قيمة الداتا الداخلية في الإنذار المبكر واضحة، وإضافة القمر في الموديل ما حسّنتش الاسترجاع هنا**. من أسباب ده إن القمر بيتأخر عن التعثر المخفي: C09 اتعثر في 2024-09، وK2 بقى ≥ 1 في 2025Q2.

## 10. قوايم الدورة: أعلى 8 في كل تاريخ حساب (المنتج: {names[prod]})
"✓" = صف إيجابي (هيتعثر في 6 شهور أو متعثر)، "؟" = ليبل مقطوع. الترتيب: المستوى ثم عدد محفزات B ثم K2 ثم K3. محفز الفجوة (> 20 نقطة) بيطلع على أغلب الكمبوندات، ومحفز ساعة K3 بيدخّل كمبوندات تسليمها متأخر وكاشها كفاية (C10 و C15 و C18)، فالقائمة بتتملي بغير المتعثرين.
{lists_md(d, score, E.N_DEFAULT, p_col)}

## 11. حدود
1. **داتا مولّدة بآليات إحنا كتبناها:** القصص طالعة من إشارات القمر الحقيقية، والتحصيل والفجوة والأقساط مولّدة. التجربة تثبت اتساق الآلية، مش إن الإنذار هيشتغل على داتا الشركة.
2. **حجم صغير جدًا:** 22 كمبوند، 6 بس فيهم إيجابي، 12 صف إيجابي في التدريب (من 4 كمبوندات)، 13 في الاختبار (3 منهم متعثرين من قبل)، حدثين onset في الاختبار و6 في المكمّل. إصابة واحدة بتغيّر النسبة 8 نقاط. مفيش فواصل ثقة ولا اختبار دلالة غير المقارنة بالعشوائي.
3. **الليبل بيفضل 1 طول التعثر،** فالاسترجاع على الصفوف بيكافئ مسك المتعثر الحالي. الـonset الجديد (صفين) هو الأقرب للإنذار المبكر.
4. **فصل المطوّرين** اتقيّم على مجموعة صغيرة جدًا وصف إيجابي واحد: مفيش استنتاج.
5. **افتراضات توقيت:** بيانات الشهر متاحة آخره، وربع القمر متاح عند نهايته (حساسية تأخير ربع موجودة).
6. **ربط القمر بالتعثر جزء منه بتصميم المولّد** (القصة بتتبني من A و K2 الحقيقيين)، فالنتيجة بتدل على الآلية مش على قيمة القمر الحقيقية.
7. **الرؤية المكمّلة غير زمنية** (تسرّب بين مطوّرين على مستوى الزمن)، فهي دليل مساند مش رقم رئيسي.

## 12. الملفات
`app_data/ew/`: `comparison_*.csv` (كل الأنماط والحساسيات)، `topn_lists.csv`، `event_leads.csv`، `feature_importance.csv`، `lead_time.png`، `calibration.png`. الكود: `src/analysis/early_warning.py` (+ `ew_features.py` و`ew_eval.py` و`ew_report.py`)، واختباراته `tests/test_early_warning.py`. الأمر: `uv run --with matplotlib python -m src.analysis.early_warning`.
"""
    (APP / "EW_REPORT.md").write_text(md, encoding="utf-8")
    print("report written; product:", prod)


if __name__ == "__main__":
    run()
