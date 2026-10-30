# ruff: noqa  -- archived experiment script, kept as run
"""R7 stage table per compound and year: sub-metre figures first, the satellite/radar layer where no figure exists
(it may say only land or under construction), plus Google heights and the activity model. Every value names its source."""
import pandas as pd

RD = "F:/ACUD AI Data Lab/Project/"
vhr = pd.read_csv(RD + "real_data/37_coarse_stage/r7_vhr/r7_stage_codex_frames.csv")
vhr["year"] = vhr.capture_date.str[:4].astype(int)
vhr["stage"] = vhr.stage.replace({"mixed": "S1"})
vhr = vhr.sort_values("capture_date").groupby(["code", "year"]).agg(
    vhr_stage=("stage", "last"), vhr_date=("capture_date", "last"), vhr_conf=("confidence", "last")).reset_index()

sat = pd.read_csv(RD + "real_data/37_coarse_stage/r7_application/r7_stage_share.csv")[["code", "year", "majority", "share_S2"]]
sat = sat.rename(columns={"majority": "sat_stage", "share_S2": "sat_share_S2"})

cm = pd.read_csv(RD + "private/code_map.csv")[["project_id", "code"]]
h = pd.read_csv(RD + "real_data/29_height_final/v9/out_v9b/compound_height_yearly.csv")
h = h.merge(cm, left_on="compound_id", right_on="project_id")[["code", "year", "obt_height_mean_m", "obt_share_area_ge20m"]]

sq = pd.read_parquet(RD + "app_data/real/sat_quarterly.parquet")
sq["year"] = sq.quarter.astype(str).str[:4].astype(int)
act = sq.groupby(["code", "year"]).active.mean().rename("activity_share_active").reset_index()

codes = sorted(set(vhr.code) | set(sat.code))
grid = pd.MultiIndex.from_product([codes, range(2016, 2027)], names=["code", "year"]).to_frame(index=False)
t = grid.merge(vhr, how="left").merge(sat, how="left").merge(h, how="left").merge(act, how="left")
t = t.merge(pd.read_csv("r7_sat_radar_series.csv"), on=["code", "year"], how="left")  # ALOS PALSAR, Sentinel-1/2, Dynamic World, VIIRS


def final(r):
    if pd.notna(r.vhr_stage):
        return r.vhr_stage, f"sub-metre figure {r.vhr_date}"
    if pd.notna(r.sat_stage):
        return ("S1" if r.sat_stage == "S2" else r.sat_stage), "satellite and radar layer (cannot confirm complete)"
    return None, "no data"


t[["stage", "stage_source"]] = t.apply(lambda r: pd.Series(final(r)), axis=1)
t.to_csv("r7_stage_table.csv", index=False)
s = t.dropna(subset=["stage"])
def start_year(g):
    # a satellite-only S1 does not count if a later sub-metre figure still shows land (S0)
    last_vhr_s0 = g[(g.vhr_stage == "S0")].year.max()
    ok = g[g.stage.isin(["S1", "S2"]) & ~(g.year <= (last_vhr_s0 if pd.notna(last_vhr_s0) else -1))]
    return ok.year.min()


summary = s.groupby("code").apply(lambda g: pd.Series({
    "construction_start_year": start_year(g),
    "complete_year": g[g.stage == "S2"].year.min(),
    "last_figure": g.vhr_date.dropna().max()}), include_groups=False).reset_index()
summary.to_csv("r7_stage_summary.csv", index=False)
print(summary.to_string(index=False))
print(t.stage_source.str.split(" ").str[0].value_counts().to_dict())
