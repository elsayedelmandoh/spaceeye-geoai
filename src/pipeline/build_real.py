"""
propose: step 2. build the real tables (one function per table) from the coded raw files.
origin types: real (public, audited), derived (computed by a tested method), generated (missing, drawn realistic), key.
input: app_data/raw/*.csv, raw/boundaries.geojson. output: dict of DataFrames + ORIGINS (origin of every column).
"""

import json

import numpy as np
import pandas as pd

from src.pipeline import activity
from src.pipeline.common import CFG, N_Q, RAW, qlabel

DW_CLASSES = ["water", "trees", "grass", "flooded_vegetation", "crops", "shrub_and_scrub", "built", "bare", "snow_and_ice"]
FIRST_KINDS = ["start", "project_delivery", "phased_start_to_end", "phased_end"]  # promises that carry a delivery date
HANDOVER_EVENTS = ["delivery_start", "delivery_complete", "delivery_progress"]


def _csv(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW / name)


def first_promise(prom: pd.DataFrame) -> pd.DataFrame:
    """per compound, the earliest published promise that has an end date (later promises never reset the clock)."""
    p = prom[prom.detail.isin(FIRST_KINDS) & prom.period_end.notna()]
    return p.sort_values(["code", "published_date", "period_end"]).groupby("code").head(1).set_index("code")


def boundaries() -> pd.DataFrame:
    feats = json.loads((RAW / "boundaries.geojson").read_text(encoding="utf-8"))["features"]
    return pd.DataFrame([f["properties"] for f in feats]).set_index("code")


def _handover_dates(comp_raw: pd.DataFrame) -> pd.Series:
    """first date a handover (start, progress or completion) was published, from events and the register's delivery status."""
    ev = _csv("events.csv")
    d = ev[ev.event_type.isin(HANDOVER_EVENTS)].groupby("code").published_date.min()
    st = comp_raw.delivery_status_published.where(comp_raw.delivery_status != "no_delivery_information")
    return pd.concat([d, st.dropna()]).groupby(level=0).min()


def compounds() -> pd.DataFrame:
    rng = np.random.default_rng(CFG["seed"])
    c, k = _csv("compounds.csv").set_index("code").sort_index(), CFG["compounds"]
    out = pd.DataFrame(index=c.index)
    out["developer_code"], out["district"] = c.developer_code, c.district
    out["land_area_m2"], out["land_area_origin"] = c.land_area_m2, "real"
    for code in out.index[out.land_area_m2.isna()]:  # missing: drawn inside the range of the same district
        known = c.land_area_m2[(c.district == c.at[code, "district"]) & c.land_area_m2.notna()]
        out.at[code, "land_area_m2"], out.at[code, "land_area_origin"] = round(rng.uniform(known.min(), known.max())), "generated"
    out["floors_allowed"], out["floors_origin"] = k["floors"], "generated"
    out["coverage_max"] = k["coverage"]
    out["bua_m2"] = (out.land_area_m2 * np.minimum(k["coverage"] * k["floors"], k["far_cap"])).round()
    u = rng.uniform(*k["unit_m2"], len(out))
    gen = c.units_total.isna()
    out["units"] = np.where(gen, (out.bua_m2 / u).round(), c.units_total).astype(int)
    out["units_origin"] = np.where(gen, "generated", "real")
    feddan = out.land_area_m2 / k["feddan_m2"]
    out["cover_pct"] = np.select([feddan < 50, feddan < 100], [k["cover_class"]["limited"], k["cover_class"]["small"]], 0.10) * 100
    fp = first_promise(_csv("promises.csv").rename(columns={"promise_kind": "detail"}))
    out["first_deadline"] = fp.period_end.reindex(out.index)
    out["first_deadline_published"] = fp.published_date.reindex(out.index)
    b = boundaries()
    out["boundary_confidence"], out["boundary_area_m2"] = b.boundary_confidence, b.area_m2
    out["handover_first_published"] = _handover_dates(c).reindex(out.index)
    return out.reset_index()


