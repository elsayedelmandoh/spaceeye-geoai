"""Tests for Inspection Agent Plain Python Tools (T-VE-02) - Leak-Free Verification."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from src.inference.tools import (
    get_facts,
    get_kpis,
    get_images,
    get_rules,
    get_complaints_summary,
    build_inspection_context,
    quarter_cutoff_date
)


def test_quarter_cutoff_date():
    p = quarter_cutoff_date("2026Q3")
    assert p.year == 2026
    assert p.month == 9
    assert p.day == 30


def test_get_facts_leak_free():
    facts = get_facts("C07", "2026Q3")
    assert "error" not in facts
    assert facts["code"] == "C07"
    assert facts["district"] == "R7"
    assert facts["land_area_m2"] == 96619.0
    assert facts["cutoff_date"] == "2026-09-30"
    assert isinstance(facts["published_statements"], list)


def test_get_kpis_real_satellite_values():
    kpis = get_kpis("C07", "2026Q3")
    assert "error" not in kpis
    assert kpis["code"] == "C07"
    assert kpis["level"] == 2
    assert "reason_ar" in kpis
    assert len(kpis["reason_ar"]) > 10
    assert kpis["K2_stoppage_quarters"] == 2.0


def test_get_complaints_summary_cutoff():
    cmp = get_complaints_summary("C07", "2026Q3")
    assert "total_count" in cmp
    assert cmp["total_count"] >= 0
    assert "synthetic" in cmp["origin"]


def test_get_images_explicit_missing_status(tmp_path, monkeypatch):
    monkeypatch.setattr("src.inference.tools.APP", tmp_path)
    images = get_images("C07")
    assert images["status"] == "missing_image"
    assert "T-AH-15" in images["reason"]


def test_get_rules_decree_and_laws():
    rules = get_rules()
    assert len(rules) >= 15
    sources = {r["source"] for r in rules}
    assert "decree_2184" in sources
    assert "acud_conditions" in sources


def test_build_inspection_context_complete():
    ctx = build_inspection_context("C07", "2026Q3")
    assert ctx["compound_code"] == "C07"
    assert ctx["quarter"] == "2026Q3"
    assert "facts" in ctx
    assert "kpis" in ctx
    assert "complaints_summary" in ctx
    assert "images" in ctx
    assert "applicable_rules" in ctx


if __name__ == "__main__":
    test_quarter_cutoff_date()
    test_get_facts_leak_free()
    test_get_kpis_real_satellite_values()
    test_get_complaints_summary_cutoff()
    test_get_images_explicit_missing_status()
    test_get_rules_decree_and_laws()
    test_build_inspection_context_complete()
    print("All 7 inspection tool unit tests passed successfully!")
