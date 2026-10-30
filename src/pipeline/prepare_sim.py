"""Prepare safe-to-use synthetic tables while retaining the deliberately dirty raw simulation.

Run: python -m src.pipeline.prepare_sim. Outputs: app_data/sim_clean, never private truth.
Unknown launch dates cannot validate every pre-launch complaint; this limit is reported explicitly.
"""

import hashlib
import json

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.analysis.ew_features import SIM, clean_complaints, clean_fin
from src.generator.defects import PHONE
from src.pipeline.common import APP, BASE_DIR, CFG, REAL


def prepare(fin, complaints, compounds):
    monthly, reports, fixed = clean_fin(fin)
    original = fin.drop_duplicates(["code", "month"], keep="first").copy()
    dates = pd.to_datetime(original.report_date, errors="coerce")
    invalid = original.reported_pct.notna() & (dates.isna() | dates.dt.to_period("M").ne(pd.PeriodIndex(original.month, freq="M")))
    rejected_reports = original.loc[invalid, ["code", "month", "reported_pct", "report_date"]].assign(dq_reason="report_date_not_in_recorded_month")
    gen = CFG["generator"]
    clean, rejected, masked = clean_complaints(complaints, compounds.code, gen["start"] + "-01", (pd.Period(gen["end"], "M") + 1).start_time)
    monthly["month"] = monthly.month.astype(str)
    checks = {
        "unique_fin_months": not monthly.duplicated(["code", "month"]).any(),
        "known_fin_codes": bool(monthly.code.isin(compounds.code).all()),
        "known_complaint_codes": bool(clean.code.isin(compounds.code).all()),
        "unique_complaint_ids": not clean.complaint_id.duplicated().any(),
        "no_phones_in_text": not clean.text_ar.dropna().map(lambda t: bool(PHONE.search(t))).any(),
        "nonnegative_balances": bool((monthly.cover_balance_egp >= 0).all()),
    }
    summary = {
        "synthetic_label": gen["label"], "raw_fin_rows": len(fin), "fin_rows": len(monthly),
        "duplicate_months_removed": len(fin) - len(monthly), "balance_rows_corrected": fixed,
        "invalid_report_observations_removed": len(rejected_reports), "valid_reports": len(reports),
        "raw_complaints": len(complaints), "complaints": len(clean),
        "complaints_quarantined": len(rejected), "phone_texts_masked": masked,
        "prelaunch_validation": "Not fully verifiable from public launch dates; no private truth used to repair complaints.",
        "checks": {k: bool(v) for k, v in checks.items()},
    }
    return {"fin_monthly": monthly, "complaints": clean, "rejected_reports": rejected_reports, "quarantine_complaints": rejected}, summary


def main():
    inputs = {"sim/fin_monthly.parquet": SIM / "fin_monthly.parquet", "sim/complaints.parquet": SIM / "complaints.parquet",
              "real/compounds.parquet": REAL / "compounds.parquet", "configs/data.yaml": BASE_DIR / "configs" / "data.yaml",
              "src/analysis/ew_features.py": BASE_DIR / "src" / "analysis" / "ew_features.py",
              "src/pipeline/prepare_sim.py": BASE_DIR / "src" / "pipeline" / "prepare_sim.py"}
    hashes = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in inputs.items()}
    tables, summary = prepare(pd.read_parquet(inputs["sim/fin_monthly.parquet"]), pd.read_parquet(inputs["sim/complaints.parquet"]), pd.read_parquet(inputs["real/compounds.parquet"]))
    if not all(summary["checks"].values()):
        raise RuntimeError(f"Prepared simulation failed checks: {summary['checks']}")
    out = APP / "sim_clean"
    out.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df = df.assign(synthetic_label=CFG["generator"]["label"])  # a column too, so CSV and DuckDB copies keep the flag
        tab = pa.Table.from_pandas(df, preserve_index=False)
        tab = tab.replace_schema_metadata({**(tab.schema.metadata or {}), b"synthetic_label": CFG["generator"]["label"].encode()})
        pq.write_table(tab, out / f"{name}.parquet")
    summary["input_sha256"] = hashes
    (out / "quality_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = [{"file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.iterdir()) if p.is_file() and p.name != "manifest.csv"]
    pd.DataFrame(manifest).to_csv(out / "manifest.csv", index=False)
    print(json.dumps({k: v for k, v in summary.items() if k != "input_sha256"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
