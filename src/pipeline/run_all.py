"""
propose: one command that builds everything from the audited files: python -m src.pipeline.run_all
input: configs/data.yaml and the audited sources (read only), earth engine pull results already cached in app_data/raw.
output: app_data/real/*.parquet, compound_boundaries.geojson, spaceeye.duckdb, model/, backtest/, manifest.csv. exit code 1 if a gate says STOP.
"""

import hashlib
import shutil

import duckdb
import pandas as pd

from src.pipeline import activity, backtest_check, build_real, codify, gates, kpis
from src.pipeline.common import APP, BASE_DIR, CFG, RAW, REAL


def sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_run_id() -> str:
    h = hashlib.sha256((BASE_DIR / "configs" / "data.yaml").read_bytes())
    for p in sorted(RAW.glob("*")):
        h.update(p.name.encode() + p.read_bytes())
    return "R1-" + h.hexdigest()[:10]


def write_real(tables: dict[str, pd.DataFrame]) -> None:
    REAL.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_parquet(REAL / f"{name}.parquet", index=False)
    shutil.copyfile(RAW / "boundaries.geojson", REAL / "compound_boundaries.geojson")


def write_duckdb() -> None:
    db = APP / "spaceeye.duckdb"
    db.unlink(missing_ok=True)
    con = duckdb.connect(str(db))
    for p in sorted(REAL.glob("*.parquet")):
        con.execute(f"create table {p.stem} as select * from read_parquet('{p.as_posix()}')")
    con.close()


def manifest() -> pd.DataFrame:
    """hash of every output of this pipeline (the generator's `sim/` folder has its own manifest); the duckdb file is hashed by table content because its bytes carry no meaning."""
    rows = [(str(p.relative_to(APP)), sha(p)) for p in sorted(APP.rglob("*"))
            if p.is_file() and p.suffix not in {".duckdb", ".md"} and p.name != "manifest.csv" and p.relative_to(APP).parts[0] != "sim"]
    con = duckdb.connect(str(APP / "spaceeye.duckdb"), read_only=True)
    for (tab,) in con.execute("select table_name from information_schema.tables order by 1").fetchall():
        df = con.execute(f"select * from {tab}").df().astype(str)
        rows.append((f"spaceeye.duckdb:{tab}", hashlib.sha256(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()))
    con.close()
    out = pd.DataFrame(rows, columns=["file", "sha256"])
    out.to_csv(APP / "manifest.csv", index=False)
    return out


def main() -> int:
    log = []

    def step(name: str, rows: int, detail: str, status: str = "ok") -> None:
        log.append({"step": name, "rows": rows, "detail": detail, "status": status})
        print(f"{name}: {rows} rows, {detail}", flush=True)

    cm = codify.run()
    step("codify", len(cm), "names replaced by codes; raw copies written")
    run_id = make_run_id()
    t = build_real.build_all()
    for name, df in t.items():
        step(f"build_{name}", len(df), f"{df.shape[1]} columns")

    model, thr, meta = activity.fit_final()
    mode = meta["mode"]
    activity.save(model, meta)
    v = meta["validation"]
    rq = meta.get("rejected_quarterly", {}).get("validation")
    step("activity", meta["n_train"], f"mode {mode}; threshold {thr:.4f}; oof ba {meta['oof_sens_spec_ba'][2]}; T1 gain {v['T1']['gain_ba']} T2 {v['T2']['gain_ba']}; "
         f"T3 A {v['T3']['A_active_pct']}% vs K1 {v['T3']['K1_active_pct']}%; seasonal spread {v['seasonal']['stable_plots_2024_2025']['A']['spread_pp']} pp"
         + (f"; quarterly A rejected (T1 {rq['T1']['gain_ba']}, T2 {rq['T2']['gain_ba']}, T3 {rq['T3']['pass']}, spread {rq['seasonal']['stable_plots_2024_2025']['A']['spread_pp']})" if rq else ""))
    leak = activity.overlapping_plots()
    model_bt, thr_bt, meta_bt = activity.fit(leak, mode)  # backtest variant: trained without the plots that cover a compound
    activity.save(model_bt, meta_bt, "_backtest")
    step("activity_backtest", meta_bt["n_train"], f"{len(leak)} plots covering a compound left out of training; threshold {thr_bt:.4f}; T1 gain {meta_bt['validation']['T1']['gain_ba']} "
         f"T2 {meta_bt['validation']['T2']['gain_ba']}")
    raw_sat = t["sat_quarterly"]
    sat = raw_sat.merge(activity.score(raw_sat, model, thr, mode=mode)[["code", "qi", "activity_prob", "active"]], on=["code", "qi"], how="left")
    t["sat_quarterly"] = kpis.add_k2(sat, t["statements"])
    kpi = kpis.kpi_values(t["sat_quarterly"], t["compounds"], t["statements"], t["sat_yearly"], run_id)
    step("kpis", len(kpi), f"asof {CFG['asof']}: " + ", ".join(f"{k}: {v}" for k, v in kpi[kpi.quarter == CFG["asof"]].level_label.value_counts().sort_index().items()))

    sat_bt = raw_sat.merge(activity.score(raw_sat, model_bt, thr_bt, mode=mode)[["code", "qi", "activity_prob", "active"]], on=["code", "qi"], how="left")
    kpi_bt = kpis.kpi_values(sat_bt, t["compounds"], t["statements"], t["sat_yearly"], run_id)
    cases, summary = backtest_check.run(kpi_bt, t["eval_outcomes"])
    summary["activity_variant"] = {"mode": mode, "plots_left_out": len(leak), "threshold": thr_bt}
    summary["frozen_clock_check"] = backtest_check.frozen_clock_check(model, thr, mode, t["sat_quarterly"], kpi, t["compounds"], t["statements"], t["sat_yearly"], run_id)
    backtest_check.save(cases, summary)
    kpi_bt.to_parquet(APP / "backtest" / "kpi_values_backtest.parquet", index=False)
    step("backtest", len(cases), f"after start {summary['after_start_reading']['n']}/{summary['n_cases']}, point in time {summary['point_in_time_reading']['n']}/{summary['n_cases']}, literal {summary['literal_reading']['n']}/{summary['n_cases']}; "
         f"frozen clock {summary['frozen_clock_check']}")

    out = {**t, "kpi_values": kpi}
    write_real(out)
    kpis.cycle_list(kpi, CFG["asof"]).to_csv(REAL / f"cycle_list_{CFG['asof']}.csv", index=False, encoding="utf-8-sig")
    qlog = gates.run_gates(t, kpi)
    step("gates", len(qlog), ", ".join(f"{r.gate}={r.status}" for r in qlog.itertuples()))
    stop = qlog[qlog.status == "STOP"]
    log_df = pd.DataFrame(log).assign(run_id=run_id, computed_at=CFG["computed_on"])
    log_df.loc[len(log_df)] = ["done", 0, f"gates failed: {len(stop)}", "ok" if stop.empty else "STOP", run_id, CFG["computed_on"]]
    write_real({"quality_checks_log": qlog.assign(run_id=run_id, computed_at=CFG["computed_on"]), "run_log": log_df})
    write_duckdb()
    m = manifest()
    print(f"run_id {run_id}; {len(m)} files hashed; manifest sha {hashlib.sha256(m.to_csv(index=False).encode()).hexdigest()[:16]}")
    return 0 if stop.empty else 1


if __name__ == "__main__":
    raise SystemExit(main())
