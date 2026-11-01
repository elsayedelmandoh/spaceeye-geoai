import pandas as pd

import app


def test_v7_generated_paths_are_refused_in_track_a():
    for rel in ("what_if/S3/who_moved_and_why.csv", "tables/current/ml_current.parquet",
                "training/ml_dataset_extended.parquet", "docs/CURRENT_MODEL_METRICS.csv"):
        assert app.is_generated_path(rel)
    assert not app.is_generated_path("real/kpi_values.parquet")


def test_latest_predictions_keeps_every_method_of_the_latest_quarter():
    preds = pd.DataFrame({
        "code": ["C01", "C01", "C01", "C01"],
        "quarter": ["2026Q2", "2026Q3", "2026Q3", "2026Q3"],
        "method": ["a", "a", "b", "c"],
        "p_distressed": [0.9, 0.1, 0.2, 0.3],
    })
    table = app.latest_predictions(preds)
    assert list(table.columns) == ["a", "b", "c"]
    assert table.loc["C01", "a"] == 0.1


def test_s3_view_reports_list_changes_not_level_changes():
    raw = pd.DataFrame({
        "quarter": ["2026Q2", "2026Q3", "2026Q3", "2026Q3"],
        "code": ["C03", "C03", "C12", "C18"],
        "level": [3, 3, 3, 1],
        "baseline_selected": [True, True, False, True],
        "selected": [False, False, True, True],
        "selection_changed": [True, True, True, False],
        "reason": ["", "", "", ""],
    })
    view, label = app.whatif_view(raw, "S3")
    assert label == "2026Q3"
    assert list(view["change"]) == ["leaves the list", "joins the list", "unchanged"]
    assert app.count_changed_rows(raw) == 3


def test_s1_view_compares_track_b_levels_and_lists():
    raw = pd.DataFrame({
        "month": ["2026-09", "2026-09"],
        "code": ["C01", "C02"],
        "baseline_hypothetical_level": [2.0, None],
        "hypothetical_level": [1.0, None],
        "baseline_selected": [False, False],
        "selected": [False, False],
        "level_changed": [True, False],
        "selection_changed": [False, False],
        "reason": ["x", None],
    })
    view, _ = app.whatif_view(raw, "S1")
    assert list(view["change"]) == ["changes", "unchanged"]
    assert view.loc[1, "level in scenario (Track B)"] == "unknown"
