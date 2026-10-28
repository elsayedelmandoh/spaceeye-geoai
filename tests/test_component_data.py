"""Check component data semantics without external files or model fitting."""

import pandas as pd

from src.generator.complaints import BODY, CATS
from src.pipeline.component_data import (
    complaint_benchmark,
    complaint_dataset,
    inspection_context,
    priority_paths,
)


def test_complaint_gold_is_target_only_and_shared_templates_never_cross_splits():
    rows = []
    for cat in CATS:
        for i, text in enumerate(BODY[cat][:3]):
            rows.append({"complaint_id": f"{cat}-{i}", "code": "C01", "created_at": "2024-01-01", "text_ar": text, "category": "other"})
    raw = pd.DataFrame(rows)
    gold = pd.DataFrame({"complaint_id": raw.complaint_id, "true_category": [c.split("-")[0] for c in raw.complaint_id], "duplicate_of": None})
    out = complaint_dataset(raw, gold)
    assert out.groupby("group_id").split.nunique().eq(1).all()
    assert out.label_category.tolist() == [c.split("-")[0] for c in out.complaint_id]
    assert not any(c.startswith("true_") for c in out) and "duplicate_of" not in out
    assert out.desk_category.eq("other").all()


def test_benchmark_has_all_classes_and_disjoint_template_families():
    one, two = complaint_benchmark(), complaint_benchmark()
    pd.testing.assert_frame_equal(one, two)
    families = []
    for _, group in one.groupby("split"):
        assert set(group.label_category) == set(CATS)
        families.append(set(";".join(group.template_ids).split(";")))
    assert all(not families[i] & families[j] for i in range(3) for j in range(i + 1, 3))


def test_inspection_context_excludes_future_statements_and_field_records():
    comp = pd.DataFrame({"code": ["C01"], "units": [100], "first_deadline": ["2030-01-01"]})
    sat = pd.DataFrame({"code": ["C01"], "qi": [36], "quarter": ["2025Q1"], "activity_prob": [0.5], "active": [True], "K4": [True]})
    yearly = pd.DataFrame({"code": ["C01"], "year": [2025]})
    statements = pd.DataFrame({"code": ["C01", "C01"], "published_date": ["2025-03-31", "2025-04-01"], "statement_id": ["S1", "S2"], "record_id": ["R1", "R2"]})
    kpi = pd.DataFrame({"code": ["C01"], "quarter": ["2025Q1"], "level": [3]})
    financial = pd.DataFrame({"code": ["C01"], "month": ["2025-03"]})
    complaints = pd.DataFrame({"code": ["C01"], "created_at": [pd.Timestamp("2025-03-31 14:00")], "text_ar": ["test"]})
    sources = pd.DataFrame({"code": ["C01"], "record_id": ["R1"], "published_date": ["2025-03-31"], "url": ["https://example.org/123"]})
    visits = pd.DataFrame({"code": ["C01"], "visit_date": [pd.Timestamp("2025-04-01")]})
    out = inspection_context(comp, sat, yearly, statements, kpi, financial, complaints, pd.DataFrame(), sources, visits, "C01", "2025Q1", [])
    assert len(out["public_evidence"]["statements"]) == 1
    assert not out["public_evidence"]["annual_context"]
    assert "first_deadline" not in out["public_evidence"]["register"][0]
    assert out["generated_operations"]["complaint_count"] == 1
    assert not out["generated_operations"]["synthetic_visits"]


def test_financial_priority_uses_declared_b5_rule_and_ignores_future_finance():
    paths = pd.DataFrame({"code": ["C01"] * 2, "month": ["2025-04"] * 2, "scenario_id": ["baseline", "collections_drop"], "simulated_progress_pct": [30.0, 0.0]})
    state = pd.DataFrame({"code": ["C01"], "cutoff": ["2025-03"], "capacity_pct_month": [1.0]})
    kpi = pd.DataFrame({"code": ["C01"], "quarter": ["2025Q1"], "K4": [True], "level": [4], "K2": [0], "K3": [0], "may_be_complete": [False]})
    financial = pd.DataFrame({"code": "C01", "month": pd.period_range("2023-01", "2025-03", freq="M").astype(str), "cover_required_egp": 0, "cover_balance_egp": 100, "land_months_late": 0, "planned_pct": 40, "units_sold": 1})
    complaints = pd.DataFrame({"code": pd.Series(dtype=str), "created_at": pd.Series(dtype="datetime64[ns]")})
    one = priority_paths(paths, state, kpi, financial, complaints, pd.DataFrame())
    future = pd.concat([financial, financial.iloc[[-1]].assign(month="2025-04", cover_balance_egp=-1, land_months_late=999)])
    two = priority_paths(paths, state, kpi, future, complaints, pd.DataFrame())
    pd.testing.assert_frame_equal(one, two)
    levels = one.set_index("scenario_id").hypothetical_level
    assert levels["baseline"] == 4 and levels["collections_drop"] == 2
    assert one.groupby(["scenario_id", "month"]).selected.sum().max() <= 4
