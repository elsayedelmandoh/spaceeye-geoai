"""Scenario interventions preserve history and are constrained by declared cash."""

import numpy as np
import pandas as pd
import pytest

from src.generator.scenarios import simulate, summary


def settings(**updates):
    return {
        "cutoff": "2025-03", "horizon_months": 12, "history_months": 3,
        "min_capacity_pct": 1.0, "max_capacity_pct": 5.0,
        "working_cash_months": 0.0, "credit_months": 0.0,
        "overhead_cost_share_month": 0.0, "release_share": 1.0,
        "annual_credit_rate_pct": 0.0, "productivity_sd": 0.0,
        "collections_drop": 0.25, "shock_months": 6,
        "usd_cost_rise": 0.30, "imported_share": 0.40, **updates,
    }


def observations(collections=30.0):
    return pd.DataFrame({
        "code": ["C01"] * 5, "month": ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05"],
        "planned_pct": [10., 15., 20., 25., 30.], "reported_pct": [10., 15., 20., 25., 30.],
        "report_date": pd.to_datetime(["2025-01-31", "2025-02-28", "2025-03-31", "2025-04-30", "2025-05-31"]),
        "collections_egp": [collections] * 5, "land_due_egp": [0.] * 5,
        "cost_to_complete_egp": [900., 850., 800., 750., 700.],
        "cover_balance_egp": [1e9] * 5,
    })


def test_scenarios_have_the_same_initial_state_and_preserve_history():
    fin = observations()
    history, state, paths = simulate(fin, ["C01"], settings(), 2026)
    pd.testing.assert_frame_equal(history, fin.iloc[:3].reset_index(drop=True))
    assert state.initial_progress_pct.iloc[0] == 20
    assert paths.groupby("scenario_id").first().progress_before_pct.eq(20).all()
    assert paths.month.min() == "2025-04" and len(paths) == 36


def test_future_contamination_does_not_change_initial_state_or_paths():
    fin = observations()
    before = simulate(fin, ["C01"], settings(productivity_sd=0.05), 2026)
    bad = fin.copy()
    future = bad.month > "2025-03"
    for col in ("planned_pct", "reported_pct", "collections_egp", "cost_to_complete_egp", "cover_balance_egp", "land_due_egp"):
        bad.loc[future, col] = 1e12
    bad.loc[future, "report_date"] = pd.Timestamp("2000-01-01")
    after = simulate(bad, ["C01"], settings(productivity_sd=0.05), 2026)
    for a, b in zip(before, after):
        pd.testing.assert_frame_equal(a, b)


def test_report_unavailable_at_cutoff_is_not_used_as_initial_progress():
    fin = observations()
    fin.loc[2, "reported_pct"] = 99
    fin.loc[2, "report_date"] = pd.Timestamp("2025-04-01")
    _, state, _ = simulate(fin, ["C01"], settings(), 2026)
    assert state.initial_progress_pct.iloc[0] == 15


def test_lower_collections_and_higher_cost_reduce_progress_when_cash_is_binding():
    _, _, paths = simulate(observations(), ["C01"], settings(), 2026)
    pivot = paths.pivot(index="month", columns="scenario_id", values="simulated_progress_pct")
    assert (pivot.collections_drop <= pivot.baseline + 1e-9).all()
    assert (pivot.usd_cost_shock <= pivot.baseline + 1e-9).all()
    assert pivot.collections_drop.iloc[-1] < pivot.baseline.iloc[-1]
    assert pivot.usd_cost_shock.iloc[-1] < pivot.baseline.iloc[-1]
    assert summary(paths).set_index("scenario_id").loc["collections_drop", "progress_difference_vs_baseline_pp"] < 0


def test_abundant_cash_follows_capacity_and_never_uses_cover_as_cash():
    _, _, paths = simulate(observations(10000), ["C01"], settings(), 2026)
    base = paths[paths.scenario_id == "baseline"]
    assert np.allclose(base.simulated_progress_pct, 20 + np.arange(1, 13) * 5)
    _, _, no_cash = simulate(observations(0), ["C01"], settings(), 2026)
    assert no_cash.simulated_progress_pct.eq(20).all()  # even a billion-EGP cover is not liquid cash
    assert no_cash.construction_spend_egp.eq(0).all()


def test_cash_restricted_funds_and_credit_conserve_every_month_and_reproduce():
    opts = settings(release_share=0.75, working_cash_months=1, credit_months=2,
                    annual_credit_rate_pct=20, overhead_cost_share_month=0.001, productivity_sd=0.05)
    first = simulate(observations(), ["C01"], opts, 2026)
    second = simulate(observations(), ["C01"], opts, 2026)
    for a, b in zip(first, second):
        pd.testing.assert_frame_equal(a, b)
    p = first[2]
    assert p.cash_accounting_residual_egp.abs().max() < 1e-8
    assert p.restricted_accounting_residual_egp.abs().max() < 1e-8
    assert (p.closing_debt_egp <= p.credit_limit_egp + 1e-8).all()
    assert (p.construction_spend_egp <= p.desired_construction_spend_egp + 1e-8).all()
    assert p.closing_cash_egp.ge(0).all() and p.simulated_progress_pct.between(0, 100).all()


def test_missing_cutoff_and_invalid_settings_fail_explicitly():
    with pytest.raises(ValueError, match="missing cutoff"):
        simulate(observations().iloc[:2], ["C01"], settings(), 2026)
    with pytest.raises(ValueError, match="release_share"):
        simulate(observations(), ["C01"], settings(release_share=1.1), 2026)
