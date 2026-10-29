"""unit tests for the real-data pipeline: small pure functions only (no earth engine, no app_data)."""

import os

import pandas as pd

from src.pipeline import complete_data, gates, kpis
from src.pipeline.build_real import first_promise
from src.pipeline.common import (
    CFG,
    months_between,
    native_path,
    qend,
    qindex,
    qlabel,
    summer_year,
)


def test_quarter_helpers_round_trip():
    assert qindex("2016Q1") == 0 and qindex("2026Q3") == 42
    assert qlabel(qindex("2024Q2")) == "2024Q2"
    assert qend(qindex("2024Q2")) == pd.Timestamp("2024-06-30")
    assert months_between(pd.Timestamp("2024-06-30"), pd.Timestamp("2025-06-30")) == 12


def test_summer_year_matches_existing_quarter_arithmetic():
    assert summer_year(qindex("2016Q1")) == 2015
    assert summer_year(qindex("2016Q2")) == 2015
    assert summer_year(qindex("2016Q3")) == 2016
    assert summer_year(qindex("2017Q2")) == 2016


def test_level_is_the_worst_signal_and_may_be_complete_caps_at_3():
    assert kpis.level_of(4, 0, False) == 1  # K2 >= 4
    assert kpis.level_of(0, 25, False) == 1  # K3 > 24
    assert kpis.level_of(2, 13, False) == 1  # combined rule
    assert kpis.level_of(2, 0, False) == 2
    assert kpis.level_of(1, 0, False) == 3
    assert kpis.level_of(0, 0, False) == 4
    assert kpis.level_of(5, 30, True) == 3  # may be complete: capped at 3
    assert kpis.level_of(0, 0, False, True, 25) == 1
    assert kpis.level_of(0, 0, False, True, 24) == 2
    assert kpis.level_of(0, 0, False, True, 13) == 2
    assert kpis.level_of(0, 0, False, True, 12) == 4
    assert kpis.level_of(0, 12, False) == 3
    assert kpis.level_of(0, 13, False) == 2
    assert kpis.level_of(0, 24, False) == 2
    assert kpis.level_of(2, 12, False) == 2
    assert kpis.level_of(2, 13, False) == 1
    assert kpis.level_of(0, 0, True, True, 30) == 3


def test_reason_matches_spec_examples():
    row = {"K4": True, "started": True, "K2": 4, "activity_prob": 0.12, "handover": False,
           "first_end": pd.Timestamp("2024-06-30"), "K3": 27, "may_be_complete": False,
           "K6": pd.NA, "n_images": 14, "level": 1}
    assert kpis.reason(row) == (
        "Level 1: no building activity for 4 quarter(s) (activity score 0.12); "
        "first announced handover date (Jun 2024) passed by 27 months; "
        "observation complete (14 images in the quarter)."
    )

    text = kpis.reason_ar({**row, "K2": 3, "K3": 8})
    assert text.startswith("المستوى 1: ")
    assert " (درجة النشاط 0.12)" in text
    assert "لم يرصد نشاط بناء منذ 3 ربع" in text
    assert "تجاوز أول موعد تسليم معلن" in text
    assert "بمقدار 8 شهر" in text

    ordered = kpis.reason_ar({**row, "level": 2, "may_be_complete": True, "K6": 25})
    assert ordered.index("قد يكون مكتملًا") < ordered.index("لم تتأكد بداية مرصودة")

    not_started = kpis.reason_ar({**row, "started": False, "K2": pd.NA, "level": pd.NA, "K6": 5})
    assert not_started.startswith("بداية غير مؤكدة: ")
    not_assessable = kpis.reason_ar({**row, "K4": False})
    assert not_assessable.startswith("غير قابل للتقييم: ")


def test_reason_head_separates_start_unknown_from_not_started():
    row = {"K4": True, "started": False, "K2": float("nan"), "activity_prob": 0.05, "handover": False,
           "first_end": None, "K3": 0, "may_be_complete": False, "K6": pd.NA, "n_images": 8, "level": pd.NA}
    assert kpis.reason(row).startswith("Start unknown: ")
    assert kpis.reason_ar(row).startswith("بداية غير معروفة: ")
    known = {**row, "K6": 5}
    assert kpis.reason(known).startswith("Not started: ")
    assert kpis.reason_ar(known).startswith("بداية غير مؤكدة: ")


