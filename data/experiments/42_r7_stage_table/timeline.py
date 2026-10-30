# ruff: noqa  -- archived experiment script, kept as run
"""Per-compound construction timeline from the visual component table (r7_components.csv): buildings over time,
pauses, last structural change, finishing start and completion (owner definition)."""
import pandas as pd

c = pd.read_csv("r7_components.csv").sort_values(["code", "capture_date"])
num = ["n_buildings", "n_frames", "n_finished_facades", "new_buildings_since_prev"]
c[num] = c[num].apply(pd.to_numeric, errors="coerce").fillna(0)
STRUCT = {"new_structure", "vertical_growth"}
FINISH = {"finishing", "landscaping"}
out = []
for code, g in c.groupby("code"):
    g = g.reset_index(drop=True)
    built = g[g.n_buildings > 0]
    struct = g[g.change_vs_prev.isin(STRUCT) | (g.new_buildings_since_prev > 0) | (g.cranes == "yes")]
    fin = g[(g.n_finished_facades > 0) | g.roads.isin(["partial", "paved"]) | g.greenery.isin(["little", "much"]) | (g.pools.astype(str) != "0") | g.change_vs_prev.isin(FINISH)]
    done = g[(g.greenery == "much") & (g.roads == "paved") & (g.n_finished_facades >= 0.5 * g.n_buildings.clip(lower=1))]
    pauses = [f"{g.capture_date[i - 1]}→{g.capture_date[i]}" for i in range(1, len(g))
              if g.change_vs_prev[i] == "none" and g.n_buildings[i] > 0 and (done.empty or g.capture_date[i] < done.capture_date.iloc[0])]
    out.append({
        "code": code,
        "figures": f"{g.capture_date.iloc[0]}..{g.capture_date.iloc[-1]} ({len(g)})",
        "first_building_seen": built.capture_date.iloc[0] if len(built) else "none",
        "buildings_over_time": " ".join(f"{d[:7]}:{int(n)}" for d, n in zip(g.capture_date, g.n_buildings)),
        "last_structural_change": struct.capture_date.iloc[-1] if len(struct) else "none",
        "finishing_first_seen": fin.capture_date.iloc[0] if len(fin) else "not by last figure",
        "complete_first_seen": done.capture_date.iloc[0] if len(done) else "not by last figure",
        "no_change_intervals": "; ".join(pauses) or "none",
        "latest_state": f"{int(g.n_buildings.iloc[-1])} blocks, {int(g.n_frames.iloc[-1])} frames, {int(g.n_finished_facades.iloc[-1])} finished; greenery {g.greenery.iloc[-1]}; roads {g.roads.iloc[-1]}",
    })
t = pd.DataFrame(out)
t.to_csv("r7_timeline.csv", index=False)
for r in t.itertuples():
    print(f"{r.code} | first {r.first_building_seen} | last structural {r.last_structural_change} | finishing {r.finishing_first_seen} | complete {r.complete_first_seen}\n   counts {r.buildings_over_time}\n   no-change {r.no_change_intervals}\n   latest {r.latest_state}")
