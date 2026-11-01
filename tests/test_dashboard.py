import pandas as pd

import app


def test_v7_generated_paths_are_refused_in_track_a():
    for rel in ("what_if/S3/who_moved_and_why.csv", "tables/current/ml_current.parquet",
                "training/ml_dataset_extended.parquet", "docs/CURRENT_MODEL_METRICS.csv"):
        assert app.is_generated_path(rel)
    assert not app.is_generated_path("real/kpi_values.parquet")


def test_capacity_view_lists_joins_and_leaves_with_a_short_arabic_reason():
    raw = pd.DataFrame({
        "quarter": ["2026Q2", "2026Q3", "2026Q3", "2026Q3"],
        "code": ["C03", "C03", "C12", "C18"],
        "selected": [False, False, True, True],
        "selection_changed": [True, True, True, False],
        "reason_ar": ["", "المستوى 3: رصد نشاط بناء (درجة النشاط 0.58)؛ عدد الصور 8؛ تأخر التسليم", "", ""],
    })
    view, label = app.whatif_view(raw)
    assert label == "2026Q3"
    assert list(view["change"]) == ["leaves the list", "joins the list", "unchanged"]
    assert view.loc[0, "reason"] == "رصد نشاط بناء، تأخر التسليم"
