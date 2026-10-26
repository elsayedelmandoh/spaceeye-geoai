"""unit tests for the real-data pipeline: small pure functions only (no earth engine, no app_data)."""

import pandas as pd

from src.pipeline import gates, kpis
from src.pipeline.build_real import first_promise
from src.pipeline.common import months_between, qend, qindex, qlabel


def test_quarter_helpers_round_trip():
    assert qindex("2016Q1") == 0 and qindex("2026Q3") == 42
    assert qlabel(qindex("2024Q2")) == "2024Q2"
    assert qend(qindex("2024Q2")) == pd.Timestamp("2024-06-30")
    assert months_between(pd.Timestamp("2024-06-30"), pd.Timestamp("2025-06-30")) == 12


def test_level_is_the_worst_signal_and_may_be_complete_caps_at_3():
    assert kpis.level_of(4, 0, False) == 1  # K2 >= 4
    assert kpis.level_of(0, 25, False) == 1  # K3 > 24
    assert kpis.level_of(2, 13, False) == 1  # combined rule
    assert kpis.level_of(2, 0, False) == 2
    assert kpis.level_of(1, 0, False) == 3
    assert kpis.level_of(0, 0, False) == 4
    assert kpis.level_of(5, 30, True) == 3  # may be complete: capped at 3


def test_not_started_has_no_level_unless_a_promised_date_passed():
    assert kpis.level_of(31, 0, False, started=False) is None  # K2 is not counted before construction starts
    assert kpis.level_of(5, 0, True, started=False) is None
    assert kpis.level_of(5, 25, False, started=False) == 1  # K3 alone still drives the level
    assert kpis.level_of(0, 5, False, started=False) == 3


def _stm(*events):
    return pd.DataFrame(events, columns=["code", "kind", "subtype", "period_start", "published_date"])


def test_k2_counts_only_after_a_four_quarter_run_of_activity():
    act = [False, False, False, True, True, True, True, False, False, pd.NA, False]
    sat = pd.DataFrame({"code": "C01", "qi": range(len(act)), "active": pd.array(act, dtype="boolean")})
    out = kpis.add_k2(sat, _stm())
    assert out.started.tolist() == [False] * 6 + [True] * 5  # the run 3..6 is known at quarter 6
    assert out.start_quarter.iloc[6] == "2016Q4"
    assert pd.isna(out.K2[:6]).all()
    assert out.K2.tolist()[6:9] == [0, 1, 2] and pd.isna(out.K2[9]) and out.K2[10] == 1  # a missing quarter is not counted, the next one restarts


def test_k2_counts_from_a_published_launch_event_even_before_any_activity():
    sat = pd.DataFrame({"code": "C01", "qi": range(6), "active": pd.array([False] * 6, dtype="boolean")})
    out = kpis.add_k2(sat, _stm(("C01", "event", "launch", None, "2016-05-10"), ("C01", "event", "postponement", None, "2016-01-10")))
    assert out.started.tolist() == [False, True, True, True, True, True]  # published in quarter 1 (2016Q2); a postponement does not start anything
    assert out.K2.tolist()[1:] == [1, 2, 3, 4, 5] and pd.isna(out.K2[0])


def test_first_promise_is_the_earliest_published_and_later_promises_do_not_reset_it():
    p = pd.DataFrame({"code": ["C01"] * 2, "detail": ["project_delivery", "start"], "period_end": ["2022-12-31", "2026-12-31"],
                      "published_date": ["2019-06-03", "2024-09-24"]})
    assert first_promise(p).period_end["C01"] == "2022-12-31"


def test_name_gate_matches_whole_words_in_english_and_arabic_and_ignores_accents():
    pats = gates._patterns({gates._norm("Zeta Heights"), gates._norm("زيتا"), gates._norm("Café Delta")})
    assert gates._hits("the Zeta  Heights block", pats) == 1
    assert gates._hits("code زيتا here", pats) == 1
    assert gates._hits("cafe delta", pats) == 1
    assert gates._hits("C01 and D02 only, planet lanes", pats) == 0
