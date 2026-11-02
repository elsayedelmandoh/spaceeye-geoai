import pandas as pd
import pytest

from src.generator.inputs import LABEL
from src.generator.twin_progress import OUTPUT_COLUMNS, progress_vs_baseline


def fabricated_paths() -> pd.DataFrame:
    rows = []
    for scenario_id, progress in (
        ("baseline", 80.0), ("usd_cost_shock", 79.0), ("collections_drop", 78.5), ("material_cost_jump", 79.5),
    ):
        for month in ("2026-08", "2026-09"):
            rows.append({"code": "C01", "month": pd.Period(month, "M"), "scenario_id": scenario_id,
                         "simulated_progress_pct": progress})
    return pd.DataFrame(rows)


def test_one_row_per_compound_month_and_finance_scenario():
    out = progress_vs_baseline(fabricated_paths())
    assert len(out) == 4  # 2 finance scenarios x 2 months x 1 compound
    assert set(out["scenario_id"]) == {"S1", "S2"}


def test_delta_is_scenario_minus_baseline_from_the_same_run():
    out = progress_vs_baseline(fabricated_paths())
    s1 = out[out["scenario_id"] == "S1"].iloc[0]
    s2 = out[out["scenario_id"] == "S2"].iloc[0]
    assert s1["delta_pp"] == pytest.approx(-1.0)
    assert s2["delta_pp"] == pytest.approx(-1.5)


def test_material_cost_scenario_is_not_in_the_screen_output():
    out = progress_vs_baseline(fabricated_paths())
    assert "material_cost_jump" not in set(out["scenario_id"])


def test_output_is_labelled_generated_and_has_the_stored_columns():
    out = progress_vs_baseline(fabricated_paths())
    assert list(out.columns) == OUTPUT_COLUMNS
    assert out["origin"].eq("generated").all()
    assert out["synthetic_label"].eq(LABEL).all()
    assert out["month"].map(type).eq(str).all()


def test_missing_baseline_rows_give_an_empty_table_not_a_guess():
    paths = fabricated_paths()
    out = progress_vs_baseline(paths[paths["scenario_id"] != "baseline"])
    assert out.empty
