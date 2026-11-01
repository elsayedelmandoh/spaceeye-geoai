import numpy as np
import pandas as pd
import pytest

from src.dashboard import insights


def test_cycle_changes_name_who_joined_and_who_left_since_the_previous_quarter():
    kpis = pd.DataFrame({
        "code": ["C07", "C10", "C18", "C07", "C10", "C18"],
        "quarter": ["2026Q2"] * 3 + ["2026Q3"] * 3,
        "level": [3, 1, 1, 2, 4, 1],
        "cycle_rank": [None, 2, 1, 2, None, 1],
        "reason_ar": [""] * 6,
    })
    changes = insights.cycle_changes(kpis, "2026Q3")
    assert changes["prev"] == "2026Q2"
    assert [(m["code"], m["was"], m["now"]) for m in changes["joined"]] == [("C07", 3, 2)]
    assert [(m["code"], m["was"], m["now"]) for m in changes["left"]] == [("C10", 1, 4)]


def test_cycle_changes_is_none_for_the_first_quarter():
    kpis = pd.DataFrame({"code": ["C07"], "quarter": ["2026Q1"], "level": [3], "cycle_rank": [1], "reason_ar": [""]})
    assert insights.cycle_changes(kpis, "2026Q1") is None


def test_only_developers_with_several_compounds_are_grouped_most_urgent_first():
    compounds = pd.DataFrame({"code": ["C01", "C18", "C14", "C21", "C07"],
                              "developer_code": ["D14", "D14", "D13", "D13", "D07"]})
    latest = pd.DataFrame({"code": ["C01", "C18", "C14", "C21", "C07"], "level": [4, 1, 2, 3, 2]})
    groups = insights.developer_groups(compounds, latest)
    assert [g["developer"] for g in groups] == ["D14", "D13"]
    assert [c["code"] for c in groups[0]["compounds"]] == ["C18", "C01"]


def test_period_text_reads_as_short_english():
    assert insights.period_text("2023-06-01", "2023-07-31") == "Jun-Jul 2023"
    assert insights.period_text("2023-06-01", "2023-06-30") == "Jun 2023"
    assert insights.period_text("2022-12-01", "2023-02-28") == "Dec 2022-Feb 2023"
    assert insights.period_text("2025-01-01", "2025-12-31") == "in 2025"
    assert insights.period_text(None, "2024-12-31") == "by Dec 2024"
    assert insights.period_text(None, None) == "with no date"


def test_claim_text_covers_progress_and_promises():
    progress = {"kind": "progress", "value": 65.0, "subtype": "progress_pct"}
    assert insights.claim_text(pd.Series({**progress, "qualifier": "exact"})) == "progress 65%"
    assert insights.claim_text(pd.Series({**progress, "qualifier": "over", "value": 70.0})) == "progress over 70%"
    assert insights.progress_amount(pd.Series({**progress, "qualifier": "about", "value": 75.0})) == "about 75%"
    promise = pd.Series({"kind": "promise", "subtype": "promised_delivery",
                         "period_start": "2023-06-01", "period_end": "2023-07-31"})
    assert insights.claim_text(promise) == "promised handover Jun-Jul 2023"
    phase = promise.replace({"promised_delivery": "promised_delivery_phase1",
                             "2023-06-01": "2021-10-01", "2023-07-31": "2021-12-31"})
    assert insights.claim_text(phase) == "promised phase 1 handover Oct-Dec 2021"
    assert insights.claim_text(promise.replace({"2023-07-31": None})) == "promised handover with no date"


def test_arabic_counted_nouns_follow_the_number():
    assert [insights.count_ar(n, "شهر") for n in (1, 2, 3, 10, 11, 57, 100, 106)] == [
        "شهر", "شهر", "أشهر", "أشهر", "شهرًا", "شهرًا", "شهر", "أشهر"]
    reason = "المستوى 3: لم يرصد نشاط بناء منذ 6 ربع (درجة النشاط 0.24)؛ يوجد إعلان تسليم منشور"
    assert insights.short_reason_ar(reason) == "لم يرصد نشاط بناء منذ 6 أرباع، يوجد إعلان تسليم منشور"


def _statements() -> pd.DataFrame:
    base = {"kind": "promise", "subtype": "promised_delivery", "value": None, "qualifier": None,
            "verdict": "CONFIRMED", "period_start": None}
    return pd.DataFrame([
        {**base, "code": "C14", "published_date": "2025-03-01", "period_end": "2026-12-31"},
        {**base, "code": "C14", "published_date": "2025-04-01", "period_end": "2027-12-31"},
        {**base, "code": "C21", "published_date": "2025-05-01", "period_end": "2027-12-31"},
        {**base, "code": "C21", "published_date": "2025-05-01", "period_end": "2026-06-30"},
        {**base, "code": "C21", "published_date": "2025-05-01", "period_end": "2028-12-31", "verdict": "REJECTED"},
        {**base, "code": "C21", "published_date": "2026-11-01", "period_end": "2029-12-31"},
        {**base, "code": "C99", "published_date": "2025-05-01", "period_end": "2027-01-31"},
    ])


