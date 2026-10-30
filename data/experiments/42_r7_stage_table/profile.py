# ruff: noqa  -- archived experiment script, kept as run
"""One profile row per compound: build pace, quarterly activity and stall runs, Google heights, radar/night-light trend,
and the published plan (first promised delivery, postponements, handover) against what the figures show."""
import pandas as pd

RD = "F:/ACUD AI Data Lab/Project/"
tl = pd.read_csv("r7_timeline.csv").set_index("code")
comp = pd.read_csv("r7_components.csv")
comp["n_buildings"] = pd.to_numeric(comp.n_buildings, errors="coerce")
st = pd.read_csv("r7_stage_table.csv")
q = pd.read_parquet(RD + "app_data/real/sat_quarterly.parquet")[["code", "quarter", "active"]].dropna()
s = pd.read_parquet(RD + "app_data/real/statements.parquet")
rows = []
for code in tl.index:
    r = {"code": code}
    g = comp[comp.code == code].sort_values("capture_date")
    built = g[g.n_buildings > 0]
    if len(built) >= 2:
        months = (pd.Timestamp(built.capture_date.iloc[-1]) - pd.Timestamp(built.capture_date.iloc[0])).days / 30.4
        r["blocks_latest"] = int(built.n_buildings.iloc[-1])
        r["blocks_per_year"] = round((built.n_buildings.iloc[-1] - built.n_buildings.iloc[0]) / max(months / 12, 0.5), 1)
    qq = q[q.code == code].sort_values("quarter")
    if len(qq):
        a = qq.active.astype(bool).tolist()
        runs, cur = [], 0
        for x in a:
            cur = cur + 1 if not x else 0
            runs.append(cur)
        r["active_quarter_share"] = round(sum(a) / len(a), 2)
        r["longest_inactive_run_quarters"] = max(runs)
        r["inactive_quarters_since_2023"] = int((~qq[qq.quarter.astype(str) >= "2023"].active.astype(bool)).sum())
    h = st[(st.code == code)].set_index("year")
    r["height_2023_m"] = round(h.obt_height_mean_m.get(2023, float("nan")), 1)
    r["share_ge20m_2023"] = round(h.obt_share_area_ge20m.get(2023, float("nan")), 2)
    r["palsar_hh_jump_db"] = round(h.palsar_hh_db.get(2024, float("nan")) - h.palsar_hh_db.get(2018, float("nan")), 1)
    r["night_light_2025_vs_2019"] = round(h.viirs_rad.get(2025, float("nan")) - h.viirs_rad.get(2019, float("nan")), 1)
    ss = s[s.code == code]
    prom = ss[ss.kind == "promise"].sort_values("published_date")
    r["first_promise"] = f"{prom.subtype.iloc[0]} {prom.period_end.iloc[0] or prom.value.iloc[0]} (pub {prom.published_date.iloc[0]})" if len(prom) else "none published"
    r["postponements"] = int((ss.subtype == "postponement").sum())
    ho = ss[ss.subtype.isin(["delivery_start", "delivery_complete"])].sort_values("published_date")
    r["handover_published"] = f"{ho.subtype.iloc[0]} {ho.published_date.iloc[0]}" if len(ho) else "none"
    r["status_2025_07"] = tl.loc[code, "latest_state"]
    r["complete_first_seen"] = tl.loc[code, "complete_first_seen"]
    rows.append(r)
p = pd.DataFrame(rows)
p.to_csv("r7_profile.csv", index=False)
pd.set_option("display.width", 250)
print(p.drop(columns=["status_2025_07"]).to_string(index=False))
