# Synthetic - for training only. Progress of the finance scenarios against the baseline run.
"""Digital twin what-if input: per compound and month, how far each scenario moves progress.

Uses the rows that `scenarios.simulate` already returns (baseline and shock scenarios from
the same run and seed). Nothing is re-tuned here.
"""

import pandas as pd

from src.generator.inputs import LABEL

SCENARIO_LABELS = {"usd_cost_shock": "S1", "collections_drop": "S2"}
OUTPUT_COLUMNS = [
    "code", "month", "scenario_id", "baseline_progress_pct", "scenario_progress_pct",
    "delta_pp", "origin", "synthetic_label",
]


def progress_vs_baseline(paths: pd.DataFrame) -> pd.DataFrame:
    """One row per compound, month and finance scenario: baseline progress, scenario progress and the difference."""
    key = ["code", "month"]
    base = (paths[paths["scenario_id"] == "baseline"][key + ["simulated_progress_pct"]]
            .rename(columns={"simulated_progress_pct": "baseline_progress_pct"}))
    frames = []
    for scenario_id, label in SCENARIO_LABELS.items():
        scen = (paths[paths["scenario_id"] == scenario_id][key + ["simulated_progress_pct"]]
                .rename(columns={"simulated_progress_pct": "scenario_progress_pct"}))
        merged = base.merge(scen, on=key, how="inner", validate="one_to_one")
        merged["scenario_id"] = label
        frames.append(merged)
    out = pd.concat(frames, ignore_index=True)
    out["delta_pp"] = out["scenario_progress_pct"] - out["baseline_progress_pct"]
    out["origin"] = "generated"
    out["synthetic_label"] = LABEL
    out["month"] = out["month"].astype(str)
    return out[OUTPUT_COLUMNS].sort_values(["scenario_id", "code", "month"]).reset_index(drop=True)


def main() -> None:
    """Write the stored screen input from the same scenario run that scenarios.py uses (no settings changed)."""
    import argparse
    from pathlib import Path

    from src.generator.scenarios import simulate
    from src.pipeline.common import APP, CFG, REAL

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="CSV to write (the ready-data what_if folder)")
    parser.add_argument("--fin", type=Path, default=APP / "sim" / "fin_monthly.parquet")
    args = parser.parse_args()
    codes = sorted(pd.read_parquet(REAL / "compounds.parquet").code)
    _, _, paths = simulate(pd.read_parquet(args.fin), codes, CFG["generator"]["scenarios"], int(CFG["seed"]))
    progress_vs_baseline(paths).to_csv(args.out, index=False, encoding="utf-8-sig")
    print(f"progress_vs_baseline: {args.out}")


if __name__ == "__main__":
    main()
