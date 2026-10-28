"""
propose: step 5. the 9 quality gates of docs/plan/project-plan.md section 9 plus a "no names" gate.
input: the built tables, kpi_values, the files in app_data. output: quality_checks_log rows (gate, status PASS/FLAG/FIX/STOP, value, impact).
the no-names gate never writes a matched name anywhere: it reports file paths and counts only.
"""

import json
import re
import unicodedata

import duckdb
import pandas as pd

from src.pipeline.build_real import ORIGINS
from src.pipeline.common import (
    APP,
    CFG,
    N_Q,
    PRIVATE,
    months_between,
    qend,
    qindex,
    src,
)

ACCEPTED = ("CONFIRMED", "CONFIRMED_MINOR_FIX", "AUDIT_LIVE_CHECKED")
TEXT_EXT = {".csv", ".json", ".geojson", ".md", ".txt", ".yaml", ".yml"}
AR = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ـ": "", "ً": "", "ٌ": "", "ٍ": "", "َ": "", "ُ": "", "ِ": "", "ّ": "", "ْ": ""})


def _row(gate, dimension, rule, threshold, owner, on_fail, value, ok, impact, flag_status="FLAG"):
    status = "PASS" if ok else flag_status
    return {"gate": gate, "dimension": dimension, "rule": rule, "threshold": threshold, "owner": owner, "on_failure": on_fail, "value": str(value), "status": status, "impact": impact}


# ---- the nine gates ---------------------------------------------------------------------------------------------------------------------

def g_source(stm: pd.DataFrame) -> dict:
    excl = pd.read_csv(src("facts") / "records_excluded_misinterpreted.csv", encoding="utf-8-sig").record_id
    ids = stm.record_id.dropna().str.split(";").explode()
    bad = int(stm.record_id.isna().sum() + (stm.verdict.notna() & ~stm.verdict.isin(ACCEPTED)).sum() + ids.isin(excl).sum())
    return _row("source", "Accuracy", "every fact has a record_id and an accepted review verdict", "100%", "R2", "fix: excluded", f"{bad} bad of {len(stm)}", bad == 0,
                "bad statements would change K3 and may-be-complete", "FIX")


def g_completeness(sat: pd.DataFrame, asof: int) -> dict:
    now = sat[sat.qi == asof]
    share = round(100 * sat.K4.mean(), 1)
    return _row("completeness", "Completeness", ">= 6 dynamic world images in the quarter", "all compounds at the as-of quarter", "R3", "flag: not assessable",
                f"{int(now.K4.sum())} of {len(now)} assessable at {CFG['asof']}; {share}% of all compound-quarters", bool(now.K4.all()), "a compound below the minimum gets no level")


def g_validity(t: dict, kpi: pd.DataFrame) -> dict:
    sq = t["sat_quarterly"]
    prob = ["built_prob_mean", "activity_prob"] + [c for c in sq if c.startswith("dw12_")]
    bad = int(sum(((sq[c].dropna() < 0) | (sq[c].dropna() > 1)).sum() for c in prob) + (sq.n_images < 0).sum() + (kpi.K2.dropna() < 0).sum()
              + (~kpi.level.dropna().isin([1, 2, 3, 4])).sum())
    for col in ("first_deadline", "first_deadline_published", "handover_first_published"):
        bad += int(pd.to_datetime(t["compounds"][col], errors="coerce").isna().sum() - t["compounds"][col].isna().sum())
    bad += int(pd.to_datetime(t["statements"].published_date, errors="coerce").isna().sum())
    return _row("validity", "Validity", "probabilities 0-1, counts >= 0, levels 1-4, dates valid", "0 violations", "R1", "stop", f"{bad} violations", bad == 0, "invalid values break K1, A and K3", "STOP")


def g_uniqueness(t: dict, kpi: pd.DataFrame) -> dict:
    d = (int(t["sat_quarterly"].duplicated(["code", "qi"]).sum()) + int(kpi.duplicated(["code", "qi"]).sum()) + int(t["sat_yearly"].duplicated(["code", "year"]).sum())
         + int(t["compounds"].code.duplicated().sum()) + int(t["statements"].statement_id.duplicated().sum()))
    return _row("uniqueness", "Uniqueness", "(compound, quarter) and (compound, year) are unique", "0 duplicates", "R1", "stop", f"{d} duplicates", d == 0, "duplicates double-count a quarter", "STOP")


