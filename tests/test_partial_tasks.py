"""Critical semantics of committee exports, privacy and missing-class evaluation."""

import numpy as np
import pandas as pd
import pytest

from src.analysis.current_evaluation import (
    estimator,
    masks,
    probabilities,
    rule_columns,
    top_flags,
)
from src.pipeline.kpis import reason_ar
from src.pipeline.privacy import assert_safe_texts, mask_text


def test_arabic_reason_keeps_unknown_deadline_and_missing_start_distinct():
    row = {"K4": True, "started": False, "K2": np.nan, "first_end": None, "K3": 0, "K6": 25,
           "handover": False, "may_be_complete": False, "n_images": 8}
    text = reason_ar(row)
    assert "25" in text and "لا يوجد موعد" in text and "غير مؤكدة" in text
    row["K4"] = False
    assert "غير قابل للتقييم" in reason_ar(row)


def test_pre_model_masking_handles_unicode_phones_and_supplied_names():
    text = "الاسم: شخص تجريبي، هاتف +٢٠ ١٠١٢٣٤٥٦٧٨؛ Contact Example Person."
    masked = mask_text(text, ["Example Person"])
    assert "شخص تجريبي" not in masked and "Example Person" not in masked and "١٠١٢٣٤٥٦٧٨" not in masked
    assert_safe_texts([masked], ["Example Person"])
    with pytest.raises(ValueError):
        assert_safe_texts(["Call 01012345678"])


def test_binary_probabilities_are_normalized_and_imputer_is_train_only():
    model = estimator("logistic").fit(pd.DataFrame({"x": [0., 2., 4., np.nan]}), ["not_distressed", "not_distressed", "distressed", "distressed"])
    before = model.steps[0][1].statistics_.copy()
    out = probabilities(model, pd.DataFrame({"x": [np.nan, 1e9]}))
    assert set(out.columns) == {"distressed", "not_distressed"}
    np.testing.assert_allclose(out.sum(axis=1), 1)
    np.testing.assert_equal(before, model.steps[0][1].statistics_)


def test_current_split_never_trains_on_embargo_censor_or_existing_completion():
    frame = pd.DataFrame({"quarter": ["2024Q4", "2025Q1", "2025Q2", "2024Q3", "2024Q2"],
                          "label_censored": [False, False, False, True, False],
                          "already_completed_at_cutoff": [False, False, False, False, True]})
    train, test = masks(frame)
    assert train.tolist() == [True, False, False, False, False]
    assert test.tolist() == [False, False, True, False, False]


def test_rank_excludes_unassessable_even_with_highest_model_score():
    frame = pd.DataFrame({"code": ["C01", "C02", "C03"], "quarter": "2026Q1", "K4": [False, True, True]})
    assert top_flags(frame, pd.Series([1., .1, .2]), 1).tolist() == [False, False, True]


def test_financial_rule_keeps_completion_cap_and_unknown_level():
    frame = pd.DataFrame({"level": [2, 5], "cover_req0": 0, "cover_ratio": .5, "land_late": 3,
                          "cmp_pctl": .99, "gap": 30, "K2": 4, "K3": 10, "may_be_complete": True, "K4": True})
    out = rule_columns(frame)
    assert out.current_rule_level.iloc[0] == 3 and pd.isna(out.current_rule_level.iloc[1])
