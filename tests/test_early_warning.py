"""tests for the early-warning experiment: pure helpers, plus a leakage check that runs when app_data exists."""

import copy

import numpy as np
import pandas as pd
import pytest

from src.analysis import ew_eval as E
from src.analysis import ew_features as F
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
