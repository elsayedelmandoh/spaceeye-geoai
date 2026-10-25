"""
propose: step 8 (entry point): python -m src.generator.simulate
input: R1 outputs in app_data/real, configs/data.yaml (seed, generator block).
output: app_data/sim/{fin_monthly,complaints}.parquet, realism_checks.csv, manifest_sim.csv, dictionaries/*.md;
        private/{answer_key,answer_key_complaints}.parquet, defects_log.csv, stories.csv, dictionaries/*.md.
every file carries the label "Synthetic - for training only" (parquet header metadata, a column in the csv files, a line in the markdown).
exit code 1 if a hard realism check fails (the tables are then not written) or if a gate says STOP.
"""

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.generator import answer, checks, complaints, defects, dictionaries, economy, inputs, observe, stories, truth
from src.generator.inputs import GEN, LABEL, N, SIM, mi
from src.pipeline.common import CFG, PRIVATE

SEED = CFG["seed"]
F = GEN["funding"]


def rng_for(*key: int) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence([SEED, *key])))


@dataclass
class Unit:
    sig: stories.Signals
    st: truth.Setup
    tr: truth.Truth
    rep: observe.Reports
    eco: economy.Economy
    mt: np.ndarray
    kwh: np.ndarray
    home_occ: np.ndarray
    warn: np.ndarray
    level: np.ndarray
    warn_events: list
    distress: np.ndarray = None


def developers(sigs: list[stories.Signals]) -> dict[str, dict]:
    """developer traits: financial strength and reporting style. a developer with a stalled compound is weak; slow ones are medium or weak."""
    out = {}
    for d in sorted({s.developer for s in sigs}):
        rng = rng_for(11, int(d[1:]))
        story = {s.story for s in sigs if s.developer == d}
        if story & {"gradual_stall", "stall_recovery"}:
            strength = "weak"
        elif "slow_late" in story:
            strength = str(rng.choice(["medium", "weak"]))
        else:
            strength = str(rng.choice(["strong", "medium", "weak"], p=F["strength_shares"]))
        pw = {"accurate": 0.4, "optimistic": 0.4, "late": 0.2} if strength != "weak" else {"accurate": 0.2, "optimistic": 0.6, "late": 0.2}
        style = str(rng.choice(list(pw), p=list(pw.values())))
        out[d] = {"strength": strength, "style": style, "optimism": float(rng.uniform(*GEN["reports"]["optimism_points"])) if style == "optimistic" else 0.0}
    return out


def trouble_month(sig: stories.Signals) -> int | None:
    """first month this compound is in visible trouble: grace period over (K3 > 12) or a stall starts."""
    c = [m for m in (next((t for t in range(N) if sig.k3[t] > GEN["warnings"]["grace_months"]), None), sig.onset) if m is not None]
    return min(c) if c else None


def drain_masks(sigs: list[stories.Signals]) -> dict[str, np.ndarray]:
    """a developer with several compounds: trouble in one pulls cash out of the others 2-4 months later, for 3 months (half of their releases)."""
    out = {s.code: np.zeros(N) for s in sigs}
    for d in sorted({s.developer for s in sigs}):
        group = [s for s in sigs if s.developer == d]
        if len(group) < 2:
            continue
        rng = rng_for(12, int(d[1:]))
        for a in group:
            tm = trouble_month(a)
            if tm is None:
                continue
            for b in group:
                if b is not a:
                    start = tm + int(rng.integers(2, 5))
                    out[b.code][start:start + 3] = 0.5
    return out


def build() -> dict:
    real = inputs.load_real()
    sigs = stories.derive(real)
    drv = inputs.drivers(real["drivers_monthly"])
    season = inputs.seasonal_work(drv)
    devs, drains = developers(sigs), drain_masks(sigs)
    healthy = [s.code for s in sigs if s.story == "healthy"]
    bulk_code, viral_code = (str(x) for x in rng_for(10).choice(healthy, 2, replace=False))
    units = []
    for s in sigs:
        rng = rng_for(20, int(s.code[1:]))
        st = truth.sample_setup(s, rng, devs[s.developer], float(rng.uniform(*GEN["cost"]["usd_m2"])))
        tr = truth.run(s, st, season, rng)
        rep = observe.reports(s, st, tr, rng)
        eco = economy.run(s, st, tr, drv, rep.val, ~np.isnan(rep.val), rng, drains[s.code], mi("2025-02-01") if s.code == bulk_code else None)
        mt, kwh, home = observe.meters(s, st, tr, drv, rng)
        warn, level, wev = observe.acud(s, st, tr, eco, rep, rng)
        u = Unit(s, st, tr, rep, eco, mt, kwh, home, warn, level, wev)
        u.distress = answer.distress(u)
        units.append(u)
    return {"units": units, "drv": drv, "devs": devs, "bulk": bulk_code, "viral": viral_code, "real": real}


def fin_monthly(run: dict) -> pd.DataFrame:
    rows = []
    for u in run["units"]:
        rows.append(observe.fin_rows(u.sig, u.st, u.tr, u.eco, u.rep, u.mt, u.kwh, u.warn, u.level, rng_for(30, int(u.sig.code[1:]))))
    return pd.concat(rows, ignore_index=True)


