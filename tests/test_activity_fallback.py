"""T-AH-14: the K1 fallback switch for the activity flag."""

import numpy as np
import pandas as pd
import pytest

from src.pipeline import activity


def _scored():
    return pd.DataFrame({"code": ["C01"] * 3, "qi": [12, 13, 14], "K1": [0.05, 0.0, np.nan],
                         "activity_prob": [0.2, 0.9, 0.7], "active": pd.array([False, True, True], dtype="boolean")})


def test_model_source_keeps_the_activity_score():
    out = activity.apply_source(_scored(), "model")
    assert out.active.tolist() == [False, True, True]
    assert out.activity_prob.notna().all()


def test_k1_source_uses_k1_and_leaves_a_empty():
    out = activity.apply_source(_scored(), "k1")
    assert out.activity_prob.isna().all()
    assert out.active[0] == (0.05 > activity.THR) and not out.active[1]
    assert pd.isna(out.active[2])  # unknown K1 stays unknown, never "inactive"


def test_unknown_source_is_rejected():
    with pytest.raises(ValueError):
        activity.apply_source(_scored(), "ndbi")
