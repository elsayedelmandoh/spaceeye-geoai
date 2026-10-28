"""Critical data semantics only: no model fitting and no workspace inputs."""

import pandas as pd

from src.pipeline import kpis
from src.pipeline.complete_data import (
    capacity_paths,
    land_assumptions,
    outcome_labels,
    quarterly_finances,
)


def test_fine_union_retains_exposure_and_does_not_double_count_grace():
    r = kpis.fine_months(pd.Timestamp("2020-01-31"), pd.Timestamp("2022-01-31"), None, True)
    assert r == {"K5_no_start_months": 24, "K5_post_grace_months": 12, "K5_overlap_months": 12, "K5_months": 24}
    r = kpis.fine_months(pd.Timestamp("2020-01-31"), pd.Timestamp("2022-01-31"), "2020Q3", True)
    assert r["K5_no_start_months"] == 5 and r["K5_months"] == 17
    stopped = kpis.fine_months(pd.Timestamp("2020-01-31"), pd.Timestamp("2022-01-31"), None, True, pd.Timestamp("2021-03-01"))
    assert stopped["K5_months"] == 14


def test_missing_contract_deadline_or_no_start_evidence_is_not_zero_fine():
    assert pd.isna(kpis.fine_months(None, pd.Timestamp("2022-01-31"), None, True)["K5_months"])
    r = kpis.fine_months(pd.Timestamp("2020-01-31"), pd.Timestamp("2022-01-31"), None, False)
    assert pd.isna(r["K5_months"]) and r["K5_post_grace_months"] == 12


def test_k6_priority_and_promise_publication_fallback_have_no_future_leakage():
    assert kpis.level_of(0, 0, False, False, 25) == 1
    assert kpis.level_of(0, 0, False, False, 13) == 2
    assert kpis.level_of(0, 0, False, False, 12) is None
    assert kpis.level_of(0, 0, True, False, 25) == 3
    sat = pd.DataFrame({"code": "C01", "qi": range(8), "active": False, "K4": True})
    stm = pd.DataFrame({"code": ["C01"], "kind": ["promise"], "subtype": [None], "period_start": ["2020-01-01"], "published_date": ["2016-05-10"]})
    out = kpis.add_k2(sat, stm)
    assert pd.isna(out.K6.iloc[0]) and out.start_reference_source.iloc[-1] == "promise_publication"
    assert out.K6.iloc[-1] == 20  # reference is publication, never future delivery period
    pd.testing.assert_frame_equal(out.iloc[:4].reset_index(drop=True), kpis.add_k2(sat.iloc[:4], stm))


def test_capacity_scenarios_only_select_eligible_rows():
    kpi = pd.DataFrame({"code": [f"C{i:02}" for i in range(1, 9)], "quarter": "2026Q3", "level": [1, 1, 2, 2, 3, 3, 4, pd.NA], "K2": 0, "K3": 0})
    out = capacity_paths(kpi, 4)
    assert out.groupby("scenario_id").selected.sum().to_dict() == {"baseline": 4, "capacity_minus_2": 2, "capacity_plus_2": 6}
    assert not out.loc[out.code.isin(["C07", "C08"]), "selected"].any()


def test_completion_label_requires_full_handover_and_full_future_horizon():
    truth = pd.DataFrame({"code": "C01", "month": pd.period_range("2024-01", periods=8, freq="M").astype(str), "handed_over_units": [0, 30, 30, 30, 100, 100, 100, 100], "true_distress": False})
    keys = pd.DataFrame({"code": ["C01"] * 3, "quarter": ["2024Q1", "2024Q2", "2024Q3"], "month": ["2024-01", "2024-02", "2024-03"]})
    comp = pd.DataFrame({"code": ["C01"], "units": [100]})
    out = outcome_labels(keys, truth, comp)
    assert out.y_outcome_6m.iloc[:2].tolist() == ["completed", "completed"]
    assert pd.isna(out.y_outcome_6m.iloc[2])
    partial = truth.assign(handed_over_units=30)
    assert outcome_labels(keys, partial, comp).y_outcome_6m.iloc[0] == "ongoing"
    truth.loc[2, "true_distress"] = True
    assert outcome_labels(keys, truth, comp).y_outcome_6m.iloc[0] == "distressed"


def test_generated_allocation_and_old_price_are_bounded_and_reproducible():
    comp = pd.DataFrame({"code": ["C01"], "land_area_m2": [10000], "land_area_origin": ["real"]})
    sat = pd.DataFrame({"code": ["C01"], "observed_start_quarter": ["2019Q2"]})
    stm = pd.DataFrame({"code": ["C01"], "published_date": ["2018-01-15"]})
    one, two = land_assumptions(comp, sat, stm), land_assumptions(comp, sat, stm)
    pd.testing.assert_frame_equal(one, two)
    r = one.iloc[0]
    assert r.allocation_date_assumed < pd.Timestamp("2018-01-15")
    assert 2500 <= r.assumed_land_price_egp_m2 <= 5000
    assert r.assumed_land_value_egp == r.assumed_land_price_egp_m2 * 10000


def test_quarterly_sales_are_summed_flows_and_balances_use_last_month():
    mon = pd.DataFrame({"code": "C01", "month": pd.period_range("2024-01", periods=3, freq="M"),
                        "units_sold": [2, 3, 4], "collections_egp": [100, 200, 300], "land_due_egp": 0,
                        "land_paid_egp": 0, "kwh": 10, "planned_pct": [10, 20, 30], "cover_required_egp": 50,
                        "cover_balance_egp": [1, 2, 3], "cost_to_complete_egp": 100, "land_months_late": 0,
                        "meters_active": 2, "roads_paved_share": 0.1})
    reports = pd.DataFrame({"code": ["C01"], "report_date": [pd.Timestamp("2024-04-01")], "reported_pct": [90]})
    kpi = pd.DataFrame({"code": ["C01"], "quarter": ["2024Q1"], "K5_months": [1], "K6": [pd.NA]})
    land = pd.DataFrame({"code": ["C01"], "assumed_land_value_egp": [1000], "fine_rate_month": [0.01]})
    out = quarterly_finances(mon, reports, kpi, land).iloc[0]
    assert out.units_sold == 9 and out.collections_egp == 600 and out.cover_balance_egp == 3
    assert pd.isna(out.reported_pct)  # April report cannot enter a March cutoff
