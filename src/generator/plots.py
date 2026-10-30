"""
propose: sample chart for the R2 report: three compounds, hidden truth vs supervisor report vs real announced values vs the satellite-implied progress.
input: app_data/sim/fin_monthly.parquet, private/answer_key.parquet, the real tables. output: app_data/sim/charts/truth_vs_reported_<codes>.png
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.generator import inputs, stories
from src.generator.inputs import LABEL, SIM
from src.pipeline.common import PRIVATE

INK, MUTED = "#1f2933", "#6b7280"
TRUTH, REPORT, ANNOUNCE, SAT, PLAN = "#1f5fbf", "#d9822b", "#111111", "#2a9d8f", "#9ca3af"


def draw(codes: list[str]) -> str:
    real = inputs.load_real()
    sigs = {s.code: s for s in stories.derive(real)}
    fin, key = pd.read_parquet(SIM / "fin_monthly.parquet"), pd.read_parquet(PRIVATE / "answer_key.parquet")
    sat = real["sat_quarterly"]
    l0 = min(v for s in sigs.values() for v in s.dw_year.values())
    fig, axes = plt.subplots(1, len(codes), figsize=(5.2 * len(codes), 4.4), sharey=True)
    for ax, c in zip(axes, codes):
        k, f = key[key.code == c], fin[fin.code == c].drop_duplicates("month")
        t = pd.to_datetime(k.month + "-01")
        ax.plot(t, f.planned_pct.values, color=PLAN, lw=1.2, label="plan")
        ax.plot(t, k.true_progress_pct, color=TRUTH, lw=2, label="hidden truth")
        r = f.dropna(subset=["reported_pct"])
        ax.scatter(pd.to_datetime(r.month + "-01"), r.reported_pct, s=26, color=REPORT, edgecolor="white", linewidth=0.8, zorder=3, label="supervisor report")
        sq = sat[(sat.code == c) & (sat.qi >= 28)]
        dw = (stories.DW_K[0] * (sq.built_prob_mean.rolling(4, min_periods=1).mean() - l0)).clip(0, stories.G["dw_cap"])
        ax.plot(pd.to_datetime(sq.quarter.str[:4] + "-" + (sq.quarter.str[5].astype(int) * 3 - 2).astype(str) + "-01"), dw, color=SAT, lw=1.6, ls="--", label="satellite-implied (real)")
        a = [(inputs.MONTHS[min(m, inputs.N - 1)].to_timestamp(), v) for m, v, _ in sigs[c].anchors if m >= inputs.O0]
        if a:
            ax.scatter(*zip(*a), s=70, marker="D", color=ANNOUNCE, zorder=4, label="announced (real)")
        for m, _, _ in sigs[c].handovers:
            if m >= inputs.O0:
                ax.axvline(inputs.MONTHS[m].to_timestamp(), color=MUTED, lw=0.8, ls=":")
        ax.set_title(f"{c}  ·  {sigs[c].story}", color=INK, fontsize=11, loc="left")
        ax.set_ylim(-2, 104)
        ax.grid(axis="y", color="#e5e7eb", lw=0.6)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(colors=MUTED, labelsize=8)
    axes[0].set_ylabel("progress, %", color=MUTED)
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=5, frameon=False, fontsize=9)
    fig.suptitle(f"{LABEL}. Dotted vertical line: real handover event.", fontsize=9, color=MUTED, x=0.01, ha="left", y=0.995)
    fig.tight_layout(rect=(0, 0.08, 1, 0.97))
    out = SIM / "charts" / f"truth_vs_reported_{'_'.join(codes)}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=140)
    return str(out)


if __name__ == "__main__":
    print(draw(sys.argv[1:] or ["C09", "C14", "C21"]))
