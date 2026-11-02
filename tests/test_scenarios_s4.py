import pytest

from src.generator.scenarios import SCENARIOS, cost_multiplier_for

SETTINGS = {"imported_share": 0.40, "usd_cost_rise": 0.30, "material_cost_rise": 0.40, "shock_months": 6}


def test_s4_is_a_registered_scenario():
    assert "material_cost_jump" in SCENARIOS


def test_s4_multiplier_is_zero_before_shock_month_then_forty_percent():
    assert cost_multiplier_for("material_cost_jump", 5, SETTINGS) == pytest.approx(1.0)
    assert cost_multiplier_for("material_cost_jump", 6, SETTINGS) == pytest.approx(1.40)


def test_baseline_and_s1_multipliers_unchanged():
    assert cost_multiplier_for("baseline", 0, SETTINGS) == 1.0
    assert cost_multiplier_for("usd_cost_shock", 0, SETTINGS) == pytest.approx(1 + 0.40 * 0.30)
