"""Finish existing backtest explanations, scenario contracts and data audits.

Uses saved rule outputs. Private generator launch dates are used ONLY to audit
planted defects, never to repair observations or to build features.
"""

import hashlib
import json

import pandas as pd

from src.generator import simulate
from src.generator.inputs import MONTHS
from src.pipeline import backtest_check
from src.pipeline.common import APP, BASE_DIR, CFG, PRIVATE, REAL, qend
from src.pipeline.privacy import assert_safe_texts

OUT = APP / "partial_task_exports"
LABEL = "Synthetic - for training only"


def save(frame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def scenario_level_labels(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply hypothetical levels while preserving the public label when no level exists."""
    return frame.assign(
        level_word=frame.level.map({1: "first", 2: "second", 3: "third", 4: "fourth"}).fillna(frame.level_word),
        level_word_ar=frame.level.map({1: "الأولى", 2: "الثانية", 3: "الثالثة", 4: "الرابعة"}).fillna(frame.level_word_ar),
        level_label=frame.level.map(lambda value: str(int(value)) if pd.notna(value) else pd.NA).fillna(frame.level_label),
    )


def backtest_report():
    kpi = pd.read_parquet(APP / "backtest/kpi_values_backtest.parquet")
    events = pd.read_parquet(REAL / "eval_outcomes.parquet")
    cases, summary = backtest_check.run(kpi, events)
    rows = []
    for e in events.itertuples():
        freeze = pd.Timestamp(e.first_deadline) - pd.DateOffset(months=CFG["backtest"]["months_before"])
        mine = kpi.loc[kpi.code.eq(e.code) & kpi.qi.map(qend).le(freeze)].sort_values("qi")
        valid = mine.loc[mine.K4]
        alerts = valid.loc[valid.level.isin([1, 2]) & valid.started]
        point = alerts.iloc[0] if len(alerts) else valid.iloc[-1] if len(valid) else None
        if len(valid):
            alternative = "The absence or timing of the warning was solely due to no assessable quarter."
            rejection = f"Rejected: {len(valid)} assessable quarters existed before the frozen cutoff. This does not rule out coverage effects within those quarters."
        elif pd.notna(e.delay_months_vs_promise) and e.delay_months_vs_promise > 0:
            alternative = "No warning means there was no documented delay in the check set."
            rejection = f"Rejected: the check-set delay is {e.delay_months_vs_promise:g} months; missing early coverage is not evidence of no delay."
        else:
            alternative = "No warning means no underlying problem."
            rejection = "Not rejectable numerically with the saved pre-cutoff evidence; retain unknown."
        rows.append({"case": e.case, "code": e.code, "freeze_date": str(freeze.date()),
                     "what_happened": f"{e.outcome_type}; outcome date {e.outcome_date}; first published {e.outcome_first_published}",
                     "assessable_quarters_before_cutoff": len(valid), "after_start_alert_quarters": len(alerts),
                     "why": point.reason if point is not None else "No assessable pre-cutoff KPI quarter exists in the saved window.",
                     "competing_explanation": alternative, "numeric_check": rejection,
                     "what_next": "Review the cited public outcome and original promise; confirm actual status on site. Do not infer predictive success from a later alert."})
    details = pd.DataFrame(rows).merge(cases, on=["case", "code"], validate="one_to_one")
    save(details, OUT / "backtest/cases_explained.csv")
    (OUT / "backtest/summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    lines = ["# Current Track A real-case check", "", "Six R7 public check cases; no generated financial labels are used here. The saved activity backtest excludes overlapping training plots.", "",
             f"After-start reading: {summary['after_start_reading']['n']} of {len(events)}. Point-in-time reading: {summary['point_in_time_reading']['n']} of {len(events)}. Original criterion remains {CFG['backtest']['min_cases']} cases; it is not reduced to obtain a pass.", "",
             "| Case / code | Assessable pre-cutoff quarters | After-start alert quarters | Numeric alternative check |", "| --- | ---: | ---: | --- |"]
    lines += [f"| {r.case} / {r.code} | {r.assessable_quarters_before_cutoff} | {r.after_start_alert_quarters} | {r.numeric_check} |" for r in details.itertuples()]
    lines += ["", "The full CSV contains what happened, the rule explanation, the competing explanation and next action. Warning detection is not causal proof. No percentages or retuned thresholds are used."]
    (BASE_DIR / "data/BACKTEST_CURRENT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def scenario_exports():
    priorities = pd.read_parquet(APP / "component_data/hypothetical_priorities.parquet")
    capacity = pd.read_csv(APP / "data_completion/inspection_capacity.csv")
    public = pd.read_parquet(REAL / "kpi_values.parquet")
    for label, original in (("S1", "usd_cost_shock"), ("S2", "collections_drop")):
        frame = priorities.loc[priorities.scenario_id.eq(original)].copy()
        frame["reason"] = frame.apply(lambda r, scenario=original: (
            f"{scenario}: simulated gap {r.projected_gap_pp:.2f}pp versus the frozen-context projected plan; "
            f"B1={r.frozen_B1}, B2={r.frozen_B2}, B3={r.frozen_B3}, projected B5={r.projected_B5}; "
            f"selection changed={r.selection_changed}, level changed={r.level_changed}. No new satellite or field observation."), axis=1)
        frame["quarter"] = pd.PeriodIndex(frame.month, freq="M").asfreq("Q").astype(str)
        frame["level"] = frame.hypothetical_level
        frame["cycle_rank"] = frame.eligible_rank.where(frame.selected)
        frame["K2"], frame["K3"] = frame.K2_frozen, frame.K3_frozen
        frame["origin"] = "generated hypothetical rule"
        source_quarter = str(pd.Period(frame.cutoff.iloc[0], "M").asfreq("Q"))
        frozen = public.loc[public.quarter.eq(source_quarter)].set_index("code")
        for column in public.columns:
            if column not in frame and column != "code":
                frame[column] = frame.code.map(frozen[column])
        frame["qi"] = frame.quarter.map(lambda q: (int(q[:4]) - 2016) * 4 + int(q[-1]) - 1)
        frame["frozen_context_quarter"] = source_quarter
        frame["source_run_id"] = frame.run_id
        frame["run_id"] = "SC-" + original + "-" + hashlib.sha256((APP / "scenarios/paths.parquet").read_bytes()).hexdigest()[:10]
        frame = scenario_level_labels(frame)
        frame["reason_ar"] = "حالة افتراضية بسياق رصد ثابت؛ يلزم تحقق ميداني مستقل."
        (OUT / label).mkdir(exist_ok=True)
        # Last simulated month in each quarter; all public context is explicitly frozen.
        quarterly = frame.sort_values("month").groupby(["code", "quarter"], sort=True).tail(1)
        if not set(public).issubset(quarterly.columns) or quarterly.duplicated(["code", "quarter"]).any():
            raise RuntimeError("Scenario KPI schema or quarterly keys are invalid")
        quarterly.to_parquet(OUT / label / "kpi_values.parquet", index=False)
        save(frame, OUT / label / "who_moved_and_why.csv")
    base = capacity.loc[capacity.scenario_id.eq("baseline"), ["code", "quarter", "selected", "eligible_rank"]].rename(columns={"selected": "baseline_selected", "eligible_rank": "baseline_rank"})
    frame = capacity.loc[~capacity.scenario_id.eq("baseline")].merge(base, on=["code", "quarter"], validate="many_to_one")
    frame["selection_changed"] = frame.selected.ne(frame.baseline_selected)
    frame["reason"] = frame.apply(lambda r: f"Capacity {r.capacity}: eligible rank {r.eligible_rank}; selection changed={r.selection_changed}; levels, progress and cash unchanged.", axis=1)
    frame["synthetic_label"] = LABEL
    frame = frame.merge(public.drop(columns=["level", "cycle_rank", "reason"]), on=["code", "quarter"], validate="many_to_one", suffixes=("", "_public"))
    frame["cycle_rank"] = frame.eligible_rank.where(frame.selected)
    save(frame, OUT / "S3/who_moved_and_why.csv")
    frame.to_parquet(OUT / "S3/kpi_values.parquet", index=False)
    return {"S1": "USD cost +30% on imported share", "S2": "Collections -25% for six months", "S3": "Capacity 2/6 versus baseline 4; rerank only"}


def defect_audit():
    # Private audit only; no generated hidden state enters prepared feeds or X.
    rebuilt = simulate.build()
    launches = {u.sig.code: MONTHS[u.st.launch].start_time for u in rebuilt["units"]}
    raw = pd.read_parquet(APP / "sim/complaints.parquet")
    before_launch = sum(pd.Timestamp(r.created_at) < launches[r.code] for r in raw.itertuples() if r.code in launches)
    quality = json.loads((APP / "sim_clean/quality_report.json").read_text(encoding="utf-8"))
    expected = pd.read_csv(PRIVATE / "defects_log.csv").set_index("defect_id").rows_affected
    observed = [quality["balance_rows_corrected"], quality["duplicate_months_removed"], quality["invalid_report_observations_removed"],
                quality["complaints_quarantined"], before_launch, quality["phone_texts_masked"]]
    report = pd.DataFrame({"defect_id": range(1, 7), "expected": expected.reindex(range(1, 7)).to_numpy(), "observed": observed})
    report["matched"] = report.expected.eq(report.observed)
    report["scope"] = ["prepared-feed check"] * 4 + ["private synthetic generator audit only"] + ["prepared-feed masking"]
    report["synthetic_label"] = LABEL
    save(report, OUT / "defects_audit.csv")
    if not report.matched.all():
        raise RuntimeError("Planted-defect audit mismatch; inspect the saved aggregate report")
    clean = pd.read_parquet(APP / "sim_clean/complaints.parquet")
    assert_safe_texts(clean.text_ar.dropna())
    checks = pd.read_csv(APP / "sim/realism_checks.csv")
    return {"planted_defects_matched": int(report.matched.sum()), "realism_checks": len(checks), "realism_failed": int((~checks.ok.astype(bool)).sum()),
            "public_prelaunch_validation": "Unknown where public launch dates are missing; the private audit did not repair or relabel observations."}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    backtest_report()
    scenario_info = scenario_exports()
    audit = defect_audit()
    annual = pd.read_parquet(REAL / "sat_yearly.parquet")
    save(annual, OUT / "annual_context.csv")
    coverage = annual.groupby("year").agg(compounds=("code", "count"), vegetation_nonnull=("veg_share", "count"), heights_nonnull=("height_mean_m", "count")).reset_index()
    save(coverage, BASE_DIR / "data/ANNUAL_CONTEXT_COVERAGE.csv")
    (BASE_DIR / "data/DEFECT_AUDIT_CURRENT.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    (OUT / "scenario_contract.json").write_text(json.dumps({"scenarios": scenario_info, "synthetic_label": LABEL,
        "schema_note": "S1/S2 KPI exports use the last simulated month per quarter. Public A/K2/K3/K4/K5/K6 and other context are frozen at frozen_context_quarter, not future observations or forecasts; only hypothetical level/rank change through projected B5. Monthly change explanations remain separate. S3 keeps the source quarter and levels; scenario_id distinguishes capacity 2/6. No new satellite observations, fine exposures or delivery events are predicted."}, indent=2), encoding="utf-8")
    print("Current backtest explanations, S1/S2/S3 exports, six-defect private audit and annual context exported")


if __name__ == "__main__":
    main()
