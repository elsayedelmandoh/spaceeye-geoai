"""unit tests for the synthetic generator: small pure functions only (no app_data, no earth engine)."""

from itertools import pairwise

import numpy as np

from src.generator import defects, stories, truth
from src.generator.complaints import BODY, CATS, one_text
from src.generator.inputs import MONTHS, N, mi


def test_majority_vote_removes_one_quarter_flicker_and_runs_find_the_stall():
    raw = np.array([1, 1, 0, 1, 1, 0, 0, 0, 0, 0], dtype=bool)
    sm = stories.smooth(raw, 3)
    assert sm.tolist() == [True, True, True, True, True, False, False, False, False, False]
    assert stories.runs(sm, False) == [(5, 5)]


def test_isotonic_fit_is_non_decreasing_and_keeps_the_mean():
    y = [3.0, 1.0, 2.0, 5.0, 4.0]
    f = stories.isotonic(y)
    assert all(b >= a for a, b in pairwise(f)) and abs(sum(f) - sum(y)) < 1e-9


def test_bridge_passes_through_every_knot_and_never_falls():
    knots = [(10, 0.0, "start"), (30, 40.0, "announced"), (60, 70.0, "announced"), (N - 1, 70.0, "end")]
    w = np.random.default_rng(1).uniform(0.0, 2.0, N)
    w[35:45] = 0.0                                          # a stall inside a segment
    p = truth.bridge(knots, w)
    assert all(abs(p[m] - v) < 1e-9 for m, v, _ in knots)
    assert np.diff(p).min() >= -1e-12 and p[:11].max() == 0
    assert np.ptp(p[35:45]) < 1e-9                          # no progress while the weight is zero


def test_plan_hits_100_exactly_at_the_deadline_and_is_flat_after():
    st = truth.Setup(launch=0, cstart=20, plan_start=20, plan_T=36, deadline=56, phase_share=0.4, occ_cap=0.5, optimism=0.0, style="accurate", strength="medium",
                     cost_usd_m2=1000, cover_cancel_pct=30, cover_pct=20, shape=2.5)
    plan = truth.plan_curve(st)
    assert plan[19] == 0 and abs(plan[56] - 100) < 1e-9 and plan[57:].min() == 100 and np.diff(plan).min() >= 0


def test_handover_floor_depends_on_scope():
    st = truth.Setup(0, 0, 0, 36, 36, 0.4, 0.5, 0.0, "accurate", "medium", 1000, 30, 20)
    assert truth.handover_floor("delivery_start", "project", st) == 85
    assert truth.handover_floor("delivery_start", "phase1", st) == 85 * 0.4
    assert truth.handover_floor("delivery_complete", "project", st) == 100


def test_month_grid_and_index_round_trip():
    assert str(MONTHS[0]) == "2017-01" and str(MONTHS[-1]) == "2026-09"
    assert str(MONTHS[mi("2024-03-06")]) == "2024-03"


def test_planted_phone_is_found_by_the_masking_pattern_and_templates_carry_no_digits():
    rng = np.random.default_rng(7)
    assert all(defects.PHONE.search(f"رقمي {defects.fake_phone(rng)}") for _ in range(20))
    assert not any(ch.isdigit() for cat in CATS for t in BODY[cat] for ch in t)
    assert not defects.PHONE.search(one_text(rng, "delay"))
