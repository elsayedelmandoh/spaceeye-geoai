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


def _sat_start(active, quality=None, quarters=None):
    return pd.DataFrame({"code": "C01", "qi": list(range(len(active))) if quarters is None else quarters,
                         "active": pd.array(active, dtype="boolean"), "K4": True if quality is None else quality})


def test_launch_does_not_confirm_observed_construction_and_k6_waits_for_publication():
    sat = _sat_start([False] * 6)
    stm = _stm(("C01", "event", "launch", "2016-03-31", "2016-05-10"))
    out = kpis.add_k2(sat, stm)
    assert out.started.iloc[1] and not out.observed_started.any()  # legacy rule remains compatible
    assert pd.isna(out.K6.iloc[0]) and pd.isna(out.launch_date_asof.iloc[0])
    assert out.K6.iloc[1] == 3 and out.K6.iloc[-1] == 15
    assert out.launch_date_asof.iloc[1] == pd.Timestamp("2016-03-31")
    assert out.launch_first_published.iloc[1] == pd.Timestamp("2016-05-10")


def test_published_delivery_confirms_observed_start_only_when_known():
    sat = _sat_start([False] * 6, quality=[False] * 6)
    stm = _stm(("C01", "event", "delivery_start", "2016-08-01", "2016-11-10"))
    out = kpis.add_k2(sat, stm)
    assert out.observed_started.tolist() == [False] * 3 + [True] * 3
    assert out.observed_start_quarter.iloc[3] == "2016Q3"
    assert out.observed_start_source.iloc[3] == "published_delivery"
    assert out.start_observation_sufficient.iloc[3] and out.K6.isna().all()


def test_observed_activity_run_needs_four_known_consecutive_quarters_and_respects_cutoff():
    sat = _sat_start([False, True, True, True, True, False])
    stm = _stm(("C01", "event", "launch", None, "2016-02-10"))
    full = kpis.add_k2(sat, stm)
    assert full.observed_started.tolist() == [False] * 4 + [True] * 2
    assert full.observed_start_quarter.iloc[4] == "2016Q2"
    assert full.observed_start_source.iloc[4] == "activity_run" and pd.isna(full.K6.iloc[4])
    prefix = kpis.add_k2(sat.iloc[:4], stm)
    pd.testing.assert_frame_equal(prefix[list(kpis.START_EVIDENCE_COLUMNS)], full.iloc[:4][list(kpis.START_EVIDENCE_COLUMNS)])
    gap = kpis.add_k2(_sat_start([True] * 4, quarters=[0, 2, 3, 4]), stm)
    assert not gap.observed_started.any() and pd.isna(gap.K6.iloc[-1])


def test_k6_does_not_treat_missing_or_unassessable_history_as_no_start():
    stm = _stm(("C01", "event", "launch", None, "2016-02-10"))
    for sat in (_sat_start([False, pd.NA, False, False]),
                _sat_start([False] * 4, quality=[True, False, True, True])):
        out = kpis.add_k2(sat, stm)
        assert not out.observed_started.any()
        assert pd.isna(out.K6.iloc[-1]) and not out.start_observation_sufficient.iloc[-1]


def test_start_evidence_ignores_future_publications_and_future_event_dates():
    sat = _sat_start([False] * 4)
    future = _stm(("C01", "event", "launch", "2016-01-01", "2017-02-01"),
                  ("C01", "event", "delivery_complete", "2016-03-01", "2017-02-01"))
    out = kpis.add_k2(sat, future)
    assert not out.observed_started.any() and out.K6.isna().all() and out.launch_date_asof.isna().all()
    clamped = kpis.add_k2(sat, _stm(("C01", "event", "delivery_start", "2017-08-01", "2016-11-01")))
    assert clamped.observed_start_quarter.iloc[-1] == "2016Q4"


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


def test_name_gate_distinguishes_generic_identifiers_from_standalone_names():
    pats = gates._patterns({"alpha"})
    assert gates._hits("alpha_id, alpha_value, source_alpha", pats) == 0
    assert gates._hits("compound alpha", pats) == 1
