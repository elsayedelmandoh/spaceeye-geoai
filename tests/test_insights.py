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
        "reason": [""] * 6,
    })
    changes = insights.cycle_changes(kpis, "2026Q3")
    assert changes["prev"] == "2026Q2"
    assert [(m["code"], m["was"], m["now"]) for m in changes["joined"]] == [("C07", 3, 2)]
    assert [(m["code"], m["was"], m["now"]) for m in changes["left"]] == [("C10", 1, 4)]


def test_cycle_changes_is_none_for_the_first_quarter():
    kpis = pd.DataFrame({"code": ["C07"], "quarter": ["2026Q1"], "level": [3], "cycle_rank": [1], "reason": [""]})
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


def test_a_compound_that_may_be_handed_over_is_confirmed_before_any_warning():
    row = pd.Series({"level": 3, "K2": 6, "K3": 0, "K5_months": 4, "may_be_complete": np.bool_(True)})
    assert insights.suggested_action(row)[0] == "Confirm handover on site"


def test_timeline_frames_are_sorted_by_date_and_skip_other_files(tmp_path):
    folder = tmp_path / "C01"
    folder.mkdir()
    for name in ("C01_02_2019-10-06.jpg", "C01_01_2016-11-08.jpg", "C01_timeline.jpg", "C01_03_2021-04-09.png"):
        (folder / name).write_bytes(b"")
    frames = insights.timeline_frames("C01", tmp_path)
    assert [date for date, _ in frames] == ["2016-11-08", "2019-10-06"]
    assert frames[0][1].name == "C01_01_2016-11-08.jpg"


def test_timeline_frames_of_an_unknown_compound_are_empty(tmp_path):
    assert insights.timeline_frames("C99", tmp_path) == []

WHY = ("Level 1: no building activity for 6 quarter(s) (activity score 0.30); first announced handover date "
       "(Dec 2023) is still ahead; observation complete (19 images in the quarter).")


def test_what_space_saw_drops_the_level_prefix_and_the_observation_clause():
    assert insights.what_space_saw(WHY) == ("No building activity for 6 quarters (activity score 0.30); "
                                            "first announced handover date (Dec 2023) is still ahead")


def test_warning_case_picks_the_earliest_warning_after_start_and_words_the_outcome():
    cases = pd.DataFrame({
        "code": ["C14", "C21"], "after_start": [False, True], "after_start_months_before": [np.nan, 39.0],
        "first_alert_quarter": [None, "2020Q3"], "first_deadline": ["2024-12-31", "2023-12-31"], "why": ["", WHY],
        "what_happened": ["delivered_late; outcome date 2024-09-24",
                          "partial_delivery_late_completion_postponed; outcome date 2026-01-29; first published 2026-01-29"],
    })
    case = insights.warning_case(cases)
    assert (case["code"], case["alert"], case["months"], case["deadline"]) == ("C21", "2020Q3", 39, "Dec 2023")
    assert case["outcome"] == "partly handed over late, completion postponed"
    assert case["reported"] == "Jan 2026"
    assert insights.warning_case(cases.assign(after_start=False)) is None


def test_frame_pair_is_the_chosen_frame_and_the_latest():
    frames = [{"date": "2019-01-01"}, {"date": "2021-04-09"}, {"date": "2025-07-23"}]
    index = insights.first_frame_after(frames, pd.Timestamp("2020-09-30"))
    assert index == 1
    assert [f["date"] for f in insights.frame_pair(frames, index)] == ["2021-04-09", "2025-07-23"]
    assert [f["date"] for f in insights.frame_pair(frames, 2)] == ["2025-07-23"]
    assert insights.first_frame_after(frames, pd.Timestamp("2026-01-01")) is None
    assert [f["date"] for f in insights.frame_pair(frames, None)] == ["2025-07-23"]
    assert insights.frame_pair([], None) == []


def test_flagged_early_keeps_listed_compounds_with_no_date_passed():
    latest = pd.DataFrame({
        "code": ["C18", "C07", "C14", "C03", "C21"], "level": [1, 2, 2, 3, 3], "cycle_rank": [1, 2, 3, 4, None],
        "K3": [57, 0, 21, 0, 0],
        "k3_first_deadline": ["2021-12-31", None, "2024-12-31", None, "2023-12-31"],
        "may_be_complete": [False, False, False, False, True], "reason": [""] * 5,
    })
    flagged = insights.flagged_early(latest)
    assert [r["code"] for r in flagged] == ["C07", "C03"]
    assert flagged[0]["level"] == 2


