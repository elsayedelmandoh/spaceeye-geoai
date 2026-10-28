"""Finish the imported-spec DATA contract from cached observations. No fitting or UI.

Run: uv run --locked --offline python -m src.pipeline.complete_data
The prior binary evaluation/export stays frozen; the expanded dataset is separate.
"""

import json
import math
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.analysis import ew_features as F
from src.generator import scenarios
from src.pipeline import build_real, gates, kpis, prepare_sim, run_all
from src.pipeline.common import APP, BASE_DIR, CFG, PRIVATE, REAL, qend, qindex

LABEL = CFG["generator"]["label"]
OUT = APP / "data_completion"


def write_table(frame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    table = table.replace_schema_metadata({**(table.schema.metadata or {}), b"synthetic_label": LABEL.encode()})
    pq.write_table(table, path)


def capacity_paths(kpi, n):
    """S3 is a stored re-ranking only. Never changes levels, cash or progress."""
    rows = []
    for quarter, group in kpi.groupby("quarter"):
        order = group[group.level.notna() & group.level.le(3)].assign(k2=lambda d: d.K2.fillna(0)).sort_values(
            ["level", "k2", "K3", "code"], ascending=[True, False, False, True])
        for scenario, cap in (("capacity_minus_2", max(1, n - 2)), ("baseline", n), ("capacity_plus_2", min(kpi.code.nunique(), n + 2))):
            ranks = {c: i + 1 for i, c in enumerate(order.code)}
            for r in group.itertuples():
                rank = ranks.get(r.code)
                rows.append({"quarter": quarter, "code": r.code, "scenario_id": scenario, "capacity": cap,
                             "eligible_rank": rank, "selected": rank is not None and rank <= cap, "level": r.level,
                             "origin": "derived", "assumption": True})
    return pd.DataFrame(rows)


def land_assumptions(comp, sat, statements):
    """Synthetic contracts bounded by known anchors, not newly discovered facts.

    Allocation dates use retrospective anchors and therefore never enter X or
    the public K6 clock. Price envelopes reflect contract vintage, not2026 price
    indiscriminately assigned to old land. Exact dates/rates remain assumptions.
    """
    rows = []
    for r in comp.itertuples():
        rng = np.random.default_rng(np.random.SeedSequence([int(CFG["seed"]), 905, int(r.code[1:])]))
        public = pd.to_datetime(statements.loc[statements.code.eq(r.code), "published_date"])
        starts = sat.loc[sat.code.eq(r.code) & sat.observed_start_quarter.notna(), "observed_start_quarter"]
        anchors = public.dropna().tolist() + [pd.Period(q, "Q").start_time for q in starts.unique()]
        anchor = min(anchors)
        lag = int(rng.integers(CFG["fines"]["allocation_lead_months"][0], CFG["fines"]["allocation_lead_months"][1] + 1))
        allocation = max(pd.Timestamp(CFG["fines"]["earliest_allocation"]), anchor - pd.DateOffset(months=lag))
        if allocation > anchor:
            raise ValueError("Synthetic allocation cannot follow the earliest public/observed anchor")
        vintage = "old_contract_price_egp_m2" if allocation.year < 2023 else "recent_contract_price_egp_m2"
        price = round(float(rng.uniform(*CFG["fines"][vintage])), 2)
        rows.append({"code": r.code, "land_area_m2": r.land_area_m2, "land_area_origin": r.land_area_origin,
                     "allocation_date_assumed": allocation, "calibration_anchor_date": anchor,
                     "allocation_origin": "generated; conditioned on full historical evidence; excluded from X",
                     "assumed_land_price_egp_m2": price, "assumed_land_value_egp": r.land_area_m2 * price,
                     "fine_rate_month": CFG["fines"]["fine_rate_month"], "assumption": True,
                     "assumption_available_from": allocation, "price_context_source": "PRICE_CONTEXT_2026;PRICE_EXISTING_AUDIT",
                     "rate_source": "illustrative assumption; not published contract rate", "synthetic_label": LABEL})
    return pd.DataFrame(rows)


def quarterly_finances(mon, reports, kpi, land):
    mon = mon.copy()
    mon["quarter"] = mon.month.map(lambda m: str(m.asfreq("Q")))
    rows = []
    for (code, quarter), group in mon.groupby(["code", "quarter"]):
        last = group.sort_values("month").iloc[-1]
        available = reports[(reports.code == code) & (reports.report_date <= qend(qindex(quarter)))].sort_values("report_date")
        row = {"code": code, "quarter": quarter, "month": str(last.month), "months_present": len(group)}
        for col in ("collections_egp", "land_due_egp", "land_paid_egp", "kwh", "units_sold"):
            row[col] = float(group[col].sum())
        for col in ("planned_pct", "cover_required_egp", "cover_balance_egp", "cost_to_complete_egp", "land_months_late", "meters_active", "roads_paved_share"):
            row[col] = last[col]
        row["reported_pct"] = available.reported_pct.iloc[-1] if len(available) else np.nan
        row["report_date"] = available.report_date.iloc[-1] if len(available) else pd.NaT
        # Existing generated installments take precedence over an independent price guess.
        known_dues = mon.loc[mon.code.eq(code) & mon.month.le(last.month) & mon.land_due_egp.gt(0), "land_due_egp"]
        row["land_value_from_known_installments_egp"] = float(known_dues.median()) * CFG["generator"]["land"]["installments"] if len(known_dues) else np.nan
        rows.append(row)
    out = pd.DataFrame(rows).merge(kpi[["code", "quarter", "K5_months", "K6"]], on=["code", "quarter"], validate="one_to_one")
    out = out.merge(land[["code", "assumed_land_value_egp", "fine_rate_month"]], on="code", validate="many_to_one")
    known = out.land_value_from_known_installments_egp.notna()
    out["land_value_basis"] = np.where(known, "derived from generated installments available by cutoff", "vintage-based generated assumption")
    out.loc[known, "assumed_land_value_egp"] = out.loc[known, "land_value_from_known_installments_egp"]
    out["K5_egp"] = out.K5_months * out.assumed_land_value_egp * out.fine_rate_month
    relief_known = out.quarter.map(lambda q: qend(qindex(q))) >= pd.Timestamp(CFG["fines"]["relief_published"])
    out["K5_egp_discount_scenario"] = (out.K5_egp * (1 - CFG["fines"]["relief_discount_scenario"])).where(relief_known)
    out["K5_egp_installment_scenario_monthly"] = (out.K5_egp / CFG["fines"]["relief_installments_months"]).where(relief_known)
    out["relief_basis"] = "optional hypothetical eligibility, not automatic relief; expiry unknown"
    out["fine_assumption"], out["synthetic_label"] = True, LABEL
    return out


def outcome_labels(keys, truth, comp):
    """Binary future distress labels; handover state only defines the cutoff cohort."""
    truth = truth.copy()
    truth["month"] = pd.PeriodIndex(truth.month, freq="M")
    total = comp.set_index("code").units
    rows = []
    for r in keys.itertuples():
        cutoff = pd.Period(r.month, "M")
        mine = truth[truth.code == r.code].sort_values("month")
        now = mine[mine.month == cutoff]
        horizon = mine[mine.month.isin(pd.period_range(cutoff + 1, cutoff + 6, freq="M"))]
        censored = len(horizon) != 6 or horizon.month.nunique() != 6
        already = bool(len(now) and now.handed_over_units.iloc[-1] >= total[r.code])
        distress = bool(horizon.true_distress.any())
        label = None if censored else "distressed" if distress else "not_distressed"
        rows.append({"code": r.code, "quarter": r.quarter, "y_outcome_6m": label,
                     "label_distress_next_6m": pd.NA if censored else distress, "label_censored": censored,
                     "already_completed_at_cutoff": already})
    return pd.DataFrame(rows)


def expanded_dataset(src, sat, yearly, kpi, quarterly, comp, truth):
    # Build observations only; discard every evaluation-only column before X.
    quarters = pd.period_range(CFG["generator"]["start"], CFG["generator"]["end"], freq="Q").astype(str).tolist()
    base = F.build_table(src=src, quarters=quarters)
    keys = ["code", "developer_code", "quarter", "qi", "month"]
    out = base[["code", "developer", "quarter", "month", *F.FEATURES]].rename(columns={"developer": "developer_code"})
    out["month"] = out.month.astype(str)
    out["qi"] = out.quarter.map(qindex)
    extra = kpi[["code", "quarter", "K4", "K5_months", "K6", "may_be_complete", "observed_started", "start_observation_sufficient"]]
    out = out.merge(extra, on=["code", "quarter"], validate="one_to_one")
    out = out.merge(sat[["code", "quarter", "K1"]], on=["code", "quarter"], validate="one_to_one")
    # Only whole finished years, and approved height years <=2024, are available.
    vegetation, heights = [], []
    for r in out.itertuples():
        y = yearly[(yearly.code == r.code) & (yearly.year < int(r.quarter[:4]) + (r.quarter.endswith("Q4")))]
        v = y.dropna(subset=["veg_share"]).sort_values("year")
        h = y[y.year <= CFG["heights_max_year"]].dropna(subset=["height_mean_m"]).sort_values("year")
        vegetation.append(v.veg_share.iloc[-1] if len(v) else np.nan)
        heights.append(h.height_mean_m.iloc[-1] if len(h) else np.nan)
    out["veg_share"], out["height_mean_m"] = vegetation, heights
    out = out.merge(quarterly[["code", "quarter", "planned_pct", "reported_pct", "K5_egp"]], on=["code", "quarter"], validate="one_to_one")
    out["activity_prob"], out["land_months_late"] = out.A, out.land_late
    # Imported spec uses sold units, while the historical EW used total register units.
    counts90 = F.complaint_rates(src.cmp, pd.Series(1.0, index=src.codes), src.months)
    sold = src.mon.pivot(index="month", columns="code", values="units_sold").reindex(src.months)
    sold_rates = counts90 / sold.replace(0, np.nan)
    rates, percentiles, changes = [], [], []
    for r in out.itertuples():
        month = pd.Period(r.month, "M")
        rate = sold_rates.loc[month, r.code]
        history = sold_rates.loc[sold_rates.index < month, r.code].dropna()
        rates.append(rate)
        percentiles.append(((history < rate).sum() + 0.5 * (history == rate).sum()) / len(history)
                           if len(history) >= 12 and pd.notna(rate) else np.nan)
        before = sold_rates.loc[month - 6, r.code] if month - 6 in sold_rates.index else np.nan
        changes.append(rate - before)
    out["cmp_rate90"], out["cmp_pctl"], out["d_cmp_rate90"] = rates, percentiles, changes
    labels = outcome_labels(out[keys], truth, comp)
    features = [c for c in out if c not in keys]
    out = out.merge(labels, on=["code", "quarter"], validate="one_to_one")
    out["label_distress_next_6m"] = pd.array(out.label_distress_next_6m, dtype="boolean")
    return out.sort_values(["quarter", "code"]).reset_index(drop=True), features, keys


def build(refresh_inputs=True):
    OUT.mkdir(parents=True, exist_ok=True)
    tables = {name: pd.read_parquet(REAL / f"{name}.parquet") for name in build_real.ORIGINS}
    n = len(tables["compounds"])
    if CFG["cycle_capacity"] != max(1, math.ceil(n * CFG["inspection_capacity_fraction"])):
        raise ValueError("Inspection capacity must equal one third of the configured scope, rounded up")
    sat = kpis.add_k2(tables["sat_quarterly"], tables["statements"])
    kpi = kpis.kpi_values(sat, tables["compounds"], tables["statements"], tables["sat_yearly"], run_all.make_run_id())
    tables["sat_quarterly"] = sat
    run_all.write_real({"sat_quarterly": sat, "kpi_values": kpi})
    # Replace only derived tables. No activity model or historical simulator is fitted.
    with duckdb.connect(str(APP / "spaceeye.duckdb")) as con:
        for name, frame in (("sat_quarterly", sat), ("kpi_values", kpi)):
            con.register("updated_frame", frame)
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM updated_frame")
            con.unregister("updated_frame")
    if refresh_inputs:
        prepare_sim.main()
        scenarios.main()
    src = F.Source()
    land = land_assumptions(tables["compounds"], sat, tables["statements"])
    quarterly = quarterly_finances(src.mon, src.rep, kpi, land)
    truth = pd.read_parquet(PRIVATE / "answer_key.parquet")
    dataset, features, keys = expanded_dataset(src, sat, tables["sat_yearly"], kpi, quarterly, tables["compounds"], truth)
    caps = capacity_paths(kpi, CFG["cycle_capacity"])
    write_table(land, APP / "sim_clean" / "fine_assumptions.parquet")
    write_table(quarterly, APP / "sim_clean" / "fin_quarterly.parquet")
    write_table(dataset, PRIVATE / "ml_dataset_extended.parquet")
    caps.to_csv(OUT / "inspection_capacity.csv", index=False)
    cycle = kpis.cycle_list(kpi, CFG["asof"])
    cycle.to_csv(OUT / "cycle_list.csv", index=False, encoding="utf-8-sig")
    cycle.to_csv(REAL / f"cycle_list_{CFG['asof']}.csv", index=False, encoding="utf-8-sig")
    counts = {}
    for split, mask in (("train", dataset.quarter.le("2024Q4")), ("embargo", dataset.quarter.eq("2025Q1")),
                        ("time_test", dataset.quarter.between("2025Q2", "2026Q1")), ("censored", dataset.label_censored)):
        counts[split] = {"rows": int(mask.sum()), "classes": dataset.loc[mask, "y_outcome_6m"].value_counts().to_dict(),
                         "already_completed": int(dataset.loc[mask, "already_completed_at_cutoff"].sum())}
    inputs = {p.relative_to(APP.parent).as_posix() if p.is_relative_to(APP.parent) else p.relative_to(BASE_DIR).as_posix(): run_all.sha(p)
              for p in [REAL / f"{name}.parquet" for name in build_real.ORIGINS] + [REAL / "kpi_values.parquet", APP / "sim" / "fin_monthly.parquet",
                        APP / "sim" / "complaints.parquet", PRIVATE / "answer_key.parquet", BASE_DIR / "configs" / "data.yaml",
                        BASE_DIR / "configs" / "synthetic_sources.json", Path(__file__), BASE_DIR / "src" / "pipeline" / "kpis.py", BASE_DIR / "src" / "analysis" / "ew_features.py"]}
    meta = {"synthetic_label": LABEL, "dataset": "private/ml_dataset_extended.parquet", "rows": len(dataset), "keys": keys,
            "features": features, "targets": ["label_distress_next_6m", "y_outcome_6m"], "censor_column": "label_censored",
            "excluded_from_X": ["already_completed_at_cutoff"], "split_counts": counts, "input_and_code_sha256": inputs,
            "target_definition": "Binary distressed/not_distressed in the next six calendar months, excluding cutoff. Completion is not predicted. Already-handed-over cutoffs are excluded from the cohort. Censored targets are null. Boolean and categorical targets encode the same distress event.",
            "fine_policy": {**CFG["fines"], "basis": "research screening proxy, not verified contractual eligibility; monthly union, stops accruing at first published handover"},
            "complaint_rate": "90-day complaints per 1000 units sold in the cutoff MONTH (monthly flow, not cumulative sold inventory); own-history percentile requires 12 prior valid months. Historical binary EW instead used total register units. Sales-denominator stock is unavailable in the exported feed; interpret this as a flow-normalized diagnostic, not a buyer incidence rate.",
            "column_origins": {c: "key" if c in keys else "derived_public_observation" if c in [*F.SAT_ALL, "activity_prob", "K1", "K4", "K5_months", "K6", "may_be_complete", "observed_started", "start_observation_sufficient", "veg_share", "height_mean_m"] else "generated_or_derived_from_generated" for c in dataset},
            "missing_features": {c: int(dataset[c].isna().sum()) for c in features}, "dataset_sha256": run_all.sha(PRIVATE / "ml_dataset_extended.parquet"),
            "evaluation": "Current binary evaluation is separate in ml_current and EW_REPORT_CURRENT.md; historical experiments remain versioned evidence."}
    (PRIVATE / "ml_dataset_extended_metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    (PRIVATE / "dictionaries" / "ml_dataset_extended.md").write_text("# Expanded data contract\n\n" + LABEL + "\n\n" +
        "| Column | Role | Type |\n| --- | --- | --- |\n" + "\n".join(f"| {c} | {'X' if c in features else 'key' if c in keys else 'target/evaluation only'} | {dataset[c].dtype} |" for c in dataset) + "\n", encoding="utf-8")
    q = gates.run_gates(tables, kpi)
    private_names = gates.g_no_names(extra=gates.generator_files() + [PRIVATE / "ml_dataset_extended.parquet", PRIVATE / "ml_dataset_extended_metadata.json"])
    q.loc[q.gate.eq("no_names"), ["status", "value"]] = [private_names["status"], private_names["value"]]
    if q.status.eq("STOP").any():
        raise RuntimeError("Data quality STOP: " + ", ".join(q.loc[q.status.eq("STOP"), "gate"]))
    q.to_csv(OUT / "quality_checks.csv", index=False)
    pd.DataFrame(columns=["code", "visit_date", "result", "note"]).to_csv(OUT / "ops_visits_template.csv", index=False)
    checks = {"extended_unique_keys": not dataset.duplicated(["code", "quarter"]).any(), "quarterly_fin_unique_keys": not quarterly.duplicated(["code", "quarter"]).any(),
              "quarterly_fin_full_grid": len(quarterly) == n * 15 and quarterly.months_present.eq(3).all(),
              "censored_targets_null": dataset.loc[dataset.label_censored, meta["targets"]].isna().all().all(),
              "uncensored_targets_known": dataset.loc[~dataset.label_censored, meta["targets"]].notna().all().all(),
              "fine_union_no_double_count": (kpi.K5_months == kpi.K5_no_start_months + kpi.K5_post_grace_months - kpi.K5_overlap_months).dropna().all(),
              "fine_amount_formula": np.allclose(quarterly.K5_egp.fillna(0).astype(float), (quarterly.K5_months * quarterly.assumed_land_value_egp * quarterly.fine_rate_month).fillna(0).astype(float)),
              "generated_allocation_precedes_anchor": land.allocation_date_assumed.le(land.calibration_anchor_date).all(),
              "retrospective_allocation_excluded_from_X": not any("allocation" in c for c in features),
              "relief_not_available_before_publication": quarterly.loc[quarterly.quarter.lt("2024Q4"), ["K5_egp_discount_scenario", "K5_egp_installment_scenario_monthly"]].isna().all().all(),
              "land_value_matches_available_installments": np.allclose(quarterly.loc[quarterly.land_value_from_known_installments_egp.notna(), "assumed_land_value_egp"], quarterly.loc[quarterly.land_value_from_known_installments_egp.notna(), "land_value_from_known_installments_egp"]),
              "cycle_within_capacity": kpi.cycle_rank.dropna().le(CFG["cycle_capacity"]).all(),
              "capacity_selection_consistent": (caps.selected == (caps.eligible_rank <= caps.capacity)).all(),
              "feature_label_separation": not set(features) & set(keys + meta["targets"] + ["label_censored", "already_completed_at_cutoff"]),
              "no_name_gate": q.loc[q.gate.eq("no_names"), "status"].eq("PASS").all()}
    if not all(checks.values()):
        raise RuntimeError(f"Data completion checks failed: {checks}")
    report = {"status": "PASS", "scope": "data only; no model training", "checks": {k: bool(v) for k, v in checks.items()},
              "compounds": n, "capacity": CFG["cycle_capacity"], "quarterly_fin_rows": len(quarterly), "expanded_rows": len(dataset),
              "features": len(features), "split_counts": counts, "fine_assumptions": CFG["fines"], "input_and_code_sha256": inputs,
              "generated_missing_inputs": ["Synthetic allocation dates and vintage-based contract price assumptions; allocation dates excluded from X/public K6.", "Assumed fine rate and optional relief/scheduling scenarios, not actual decisions."],
              "not_available": ["Actual contract fine rate/eligibility and assessed fines; synthetic stand-ins supplied.", "Actual allocation dates; synthetic register supplied, public K6 keeps published launch/promise fallback.",
                                "Finishing feature and later heights; failed tests, not invented.", "Independent real complete/distress check labels for every compound/cutoff; source cases do not support them."],
              "not_run": ["New classifiers, model comparison, dashboard, agent, forms and slides; user requested data only."],
              "legacy_evaluation": "Historical binary results at N=8 are archived evidence, not current validation of capacity 4 or the extended dataset."}
    (OUT / "audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    # Include new prepared artifacts in the existing prepared-output manifest.
    prepared = APP / "sim_clean"
    pd.DataFrame([{"file": p.name, "sha256": run_all.sha(p)} for p in sorted(prepared.iterdir()) if p.is_file() and p.name != "manifest.csv"]).to_csv(prepared / "manifest.csv", index=False)
    print(f"data completion PASS: {len(checks)} checks, {len(dataset)} rows/{len(features)} features, {len(quarterly)} financial quarters, capacity {CFG['cycle_capacity']}")
    return report


def main():
    build()
    from src.pipeline.release import audit
    audit(require_current_evaluation=False)


if __name__ == "__main__":
    main()