def g_consistency(t: dict, kpi: pd.DataFrame) -> dict:
    codes = set(t["compounds"].code)
    n = len(codes)
    stray = sum(len(set(df.code) - codes) for df in (t["sat_quarterly"], t["sat_yearly"], t["statements"], t["eval_outcomes"], kpi))
    counts_ok = (len(t["sat_quarterly"]) == n * N_Q and len(t["sat_yearly"]) == n * 11
                 and len(kpi) == n * (qindex(CFG["last_quarter"]) - qindex(CFG["backtest"]["first_quarter"]) + 1))
    return _row("consistency", "Consistency", "every compound_id is in the register; row counts equal after each join", "0 stray codes, counts as expected", "R1", "stop",
                f"{stray} stray codes; counts ok={counts_ok}", stray == 0 and counts_ok, "a join that changes rows silently changes every KPI", "STOP")


def g_freshness(sat: pd.DataFrame) -> dict:
    last = int(sat.dropna(subset=["built_prob_mean"]).qi.max())
    lag = months_between(qend(last), pd.Timestamp(CFG["computed_on"]))
    return _row("freshness", "Freshness", "last quarter is at most one quarter before the computation date", "<= 3 months", "R3", "flag: stale",
                f"last quarter {CFG['last_quarter']}, {lag} months before {CFG['computed_on']}", lag <= 3, "stale data means levels describe the past")


def g_separation(t: dict, kpi: pd.DataFrame) -> dict:
    cols = {tab: set(df.columns) for tab, df in {**t, "kpi_values": kpi}.items()}
    missing = [f"{tab}.{c}" for tab, cs in cols.items() for c in cs if c not in {**ORIGINS, "kpi_values": {c: "derived" for c in kpi}}[tab]]
    gen_in_kpi = [c for c in ("land_area_origin", "units_origin", "floors_origin") if c in kpi]
    prefixed = [tab for tab in cols if tab.startswith(("g_", "fin_", "complaints"))]
    bad = len(missing) + len(gen_in_kpi) + len(prefixed)
    return _row("separation", "Consistency", "no generated table is joined to a real compound; every column carries an origin type", "0", "R1", "stop",
                f"{len(missing)} columns without origin, {len(prefixed)} generated tables", bad == 0, "mixing generated and real numbers on the map", "STOP")


def g_data_or_city(kpi: pd.DataFrame) -> dict:
    ok = kpi[kpi.level.notna()]
    share = ok.groupby("quarter").K2.apply(lambda s: (s == 1).mean())
    hits = list(share[share > 0.30].index)
    return _row("data_or_city", "Accuracy", "if more than 30% of compounds move to 'no change' in the same quarter it is an event in the source", "<= 30%",
                "R4", "flag the quarter and review", f"{len(hits)} quarters flagged: {', '.join(hits) if hits else 'none'}", not hits, "flagged quarters may be a data event, not the city")


def g_stuck(sat: pd.DataFrame) -> dict:
    n = 0
    for _, g in sat.sort_values("qi").groupby("code"):
        v = g.built_prob_mean.dropna().round(12)
        n += int(((v == v.shift(1)) & (v == v.shift(2)) & (v == v.shift(3))).sum())
    return _row("stuck_series", "Accuracy", "a value exactly identical for 4 consecutive quarters", "0", "R3", "flag and review", f"{n} stuck points", n == 0, "a frozen series reads as 'no change'")


# ---- no names -----------------------------------------------------------------------------------------------------------------------------

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s).lower())
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).translate(AR)
    return re.sub(r"\s+", " ", s).strip()


def forbidden_names() -> set[str]:
    """every compound and developer name of the 29 audited compounds (english and arabic), with parenthesis and slash variants."""
    reg = pd.read_csv(src("facts") / "r_compounds_candidate.csv", encoding="utf-8-sig")
    ev = pd.read_csv(src("facts") / "eval_outcomes_candidate.csv", encoding="utf-8-sig")
    raw = list(reg.name_en) + list(reg.name_ar.dropna()) + list(reg.developer) + list(ev.compound)
    for key in ("boundaries", "boundaries_added"):
        raw += [f["properties"].get("name", "") for f in json.loads(src(key).read_text(encoding="utf-8"))["features"]]
    out = set()
    for s in raw:
        s = str(s).replace("also written", "(")
        parts = re.split(r"[()/]", s) + [re.sub(r"\(.*", "", s)]
        out |= {_norm(p.strip(' "')) for p in parts if len(p.strip(' "')) >= 3}
    return out


