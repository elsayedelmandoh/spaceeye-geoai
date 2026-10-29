"""Prepare component inputs: complaint labels, inspection contexts and hypothetical review data.

No model fitting,LLM calls or actual field-inspection claims. Existing source tables are read only.
Run: uv run --locked --offline python -m src.pipeline.component_data
"""

import hashlib
import json
import re
import unicodedata

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from src.generator.complaints import BODY, CATS, CLOSE, OPEN, TYPO
from src.generator.defects import PHONE
from src.generator.simulate import write_parquet
from src.pipeline import gates, run_all
from src.pipeline.common import APP, BASE_DIR, CFG, PRIVATE, REAL, qend, qindex

OUT = APP / "component_data"
LABEL = CFG["generator"]["label"]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def records(frame):
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def normalized(text):
    text = unicodedata.normalize("NFKC", text).translate(str.maketrans({"ة": "ه", "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ؤ": "و", "ئ": "ي"}))
    return re.sub(r"[\s،,.!?؟]+", " ", text).strip()


def complaint_dataset(clean, gold):
    """Gold is joined for target/group creation only. No hidden cause/code enters X."""
    data = clean.loc[clean.text_ar.fillna("").str.strip().ne("")].copy()
    data = data.merge(gold[["complaint_id", "true_category", "duplicate_of"]], on="complaint_id", validate="one_to_one")
    data = data.rename(columns={"category": "desk_category", "true_category": "label_category"}).sort_values("complaint_id").reset_index(drop=True)
    if not data.label_category.isin(CATS).all() or data.text_ar.map(lambda t: bool(PHONE.search(t))).any():
        raise ValueError("Invalid complaint labels or unmasked phone")
    parents = list(range(len(data)))

    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    tokens = {}
    bodies = [(f"body:{cat}:{i}", normalized(text)) for cat, texts in BODY.items() for i, text in enumerate(texts)]
    duplicate = gold.set_index("complaint_id").duplicate_of.to_dict()
    for i, row in data.iterrows():
        text = normalized(row.text_ar)
        family, seen = row.complaint_id, set()
        while family not in seen and pd.notna(duplicate.get(family)):
            seen.add(family)
            family = str(duplicate[family])
        keys = ["text:" + text, "family:" + family] + [key for key, body in bodies if body in text]
        for key in keys:
            if key in tokens:
                a, b = root(i), root(tokens[key])
                parents[max(a, b)] = min(a, b)
            else:
                tokens[key] = i
    data["group_id"] = [f"G{root(i):04}" for i in range(len(data))]
    data["split"] = "train"
    if data.group_id.nunique() >= 3:
        trainval, test = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=int(CFG["seed"])).split(data, groups=data.group_id))
        data.loc[test, "split"] = "test"
        if data.iloc[trainval].group_id.nunique() >= 2:
            _train, validation = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=int(CFG["seed"])).split(data.iloc[trainval], groups=data.iloc[trainval].group_id))
            data.loc[trainval[validation], "split"] = "validation"
    data["synthetic_label"] = LABEL
    return data.drop(columns="duplicate_of")


def complaint_benchmark():
    """Separate synthetic capability corpus. Allocate body families before text generation.

    No copied template family crosses splits;secondary mixed topics come from
    that same split. Do not mix this corpus with the observed-feed export.
    """
    rng = np.random.default_rng(np.random.SeedSequence([int(CFG["seed"]), 991]))
    families = {s: [] for s in ("train", "validation", "test")}
    for cat in CATS:
        order = rng.permutation(len(BODY[cat]))
        n_train = max(1, int(len(order) * 0.6))
        n_validation = max(1, int(len(order) * 0.2))
        for i, body_index in enumerate(order):
            split = "train" if i < n_train else "validation" if i < n_train + n_validation else "test"
            families[split].append((f"{cat}-{body_index}", cat, BODY[cat][body_index]))
    rows, seen = [], set()
    for split, templates in families.items():
        for family, cat, body in templates:
            for _ in range(8):
                while True:
                    parts = [str(rng.choice(OPEN)), body]
                    used = [family]
                    if rng.random() < 0.25:
                        others = [(f, b) for f, c, b in templates if c != cat]
                        extra, text = others[int(rng.integers(len(others)))]
                        parts.append(text)
                        used.append(extra)
                    parts.append(str(rng.choice(CLOSE)))
                    text = "، ".join(parts)
                    if rng.random() < 0.25:
                        for a, b in TYPO:
                            text = text.replace(a, b)
                    key = normalized(text)
                    if key not in seen:
                        seen.add(key)
                        break
                rows.append({"complaint_id": f"SYN-B{len(rows) + 1:04}", "text_ar": text, "label_category": cat,
                             "split": split, "template_ids": ";".join(used), "mixed_topic": len(used) > 1,
                             "origin": "generated capability corpus;not an operational complaint", "synthetic_label": LABEL})
    return pd.DataFrame(rows)