def sat_quarterly() -> pd.DataFrame:
    """compound x quarter 2016Q1-2026Q3: dynamic world series, 12-month class shares, K1, K4. A and K2 are added later."""
    dw = pd.concat([_csv("dw_compounds_quarterly.csv"), _csv("dw_compounds_new.csv")]).drop_duplicates(["code", "qi"])
    dw = dw[dw.code.isin(_csv("compounds.csv").code)]  # the pulled file can hold compounds outside the scope
    codes = sorted(dw.code.unique())
    grid = pd.MultiIndex.from_product([codes, range(N_Q)], names=["code", "qi"]).to_frame(index=False)
    out = grid.merge(dw, on=["code", "qi"], how="left")
    assert len(out) == len(grid), "join changed the row count"
    win = activity.load_s4().reset_index()
    win = win[win.pid.isin(codes)].rename(columns={"pid": "code", **{c: "dw12_" + c for c in DW_CLASSES}})
    out = out.merge(win[["code", "qi"] + ["dw12_" + c for c in DW_CLASSES]], on=["code", "qi"], how="left")
    assert len(out) == len(grid), "join changed the row count"
    k1 = activity.rolling_delta(activity.wide(dw, "code")).stack(future_stack=True).rename("K1").reset_index()
    out = out.merge(k1, on=["code", "qi"], how="left")
    out["quarter"] = out.qi.map(qlabel)
    out["K4"] = out.n_images >= CFG["n_images_min"]  # boundaries of all 22 compounds are accepted
    cols = ["code", "quarter", "qi", "built_prob_mean", "n_images"] + ["dw12_" + c for c in DW_CLASSES] + ["K1", "K4"]
    return out[cols].sort_values(["code", "qi"]).reset_index(drop=True)


def sat_yearly(codes: list[str]) -> pd.DataFrame:
    """compound x year 2016-2026: vegetation share (audited rows first, then the pull) and building heights."""
    aud, pull = _csv("veg_audited.csv"), _csv("veg_pulled.csv")
    veg = pd.concat([aud, pull]).drop_duplicates(["code", "year"])[["code", "year", "veg_share"]]
    h = _csv("heights.csv")
    h["height_origin"] = np.where(h.source == "OBT", "real", "derived")
    grid = pd.MultiIndex.from_product([codes, range(2016, 2027)], names=["code", "year"]).to_frame(index=False)
    out = grid.merge(veg, on=["code", "year"], how="left").merge(h.drop(columns="source"), on=["code", "year"], how="left")
    assert len(out) == len(grid), "join changed the row count"
    out["veg_origin"] = np.where(out.veg_share.notna(), "derived", None)
    return out


def statements() -> pd.DataFrame:
    """promises, progress statements and project events, one row each, published dates only (no text)."""
    pr = _csv("promises.csv").rename(columns={"attribute": "subtype", "promise_scope": "scope", "promise_kind": "detail"})
    pr["kind"] = "promise"
    pg = _csv("progress.csv").rename(columns={"progress_pct": "value"})
    pg["kind"], pg["subtype"] = "progress", "progress_pct"
    ev = _csv("events.csv").rename(columns={"event_type": "subtype"})
    ev["kind"] = "event"
    dates = ev.event_period.fillna(ev.event_date).str.split("..", regex=False, expand=True)
    ev["period_start"], ev["period_end"] = dates[0], dates[1].fillna(dates[0])
    cols = ["code", "kind", "subtype", "detail", "published_date", "scope", "period_start", "period_end", "value", "qualifier", "record_id", "verdict", "origin"]
    out = pd.concat([pr, pg, ev], ignore_index=True).reindex(columns=cols)
    out["origin"] = "real"
    out = out.sort_values(["code", "published_date", "kind", "record_id"]).reset_index(drop=True)
    out.insert(0, "statement_id", [f"S{i + 1:04d}" for i in range(len(out))])
    return out


def eval_outcomes(comp: pd.DataFrame) -> pd.DataFrame:
    e = _csv("eval_outcomes.csv")
    e["promise_original_end"] = e.promise_original_period.str.split("..", regex=False).str[1]
    e["first_deadline"] = e.code.map(comp.set_index("code").first_deadline)
    return e


def drivers_monthly() -> pd.DataFrame:
    m, w, k = _csv("macro_monthly.csv"), _csv("weather_monthly.csv"), CFG["drivers"]
    d = m[["month", "egp_per_usd_avg_mid", "cbe_overnight_deposit_rate_pct", "rebar_egp_per_t", "cement_opc_egp_per_t"]].copy()
    d.columns = ["month", "usd_egp", "policy_rate_pct", "rebar_egp_t", "cement_egp_t"]
    d["materials_index"] = ((d.rebar_egp_t / d.rebar_egp_t.iloc[0] + d.cement_egp_t / d.cement_egp_t.iloc[0]) / 2 * 100).round(1)
    d["shock_month"] = d.usd_egp.pct_change() >= k["shock_fx_mom"]
    d = d.merge(w[["month", "tmax_mean_c", "days_tmax_ge40"]], on="month", how="left")

    def days_in(month: str, ranges: list) -> int:
        days = pd.date_range(month + "-01", pd.Period(month).end_time.normalize(), freq="D")
        return int(sum(((days >= a) & (days <= b)).sum() for a, b in ranges))

    d["ramadan_days"] = [days_in(x, k["ramadan"]) for x in d.month]
    d["eid_days"] = [days_in(x, k["eid"]) for x in d.month]
    return d


