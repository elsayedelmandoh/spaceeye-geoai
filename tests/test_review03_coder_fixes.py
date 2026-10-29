"""Focused regressions for the remaining coder fixes in logs/review-03.md."""

import pandas as pd

from src.pipeline import backtest_check, codify, complete_data, partial_exports, quality_report
from src.pipeline.common import CFG, qindex


def test_height_rows_drops_published_years_after_the_configured_cap():
    heights = pd.DataFrame(
        {
            "year": [2024, 2025],
            "published": [True, True],
            "height_mean_m": [20.0, 21.0],
        }
    )

    kept = codify.height_rows(heights)

    assert kept.year.tolist() == [2024]


def _quality_rows(status="PASS"):
    return [
        {
            "gate": "data_or_city",
            "dimension": "Accuracy",
            "status": status,
            "value": "1 quarters flagged: 2019Q2" if status == "FLAG" else "all checks passed",
            "owner": "R4",
            "on_failure": "flag the quarter and review",
            "impact": "flagged quarters may be a data event, not the city",
            "run_id": "R1-test-run",
            "computed_at": "2026-10-26",
        }
    ]


def test_saved_quality_checks_include_run_metadata():
    checks = pd.DataFrame({"gate": ["source"], "status": ["PASS"]})

    enriched = complete_data.quality_checks_with_metadata(checks, "R1-test-run")

    assert enriched.run_id.tolist() == ["R1-test-run"]
    assert enriched.computed_at.tolist() == [complete_data.CFG["computed_on"]]


def test_quality_report_uses_the_first_saved_run_id(tmp_path):
    source = tmp_path / "quality_checks.csv"
    target = tmp_path / "quality-report.md"
    rows = _quality_rows()

    report = quality_report.render_report(rows, "source-sha", target)

    assert "Run id: `R1-test-run`" in report
    assert target.read_text(encoding="utf-8") == report


def test_quality_report_renders_each_unresolved_flag(monkeypatch, tmp_path, capsys):
    app = tmp_path / "app_data"
    repo = tmp_path / "repo"
    source = app / "data_completion" / "quality_checks.csv"
    source.parent.mkdir(parents=True)
    source.write_text(
        "gate,dimension,status,value,owner,on_failure,impact,run_id,computed_at\n"
        "data_or_city,Accuracy,FLAG,1 quarters flagged: 2019Q2,R4,flag the quarter and review,coverage,R1-test-run,2026-10-26\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(quality_report, "APP", app)
    monkeypatch.setattr(quality_report, "BASE_DIR", repo)

    quality_report.main()

    report = (repo / "docs" / "deliverables" / "quality-report.md").read_text(encoding="utf-8")
    assert "Run id: R1-test-run" in capsys.readouterr().out
    assert "Unresolved FLAG: data_or_city: 1 quarters flagged: 2019Q2. Review before interpreting it." in report


def test_quality_report_omits_the_flag_sentence_when_no_flag_is_saved(monkeypatch, tmp_path):
    app = tmp_path / "app_data"
    repo = tmp_path / "repo"
    source = app / "data_completion" / "quality_checks.csv"
    source.parent.mkdir(parents=True)
    source.write_text(
        "gate,dimension,status,value,owner,on_failure,impact,run_id,computed_at\n"
        "data_or_city,Accuracy,PASS,all checks passed,R4,flag the quarter and review,coverage,R1-test-run,2026-10-26\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(quality_report, "APP", app)
    monkeypatch.setattr(quality_report, "BASE_DIR", repo)

    quality_report.main()

    report = (repo / "docs" / "deliverables" / "quality-report.md").read_text(encoding="utf-8")
    assert "2019Q2" not in report
    assert "Unresolved FLAG:" not in report


def test_backtest_case_readings_excludes_k4_true_level_unknown_and_uses_configured_levels(monkeypatch):
    qi = qindex("2023Q2")
    kc = pd.DataFrame(
        {
            "code": ["C01", "C01", "C01"],
            "qi": [qi, qi, qi],
            "quarter": ["2023Q2", "2023Q2", "2023Q2"],
            "level": [pd.NA, 1, 2],
            "K4": [True, True, True],
            "started": [False, True, True],
        }
    )
    monkeypatch.setitem(CFG["backtest"], "levels", [2])

    assessable, alerts, after_start = partial_exports.backtest_case_readings(
        kc,
        "C01",
        pd.Timestamp("2024-03-31"),
    )

    assert assessable.level.tolist() == [1, 2]
    assert alerts.level.tolist() == [2]
    assert after_start.level.tolist() == [2]


def test_frozen_clock_check_rejects_an_empty_comparison_and_cuts_at_summer_year(monkeypatch):
    qi = qindex("2023Q2")
    captured = {}

    def fake_kpi_values(sat, compounds, statements, yearly, run_id, upto=None):
        captured["years"] = yearly.year.tolist()
        return pd.DataFrame(
            columns=["code", "qi", "activity_prob", "K2", "K3", "level", "may_be_complete", "started"]
        )

    monkeypatch.setitem(CFG["quality"], "frozen_check_quarters", ["2023Q2"])
    monkeypatch.setattr(backtest_check.activity, "score", lambda cut, *args, **kwargs: cut[["code", "qi"]].assign(activity_prob=0.5, active=False))
    monkeypatch.setattr(backtest_check.kpis, "kpi_values", fake_kpi_values)
    sat = pd.DataFrame(
        {
            "code": ["C01"],
            "qi": [qi],
            "built_prob_mean": [0.5],
            "n_images": [8],
            "K4": [True],
        }
    )
    yearly = pd.DataFrame({"year": [2022, 2023]})
    statements = pd.DataFrame({"published_date": pd.to_datetime([])})

    result = backtest_check.frozen_clock_check(
        object(),
        0.5,
        "q2hold",
        sat,
        sat,
        pd.DataFrame(),
        statements,
        yearly,
        "R1-test-run",
    )

    assert result["2023Q2"] is False
    assert captured["years"] == [2022]