def synthetic_visits(kpi, truth, comp):
    """Synthetic cutoff states carried to a planned visit,not measured field observations."""
    rows = []
    units = comp.set_index("code").units
    for r in kpi.loc[kpi.quarter.ge("2023Q1") & kpi.cycle_rank.notna()].sort_values(["quarter", "code"]).itertuples():
        cutoff = qend(r.qi)
        rng = np.random.default_rng(np.random.SeedSequence([int(CFG["seed"]), 781, int(r.code[1:]), r.qi]))
        choices = [cutoff + pd.Timedelta(days=d) for d in range(5, 15) if (cutoff + pd.Timedelta(days=d)).weekday() not in (4, 5)]
        date = choices[int(rng.integers(len(choices)))]
        history = truth.loc[truth.code.eq(r.code) & truth.month.le(cutoff.strftime("%Y-%m"))].sort_values("month")
        if history.empty:
            continue
        last = history.iloc[-1]
        gain = float(last.true_progress_pct - history.true_progress_pct.iloc[max(0, len(history) - 6)])
        missed = bool(rng.random() < 0.08)
        result = "not_done" if missed else "complete" if last.handed_over_units >= units[r.code] else "stalled" if gain < 1 else "progressing"
        note = {"not_done": "Visit rescheduled; no observation recorded.", "complete": "Full handover assumed from the generated cutoff state; request document confirmation.", "stalled": "Limited recent site progress assumed; request contractor work plan.", "progressing": "Ongoing site progress assumed; compare current plan and supervisor report."}[result]
        rows.append({"visit_id": f"V-{r.quarter}-{r.code}", "code": r.code, "source_quarter": r.quarter, "visit_date": date,
                     "inspector_code": f"I{int(rng.integers(1, 4)):02}", "result": result, "note": note,
                     "state_basis": "generated cutoff state carried forward; not a real field measurement", "origin": "generated", "synthetic_label": LABEL})
    return pd.DataFrame(rows)