def test_upcoming_promises_are_confirmed_after_the_quarter_end_soonest_first():
    rows = insights.upcoming_promises(_statements(), ["C14", "C21"], "2026Q3")
    assert [(r["code"], r["end"]) for r in rows] == [
        ("C14", "2026-12-31"), ("C14", "2027-12-31"), ("C21", "2027-12-31")]
    assert rows[0]["claim"] == "promised handover by Dec 2026" and rows[0]["said"] == "Mar 2025"


def test_a_claim_is_paired_only_with_a_picture_from_within_a_year():
    frames = [{"date": "2016-12-17"}, {"date": "2022-06-13"}]
    assert insights.nearest_frame(frames, pd.Timestamp("2021-07-26")) == 1
    assert insights.nearest_frame(frames, pd.Timestamp("2019-06-03")) is None


def test_promise_rows_pair_each_claim_with_its_picture_and_the_stage_when_the_date_passed():
    statements = _statements()
    mine = statements[statements["code"] == "C21"]
    frames = [{"date": "2025-06-10"}]
    stages = {2025: "under construction", 2026: "complete"}
    rows = insights.promise_rows(mine, frames, stages, "2026Q3")
    assert [r["claim"] for r in rows] == ["promised handover by Dec 2027", "promised handover by Jun 2026"]
    assert rows[0]["due"] == {"year": 2027, "passed": False, "stage": None}
    assert rows[1]["due"] == {"year": 2026, "passed": True, "stage": "complete"}
    assert rows[0]["capture"] == {"date": "2025-06-10", "stage": "under construction"}
    assert insights.promise_rows(mine, [], stages, "2026Q3")[0]["capture"] is None


def test_level_history_is_tidy_and_marks_missing_levels():
    kpis = pd.DataFrame({"code": ["C01", "C01", "C02"], "quarter": ["2026Q3", "2026Q2", "2026Q3"],
                         "level": [2, 3, None], "K2": [0, 0, 0]})
    history = insights.level_history(kpis)
    assert list(history.columns) == ["code", "quarter", "level"]
    assert list(history["quarter"]) == ["2026Q2", "2026Q3", "2026Q3"]
    assert history["level"].iloc[:2].tolist() == [3.0, 2.0] and np.isnan(history["level"].iloc[2])


def _row(**fields) -> pd.Series:
    base = {"level": 2, "K2": 0, "K3": 0, "K5_months": None, "may_be_complete": False,
            "k3_first_deadline": pd.Timestamp("2022-12-31")}
    return pd.Series({**base, **fields})


def test_k3_text_covers_no_deadline_and_a_passed_date_but_not_a_real_clock():
    assert insights.k3_text(_row(k3_first_deadline=None)) == "no announced handover date"
    assert insights.k3_text(_row(may_be_complete=np.bool_(True))) == "date passed, may be handed over: confirm on site"
    assert insights.k3_text(_row(may_be_complete=np.bool_(True), K3=57)) is None
    assert insights.k3_text(_row(may_be_complete=False)) is None


@pytest.mark.parametrize(("fields", "action"), [
    ({"level": 4}, "Monitor"),
    ({"level": 3}, "Document review"),
    ({"level": 3, "may_be_complete": np.bool_(True)}, "Confirm handover on site"),
    ({"level": 2}, "Visit this cycle"),
    ({"level": 1}, "Visit now"),
    ({"level": None}, "No action"),
])
def test_suggested_action_follows_the_level(fields, action):
    assert insights.suggested_action(_row(**fields))[0] == action


def test_suggested_action_escalates_at_the_proposed_thresholds():
    assert insights.suggested_action(_row(level=3, K3=insights.WARNING_K3_MONTHS - 1))[0] == "Document review"
    assert insights.suggested_action(_row(level=3, K3=insights.WARNING_K3_MONTHS))[0] == "Written warning"
    assert insights.suggested_action(_row(level=4, K2=insights.WARNING_K2_QUARTERS))[0] == "Written warning"
    assert insights.suggested_action(_row(level=1, K5_months=insights.FINE_REVIEW_K5_MONTHS - 1))[0] == "Visit now"
    assert insights.suggested_action(_row(level=1, K5_months=insights.FINE_REVIEW_K5_MONTHS))[0] == "Fine review"
    assert insights.suggested_action(_row(level=3, K5_months=40))[0] == "Document review"
    action, why = insights.suggested_action(_row(level=1, K3=57))
    assert action == "Written warning" and "57 months" in why
