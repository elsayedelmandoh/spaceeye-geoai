import pandas as pd

import app


def test_v7_generated_paths_are_refused_in_track_a():
    for rel in ("what_if/S3/who_moved_and_why.csv", "tables/current/ml_current.parquet",
                "training/ml_dataset_extended.parquet", "docs/CURRENT_MODEL_METRICS.csv"):
        assert app.is_generated_path(rel)
    assert not app.is_generated_path("real/kpi_values.parquet")


def test_capacity_view_reports_list_changes_not_level_changes():
    raw = pd.DataFrame({
        "quarter": ["2026Q2", "2026Q3", "2026Q3", "2026Q3"],
        "code": ["C03", "C03", "C12", "C18"],
        "level": [3, 3, 3.0, 1],
        "selected": [False, False, True, True],
        "selection_changed": [True, True, True, False],
        "reason_ar": ["", "المستوى 2: رصد نشاط بناء (درجة النشاط 0.58)؛ تجاوز أول موعد تسليم معلن (2024-12-31) بمقدار 21 شهر؛ عدد الصور خلال الربع 27.", None, ""],
    })
    view, label = app.whatif_view(raw)
    assert label == "2026Q3"
    assert list(view["change"]) == ["leaves", "joins", "unchanged"]
    assert list(view["level"]) == [3, 3, 1]
    assert view.loc[0, "reason"] == "رصد نشاط بناء، تجاوز أول موعد تسليم معلن (ديسمبر 2024) بمقدار 21 شهرًا"


def test_arabic_counted_nouns_follow_the_number():
    assert [app.count_ar(n, "شهر") for n in (1, 2, 3, 10, 11, 57, 100, 106)] == [
        "شهر", "شهر", "أشهر", "أشهر", "شهرًا", "شهرًا", "شهر", "أشهر"]
    assert app.short_reason_ar("المستوى 3: لم يرصد نشاط بناء منذ 6 ربع (درجة النشاط 0.24)؛ يوجد إعلان تسليم منشور") ==         "لم يرصد نشاط بناء منذ 6 أرباع، يوجد إعلان تسليم منشور"


def test_developer_claims_read_as_short_arabic_facts():
    assert app.period_ar("2023-06-01", "2023-07-31") == "يونيو–يوليو 2023"
    assert app.period_ar("2025-01-01", "2025-12-31") == "سنة 2025"
    assert app.period_ar(None, "2024-12-31") == "لحد ديسمبر 2024"
    progress = pd.Series({"kind": "progress", "qualifier": "over", "value": 70.0, "subtype": "progress_pct"})
    promise = pd.Series({"kind": "promise", "subtype": "promised_delivery_phase1",
                         "period_start": "2021-10-01", "period_end": "2021-12-31"})
    assert app.claim_text(progress) == "نسبة التنفيذ أكتر من 70%"
    assert app.claim_text(promise) == "وعد بتسليم المرحلة الأولى أكتوبر–ديسمبر 2021"


def test_a_claim_is_paired_only_with_a_picture_from_within_a_year():
    frames = [{"date": "2016-12-17"}, {"date": "2022-06-13"}]
    assert app.nearest_frame(frames, pd.Timestamp("2021-07-26")) == 1
    assert app.nearest_frame(frames, pd.Timestamp("2019-06-03")) is None