def priority_paths(paths, states, kpi, financial, complaints, comp):
    """Frozen observed context plus declared projected-B5 rule; no future observation prediction."""
    cutoff = states.cutoff.iloc[0]
    quarter = str(pd.Period(cutoff, "M").asfreq("Q"))
    context = kpi.loc[kpi.quarter.eq(quarter)].set_index("code")
    known = financial.loc[financial.month.le(cutoff)].sort_values("month")
    state = states.set_index("code")
    rows, b3_cache = [], {}
    for r in paths.itertuples():
        observed = context.loc[r.code]
        finance = known.loc[known.code.eq(r.code)].iloc[-1]
        month_step = pd.Period(r.month, "M").ordinal - pd.Period(cutoff, "M").ordinal
        plan = min(100.0, float(finance.planned_pct) + state.loc[r.code, "capacity_pct_month"] * month_step)
        gap = plan - r.simulated_progress_pct
        b1 = bool(finance.cover_required_egp > 0 and finance.cover_balance_egp < finance.cover_required_egp)
        b2 = bool(finance.land_months_late >= 2)
        if r.code not in b3_cache:
            my = known.loc[known.code.eq(r.code)]
            history_rates = []
            for month in pd.period_range(CFG["generator"]["start"], cutoff, freq="M"):
                end = month.end_time.normalize() + pd.Timedelta(days=1)
                count = complaints.loc[complaints.code.eq(r.code) & complaints.created_at.ge(end - pd.Timedelta(days=90)) & complaints.created_at.lt(end)].shape[0]
                sold = my.loc[my.month.eq(str(month)), "units_sold"]
                history_rates.append(1000 * count / sold.iloc[-1] if len(sold) and sold.iloc[-1] > 0 else np.nan)
            past = pd.Series(history_rates[:-1]).dropna()
            rate = history_rates[-1]
            b3_known = len(past) >= 12 and pd.notna(rate)
            b3 = bool(b3_known and ((past < rate).sum() + 0.5 * (past == rate).sum()) / len(past) >= 0.95)
            b3_cache[r.code] = (b3_known, b3)
        b3_known, b3 = b3_cache[r.code]
        level = observed.level
        if observed.K4 and pd.notna(level):
            level = min(int(level), 2) if b1 or b2 or b3 or gap > 20 else int(level)
            if b1 and pd.notna(observed.K2) and observed.K2 >= 2:
                level = 1
            if observed.may_be_complete:
                level = max(level, 3)
        rows.append({"code": r.code, "cutoff": cutoff, "month": r.month, "scenario_id": r.scenario_id,
                     "frozen_public_level": observed.level, "K2_frozen": observed.K2, "K3_frozen": observed.K3,
                     "frozen_B1": b1, "frozen_B2": b2, "frozen_B3": b3, "B3_assessable": b3_known,
                     "projected_plan_pct": plan, "simulated_progress_pct": r.simulated_progress_pct, "projected_gap_pp": gap,
                     "projected_B5": gap > 20, "hypothetical_level": level, "origin": "generated/derived hypothetical rule", "synthetic_label": LABEL})
    out = pd.DataFrame(rows)
    out["eligible_rank"] = pd.array([pd.NA] * len(out), dtype="Int64")
    for _, group in out.loc[out.hypothetical_level.notna() & out.hypothetical_level.le(3)].groupby(["scenario_id", "month"]):
        order = group.assign(k2=group.K2_frozen.fillna(0)).sort_values(["hypothetical_level", "k2", "K3_frozen", "code"], ascending=[True, False, False, True])
        out.loc[order.index, "eligible_rank"] = range(1, len(order) + 1)
    out["selected"] = out.eligible_rank.le(CFG["cycle_capacity"]).fillna(False)
    baseline = out.loc[out.scenario_id.eq("baseline"), ["code", "month", "hypothetical_level", "eligible_rank", "selected"]].rename(columns={c: "baseline_" + c for c in ["hypothetical_level", "eligible_rank", "selected"]})
    out = out.merge(baseline, on=["code", "month"], validate="many_to_one")
    out["selection_changed"] = out.selected != out.baseline_selected
    out["level_changed"] = out.hypothetical_level.fillna(99) != out.baseline_hypothetical_level.fillna(99)
    return out


