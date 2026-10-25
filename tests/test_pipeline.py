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
    assert kpis.level_of(4, 0, False, False) == 1  # K2 >= 4
    assert kpis.level_of(0, 25, False, False) == 1  # K3 > 24
    assert kpis.level_of(2, 13, False, False) == 1  # combined rule
    assert kpis.level_of(2, 0, False, False) == 2
    assert kpis.level_of(1, 0, False, False) == 3
    assert kpis.level_of(0, 0, False, False) == 4
    assert kpis.level_of(0, 0, True, False) == 2  # K5 alone gives level 2
    assert kpis.level_of(5, 30, False, True) == 3  # may be complete: capped at 3


def test_k2_counts_consecutive_inactive_quarters_and_resets_on_active():
    sat = pd.DataFrame({"code": "C01", "qi": range(6), "active": pd.array([True, False, False, pd.NA, False, False], dtype="boolean")})
    assert kpis.add_k2(sat).K2.tolist()[:3] == [0, 1, 2]
    assert pd.isna(kpis.add_k2(sat).K2[3]) and kpis.add_k2(sat).K2.tolist()[4:] == [1, 2]


def test_first_promise_is_the_earliest_published_and_later_promises_do_not_reset_it():
    p = pd.DataFrame({"code": ["C01"] * 2, "detail": ["project_delivery", "start"], "period_end": ["2022-12-31", "2026-12-31"],
                      "published_date": ["2019-06-03", "2024-09-24"]})
    assert first_promise(p).period_end["C01"] == "2022-12-31"


def test_name_gate_matches_whole_words_in_english_and_arabic_and_ignores_accents():
    pats = gates._patterns({gates._norm("Park Lane"), gates._norm("سيرانو"), gates._norm("Plató")})
    assert gates._hits("the Park  Lane block", pats) == 1
    assert gates._hits("code سيرانو here", pats) == 1
    assert gates._hits("plato", pats) == 1
    assert gates._hits("C01 and D02 only, planet lanes", pats) == 0