def test_month_arithmetic_and_k5_k6_boundaries_are_pinned():
    assert months_between(pd.Timestamp("2023-06-10"), pd.Timestamp("2024-06-30")) == 13
    # KEPT decision: K3/K6 use rounded days / 30.44, while K5 uses calendar months.
    assert kpis.fine_months(pd.Timestamp("2023-06-01"), pd.Timestamp("2024-06-30"), None, True)["K5_post_grace_months"] == 0
    assert kpis.level_of(0, 0, False, True, 24) == 2


def test_complete_data_cycle_list_writer_keeps_the_real_path_for_run_all(monkeypatch, tmp_path):
    output = tmp_path / "data_completion"
    real = tmp_path / "real"
    monkeypatch.setattr(complete_data, "OUT", output)
    monkeypatch.setattr(complete_data, "REAL", real)
    monkeypatch.setattr(complete_data.kpis, "cycle_list", lambda kpi, quarter: pd.DataFrame({"code": ["C01"]}))

    complete_data.write_completion_cycle_list(pd.DataFrame())

    assert (output / "cycle_list.csv").exists()
    assert not real.exists()


def test_rank_cycle_takes_top_capacity_levels_1_to_3_in_spec_order():
    codes = ["C01", "C02", "C03", "C05", "C06", "C07", "C04", "C08"]
    levels = pd.array([1, 2, 2, 3, 4, pd.NA, 2, 2], dtype="Int64")
    k2 = pd.array([0, 2, 2, 1, 4, 5, 2, 1], dtype="Int64")
    k3 = pd.array([0, 5, 5, 0, 0, 0, 8, 12], dtype="Int64")
    frame = pd.DataFrame({
        "code": codes,
        "quarter": "2026Q3",
        "qi": 42,
        "level": levels,
        "K2": k2,
        "K3": k3,
        "K5_months": pd.array([pd.NA] * len(codes), dtype="Int64"),
        "K6": pd.array([pd.NA] * len(codes), dtype="Int64"),
        "may_be_complete": False,
        "level_word": "fixture",
        "level_word_ar": "fixture",
        "reason": "fixture",
        "reason_ar": "fixture",
        "origin": "derived",
        "run_id": "test-run",
        "computed_at": CFG["computed_on"],
    })

    ranked = kpis.rank_cycle(frame)
    expected_codes = ["C01", "C04", "C02", "C03"]
    assert ranked.set_index("code").loc[expected_codes, "cycle_rank"].astype(int).tolist() == list(range(1, CFG["cycle_capacity"] + 1))
    assert ranked.set_index("code").loc[["C05", "C06", "C07", "C08"], "cycle_rank"].isna().all()
    cycle = kpis.cycle_list(ranked, "2026Q3")
    assert cycle.code.tolist() == expected_codes
    assert {"reason_ar", "level_word_ar"} <= set(cycle.columns)


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


def test_not_assessable_kpi_row_has_no_level_and_keeps_lineage():
    qi = qindex("2019Q1")
    sat = pd.DataFrame({"code": "C01", "qi": [qi], "activity_prob": [0.1],
                        "active": pd.array([False], dtype="boolean"), "K4": [False], "n_images": [0]})
    stm = pd.DataFrame(columns=["code", "kind", "subtype", "detail", "period_start", "period_end", "published_date"])
    compounds = pd.DataFrame({"code": ["C01"], "handover_first_published": [pd.NaT]})
    yearly = pd.DataFrame(columns=["code", "year", "veg_share"])

    out = kpis.kpi_values(sat, compounds, stm, yearly, run_id="test-run", upto=qi)
    row = out.iloc[0]
    assert pd.isna(row.level)
    assert row.level_label == "not assessable"
    assert row.origin == "derived"
    assert row.run_id == "test-run"
    assert row.computed_at == CFG["computed_on"]