def inspection_context(comp, sat, yearly, statements, kpi, financial, complaints, rules, sources, visits, code, quarter, patterns):
    asof = qend(qindex(quarter)) + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
    mine = kpi.loc[kpi.code.eq(code) & kpi.quarter.eq(quarter)]
    register = comp.loc[comp.code.eq(code)].drop(columns=[c for c in comp if "deadline" in c or "handover" in c])
    facts = statements.loc[statements.code.eq(code) & pd.to_datetime(statements.published_date).le(asof)].copy()
    evidence = []
    for r in facts.itertuples():
        source = sources.loc[sources.code.eq(code) & sources.record_id.eq(r.record_id) & pd.to_datetime(sources.published_date).le(asof)]
        url = str(source.url.iloc[0]) if len(source) and pd.notna(source.url.iloc[0]) else None
        safe = bool(url and not gates._hits(url, patterns))
        evidence.append({"statement_id": r.statement_id, "record_id": r.record_id, "published_date": str(r.published_date),
                         "url": url if safe else None, "link_status": "included" if safe else "unavailable_or_withheld_by_code_only_policy"})
    finance = financial.loc[financial.code.eq(code) & financial.month.le(asof.strftime("%Y-%m"))].tail(1)
    finance = finance.drop(columns=[c for c in ("status_level", "warning_issued") if c in finance])
    cmp_ = complaints.loc[complaints.code.eq(code) & complaints.created_at.le(asof)]
    visit = visits.loc[visits.code.eq(code) & visits.visit_date.le(asof)]
    return {"code": code, "quarter": quarter, "asof": asof.isoformat(),
            "public_evidence": {"register": records(register), "register_limit": "Static register includes generated fields with origins;unknown historical publication dates are not inferred.",
                                "kpis": records(mine), "statements": records(facts), "sources": evidence,
                                "activity_history": records(sat.loc[sat.code.eq(code) & sat.qi.le(qindex(quarter)), ["quarter", "activity_prob", "active", "K4"]]),
                                "annual_context": records(yearly.loc[yearly.code.eq(code) & yearly.year.lt(asof.year + (asof.month == 12))]),
                                "rules": records(rules)},
            "generated_operations": {"synthetic_label": LABEL, "latest_financial": records(finance), "complaint_count": len(cmp_),
                                     "latest_masked_texts": records(cmp_.tail(5)), "synthetic_visits": records(visit)},
            "images": {"status": "not included;no capture dates or image judgments invented"},
            "questions": ["Confirm current site activity and the supervisor report.", "Reconcile the first published handover promise with the latest approved schedule.", "Confirm utility/occupancy and handover evidence on site."],
            "guardrails": ["Cite statement/record IDs and retain origin labels.", "Do not describe synthetic visits as real field evidence.", "Do not infer actual developer distress,completion percentage or assessed fines.", "No hidden answer key or future target is an input."]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [REAL / f"{name}.parquet" for name in ["compounds", "sat_quarterly", "sat_yearly", "statements", "kpi_values", "rules"]]
    paths += [APP / name for name in ["sim_clean/fin_monthly.parquet", "sim_clean/complaints.parquet", "scenarios/paths.parquet", "scenarios/initial_state.parquet"]]
    paths += [PRIVATE / name for name in ["answer_key.parquet", "answer_key_complaints.parquet", "evidence_sources.csv"]]
    input_hashes = {p.relative_to(APP.parent).as_posix(): run_all.sha(p) for p in paths}
    inputs = {name: pd.read_parquet(REAL / f"{name}.parquet") for name in ["compounds", "sat_quarterly", "sat_yearly", "statements", "kpi_values", "rules"]}
    financial = pd.read_parquet(APP / "sim_clean/fin_monthly.parquet")
    complaints = pd.read_parquet(APP / "sim_clean/complaints.parquet")
    complaints.created_at = pd.to_datetime(complaints.created_at)
    gold = pd.read_parquet(PRIVATE / "answer_key_complaints.parquet")
    text_data = complaint_dataset(complaints, gold)
    benchmark = complaint_benchmark()
    visits = synthetic_visits(inputs["kpi_values"], pd.read_parquet(PRIVATE / "answer_key.parquet"), inputs["compounds"])
    priority = priority_paths(pd.read_parquet(APP / "scenarios/paths.parquet"), pd.read_parquet(APP / "scenarios/initial_state.parquet"), inputs["kpi_values"], financial, complaints, inputs["compounds"])
    for name, frame in [("complaints_training", text_data), ("complaints_benchmark", benchmark), ("synthetic_visits", visits), ("hypothetical_priorities", priority)]:
        write_parquet(frame, OUT / f"{name}.parquet")
        frame.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8-sig")
    patterns = gates._patterns(gates.forbidden_names())
    sources = pd.read_csv(PRIVATE / "evidence_sources.csv")[["code", "record_id", "published_date", "url"]]
    contexts = []
    for quarter in pd.period_range(CFG["generator"]["start"], CFG["generator"]["end"], freq="Q").astype(str):
        for code in sorted(inputs["compounds"].code):
            payload = inspection_context(inputs["compounds"], inputs["sat_quarterly"], inputs["sat_yearly"], inputs["statements"], inputs["kpi_values"], financial, complaints, inputs["rules"], sources, visits, code, quarter, patterns)
            path = f"inspection_contexts/{quarter}/{code}.json"
            write_json(OUT / path, payload)
            contexts.append({"code": code, "quarter": quarter, "file": path, "asof": payload["asof"]})
    pd.DataFrame(contexts).to_csv(OUT / "inspection_index.csv", index=False)
    splits = {s: {"rows": len(g), "classes": g.label_category.value_counts().to_dict(), "groups": int(g.group_id.nunique())} for s, g in text_data.groupby("split")}
    benchmark_counts = {s: {"rows": len(g), "classes": g.label_category.value_counts().to_dict()} for s, g in benchmark.groupby("split")}
    write_json(OUT / "complaints_benchmark_metadata.json", {"synthetic_label": LABEL, "features": ["text_ar"], "target": "label_category", "split_column": "split", "split_counts": benchmark_counts,
               "generation": "Existing Arabic body families split per class before generation;8variants per family,mixed topics only within the same split;fixed seed2026.",
               "limits": "Separate generated capability corpus,not real complaint evidence. Do not combine with observed-feed labeled texts because original template families overlap between corpora. Report synthetic results only."})
    write_json(OUT / "complaints_metadata.json", {"synthetic_label": LABEL, "features": ["text_ar"], "target": "label_category", "classes": CATS,
               "split_column": "split", "group_column": "group_id", "split_counts": splits, "label_source": "Existing synthetic category truth joined only to create target;no hidden cause/code exported.",
               "grouping": "Connected components of all matched normalized body templates and duplicate families;no such group crosses a split. Fixed seed2026,not tuned to model scores.",
               "limits": "Synthetic-template capability data,not independent real complaint accuracy. Desk category is noisy and excluded from X;all other fields are keys/evaluation metadata. Grouped small holdouts do not contain every class;use the SEPARATE benchmark for five-class capability work without mixing corpora."})
    checks = {"complaint_targets_known": text_data.label_category.isin(CATS).all(), "complaint_groups_do_not_cross_splits": text_data.groupby("group_id").split.nunique().eq(1).all(),
              "text_phones_masked": not text_data.text_ar.map(lambda t: bool(PHONE.search(t))).any(), "contexts_180": len(contexts) == 180,
              "priority_unique_keys": not priority.duplicated(["code", "month", "scenario_id"]).any(),
              "priority_selection_capacity": priority.groupby(["scenario_id", "month"]).selected.sum().le(CFG["cycle_capacity"]).all(),
              "visit_origin_generated": visits.origin.eq("generated").all(), "visit_results_known": visits.result.isin(["progressing", "stalled", "complete", "not_done"]).all(),
              "visit_keys_unique": not visits.visit_id.duplicated().any()}
    template_sets = {s: set(";".join(g.template_ids).split(";")) for s, g in benchmark.groupby("split")}
    checks["benchmark_templates_disjoint"] = not any(a & b for i, a in enumerate(template_sets.values()) for j, b in enumerate(template_sets.values()) if i < j)
    checks["benchmark_all_classes_per_split"] = all(set(g.label_category) == set(CATS) for _, g in benchmark.groupby("split"))
    checks["source_tables_unchanged"] = input_hashes == {p.relative_to(APP.parent).as_posix(): run_all.sha(p) for p in paths}
    if not all(checks.values()):
        raise RuntimeError(f"Component data checks failed: {checks}")
    scan = gates.g_no_names(root=OUT, extra=[])
    if scan["status"] != "PASS":
        raise RuntimeError("Component name gate: " + scan["value"])
    write_json(OUT / "metadata.json", {"status": "PASS", "synthetic_label": LABEL, "checks": {k: bool(v) for k, v in checks.items()},
               "counts": {"complaints_training": len(text_data), "complaints_benchmark": len(benchmark), "inspection_contexts": len(contexts), "synthetic_visits": len(visits), "hypothetical_priorities": len(priority)},
               "complaint_split_counts": splits, "definition": "data/COMPONENT_DATA_PROTOCOL.md",
               "input_sha256": input_hashes,
               "priority_rule": "Frozen cutoff public/B1/B2/B3context plus projected B5gap>20;completion cap and capacity4. Not a forecast of future public observations or validated accuracy.",
               "visits": "Synthetic exercise records,not real fieldwork and not independent validation or ML features.",
               "code_sha256": hashlib.sha256(__import__("pathlib").Path(__file__).read_bytes()).hexdigest()})
    meanings = {
        "complaint_id": "Stable complaint identifier;SYN-B IDs belong only to the generated benchmark.", "code": "Compound code,key only,not text model input.",
        "created_at": "Synthetic complaint recording time.", "channel": "Recorded channel,key/context only,not text model input.",
        "text_ar": "Masked Arabic complaint;the sole classification input.", "desk_category": "Noisy recorded category,excluded from X.",
        "label_category": "Target category only;five classes,not an input.", "group_id": "Connected template/duplicate-family group;never crosses a split.",
        "split": "Fixed train/validation/test assignment;not a model feature.", "template_ids": "Generation-family IDs;disjoint between benchmark splits,not model inputs.",
        "mixed_topic": "Secondary topic present;primary body determines label,evaluation metadata only.",
        "visit_id": "Unique generated inspection record,key only.", "source_quarter": "Quarter whose generated state is carried to the assumed visit.",
        "visit_date": "Generated working date5–14days after cutoff,not an actual visit.", "inspector_code": "Fictional inspector code,I01–I03.",
        "result": "Generated progressing/stalled/complete/not_done status;not independent field validation.", "note": "Generated follow-up note,not a factual field report.",
        "state_basis": "Explicitly generated cutoff-state carry-forward.", "cutoff": "Last observed month,held fixed for all forward paths.",
        "month": "Forward simulated month.", "scenario_id": "Intervention ID:baseline,collections_drop,usd_cost_shock.",
        "frozen_public_level": "Public priority at cutoff,not future observed priority.", "K2_frozen": "Cutoff inactivity count,held fixed.", "K3_frozen": "Cutoff delivery clock,held fixed.",
        "frozen_B1": "Cutoff financial guarantee below required amount,held fixed;operating cash is never used as the guarantee.",
        "frozen_B2": "Cutoff recorded land arrears>=2months,held fixed.", "frozen_B3": "Cutoff complaint-history percentile>=95%with12valid prior months,held fixed.",
        "B3_assessable": "Whether sufficient valid complaint-rate history exists at cutoff.", "projected_plan_pct": "Cutoff contractual plan plus declared monthly capacity times elapsed months,capped100.",
        "simulated_progress_pct": "Forward-engine simulated progress,not satellite completion measurement.", "projected_gap_pp": "Projected plan minus simulated progress,in percentage points.",
        "projected_B5": "Projected gap>20pp,using existing B5threshold.", "hypothetical_level": "Frozen public/financial rules plus projected B5;completion cap retained,not validated accuracy.",
        "eligible_rank": "Rank among hypothetical levels1–3,ordered by level,K2,K3,code.", "selected": "Rank is within capacity4.",
        "baseline_hypothetical_level": "Same-month baseline level for this compound.", "baseline_eligible_rank": "Same-month baseline eligible rank.",
        "baseline_selected": "Whether this compound is selected in the same-month baseline.", "selection_changed": "Selection differs from same-month baseline.",
        "level_changed": "Level differs from same-month baseline.", "origin": "Generated/derived provenance,not actual observations.", "synthetic_label": LABEL,
    }
    for name, frame in [("complaints_training", text_data), ("complaints_benchmark", benchmark), ("synthetic_visits", visits), ("hypothetical_priorities", priority)]:
        doc = f"# {name}\n\n{LABEL}\n\n{len(frame)}rows. See COMPONENT_DATA_PROTOCOL.md for definitions and limits.\n\n| Column | Type | Meaning |\n| --- | --- | --- |\n"
        doc += "\n".join(f"| {c} | {frame[c].dtype} | {meanings[c]} |" for c in frame)
        (OUT / "dictionaries").mkdir(exist_ok=True)
        (OUT / "dictionaries" / f"{name}.md").write_text(doc + "\n", encoding="utf-8")
        published = BASE_DIR / "data/dictionaries" / f"component_data__{name}.md"
        published.parent.mkdir(parents=True, exist_ok=True)
        published.write_text(doc + "\n", encoding="utf-8")
    pd.DataFrame([{"file": p.relative_to(OUT).as_posix(), "sha256": run_all.sha(p)} for p in sorted(OUT.rglob("*")) if p.is_file() and p.name != "manifest.csv"]).to_csv(OUT / "manifest.csv", index=False)
    print(json.dumps({"status": "PASS", "complaints": len(text_data), "split_counts": splits, "benchmark_counts": benchmark_counts, "contexts": len(contexts), "synthetic_visits": len(visits), "priority_rows": len(priority)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
