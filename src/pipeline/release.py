"""Build the complete data release and fail explicitly if its contracts disagree.

Run: uv run --locked --with matplotlib python -m src.pipeline.release
No network pulls, dashboard, publication, or height-model training.
"""

import hashlib
import json
from importlib.metadata import version

import duckdb
import pandas as pd

from src.analysis import early_warning as ew
from src.generator import scenarios, simulate
from src.pipeline import gates, prepare_sim, run_all
from src.pipeline.common import APP, BASE_DIR, CFG, PRIVATE


def verify_manifest(path, base):
    rows = pd.read_csv(path)
    for r in rows.itertuples():
        if hashlib.sha256((base / r.file).read_bytes()).hexdigest() != r.sha256:
            raise RuntimeError(f"Manifest mismatch: {path.name}/{r.file}")
    return len(rows)


def audit(require_current_evaluation=True):
    tables = {p.stem: pd.read_parquet(p) for p in (APP / "real").glob("*.parquet")}
    codes = set(tables["compounds"].code)
    checks = {}
    checks["configured_district_scope"] = set(tables["compounds"].district) <= set(CFG["scope_districts"])
    for name, key in (("compounds", ["code"]), ("sat_quarterly", ["code", "quarter"]),
                      ("sat_yearly", ["code", "year"]), ("kpi_values", ["code", "quarter"]),
                      ("statements", ["statement_id"]), ("eval_outcomes", ["case"]),
                      ("drivers_monthly", ["month"]), ("rules", ["rule_id"])):
        checks[name + "_unique_keys"] = not tables[name].duplicated(key).any()
        if "code" in tables[name]:
            checks[name + "_known_codes"] = set(tables[name].code) <= codes
    q = gates.run_gates({name: tables[name] for name in gates.ORIGINS}, tables["kpi_values"])
    con = duckdb.connect(str(APP / "spaceeye.duckdb"), read_only=True)
    try:
        for name, frame in tables.items():
            persisted = con.execute(f'SELECT * FROM "{name}"').df()
            pd.testing.assert_frame_equal(persisted.astype(object).where(persisted.notna(), None),
                                          frame.astype(object).where(frame.notna(), None), check_dtype=False)
    finally:
        con.close()
    checks["duckdb_matches_real_tables"] = True
    checks["no_stop_gate"] = not q.status.eq("STOP").any()
    checks["source_gate_pass"] = q.loc[q.gate == "source", "status"].eq("PASS").all()
    checks["same_seed_historical_simulation"] = bool(pd.read_csv(APP / "sim" / "realism_checks.csv").set_index("check").loc["same_seed_same_files", "ok"])
    realism = pd.read_csv(APP / "sim" / "realism_checks.csv")
    checks["historical_hard_checks"] = bool(realism.loc[realism.kind == "hard", "ok"].all())
    prepared = json.loads((APP / "sim_clean" / "quality_report.json").read_text(encoding="utf-8"))
    checks["prepared_data_checks"] = all(prepared["checks"].values())
    prepared_inputs = {
        "sim/fin_monthly.parquet": APP / "sim" / "fin_monthly.parquet",
        "sim/complaints.parquet": APP / "sim" / "complaints.parquet",
        "real/compounds.parquet": APP / "real" / "compounds.parquet",
        "configs/data.yaml": BASE_DIR / "configs" / "data.yaml",
        "src/analysis/ew_features.py": BASE_DIR / "src" / "analysis" / "ew_features.py",
        "src/pipeline/prepare_sim.py": BASE_DIR / "src" / "pipeline" / "prepare_sim.py",
    }
    checks["prepared_current_inputs_and_code"] = prepared["input_sha256"] == {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in prepared_inputs.items()}
    expected_fin = len(codes) * len(pd.period_range(CFG["generator"]["start"], CFG["generator"]["end"], freq="M"))
    checks["prepared_monthly_grid"] = prepared["fin_rows"] == expected_fin
    clean_fin = pd.read_parquet(APP / "sim_clean" / "fin_monthly.parquet")
    expected_keys = {(code, str(month)) for code in codes for month in pd.period_range(CFG["generator"]["start"], CFG["generator"]["end"], freq="M")}
    checks["prepared_exact_monthly_keys"] = set(map(tuple, clean_fin[["code", "month"]].values)) == expected_keys and not clean_fin.duplicated(["code", "month"]).any()
    prov = json.loads((APP / "ew" / "run_provenance.json").read_text(encoding="utf-8"))
    evaluation_current = prov["sha256"] == ew.input_hashes()
    if require_current_evaluation:
        checks["ew_current_inputs_and_code"] = evaluation_current
    for name, digest in prov["training_output_sha256"].items():
        checks["training_output_" + name] = hashlib.sha256((PRIVATE.parent / name).read_bytes()).hexdigest() == digest
    ml = pd.read_parquet(PRIVATE / "ml_dataset.parquet")
    meta = json.loads((PRIVATE / "ml_dataset_metadata.json").read_text(encoding="utf-8"))
    checks["ml_explicit_features"] = set(ml) == set(meta["keys"] + meta["features"] + [meta["target"], meta["censor_column"]])
    checks["ml_unknown_future_is_null"] = bool(ml.loc[ml[ew.CENSOR], ew.TARGET].isna().all())
    checks["ml_known_target_present"] = bool(ml.loc[~ml[ew.CENSOR], ew.TARGET].notna().all())
    checks["ml_known_codes"] = set(ml.code) == codes
    paths = pd.read_parquet(APP / "scenarios" / "paths.parquet")
    checks["scenario_progress_bounds"] = bool(paths.simulated_progress_pct.between(0, 100).all())
    checks["scenario_cash_conservation"] = bool(paths.cash_accounting_residual_egp.abs().le(1e-5).all())
    checks["scenario_restricted_cash_conservation"] = bool(paths.restricted_accounting_residual_egp.abs().le(1e-5).all())
    checks["scenario_credit_limit"] = bool((paths.closing_debt_egp <= paths.credit_limit_egp + 1e-6).all())
    checks["scenario_known_codes"] = set(paths.code) == codes
    settings = CFG["generator"]["scenarios"]
    raw_fin = pd.read_parquet(APP / "sim" / "fin_monthly.parquet")
    h, s, p = scenarios.simulate(raw_fin, sorted(codes), settings, int(CFG["seed"]))
    scenario_prov = json.loads((APP / "scenarios" / "provenance.json").read_text(encoding="utf-8"))
    checks["scenario_reproduces_current_history"] = scenario_prov["known_history_sha256"] == scenarios._frame_hash(h)
    checks["scenario_reproduces_initial_state"] = scenario_prov["initial_state_sha256"] == scenarios._frame_hash(s)
    checks["scenario_reproduces_paths"] = scenario_prov["paths_sha256"] == scenarios._frame_hash(p)
    for name, frame in (("history", h), ("initial_state", s), ("paths", p)):
        checks["scenario_saved_" + name + "_matches_rebuild"] = scenarios._frame_hash(pd.read_parquet(APP / "scenarios" / f"{name}.parquet")) == scenarios._frame_hash(frame)
    checks["scenario_code_current"] = scenario_prov["source_code_sha256"] == hashlib.sha256((BASE_DIR / "src" / "generator" / "scenarios.py").read_bytes()).hexdigest()
    checks["scenario_cleaning_current"] = scenario_prov["feature_cleaning_code_sha256"] == hashlib.sha256((BASE_DIR / "src" / "analysis" / "ew_features.py").read_bytes()).hexdigest()
    checks["scenario_config_current"] = scenario_prov["config_sha256"] == hashlib.sha256((BASE_DIR / "configs" / "data.yaml").read_bytes()).hexdigest()
    manifests = {
        "raw_sim": verify_manifest(APP / "sim" / "manifest_sim.csv", APP.parent),
        "prepared_sim": verify_manifest(APP / "sim_clean" / "manifest.csv", APP / "sim_clean"),
        "scenarios": verify_manifest(APP / "scenarios" / "manifest.csv", APP / "scenarios"),
    }
    completion_path = APP / "data_completion" / "audit.json"
    completion = json.loads(completion_path.read_text(encoding="utf-8")) if completion_path.exists() else None
    if completion:
        checks["data_completion_checks"] = all(completion["checks"].values())
        for name, digest in completion["input_and_code_sha256"].items():
            path = APP.parent / name if name.startswith(("app_data/", "private/")) else BASE_DIR / name
            checks["completion_current_" + name] = hashlib.sha256(path.read_bytes()).hexdigest() == digest
        extended_meta = json.loads((PRIVATE / "ml_dataset_extended_metadata.json").read_text(encoding="utf-8"))
        checks["expanded_dataset_hash"] = extended_meta["dataset_sha256"] == hashlib.sha256((PRIVATE / "ml_dataset_extended.parquet").read_bytes()).hexdigest()
    failed = [name for name, ok in checks.items() if not bool(ok)]
    if failed:
        raise RuntimeError("Data release audit failed: " + ", ".join(failed))
    report = {
        "release": "R7-data-spec-completion-2026-10-28" if completion else "R7-data-final-2026-10-28", "synthetic_label": CFG["generator"]["label"],
        "status": "PASS", "checks": {k: bool(v) for k, v in checks.items()},
        "validation_scope": "data and current evaluation" if require_current_evaluation else "data only; no model fitting or new evaluation",
        "evaluation_status": "CURRENT" if evaluation_current else "HISTORICAL: N=8 binary evaluation does not validate new capacity/schema/K6 policy",
        "data_completion": completion,
        "counts": {name: len(t) for name, t in tables.items()}, "prepared_simulation": prepared,
        "training_split": meta["split_counts"], "scenario_rows": len(paths), "manifests_verified": manifests,
        "gates": q[["gate", "status", "value"]].to_dict(orient="records"),
        "calibration_flags": realism.loc[(realism.kind == "calibration") & ~realism.ok, ["check", "value", "rule"]].to_dict(orient="records"),
        "versions": {name: version(name) for name in ("pandas", "numpy", "scikit-learn", "pyarrow", "duckdb")},
        "limits": ["Binary mechanism experiment; few independent onsets, not real operational accuracy.",
                   "Historical progress is reconstructed from observed anchors; causal scenarios are separate hypothetical forwards.",
                   "K6 may be null with insufficient observation; current priorities include its imported-spec thresholds.",
                   "Some pre-launch complaint defects cannot be verified from public launch dates; private truth is never used to repair them.",
                   "K5 and fine EGP are policy screening/assumptions, not assessed contract fines; no completion classifier or post-2024 height publication."],
    }
    (APP / "release_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    run_all.manifest()
    print(f"release audit PASS: {len(checks)} checks; {len(codes)} compounds; {len(ml)} training rows; {len(paths)} scenario rows", flush=True)
    return report


def main():
    if run_all.main() != 0:
        raise RuntimeError("R1 pipeline stopped")
    if simulate.main() != 0:
        raise RuntimeError("Historical simulator stopped")
    prepare_sim.main()
    scenarios.main()
    ew.run()
    from src.pipeline.complete_data import build
    build(refresh_inputs=False)
    audit()


if __name__ == "__main__":
    main()