def _hits(text: str, pats: list[tuple[str, re.Pattern]]) -> int:
    t = _norm(text)
    return sum(1 for _, p in pats if p.search(t))


def _patterns(names: set[str]) -> list[tuple[str, re.Pattern]]:
    return [(n, re.compile(r"(?<![a-z0-9_])" + re.escape(n) + r"(?![a-z0-9_])" if n.isascii() else re.escape(n))) for n in sorted(names)]


def _file_texts(path):
    """yield text chunks of one file: text files, parquet strings and column names, duckdb varchar values and names, binaries as bytes."""
    yield path.name
    ext = path.suffix.lower()
    if ext in TEXT_EXT:
        yield path.read_text(encoding="utf-8", errors="ignore")
    elif ext == ".parquet":
        df = pd.read_parquet(path)
        yield " ".join(map(str, df.columns))
        for c in df.select_dtypes(include=["object", "string"]).columns:
            yield "\n".join(df[c].dropna().astype(str).unique())
    elif ext == ".duckdb":
        con = duckdb.connect(str(path), read_only=True)
        for (tab,) in con.execute("select table_name from information_schema.tables").fetchall():
            df = con.execute(f'select * from "{tab}"').df()
            yield tab + " " + " ".join(map(str, df.columns))
            for c in df.select_dtypes(include=["object", "string"]).columns:
                yield "\n".join(df[c].dropna().astype(str).unique())
        con.close()
    else:
        yield path.read_bytes().decode("latin-1")


def generator_files() -> list:
    """the private tables and dictionaries written by the generator (R2); they live outside app_data but must be free of names too."""
    names = ("answer_key.parquet", "answer_key_complaints.parquet", "defects_log.csv", "stories.csv")
    return [PRIVATE / n for n in names if (PRIVATE / n).exists()] + sorted((PRIVATE / "dictionaries").glob("*.md"))


def g_no_names(root=APP, extra=None) -> dict:
    """scan every file under `root` plus the generator's private tables (answer key, defects log, dictionaries)."""
    pats = _patterns(forbidden_names())
    extra = generator_files() if extra is None else extra
    files = [(p, str(p.relative_to(root))) for p in sorted(root.rglob("*")) if p.is_file()] + [(p, "private/" + p.name) for p in extra]
    bad = {}
    for p, label in files:
        n = sum(_hits(chunk, pats) for chunk in _file_texts(p))
        if n:
            bad[label] = n
    return _row("no_names", "Privacy", "no compound or developer name (english or arabic) in any output, generator tables included", "0 files with a match", "R1", "stop",
                f"{len(pats)} patterns, {len(files)} files; files with a match: {', '.join(bad) if bad else 'none'}", not bad, "names appear only in the backtest slide, never in data", "STOP")


# ---- extra check (not one of the nine) ---------------------------------------------------------------------------------------------------

def c_veg_pull() -> dict:
    """the new pull must reproduce the audited vegetation rows of the 3 compounds that have them."""
    aud = pd.read_csv(APP / "raw" / "veg_audited.csv").merge(pd.read_csv(APP / "raw" / "veg_pulled.csv"), on=["code", "year"], suffixes=("", "_p"))
    d = float((aud.veg_share - aud.veg_share_p).abs().max())
    return _row("veg_pull_check", "Accuracy", "pulled vegetation share equals the audited file on the 3 shared compounds", "max diff <= 0.02", "R3", "flag", f"max diff {d:.4f} on {len(aud)} rows", d <= 0.02,
                "vegetation drives the may-be-complete flag")


def run_gates(t: dict, kpi: pd.DataFrame, check_names: bool = True) -> pd.DataFrame:
    sat, asof = t["sat_quarterly"], qindex(CFG["asof"])
    rows = [g_source(t["statements"]), g_completeness(sat, asof), g_validity(t, kpi), g_uniqueness(t, kpi), g_consistency(t, kpi), g_freshness(sat), g_separation(t, kpi),
            g_data_or_city(kpi), g_stuck(sat), c_veg_pull()]
    if check_names:
        rows.append(g_no_names())
    return pd.DataFrame(rows)


if __name__ == "__main__":  # re-scan app_data for names, e.g. after writing the report
    r = g_no_names()
    print(r["status"], r["value"])
    raise SystemExit(0 if r["status"] == "PASS" else 1)
