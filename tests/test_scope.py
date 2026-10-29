"""R8 isolation (T-AH-03): no workspace data needed, fabricated tables only."""

import pandas as pd
import pytest

from src.pipeline.build_real import ORIGINS
from src.pipeline.codify import in_scope
from src.pipeline.common import CFG
from src.pipeline.release import scope_checks

NAMES = ("compounds", "kpi_values")


def _tables(kpi_codes):
    compounds = pd.DataFrame({"code": ["C01", "C02"], "district": CFG["scope_districts"] * 2})
    return {"compounds": compounds, "kpi_values": pd.DataFrame({"code": kpi_codes, "quarter": "2024Q1"})}


def test_in_scope_drops_r8_rows():
    cm = pd.DataFrame({"code": ["C01", "C99"], "district": [CFG["scope_districts"][0], "R8"]})
    assert list(in_scope(cm).code) == ["C01"]


def test_scope_checks_pass_when_kpi_values_hold_only_known_codes():
    assert all(scope_checks(_tables(["C01", "C02"]), CFG["scope_districts"], NAMES).values())


def test_scope_checks_fail_when_kpi_values_hold_an_r8_code():
    checks = scope_checks(_tables(["C01", "C99"]), CFG["scope_districts"], NAMES)
    assert checks["kpi_values_known_codes"] is False


def test_scope_checks_fail_when_compounds_hold_an_r8_district():
    tables = _tables(["C01"])
    tables["compounds"].loc[1, "district"] = "R8"
    assert scope_checks(tables, CFG["scope_districts"], NAMES)["configured_district_scope"] is False


def _every_origin_table(code):
    """one fabricated row per built table; tables without a code column carry none."""
    tables = {}
    for name, columns in ORIGINS.items():
        frame = pd.DataFrame({c: ["x"] for c in columns})
        if "code" in columns:
            frame["code"] = code
        tables[name] = frame
    tables["compounds"] = pd.DataFrame({"code": ["C01"], "district": CFG["scope_districts"]})
    return tables


def test_scope_checks_pass_for_every_built_table():
    assert all(scope_checks(_every_origin_table("C01"), CFG["scope_districts"], tuple(ORIGINS)).values())


@pytest.mark.parametrize("name", [n for n, cols in ORIGINS.items() if "code" in cols and n != "compounds"])
def test_scope_checks_fail_when_any_built_table_holds_an_r8_code(name):
    tables = _every_origin_table("C01")
    tables[name]["code"] = "C99"
    assert scope_checks(tables, CFG["scope_districts"], tuple(ORIGINS))[name + "_known_codes"] is False
