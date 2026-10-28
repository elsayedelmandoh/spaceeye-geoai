"""
propose: step 1. replace every compound and developer name with a random code and copy the audited sources into app_data/raw.
input: audited files under real_data (never modified), configs/data.yaml.
output: private/code_map.csv, private/evidence_sources.csv (names stay here), app_data/raw/*.csv, raw/boundaries.geojson (codes only).
"""

import glob
import json

import numpy as np
import pandas as pd
from shapely import affinity
from shapely.geometry import shape

from src.pipeline.common import CFG, PRIVATE, RAW, SRC, src

FACTS = src("facts")


def _csv(path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def _boundary_features() -> list[dict]:
    """20 boundaries from the location audit + 2 added; a compound enters only with a boundary (confidence >= 80%)."""
    feats = json.loads(src("boundaries").read_text(encoding="utf-8"))["features"]
    added = json.loads(src("boundaries_added").read_text(encoding="utf-8"))["features"]
    for f in added:  # added file has one confidence field; medium-high is read as medium
        c = f["properties"]["confidence"]
        f["properties"]["boundary_confidence"] = "medium" if c.startswith("medium") else c
    return feats + added


def code_map() -> pd.DataFrame:
    """random codes from the fixed seed. compounds C01.., developers D01.. (private)."""
    reg = _csv(FACTS / "r_compounds_candidate.csv")
    ids = sorted(f["properties"]["compound_id"] for f in _boundary_features())
    reg = reg[reg.project_id.isin(ids)].sort_values("project_id").reset_index(drop=True)
    rng = np.random.default_rng(CFG["seed"])
    reg["code"] = [f"C{i + 1:02d}" for i in rng.permutation(len(reg))]
    devs = sorted(reg.developer.unique())
    dmap = {d: f"D{i + 1:02d}" for d, i in zip(devs, rng.permutation(len(devs)))}
    reg["developer_code"] = reg.developer.map(dmap)
    out = reg[["project_id", "code", "name_en", "name_ar", "developer", "developer_code", "district"]]
    PRIVATE.mkdir(parents=True, exist_ok=True)
    out.sort_values("code").to_csv(PRIVATE / "code_map.csv", index=False, encoding="utf-8-sig")
    return out


def _w(df: pd.DataFrame, name: str) -> None:
    df.to_csv(RAW / name, index=False)


def _facts(cm: pd.DataFrame) -> None:
    pid2code = cm.set_index("project_id").code
    reg = _csv(FACTS / "r_compounds_candidate.csv")
    reg = reg[reg.project_id.isin(pid2code.index)].copy()
    reg["code"] = reg.project_id.map(pid2code)
    reg["developer_code"] = reg.project_id.map(cm.set_index("project_id").developer_code)
    keep = ["code", "developer_code", "district", "land_area_m2", "units_total", "first_public_mention", "delivery_status",
            "delivery_status_published", "progress_latest_pct", "progress_latest_published"]
    _w(reg[keep].sort_values("code"), "compounds.csv")

    prom = _csv(FACTS / "r_delivery_promises_candidate.csv")
    prom["code"] = prom.project_id.map(pid2code)
    cols = ["code", "record_id", "attribute", "published_date", "promise_scope", "promise_kind", "period_start", "period_end", "qualifier", "verdict", "origin"]
    _w(prom[prom.code.notna()][cols].sort_values(["code", "published_date", "record_id"]), "promises.csv")

    prog = _csv(FACTS / "r_progress_announced_candidate.csv")
    prog["code"] = prog.compound_id.map(pid2code)
    cols = ["code", "record_id", "published_date", "progress_pct", "qualifier", "scope", "verdict"]
    _w(prog[prog.code.notna()][cols].sort_values(["code", "published_date"]), "progress.csv")

    ev = _csv(FACTS / "r_project_events_candidate.csv")
    ev["code"] = ev.project_id.map(pid2code)
    cols = ["event_id", "code", "event_type", "scope", "event_date", "event_period", "published_date", "record_id", "origin"]
    _w(ev[ev.code.notna()][cols].sort_values("event_id"), "events.csv")

    out = _csv(FACTS / "eval_outcomes_candidate.csv")
    out["code"] = out.project_id.map(pid2code)
    out["case"] = "E" + out.case_id.str.extract(r"C(\d)")[0]
    cols = ["case", "code", "outcome_type", "promise_original_period", "promise_original_published", "outcome_date", "outcome_first_published",
            "delay_months_vs_promise", "evidence_gate", "outcome_visible_by_2024Q2", "outcome_visible_by_2025Q2"]
    _w(out[cols].sort_values("case"), "eval_outcomes.csv")

    # private evidence file: where every fact comes from (names allowed here)
    names = cm.set_index("project_id").name_en
    rows = []
    for df, pcol, kind in [(prom, "project_id", "promise"), (prog, "compound_id", "progress"), (ev, "project_id", "event")]:
        d = df.rename(columns={pcol: "pid"})
        d = d.assign(kind=kind, url=d.get("url", d.get("source_url")), quote=d.evidence_quote)
        rows.append(d[["pid", "kind", "record_id", "published_date", "publisher", "url", "quote"]])
    evid = _csv(FACTS / "eval_evidence_candidate.csv")
    evid = evid.assign(pid=evid.case.map(out.set_index("case_id").project_id), kind="eval_" + evid.role, url=evid.source_url, quote=evid.evidence_quote)
    rows.append(evid[["pid", "kind", "record_id", "published_date", "publisher", "url", "quote"]])
    allr = pd.concat(rows, ignore_index=True)
    allr = allr[allr.pid.isin(pid2code.index)]
    allr.insert(0, "code", allr.pid.map(pid2code))
    allr.insert(1, "name_en", allr.pid.map(names))
    allr.drop(columns="pid").sort_values(["code", "kind", "published_date"]).to_csv(PRIVATE / "evidence_sources.csv", index=False, encoding="utf-8-sig")


def _geo(cm: pd.DataFrame) -> None:
    pid2code = cm.set_index("project_id").code
    feats = []
    for f in _boundary_features():
        p = f["properties"]
        props = {"code": pid2code[p["compound_id"]], "boundary_confidence": p["boundary_confidence"],
                 "area_m2": float(p["area_m2"]), "area_ratio": float(p["area_ratio"])}
        feats.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})
    feats.sort(key=lambda f: f["properties"]["code"])
    (RAW / "boundaries.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, indent=1), encoding="utf-8")


def _satellite(cm: pd.DataFrame) -> None:
    pid2code = cm.set_index("project_id").code
    dw = pd.read_csv(src("dw_polygons"))
    dw = dw[dw.period != "YEAR"]
    dw["qi"] = (dw.year - 2016) * 4 + dw.period.str[1].astype(int) - 1
    _w(dw[["osm_id", "qi", "n_images", "built_prob_mean"]].sort_values(["osm_id", "qi"]), "dw_polygons_quarterly.csv")

    dc = pd.read_csv(src("dw_compounds"))
    dc["code"] = dc.pid.map(pid2code)
    _w(dc[dc.code.notna()][["code", "qi", "n_images", "built_prob_mean"]].sort_values(["code", "qi"]), "dw_compounds_quarterly.csv")

    s4 = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(str(SRC / CFG["sources"]["s4_windows_glob"])))])
    s4["pid"] = s4.pid.map(lambda p: pid2code.get(p, p))
    s4 = s4[s4.pid.str.startswith(("C", "way/"))]  # drops the 3 reference polygons and compounds that were removed
    s4.insert(1, "qi", (s4.Y - 2016) * 4 + 1)       # windows end 30 June
    _w(s4.drop(columns="Y").sort_values(["pid", "qi"]), "s4_windows_q2.csv")

    wq = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(str(SRC / CFG["sources"]["s4_windows_quarterly_glob"])))])
    _w(wq.sort_values(["pid", "qi"]), "s4_windows_plots_quarterly.csv")  # windows ending every quarter, plots only (pid = OSM id)

    lab = pd.read_csv(src("plot_labels"), usecols=["osm_id", "year", "area_ha", "growth", "stable", "presence_fraction", "d_presence_fraction"])
    _w(lab.sort_values(["osm_id", "year"]), "plot_labels.csv")
    _w(pd.read_csv(src("plot_split")), "plot_split.csv")

    # vegetation share already audited for the 3 compounds whose boundary is an OSM plot
    m = pd.read_csv(src("plot_to_compound"))
    m = m[m.match_type == "accepted_boundary_polygon"].assign(code=lambda d: d.compound_id.map(pid2code))
    v = pd.read_csv(src("veg_fixed")).merge(m[["osm_id", "code"]], left_on="plot_id", right_on="osm_id")
    v = v.rename(columns={"veg_share_fullpolygon": "veg_share", "ndvi_mean_fullpolygon": "ndvi_mean"})
    _w(v[["code", "year", "n_scenes", "veg_share", "ndvi_mean"]].sort_values(["code", "year"]), "veg_audited.csv")

    h = pd.read_csv(src("heights"))
    h["code"] = h.compound_id.map(pid2code)
    h = h[h.code.notna()]
    h = h[h.published] if "published" in h else h[h.year <= CFG["heights_max_year"]]
    cols = ["code", "year", "source", "n_built_cells", "height_mean_m", "height_p90_m", "share_built_ge20m"]
    h["source"] = np.where(h.source.str.startswith("OBT"), "OBT", "model")
    _w(h[cols].sort_values(["code", "year"]), "heights.csv")


