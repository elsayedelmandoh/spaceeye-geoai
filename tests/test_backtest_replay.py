"""The published checkout must reproduce cases without the producer's data drive."""

import shutil

import pytest

from src.pipeline import common, rerun_backtest


def test_published_case_replay_without_external_drive(tmp_path, monkeypatch):
    for name in ("APP", "SRC", "PRIVATE", "RAW", "REAL", "MODEL"):
        monkeypatch.setattr(common, name, tmp_path / "unavailable" / name)
    summary = rerun_backtest.replay(rerun_backtest.INPUTS, tmp_path / "results")
    assert summary["n_cases"] == 6
    assert summary["after_start_reading"] == {"n": 1, "met": False}
    assert summary["point_in_time_reading"]["n"] == 0
    assert summary["literal_reading"]["n"] == 2
    assert "frozen_clock_check" not in summary
    assert (tmp_path / "results/replay_audit.json").exists()


def test_replay_rejects_changed_prepared_input(tmp_path):
    inputs = tmp_path / "inputs"
    shutil.copytree(rerun_backtest.INPUTS, inputs)
    with (inputs / "kpi_inputs.csv").open("a", encoding="utf-8") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="Published file changed: kpi_inputs.csv"):
        rerun_backtest.replay(inputs, tmp_path / "results")
