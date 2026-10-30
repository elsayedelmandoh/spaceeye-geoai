import pandas as pd

from src.pipeline import kpis


def test_k6_status_explains_empty_values():
    assert kpis.k6_status(7, False) == "known"
    assert kpis.k6_status(pd.NA, True) == "not_applicable_started"
    assert kpis.k6_status(pd.NA, False) == "unknown_history"


def test_k5_status_explains_empty_values():
    assert kpis.k5_status(None, pd.NA) == "no_published_deadline"
    assert kpis.k5_status(pd.Timestamp("2023-12-31"), 5) == "computed"
    assert kpis.k5_status(pd.Timestamp("2023-12-31"), pd.NA) == "not_assessable"


def test_assumed_k5_only_without_published_date():
    asof = pd.Timestamp("2026-09-30")
    assert pd.isna(kpis.assumed_k5(pd.Timestamp("2023-12-31"), pd.Timestamp("2020-01-01"), asof, "2021Q1", True))
    assert pd.isna(kpis.assumed_k5(None, pd.NaT, asof, "2021Q1", True))
    value = kpis.assumed_k5(None, pd.Timestamp("2020-01-01"), asof, "2021Q1", True)
    # launch 2020-01 + 48 months = 2024-01; 32 months to 2026-09, minus the 12-month grace = 20
    assert value == 20


def test_arabic_texts_cover_every_status():
    for status in ("known", "not_applicable_started", "unknown_history"):
        assert kpis.K6_TEXT_AR[status]
    for status in ("computed", "no_published_deadline", "not_assessable"):
        assert kpis.K5_TEXT_AR[status]