def test_strongest_claim_is_the_largest_k3_among_compounds_with_confirmed_claims():
    latest = pd.DataFrame({"code": ["C18", "C14", "C99"], "K3": [57, 21, 90],
                           "k3_first_deadline": ["2021-12-31", "2024-12-31", "2020-01-31"]})
    statements = pd.DataFrame({
        "code": ["C18", "C18", "C14", "C99"], "verdict": ["CONFIRMED", "CONFIRMED", "CONFIRMED", "REJECTED"],
        "published_date": ["2021-07-26", "2022-05-25", "2022-03-16", "2021-01-01"]})
    claim = insights.strongest_claim(latest, statements, "2026Q3")
    assert (claim["code"], claim["k3"], claim["deadline"]) == ("C18", 57, "Dec 2021")
    assert claim["last_claim"] == pd.Timestamp("2022-05-25")


def test_homes_waiting_counts_real_units_only_for_compounds_with_fine_months():
    compounds = pd.DataFrame({"code": ["C02", "C10", "C01", "C12"], "units": [1750, 800, 1917, 300],
                              "units_origin": ["real", "real", "generated", "real"]})
    latest = pd.DataFrame({"code": ["C02", "C10", "C01", "C12"], "level": [4, 4, 4, 3],
                           "K5_months": [11, 21, 5, np.nan]})
    waiting = insights.homes_waiting(compounds, latest)
    assert [(r["code"], r["units"], r["k5"]) for r in waiting["rows"]] == [("C02", 1750, 11), ("C10", 800, 21)]
    assert (waiting["homes"], waiting["compounds"]) == (2550, 2)


def test_late_delays_sort_longest_first_and_list_cases_with_no_value():
    outcomes = pd.DataFrame({"code": ["C14", "C02", "C10", "C21"],
                             "delay_months_vs_promise": [np.nan, 18.0, 33.0, 25.0]})
    delays = insights.late_delays(outcomes)
    assert [(r["code"], r["months"]) for r in delays["rows"]] == [("C10", 33), ("C21", 25), ("C02", 18)]
    assert delays["median"] == 25.0
    assert delays["pending"] == ["C14"]


def test_fine_months_total_and_order():
    latest = pd.DataFrame({"code": ["C18", "C01", "C10"], "K5_months": [45, np.nan, 21]})
    fines = insights.fine_months(latest)
    assert [(r["code"], r["months"]) for r in fines["rows"]] == [("C18", 45), ("C10", 21)]
    assert (fines["total"], fines["compounds"]) == (66, 2)


def test_codes_by_current_level_put_urgent_first_and_not_assessable_last():
    history = pd.DataFrame({"code": ["C01", "C02", "C03"] * 2, "quarter": ["2026Q2"] * 3 + ["2026Q3"] * 3,
                            "level": [1.0, 1.0, 1.0, 4.0, np.nan, 2.0]})
    assert insights.codes_by_current_level(history) == ["C03", "C01", "C02"]


def _scenario_raw() -> pd.DataFrame:
    return pd.DataFrame({
        "month": ["2026-08", "2026-09", "2026-09", "2026-09"], "code": ["C01", "C01", "C02", "C03"],
        "baseline_hypothetical_level": [2.0, 2.0, 4.0, np.nan], "hypothetical_level": [2.0, 1.0, 4.0, np.nan],
        "baseline_selected": [False, False, False, False], "selected": [False, True, False, False],
        "reason": [None, "gap 20pp", "gap 3pp", None],
    })


def test_scenario_view_marks_who_changed_level_or_list_in_the_latest_month():
    view, month = insights.scenario_view(_scenario_raw())
    assert month == "2026-09"
    assert list(view["code"]) == ["C01", "C02", "C03"]
    assert list(view["changed"]) == [True, False, False]
    assert view.loc[0, "reason"] == "gap 20pp"


def test_level_counts_cover_baseline_and_scenario_including_not_assessable():
    counts = insights.level_counts(insights.scenario_view(_scenario_raw())[0])
    pairs = {(r["case"], None if pd.isna(r["level"]) else r["level"]): r["compounds"] for _, r in counts.iterrows()}
    assert pairs == {("Baseline", 2.0): 1, ("Baseline", 4.0): 1, ("Baseline", None): 1,
                     ("Scenario", 1.0): 1, ("Scenario", 4.0): 1, ("Scenario", None): 1}


def test_short_reason_drops_the_level_prefix_score_and_observation_clause():
    reason = ("Level 1: building activity detected (activity score 0.53); first announced handover date (Dec 2021) "
              "passed by 57 months; observation complete (27 images in the quarter).")
    assert insights.short_reason(reason) == (
        "building activity detected; first announced handover date (Dec 2021) passed by 57 months")
