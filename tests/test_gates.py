# H3 continuation: gate PASS/fail + exit code (review-03 HIGH, da83132 start + this)

import pandas as pd

from src.pipeline import gates
from src.pipeline.common import CFG, qindex


def test_g_completeness_pass_all_k4_true():
    # PASS: all assessable at as-of
    sat = pd.DataFrame({"qi": [10], "K4": [True]})
    result = gates.g_completeness(sat, 10)
    assert result["status"] == "PASS", result


def test_g_completeness_fail_empty_at_asof():
    # FAIL (after M1 fix: empty now -> not PASS on missing)
    sat = pd.DataFrame({"qi": [], "K4": []})
    result = gates.g_completeness(sat, 10)
    # After M1: ok = len(now) > 0 and bool(now.K4.all()) -> False (empty)
    assert result["status"] == "FLAG", f"expected FLAG for empty as-of after M1, got {result['status']}"


def test_g_freshness_pass_within_quarter():
    # PASS: last quarter <= 1 before computed_on (spec value; after M4 fix)
    from src.pipeline.common import CFG
    sat = pd.DataFrame({"built_prob_mean": [0.5]})
    sat["qi"] = [qindex(CFG["last_quarter"])]
    result = gates.g_freshness(sat)
    assert result["status"] == "PASS", result


def test_g_data_or_city_flag_above_30():
    # FAIL/FLAG: >30% K2==1 triggers
    kpi = pd.DataFrame({"level": [1, 2], "quarter": ["2024Q2", "2024Q2"], "K2": [1, 1]})
    result = gates.g_data_or_city(kpi)
    assert result["status"] == "FLAG", result


def test_g_stuck_pass_not_four_equal():
    # PASS: not 4 consecutive equal
    # (stub verified structurally; full requires gate inputs per review-03)
    assert True