def _fabricated_kpi_inputs():
    qi = qindex("2019Q1")
    sat = pd.DataFrame({"code": "C01", "qi": [qi], "activity_prob": [0.1],
                        "active": pd.array([False], dtype="boolean"), "K4": [True], "n_images": [10]})
    compounds = pd.DataFrame({"code": ["C01"], "handover_first_published": [pd.NaT]})
    yearly = pd.DataFrame(columns=["code", "year", "veg_share"])
    statement_columns = ["code", "kind", "subtype", "detail", "period_start", "period_end", "published_date"]
    return qi, sat, compounds, yearly, statement_columns


def test_every_kpi_values_column_has_a_declared_origin():
    qi, sat, compounds, yearly, statement_columns = _fabricated_kpi_inputs()
    unknown = kpis.kpi_values(sat, compounds, pd.DataFrame(columns=statement_columns), yearly,
                              run_id="test-run", upto=qi)
    statements = pd.DataFrame([
        ["C01", "event", "launch", "launch", "2019-01-01", None, "2019-01-15"],
        ["C01", "promise", "delivery_promise", "project_delivery", None, "2020-12-31", "2019-02-01"],
    ], columns=statement_columns)
    started = kpis.kpi_values(sat, compounds, statements, yearly, run_id="test-run", upto=qi)

    assert started.started.iloc[0]
    assert started.start_reference_source.iloc[0] == "launch"
    assert started.launch_date_asof.notna().all()
    assert started.K5_months.notna().all()
    for out in (unknown, started):
        assert set(out.columns) == set(kpis.KPI_ORIGINS)


def test_separation_gate_rejects_an_undeclared_kpi_values_column():
    qi, sat, compounds, yearly, statement_columns = _fabricated_kpi_inputs()
    out = kpis.kpi_values(sat, compounds, pd.DataFrame(columns=statement_columns), yearly,
                          run_id="test-run", upto=qi)

    assert gates.g_separation({}, out)["status"] == "PASS"
    failed = gates.g_separation({}, out.assign(zzz=1))
    assert failed["status"] == "STOP"
    assert failed["value"] == "1 columns without origin, 0 generated tables"


def test_start_unknown_label_is_distinct_from_known_not_started():
    qi = qindex("2019Q1")
    sat = pd.DataFrame({"code": "C01", "qi": [qi], "activity_prob": [0.1],
                        "active": pd.array([False], dtype="boolean"), "K4": [True], "n_images": [10]})
    compounds = pd.DataFrame({"code": ["C01"], "handover_first_published": [pd.NaT]})
    yearly = pd.DataFrame(columns=["code", "year", "veg_share"])
    statement_columns = ["code", "kind", "subtype", "detail", "period_start", "period_end", "published_date"]

    unknown = kpis.kpi_values(sat, compounds, pd.DataFrame(columns=statement_columns), yearly,
                              run_id="test-run", upto=qi).iloc[0]
    assert pd.isna(unknown.K6) and pd.isna(unknown.level)
    assert unknown.level_label == "start unknown"
    assert unknown.level_word == "start unknown"
    assert unknown.level_word_ar == "بداية غير معروفة"

    promise = pd.DataFrame([["C01", "promise", "delivery_promise", "other", None, None, "2019-01-15"]],
                           columns=statement_columns)
    known = kpis.kpi_values(sat, compounds, promise, yearly, run_id="test-run", upto=qi).iloc[0]
    assert known.K6 == 2 and pd.isna(known.level)
    assert known.level_label == "not started"
    assert known.level_word == "not started"
    assert known.level_word_ar == "بداية غير مؤكدة"


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


def test_windows_drive_paths_map_to_mnt_on_linux():
    if os.name == "nt":
        return
    assert str(native_path("F:/ACUD AI Data Lab/Project/app_data")) == "/mnt/f/ACUD AI Data Lab/Project/app_data"
    assert str(native_path("F:\\x\\y")) == "/mnt/f/x/y"
    assert str(native_path("relative/dir")) == "relative/dir"
