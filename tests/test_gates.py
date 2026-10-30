import pandas as pd

from src.pipeline import gates, run_all
from src.pipeline.common import CFG, qindex


def test_g_completeness_passes_when_every_asof_row_is_assessable():
    sat = pd.DataFrame({"qi": [10, 10], "K4": [True, True]})

    result = gates.g_completeness(sat, 10)

    assert result["status"] == "PASS"
    assert result["value"] == "2 of 2 assessable at 2026Q3; 100.0% of all compound-quarters"


def test_g_completeness_flags_an_unassessable_asof_row():
    sat = pd.DataFrame({"qi": [10, 10], "K4": [True, False]})

    result = gates.g_completeness(sat, 10)

    assert result["status"] == "FLAG"


def test_g_completeness_flags_a_missing_asof_quarter():
    sat = pd.DataFrame({"qi": [9], "K4": [True]})

    result = gates.g_completeness(sat, 10)

    assert result["status"] == "FLAG"
    assert "0 of 0 assessable" in result["value"]


def test_g_freshness_passes_for_data_from_the_previous_quarter(monkeypatch):
    monkeypatch.setitem(CFG, "computed_on", "2026-10-26")
    sat = pd.DataFrame({"qi": [qindex("2026Q3")], "built_prob_mean": [0.5]})

    result = gates.g_freshness(sat)

    assert result["status"] == "PASS"
    assert "last quarter 2026Q3, 1 quarter(s) before 2026-10-26" in result["value"]


def test_g_freshness_flags_data_more_than_one_quarter_old(monkeypatch):
    monkeypatch.setitem(CFG, "computed_on", "2027-01-14")
    sat = pd.DataFrame({"qi": [qindex("2026Q3")], "built_prob_mean": [0.5]})

    result = gates.g_freshness(sat)

    assert result["status"] == "FLAG"
    assert "last quarter 2026Q3, 2 quarter(s) before 2027-01-14" in result["value"]


def test_g_data_or_city_passes_at_three_of_twelve_compounds():
    kpi = pd.DataFrame(
        {
            "code": [f"C{i:02d}" for i in range(12)],
            "quarter": ["2026Q3"] * 12,
            "level": [1] * 12,
            "K2": [1, 1, 1] + [2] * 9,
        }
    )

    result = gates.g_data_or_city(kpi)

    assert result["status"] == "PASS"


def test_g_data_or_city_flags_five_of_twelve_compounds():
    kpi = pd.DataFrame(
        {
            "code": [f"C{i:02d}" for i in range(12)],
            "quarter": ["2026Q3"] * 12,
            "level": [1] * 12,
            "K2": [1] * 5 + [2] * 7,
        }
    )

    result = gates.g_data_or_city(kpi)

    assert result["status"] == "FLAG"
    assert "2026Q3" in result["value"]


def test_g_stuck_passes_when_no_four_values_are_equal():
    sat = pd.DataFrame(
        {
            "code": ["C01"] * 4,
            "qi": [1, 2, 3, 4],
            "built_prob_mean": [0.5, 0.6, 0.5, 0.6],
        }
    )

    result = gates.g_stuck(sat)

    assert result["status"] == "PASS"


def test_g_stuck_flags_four_equal_values():
    sat = pd.DataFrame(
        {
            "code": ["C01"] * 4,
            "qi": [1, 2, 3, 4],
            "built_prob_mean": [0.5] * 4,
        }
    )

    result = gates.g_stuck(sat)

    assert result["status"] == "FLAG"
    assert result["value"] == "1 stuck points"


def test_g_stuck_treats_an_unknown_gap_as_breaking_a_run():
    sat = pd.DataFrame(
        {
            "code": ["C01"] * 5,
            "qi": [1, 2, 3, 4, 5],
            "built_prob_mean": [0.5, pd.NA, 0.5, 0.5, 0.5],
        }
    )

    result = gates.g_stuck(sat)

    assert result["status"] == "PASS"


def test_g_no_names_stops_when_there_are_no_forbidden_patterns(monkeypatch, tmp_path):
    monkeypatch.setattr(gates, "forbidden_names", lambda: set())

    result = gates.g_no_names(root=tmp_path, extra=[])

    assert result["status"] == "STOP"
    assert result["value"].startswith("0 patterns")


def test_g_no_names_detects_arabic_text_in_an_html_file(monkeypatch, tmp_path):
    forbidden = "مجمع النور"
    monkeypatch.setattr(gates, "forbidden_names", lambda: {forbidden})
    html = tmp_path / "inspection.html"
    html.write_text(f"<p>{forbidden}</p>", encoding="utf-8")

    result = gates.g_no_names(root=tmp_path / "empty", extra=[html])

    assert result["status"] == "STOP"