def _plot_overlap() -> None:
    """share of every compound's area covered by each OSM plot (local metric scale, plots only). used to drop leaking plots in the backtest variant of A."""
    k = np.cos(np.radians(30.1))

    def metric(g):
        return affinity.scale(shape(g), xfact=111320 * k, yfact=110574, origin=(0, 0))

    plots = {f["properties"]["osm_id"]: metric(f["geometry"]) for f in json.loads(src("osm_polygons").read_text(encoding="utf-8"))["features"]}
    rows = []
    for f in json.loads((RAW / "boundaries.geojson").read_text(encoding="utf-8"))["features"]:
        cg = metric(f["geometry"])
        for osm_id, pg in plots.items():
            if pg.intersects(cg):
                inter = pg.intersection(cg).area
                rows.append((osm_id, f["properties"]["code"], round(inter / cg.area, 4), round(inter / pg.area, 4), round(inter / cg.union(pg).area, 4)))
    out = pd.DataFrame(rows, columns=["osm_id", "code", "share_of_compound", "share_of_plot", "iou"])
    _w(out[out.share_of_compound >= 0.01].sort_values(["code", "osm_id"]), "plot_compound_overlap.csv")


def _reference() -> None:
    _w(pd.read_csv(src("macro")), "macro_monthly.csv")
    _w(pd.read_csv(src("weather")), "weather_monthly.csv")
    _w(pd.read_csv(src("decree"))[["area_class", "project_or_phase_area_feddan", "min_financial_cover_pct_of_phase_construction_cost_Art3_3",
                                   "cover_cancelled_at_progress_pct_Art4"]], "decree_2184.csv")


def run() -> pd.DataFrame:
    RAW.mkdir(parents=True, exist_ok=True)
    cm = code_map()
    _facts(cm)
    _geo(cm)
    _satellite(cm)
    _plot_overlap()
    _reference()
    return cm


if __name__ == "__main__":
    print(len(run()), "compounds coded")
