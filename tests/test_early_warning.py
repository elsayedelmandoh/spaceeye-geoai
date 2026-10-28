"""tests for the early-warning experiment: pure helpers, plus a leakage check that runs when app_data exists."""

import copy
import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from src.analysis import early_warning as W
from src.analysis import ew_eval as E
from src.analysis import ew_features as F
from src.analysis import ew_report as R
from src.pipeline.common import APP


def test_balance_in_thousands_is_fixed_and_normal_drops_are_not():
    fin = pd.DataFrame({
        "code": ["C01"] * 6, "month": [f"2025-0{i}" for i in range(1, 7)],
        "cover_balance_egp": [100e6, 100e6, 100e3, 100e3, 100e6, 50e6],
        "reported_pct": np.nan, "report_date": pd.NaT,
    })
    mon, rep, fixed = F.clean_fin(fin)
    assert fixed == 2 and mon["cover_balance_egp"].tolist() == [100e6, 100e6, 100e6, 100e6, 100e6, 50e6] and rep.empty


def test_topn_ties_break_by_code_and_quarters_are_independent():
    df = pd.DataFrame({"quarter": ["2025Q1"] * 3 + ["2025Q2"] * 3, "code": ["C02", "C01", "C03"] * 2, "s": [1, 1, 0, 0, 1, 1]})
    f = E.topn_flag(df, "s", 1)
    assert f.tolist() == [False, True, False, False, True, False]


def test_event_lead_counts_only_flags_before_onset_and_needs_one_inside_six_months():
    months = pd.period_range("2025-03", "2026-03", freq="Q-DEC").asfreq("M", "end")
    df = pd.DataFrame({"code": "C01", "quarter": [f"{m.year}Q{m.quarter}" for m in months], "month": months})
    onset = pd.DataFrame([{"code": "C01", "onset": pd.Period("2026-02", "M")}])
    flag = pd.Series([True, False, True, True, True], index=df.index)                    # 2025-03, -06, -09, -12, 2026-03
    ev = E.event_table(df, flag, onset, df["quarter"].tolist())
    assert bool(ev["caught"].iloc[0]) and ev["lead"].iloc[0] == 11                       # earliest flag within 12 months: 2025-03 is 11 months before
    none = E.event_table(df, pd.Series([True, True, False, False, False], index=df.index), onset, df["quarter"].tolist())
    assert not bool(none["caught"].iloc[0])                                              # flagged only more than 6 months ahead


def test_holdout_picks_20_percent_and_includes_a_developer_with_a_test_positive():
    rows = []
    for i in range(10):
        for q in E.TEST_LABEL_Q:
            rows.append({"developer": f"D{i:02d}", "quarter": q, "label": i == 3, "censored": False})
    held, _ = E.holdout_developers(pd.DataFrame(rows))
    assert len(held) == 2 and "D03" in held


@pytest.mark.parametrize("size", [2, 3])
def test_report_counts_follow_scope_and_allow_no_positive_held_events(size):
    rows = []
    for i in range(1, size + 1):
        for quarter in ("2024Q4", "2025Q2", "2025Q3"):
            rows.append({
                "code": f"C{i:02d}", "developer": f"D{i:02d}", "quarter": quarter,
                "censored": False, "label": i == 1 and quarter != "2025Q2",
                "distress_now": i == 1 and quarter == "2025Q3",
            })
    event = pd.DataFrame([{"code": "C01", "onset": pd.Period("2025-07", "M")}])
    state = {"table": pd.DataFrame(rows), "held": ["D02"], "ev_all": event, "ev_test": event}
    facts = R.report_facts(state, 8)
    assert facts["n_compounds"] == size and facts["test_rows"] == 2 * size
    assert facts["train_positives"] == 1 and facts["test_positives"] == 1
    assert facts["test_current_rows"] == 1 and facts["test_current_codes"] == "C01"
    assert facts["held_codes"] == "C02" and facts["held_count"] == 1
    assert facts["held_positives"] == facts["held_events"] == 0
    assert facts["test_events_text"] == "C01 (2025-07)"
    assert facts["precision_ceiling"] == facts["test_rate"] == 1 / (2 * size)
    assert facts["constant_brier"] == pytest.approx((1 / (2 * size)) * (1 - 1 / (2 * size)))


def test_report_counts_allow_no_positive_rows_or_events():
    state = {
        "table": pd.DataFrame([{"code": "C01", "developer": "D01", "quarter": "2025Q2",
                                "censored": False, "label": False, "distress_now": False}]),
        "held": ["D01"], "ev_all": pd.DataFrame(), "ev_test": pd.DataFrame(),
    }
    facts = R.report_facts(state, 8)
    assert facts["test_positives"] == facts["test_new_rows"] == facts["held_events"] == 0
    assert facts["test_events_text"] == "لا توجد أحداث"
    assert facts["test_current_codes"] == "لا يوجد"
    assert facts["constant_brier"] == 0 and np.isnan(facts["one_hit_points"])


