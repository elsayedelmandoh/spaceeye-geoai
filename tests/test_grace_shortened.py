"""S5 shortens only the warning-clock grace and remains isolated from base outputs."""

import numpy as np

from src.generator import simulate
from src.generator.economy import Economy
from src.generator.inputs import LABEL, MONTHS, N
from src.generator.observe import Reports, acud
from src.generator.stories import Signals
from src.generator.truth import Setup, Truth
from src.pipeline.common import CFG


def fabricated_inputs(k3: np.ndarray):
    sig = Signals(
        code="C01", developer="D01", district="D01", units=100,
        bua_m2=1000.0, land_area_m2=1000.0, cover_pct=20.0,
        state=np.zeros(N, dtype=bool), k3=k3, handovers=[],
    )
    st = Setup(
        launch=0, cstart=0, plan_start=0, plan_T=24, deadline=24,
        phase_share=0.5, occ_cap=1.0, optimism=0.0, style="accurate",
        strength="strong", cost_usd_m2=1000.0, cover_cancel_pct=25.0,
        cover_pct=20.0,
    )
    tr = Truth(
        plan=np.linspace(0.0, 100.0, N),
        progress=np.linspace(0.0, 100.0, N),
        handed=np.zeros(N, dtype=int), batches=np.zeros(N, dtype=int),
        occupied=np.zeros(N, dtype=int), roads=np.zeros(N), stalled=np.zeros(N, dtype=bool),
    )
    eco_fields = {
        name: np.zeros(N)
        for name in Economy.__dataclass_fields__
        if name not in {"price", "events"}
    }
    eco_fields["price"] = np.full(N, np.nan)
    eco_fields["events"] = []
    eco = Economy(**eco_fields)
    rep = Reports(
        val=50.0 + np.arange(N) * 0.5,
        date=np.full(N, np.datetime64("NaT", "ns"), dtype="datetime64[ns]"),
        announced=np.zeros(N, dtype=bool), regular=np.zeros(N, dtype=bool),
        covers=np.full(N, -1, dtype=int),
    )
    return sig, st, tr, eco, rep, np.random.default_rng(2026)


def grace_event_month(events: list) -> int:
    return next(month for month, kind in events if kind == "grace_expiry")


def test_explicit_none_grace_matches_default_warning_clock():
    k3 = np.full(N, 7, dtype=int)
    k3[8:] = 13
    inputs = fabricated_inputs(k3)

    default_warn, default_level, default_events = acud(*inputs)
    none_warn, none_level, none_events = acud(*inputs, grace_months=None)

    np.testing.assert_array_equal(none_warn, default_warn)
    np.testing.assert_array_equal(none_level, default_level)
    assert none_events == default_events


def test_six_month_grace_expires_before_twelve_month_grace():
    k3 = np.full(N, 7, dtype=int)
    k3[8:] = 13
    inputs = fabricated_inputs(k3)

    _, _, six_month_events = acud(*inputs, grace_months=6)
    _, _, twelve_month_events = acud(*inputs, grace_months=12)

    assert grace_event_month(six_month_events) < grace_event_month(twelve_month_events)


def test_grace_below_six_month_threshold_does_not_change_warning_clock():
    inputs = fabricated_inputs(np.full(N, 5, dtype=int))

    six_warn, six_level, six_events = acud(*inputs, grace_months=6)
    twelve_warn, twelve_level, twelve_events = acud(*inputs, grace_months=12)

    np.testing.assert_array_equal(six_warn, twelve_warn)
    np.testing.assert_array_equal(six_level, twelve_level)
    assert six_events == twelve_events


def test_s5_table_has_isolated_scenario_metadata(monkeypatch):
    k3 = np.full(N, 7, dtype=int)
    k3[8:] = 13
    sig, st, tr, eco, rep, _ = fabricated_inputs(k3)
    warn = np.zeros(N, dtype=bool)
    warn[0] = True
    level = np.array(["on_plan"] * N, dtype=object)
    unit = simulate.Unit(
        sig=sig, st=st, tr=tr, rep=rep, eco=eco,
        mt=np.zeros(N, dtype=int), kwh=np.zeros(N), home_occ=np.zeros(N),
        warn=warn, level=level, warn_events=[(0, "grace_expiry")],
    )

    def fake_build(grace_months=None):
        assert grace_months == 6
        return {"units": [unit]}

    monkeypatch.setattr(simulate, "build", fake_build)
    frame = simulate.grace_shortened_table()

    assert CFG["generator"]["scenarios"]["grace_months_s5"] == 6
    assert list(frame.columns) == [
        "code", "month", "level", "warning_issued", "scenario_id", "synthetic_label",
    ]
    assert frame["scenario_id"].eq("grace_shortened").all()
    assert frame["synthetic_label"].eq(LABEL).all()
    assert frame[["code", "month"]].notna().all().all()
    assert frame["code"].eq("C01").all()
    assert frame["month"].iloc[0] == str(MONTHS[0])
    assert frame["warning_issued"].iloc[0]