def rules() -> pd.DataFrame:
    dec = _csv("decree_2184.csv")
    rows = [("decree_2184", "art 3(3)", f"financial cover on phase construction cost, project class {r.area_class} ({r.project_or_phase_area_feddan} feddan)",
             r.min_financial_cover_pct_of_phase_construction_cost_Art3_3, "% of cost") for r in dec.itertuples()]
    rows += [("decree_2184", "art 4", f"cover cancelled at progress, class {r.area_class}", r.cover_cancelled_at_progress_pct_Art4, "% progress") for r in dec.itertuples()]
    rows += [("decree_2184", "art 3(6)", "refund reserve on total collections of each phase", 5, "% of collections"),
             ("decree_2184", "art 5", "delivery grace after the promised date", 12, "months"),
             ("decree_2184", "art 5", "refund right once delivery is later than", 24, "months"),
             ("law_119_2008", "art 54", "fine for building violations, lower bound (per violation)", 200, "EGP"),
             ("law_119_2008", "art 62", "occupancy certificate issued by the supervising engineer after completion; utilities wait for it", np.nan, ""),
             ("law_119_2008", "art 67", "sale and rent contracts must carry licence number, floors and units", np.nan, ""),
             ("acud_conditions", "coverage", "maximum ground coverage", CFG["compounds"]["coverage"] * 100, "%"),
             ("acud_conditions", "floors", "maximum floors (ground + 7, 30 m)", CFG["compounds"]["floors"], "floors"),
             ("acud_conditions", "occupancy factor", "built-up area over land, official cap (decree 483/2023); 1.6 typical", CFG["compounds"]["far_cap"], "ratio")]
    out = pd.DataFrame(rows, columns=["source", "article", "rule", "value", "unit"])
    out["origin"] = "real"
    out.insert(0, "rule_id", [f"R{i + 1:02d}" for i in range(len(out))])
    return out


def _o(real=(), derived=(), generated=(), key=()) -> dict:
    return {**{c: "real" for c in real}, **{c: "derived" for c in derived}, **{c: "generated" for c in generated}, **{c: "key" for c in key}}


ORIGINS = {
    "compounds": _o(real=["district", "coverage_max", "boundary_confidence", "boundary_area_m2"], derived=["bua_m2", "cover_pct", "first_deadline", "first_deadline_published", "handover_first_published"],
                    generated=["floors_allowed"], key=["code", "developer_code", "land_area_origin", "floors_origin", "units_origin"]) | {"land_area_m2": "real|generated", "units": "real|generated"},
    "sat_quarterly": _o(real=["n_images"], derived=["built_prob_mean", "K1", "K4", "activity_prob", "active", "K2", "started"] + ["dw12_" + c for c in DW_CLASSES], key=["code", "quarter", "qi", "start_quarter"]),
    "sat_yearly": _o(real=["n_built_cells"], derived=["veg_share"], key=["code", "year", "veg_origin", "height_origin"]) | {c: "real|derived" for c in ["height_mean_m", "height_p90_m", "share_built_ge20m"]},
    "statements": _o(real=["detail", "published_date", "scope", "period_start", "period_end", "value", "qualifier", "verdict", "origin", "record_id", "subtype", "kind"], key=["statement_id", "code"]),
    "eval_outcomes": _o(real=["outcome_type", "promise_original_period", "promise_original_published", "outcome_date", "outcome_first_published", "delay_months_vs_promise",
                              "evidence_gate", "outcome_visible_by_2024Q2", "outcome_visible_by_2025Q2", "promise_original_end"], derived=["first_deadline"], key=["case", "code"]),
    "drivers_monthly": _o(real=["usd_egp", "policy_rate_pct", "rebar_egp_t", "cement_egp_t", "tmax_mean_c", "days_tmax_ge40"], derived=["materials_index", "shock_month", "ramadan_days", "eid_days"], key=["month"]),
    "rules": _o(real=["source", "article", "rule", "value", "unit", "origin"], key=["rule_id"]),
}


def build_all() -> dict[str, pd.DataFrame]:
    comp = compounds()
    return {"compounds": comp, "sat_quarterly": sat_quarterly(), "sat_yearly": sat_yearly(sorted(comp.code)), "statements": statements(),
            "eval_outcomes": eval_outcomes(comp), "drivers_monthly": drivers_monthly(), "rules": rules()}
