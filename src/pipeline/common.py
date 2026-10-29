"""
propose: shared config, paths and quarter helpers for the pipeline.
input: configs/data.yaml.
output: cfg dict, path helpers, quarter index helpers (0 = 2016Q1).
"""

from pathlib import Path

import pandas as pd
import yaml

BASE_DIR = Path(__file__).resolve().parents[2]


def load_cfg(path: Path | None = None) -> dict:
    with open(path or BASE_DIR / "configs" / "data.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


CFG = load_cfg()
SRC = Path(CFG["paths"]["real_data"])
APP = Path(CFG["paths"]["app_data"])
PRIVATE = Path(CFG["paths"]["private"])
RAW, REAL, MODEL = APP / "raw", APP / "real", APP / "model"


def src(key: str) -> Path:
    return SRC / CFG["sources"][key]


def qindex(label: str) -> int:
    """'2024Q2' -> quarters since 2016Q1."""
    return (int(label[:4]) - 2016) * 4 + int(label[5]) - 1


def qindex_of(ts: pd.Timestamp) -> int:
    """Timestamp -> quarters since 2016Q1."""
    return (ts.year - 2016) * 4 + (ts.month - 1) // 3


def qlabel(qi: int) -> str:
    return f"{2016 + qi // 4}Q{qi % 4 + 1}"


def qend(qi: int) -> pd.Timestamp:
    """last day of quarter qi."""
    return pd.Timestamp(2016 + qi // 4, 3 * (qi % 4) + 3, 1) + pd.offsets.MonthEnd(0)


def summer_year(qi: int) -> int:
    """year of the latest Jun-Sep summer already over at the end of quarter qi."""
    return 2016 + qi // 4 if qi % 4 >= 2 else 2015 + qi // 4


N_Q = qindex(CFG["last_quarter"]) + 1


def months_between(a: pd.Timestamp, b: pd.Timestamp) -> int:
    """Nearest month (days / 30.44), not completed months.

    KEPT: K3 and K6 use this nearest-month arithmetic, while K5 uses calendar months.
    Changing it after results exist would shift levels.
    """
    return round((b - a).days / 30.44)
