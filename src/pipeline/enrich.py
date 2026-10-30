"""
propose: fill the empty display fields of the real tables with labelled values, so the screens never show a blank.
input: built tables, kpi_values, real_data/42_r7_stage_table/r7_stage_table.csv (visual stage per compound-year),
       real_data/29_height_final/v9/out_v9b/compound_height_yearly.csv (candidate model heights 2024-2026), private/code_map.csv.
output: extra *_filled / *_source / stage columns on sat_yearly and compounds. Real values always win; nothing here sets a level.
"""

import pandas as pd

from src.pipeline.common import PRIVATE, SRC

STAGE_TABLE = SRC / "42_r7_stage_table" / "r7_stage_table.csv"
CANDIDATE_HEIGHTS = SRC / "29_height_final" / "v9" / "out_v9b" / "compound_height_yearly.csv"
STAGE_AR = {"S0": "أرض أو أعمال حفر", "S1": "تحت الإنشاء", "S2": "مكتمل"}


def yearly(sat_yearly: pd.DataFrame) -> pd.DataFrame:
    """Heights and vegetation: zero before any building, candidate model heights where Google heights end; visual stage per year."""
    y = sat_yearly.copy()
    if not {"n_built_cells", "height_mean_m", "height_origin", "veg_share", "veg_origin"} <= set(y.columns):
        return y  # minimal tables (tests): nothing to fill
    no_buildings = y.n_built_cells.fillna(-1).eq(0)
    y["height_mean_m_filled"], y["height_filled_source"] = y.height_mean_m, y.height_origin.astype("string")
    y.loc[no_buildings & y.height_mean_m.isna(), ["height_mean_m_filled", "height_filled_source"]] = [0.0, "observed: no buildings yet"]
    if CANDIDATE_HEIGHTS.exists() and (PRIVATE / "code_map.csv").exists():
        cm = pd.read_csv(PRIVATE / "code_map.csv")[["project_id", "code"]]
        cand = pd.read_csv(CANDIDATE_HEIGHTS).merge(cm, left_on="compound_id", right_on="project_id")[["code", "year", "model_height_mean_m"]]
        y = y.merge(cand, on=["code", "year"], how="left")
        use = y.height_mean_m_filled.isna() & y.model_height_mean_m.notna()
        y.loc[use, "height_mean_m_filled"] = y.loc[use, "model_height_mean_m"]
        y.loc[use, "height_filled_source"] = "candidate model estimate (did not pass its fresh test; context only)"
        y = y.drop(columns="model_height_mean_m")
        # finished structures do not shrink: never show a candidate below the compound's last measured height
        y = y.sort_values(["code", "year"])
        floor = y.groupby("code").height_mean_m.transform(lambda s: s.ffill())
        lower = y.height_filled_source.str.startswith("candidate", na=False) & (y.height_mean_m_filled < floor)
        y.loc[lower, "height_mean_m_filled"] = floor[lower]
        y.loc[lower, "height_filled_source"] = "carried forward: last measured height (candidate model was lower)"
    y["veg_share_filled"], y["veg_filled_source"] = y.veg_share, y.veg_origin.astype("string")
    early = y.veg_share.isna() & no_buildings
    y.loc[early, ["veg_share_filled", "veg_filled_source"]] = [0.0, "assumption: bare desert before construction"]
    if STAGE_TABLE.exists():
        st = pd.read_csv(STAGE_TABLE)[["code", "year", "stage", "stage_source"]]
        y = y.merge(st, on=["code", "year"], how="left")
    else:
        y["stage"], y["stage_source"] = pd.NA, pd.NA
    y["stage_ar"] = y.stage.map(STAGE_AR)
    return y


def compounds(comp: pd.DataFrame, kpi: pd.DataFrame, asof: str) -> pd.DataFrame:
    """Schedule dates for the compound card: published if known, otherwise the stated assumption from kpi_values."""
    cols = ["launch_assumed", "launch_assumed_source", "first_deadline_assumed", "first_deadline_assumed_source",
            "expected_handover_assumed", "expected_handover_source"]
    if not set(cols) <= set(kpi.columns):
        return comp
    latest = kpi[kpi.quarter == asof].set_index("code")
    return comp.merge(latest[cols], left_on="code", right_index=True, how="left")
