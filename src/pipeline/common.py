"""
propose: shared config, paths and quarter helpers for the pipeline.
input: configs/data.yaml.
output: cfg dict, path helpers, quarter index helpers (0 = 2016Q1).
"""

import os
import re
from pathlib import Path

import pandas as pd
import yaml

BASE_DIR = Path(__file__).resolve().parents[2]


def load_cfg(path: Path | None = None) -> dict:
    with open(path or BASE_DIR / "configs" / "data.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def native_path(path: str) -> Path:
    """a Windows drive path such as F:/x is read as /mnt/f/x on Linux and WSL (the drive must be mounted there)."""
    drive = re.match(r"^([A-Za-z]):[/\\](.*)$", path)
    if drive and os.name != "nt":
        return Path("/mnt") / drive.group(1).lower() / drive.group(2).replace("\\", "/")
    return Path(path)


def resolve_path(path: str, base: Path = BASE_DIR) -> Path:
    """Resolve a configured path against the checkout, independently of cwd."""
    result = native_path(path)
    return result.resolve() if result.is_absolute() else (base / result).resolve()


def data_paths(cfg: dict, root: str | None = None) -> dict[str, Path]:
    root = root if root is not None else os.environ.get("SPACEEYE_DATA_ROOT")
    if root:
        base = resolve_path(root)
        return {key: base / folder for key, folder in
                (("real_data", "real_data"), ("app_data", "app_data"), ("private", "private"))}
    return {key: resolve_path(value) for key, value in cfg["paths"].items()}


def require_data_root() -> None:
    """Explain how to initialize a fresh checkout without a machine-specific drive."""
    if not APP.exists():
        raise SystemExit(f"Data directory not found: {APP}\nRun python -m src.pipeline.setup_review for prepared data. "
                         "For source rebuilds, read docs/REVIEW_SETUP.md. "
                         "Set SPACEEYE_DATA_ROOT to relocate data; no particular drive is required.")


CFG = load_cfg()
_PATHS = data_paths(CFG)
SRC, APP, PRIVATE = (_PATHS[key] for key in ("real_data", "app_data", "private"))
RAW, REAL, MODEL = APP / "raw", APP / "real", APP / "model"


def artifact_path(path: Path) -> str:
    """Stable provenance labels even when the checkout and data use different roots."""
    for root, label in ((APP, "app_data"), (PRIVATE, "private"), (SRC, "real_data"), (BASE_DIR, "")):
        if path.is_relative_to(root):
            return "/".join(filter(None, (label, path.relative_to(root).as_posix())))
    raise ValueError(f"Artifact is outside configured data and repository roots: {path}")


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