def _training_table():
    rows = []
    for code in ("C01", "C02"):
        for quarter in ("2024Q4", "2025Q1", "2025Q2", "2026Q2"):
            rows.append({**dict.fromkeys(F.FEATURES, 0.25), "code": code, "developer": "D" + code[1:],
                         "quarter": quarter, "month": F.qend_month(quarter), "label": code == "C01",
                         "censored": quarter == "2026Q2", "story": "must not enter X", "true_cash_egp": 1e15,
                         "distress_now": True, "warning_issued": True, "status_level": "distressed", "p_lr_both_time": 1.0})
    return pd.DataFrame(rows)


def test_training_export_uses_only_declared_features_and_records_censoring(tmp_path):
    table = _training_table()
    state = {"table": table, "held": ["D02"], "held_seed": E.SPLIT_SEED}
    folder, public = tmp_path / "private", tmp_path / "public"
    outputs = W.export_training_dataset(state, {"source": "abc"}, folder, public)
    data = pd.read_parquet(folder / "ml_dataset.parquet")
    assert list(data) == [*W.TRAINING_KEYS, *F.FEATURES, W.TARGET, W.CENSOR]
    assert not {"story", "true_cash_egp", "distress_now", "status_level", "warning_issued", "p_lr_both_time"} & set(data)
    metadata = json.loads((folder / "ml_dataset_metadata.json").read_text(encoding="utf-8"))
    assert metadata["features"] == F.FEATURES and metadata["target"] == W.TARGET
    assert metadata["split_counts"] == {"train": {"rows": 2, "positive": 1, "negative": 1, "unlabelled": 0},
                                         "time_test": {"rows": 2, "positive": 1, "negative": 1, "unlabelled": 0},
                                         "censored": {"rows": 2, "positive": 0, "negative": 0, "unlabelled": 2}}
    assert data.loc[data[W.CENSOR], W.TARGET].isna().all()
    assert metadata["excluded_uncensored_quarters"] == ["2025Q1"]
    assert metadata["input_and_source_sha256"] == {"source": "abc"}
    assert metadata["dataset_sha256"] == hashlib.sha256((folder / "ml_dataset.parquet").read_bytes()).hexdigest()
    summary = json.loads((public / "dataset_summary.json").read_text(encoding="utf-8"))
    assert summary["rows"] == 8 and "codes" not in summary and "data" not in summary
    again = W.export_training_dataset(state, {"source": "abc"}, folder, public)
    assert outputs == again


def test_training_export_rejects_duplicate_keys_and_forbidden_feature_declarations(monkeypatch):
    table = _training_table()
    with pytest.raises(ValueError, match="duplicate"):
        W.training_dataset(pd.concat([table, table.iloc[:1]], ignore_index=True))
    monkeypatch.setattr(F, "FEATURES", [*F.FEATURES, "status_level"])
    with pytest.raises(ValueError, match="evaluation-only"):
        W.training_dataset(table)


def test_distress_calibration_band_scales_with_scope_without_changing_observations(monkeypatch):
    from src.generator import checks
    monkeypatch.setitem(checks.GEN, "calibration", {"reference_compounds": 22, "ever_distressed_min": 1, "ever_distressed_max": 7})
    assert checks.distress_calibration_bounds(22) == (1, 7)
    assert checks.distress_calibration_bounds(12) == (1, 4)
    assert checks.distress_calibration_bounds(1) == (1, 1)


@pytest.mark.skipif(not (APP / "sim" / "fin_monthly.parquet").exists(), reason="app_data not built")
def test_features_do_not_read_anything_dated_after_the_cutoff():
    src = F.Source()
    month = pd.Period("2025-03", "M")
    base = F.snapshot(src, month)
    base_sat = F.sat_features(src, "2025Q1")
    date = month.end_time.normalize()
    bad = copy.copy(src)
    mon = src.mon.copy()
    late = mon["month"] > month
    for c in ("cover_balance_egp", "cover_required_egp", "collections_egp", "kwh", "meters_active", "land_months_late", "planned_pct"):
        mon.loc[late, c] = 1e12
    rep = src.rep.copy()
    rep.loc[rep["report_date"] > date, "reported_pct"] = 999.0
    cmp_ = src.cmp[src.cmp["created_at"] < date + pd.Timedelta(days=1)]                                     # drop every later complaint
    bad.mon, bad.rep, bad.cmp = mon, rep, cmp_
    bad.rates = F.complaint_rates(cmp_, src.compounds["units"], src.months)
    kpi = src.kpi.copy()
    kpi.loc[kpi.index.get_level_values("quarter") > "2025Q1", ["activity_prob", "K2", "K3", "level"]] = 99
    bad.kpi = kpi
    pd.testing.assert_frame_equal(F.snapshot(bad, month), base)
    pd.testing.assert_frame_equal(F.sat_features(bad, "2025Q1"), base_sat)