def tables(run: dict) -> dict:
    fin = fin_monthly(run)
    cmp_ = complaints.add_texts(complaints.generate(run["units"], run["viral"], rng_for), rng_for(41))
    cmp_["_true_code"] = cmp_.code
    return {"fin": fin, "cmp": cmp_, "key": answer.answer_key(run["units"], run["devs"])}


def digest(t: dict) -> str:
    h = hashlib.sha256()
    for k in sorted(t):
        h.update(k.encode() + t[k].to_csv(index=False).encode())
    return h.hexdigest()


def write_parquet(df: pd.DataFrame, path) -> None:
    tab = pa.Table.from_pandas(df, preserve_index=False)
    tab = tab.replace_schema_metadata({**(tab.schema.metadata or {}), b"synthetic_label": LABEL.encode()})
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(tab, path)


def write_csv(df: pd.DataFrame, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.assign(synthetic_label=LABEL).to_csv(path, index=False, encoding="utf-8")


def sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rerun_gates() -> pd.DataFrame:
    """R1's gates again on the real tables, with the generator's tables added to the no-names scan. writes nothing into R1's tables."""
    from src.pipeline import gates
    real = inputs.load_real()
    t = {k: pd.read_parquet(inputs.REAL / f"{k}.parquet") for k in ("compounds", "sat_quarterly", "sat_yearly", "statements", "eval_outcomes", "drivers_monthly", "rules")}
    return gates.run_gates(t, real["kpi_values"])


def main() -> int:
    run1, run2 = build(), build()
    t1, t2 = tables(run1), tables(run2)
    h1, h2 = digest(t1), digest(t2)
    units, real = run1["units"], run1["real"]
    fin, cmp_, key = t1["fin"], t1["cmp"], t1["key"]
    fin_def, cmp_def, dlog = defects.plant(fin, cmp_, units, rng_for(50))
    res, anchors, misses = checks.run(units, run1["drv"], fin, cmp_, fin_def, cmp_def, dlog, real, h1 == h2, f"two builds, sha256 {h1[:16]} / {h2[:16]}")
    SIM.mkdir(parents=True, exist_ok=True)
    res.assign(synthetic_label=LABEL).to_csv(SIM / "realism_checks.csv", index=False, encoding="utf-8")
    for _, r in res.iterrows():
        print(f"{'ok  ' if r.ok else 'FAIL'} [{r.kind}] {r.check}: {r.value}")
    hard_fail = res[(res.kind == "hard") & ~res.ok]
    if len(hard_fail):
        print(f"{len(hard_fail)} hard realism checks failed: the output must not be used")
        return 1
    pub_f = ["code", "month", "planned_pct", "reported_pct", "report_date", "units_sold", "avg_price_egp", "collections_egp", "cover_required_egp", "cover_balance_egp",
             "cost_to_complete_egp", "land_due_egp", "land_paid_egp", "land_months_late", "roads_paved_share", "meters_active", "kwh", "status_level", "warning_issued"]
    pub_c = ["complaint_id", "code", "created_at", "channel", "category", "text_ar"]
    write_parquet(fin_def[pub_f], SIM / "fin_monthly.parquet")
    write_parquet(cmp_def[pub_c], SIM / "complaints.parquet")
    write_parquet(key, PRIVATE / "answer_key.parquet")
    write_parquet(answer.complaint_truth(cmp_def), PRIVATE / "answer_key_complaints.parquet")
    write_csv(dlog.drop(columns="synthetic_label"), PRIVATE / "defects_log.csv")
    write_csv(pd.DataFrame([{"code": u.sig.code, "story": u.sig.story, "reason": u.sig.why} for u in units]), PRIVATE / "stories.csv")
    anchors.assign(synthetic_label=LABEL).to_csv(SIM / "anchor_diffs.csv", index=False, encoding="utf-8")
    misses.assign(synthetic_label=LABEL).to_csv(SIM / "anchor_misses.csv", index=False, encoding="utf-8")
    for n in ("fin_monthly", "complaints"):
        dictionaries.write(n, SIM / "dictionaries")
    for n in ("answer_key", "answer_key_complaints", "defects_log"):
        dictionaries.write(n, PRIVATE / "dictionaries")
    files = [SIM / "fin_monthly.parquet", SIM / "complaints.parquet", PRIVATE / "answer_key.parquet", PRIVATE / "answer_key_complaints.parquet", PRIVATE / "defects_log.csv", PRIVATE / "stories.csv",
             SIM / "realism_checks.csv", SIM / "anchor_diffs.csv", SIM / "anchor_misses.csv"]
    man = pd.DataFrame({"file": [str(p.relative_to(PRIVATE.parent)).replace("\\", "/") for p in files], "sha256": [sha(p) for p in files]})
    man.assign(synthetic_label=LABEL).to_csv(SIM / "manifest_sim.csv", index=False, encoding="utf-8")
    print(f"written {len(files)} files; tables sha256 {h1[:16]}")
    g = rerun_gates()
    g.to_csv(SIM / "gates_after_r2.csv", index=False, encoding="utf-8")
    for r in g.itertuples():
        print(f"gate {r.gate}: {r.status} ({r.value[:110]})")
    return 1 if (g.status == "STOP").any() else 0


if __name__ == "__main__":
    raise SystemExit(main())
