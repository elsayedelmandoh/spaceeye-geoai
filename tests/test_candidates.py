"""candidate switches stay off by default; the acceleration helper is causal and never fills gaps with zero."""

import numpy as np
import pandas as pd
import pytest

from src.analysis import current_evaluation as ev
from src.analysis.current_evaluation import without_height
from src.analysis.ew_features import a_acceleration
from src.pipeline.common import CFG


def test_candidate_switches_are_off_by_default():
    assert CFG["candidates"] == {"variant": "v1", "no_height_ablation": False}


def test_without_height_drops_only_height():
    cols = ["A", "height_mean_m", "veg_share"]
    assert without_height(cols) == ["A", "veg_share"]
    assert without_height(["A"]) == ["A"]


def _series(values, code="C01"):
    return pd.DataFrame({"code": code, "qi": range(len(values)), "A": values})


def test_acceleration_matches_the_year_over_year_second_difference():
    frame = _series([0, 1, 2, 3, 4, 5, 6, 7, 20])
    out = a_acceleration(frame)
    assert out.iloc[:8].isna().all()
    assert out.iloc[8] == (20 - 4) - (4 - 0)


def test_acceleration_is_causal_and_does_not_mix_codes():
    base = _series(list(range(9)))
    changed = base.copy()
    changed.loc[8, "A"] = 99
    assert a_acceleration(base).iloc[:8].isna().all() and a_acceleration(changed).iloc[:8].isna().all()
    other = pd.concat([_series([5] * 9, "C02"), base], ignore_index=True)
    assert a_acceleration(other).iloc[9 + 8] == a_acceleration(base).iloc[8]


def test_acceleration_gap_is_nan_not_zero():
    frame = _series(list(range(9))).drop(index=4).reset_index(drop=True)
    assert np.isnan(a_acceleration(frame).iloc[-1])


def test_default_variant_keeps_the_frozen_v1_paths():
    assert ev.VARIANT == "v1" and ev.STEM == "CURRENT"
    assert ev.OUT.name == "ml_current" and ev.PROTOCOL.name == "EW_PROTOCOL_CURRENT.md"


def test_non_v1_protocol_must_match_its_recorded_hash(tmp_path, monkeypatch):
    protocol = tmp_path / "EW_PROTOCOL_V2.md"
    protocol.write_text("frozen text", encoding="utf-8")
    monkeypatch.setattr(ev, "VARIANT", "v2")
    monkeypatch.setattr(ev, "PROTOCOL", protocol)
    protocol.with_suffix(".sha256").write_text(f"{ev.sha(protocol)}  EW_PROTOCOL_V2.md\n", encoding="utf-8")
    assert ev.checked_protocol_hash() == ev.sha(protocol)
    protocol.write_text("edited after freezing", encoding="utf-8")
    with pytest.raises(ValueError, match="changed after its hash"):
        ev.checked_protocol_hash()