def test_final_name_scan_covers_repo_data_files(monkeypatch, tmp_path):
    monkeypatch.setattr(gates, "forbidden_names", lambda: {"forbiddencompound"})
    monkeypatch.setattr(gates, "APP", tmp_path / "app_data")
    monkeypatch.setattr(gates, "BASE_DIR", tmp_path)
    repo_data = tmp_path / "data"
    repo_data.mkdir()
    (repo_data / "bad.csv").write_text("forbiddencompound", encoding="utf-8")
    (tmp_path / "app_data").mkdir()

    result = gates.final_no_names_scan()

    assert result["status"] == "STOP"


def _stub_run_all(monkeypatch, tmp_path, gate_status="STOP", final_scan_status="PASS"):
    sat = pd.DataFrame({"code": ["C01"], "qi": [0]})
    tables = {
        "sat_quarterly": sat,
        "statements": pd.DataFrame(),
        "compounds": pd.DataFrame(),
        "sat_yearly": pd.DataFrame(),
        "eval_outcomes": pd.DataFrame(),
    }
    validation = {
        "T1": {"gain_ba": 1.0},
        "T2": {"gain_ba": 1.0},
        "T3": {"A_active_pct": 1.0, "K1_active_pct": 1.0},
        "seasonal": {"stable_plots_2024_2025": {"A": {"spread_pp": 1.0}}},
    }
    meta = {"mode": "q2hold", "n_train": 1, "validation": validation, "oof_sens_spec_ba": [0.0, 0.0, 0.0]}
    summary = {
        "after_start_reading": {"n": 0},
        "point_in_time_reading": {"n": 0},
        "literal_reading": {"n": 0},
        "n_cases": 0,
    }

    monkeypatch.setattr(run_all, "REAL", tmp_path)
    monkeypatch.setattr(run_all, "APP", tmp_path / "app_data")
    (tmp_path / "app_data" / "backtest").mkdir(parents=True)
    monkeypatch.setattr(run_all.codify, "run", lambda: pd.DataFrame({"code": ["C01"]}))
    monkeypatch.setattr(run_all.build_real, "build_all", lambda: tables)
    monkeypatch.setattr(run_all.activity, "fit_final", lambda: (object(), 0.5, meta))
    monkeypatch.setattr(run_all.activity, "fit", lambda leak, mode: (object(), 0.5, {"n_train": 1, "validation": validation}))
    monkeypatch.setattr(run_all.activity, "save", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_all.activity, "overlapping_plots", lambda: frozenset())
    monkeypatch.setattr(
        run_all.activity,
        "score",
        lambda frame, model, threshold, **kwargs: frame[["code", "qi"]].assign(activity_prob=0.5, active=False),
    )
    monkeypatch.setattr(run_all.kpis, "add_k2", lambda frame, statements: frame)
    monkeypatch.setattr(
        run_all.kpis,
        "kpi_values",
        lambda *args, **kwargs: pd.DataFrame({"code": ["C01"], "qi": [0], "quarter": ["2026Q3"], "level_label": ["4"]}),
    )
    monkeypatch.setattr(run_all.kpis, "cycle_list", lambda frame, asof: pd.DataFrame())
    monkeypatch.setattr(run_all.backtest_check, "run", lambda *args, **kwargs: (pd.DataFrame(), summary))
    monkeypatch.setattr(run_all.backtest_check, "frozen_clock_check", lambda *args, **kwargs: {})
    monkeypatch.setattr(run_all.backtest_check, "save", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        run_all.gates,
        "run_gates",
        lambda *args, **kwargs: pd.DataFrame({"gate": ["source"], "status": [gate_status]}),
    )
    monkeypatch.setattr(
        run_all.gates,
        "g_no_names",
        lambda *args, **kwargs: {"status": final_scan_status, "value": "none"},
    )
    monkeypatch.setattr(run_all, "write_real", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_all, "write_duckdb", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_all, "manifest", lambda: pd.DataFrame({"file": [], "sha256": []}))


def test_run_all_exit_code_stops_on_bad_gate(monkeypatch, tmp_path):
    _stub_run_all(monkeypatch, tmp_path, gate_status="STOP")

    assert run_all.main() == 1


def test_run_all_exit_code_stops_on_final_name_scan(monkeypatch, tmp_path):
    _stub_run_all(monkeypatch, tmp_path, gate_status="PASS", final_scan_status="STOP")

    assert run_all.main() == 1
