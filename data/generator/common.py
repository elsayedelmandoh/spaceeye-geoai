"""Shared machinery: config, seeded RNG streams, time grids, defect tagging, writing."""
from __future__ import annotations

import json
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Africa/Cairo")
TS_FMT = "%Y-%m-%d %H:%M"


def load_config(path: Path | None = None) -> dict:
    with open(path or ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class Ctx:
    cfg: dict
    edition: str
    root: Path = ROOT
    log: list = field(default_factory=list)          # defect / story log entries
    rowlog: list = field(default_factory=list)       # (dataset, row_index, tag) frames
    ref: dict = field(default_factory=dict)          # reference tables
    cal: pd.DataFrame | None = None
    files: dict = field(default_factory=dict)

    @property
    def seed(self) -> int:
        return int(self.cfg["seed"])

    @property
    def ed(self) -> dict:
        return self.cfg["editions"][self.edition]

    @property
    def start(self) -> pd.Timestamp:
        return pd.Timestamp(str(self.ed["start"]))

    @property
    def end(self) -> pd.Timestamp:
        return pd.Timestamp(str(self.ed["end"]))

    @property
    def data_dir(self) -> Path:
        return self.root / "data" / self.edition

    @property
    def ref_dir(self) -> Path:
        return self.root / "reference"

    def rng(self, name: str) -> np.random.Generator:
        """Independent, stable random stream per name: order of generation never changes results."""
        return np.random.default_rng([self.seed, zlib.crc32(name.encode())])

    def note(self, **entry):
        self.log.append(entry)


# ---------------------------------------------------------------- time
def time_grid(start: pd.Timestamp, end: pd.Timestamp, freq: str, dst: str = "aware") -> pd.DataFrame:
    """Local wall-clock grid for Africa/Cairo.

    dst="aware":   the non-existent spring-forward hour is skipped (a 23-hour day) and the
                   repeated fall-back hour appears twice (a 25-hour day).
    dst="phantom": the gateway does not know about DST; it writes rows for the non-existent
                   hour and only one row for the repeated hour.  (DQ4)
    """
    idx = pd.date_range(start, end + pd.Timedelta(days=1), freq=freq, inclusive="left")
    nonexist = idx.tz_localize(TZ, nonexistent="NaT", ambiguous=False).isna()
    a1 = idx.tz_localize(TZ, nonexistent="shift_forward", ambiguous=True)
    a2 = idx.tz_localize(TZ, nonexistent="shift_forward", ambiguous=False)
    ambiguous = np.asarray(a1 != a2)
    g = pd.DataFrame({"timestamp": idx, "dst_phantom": nonexist, "dst_repeat": False})
    if dst == "aware":
        g = g[~g.dst_phantom]
        rep = g[ambiguous[~nonexist]].copy()
        rep["dst_repeat"] = True
        g = pd.concat([g, rep]).sort_values(["timestamp", "dst_repeat"], kind="stable")
    return g.reset_index(drop=True)


def interp_profile(profile, hours_frac: np.ndarray) -> np.ndarray:
    """Linear interpolation of a 24-value hourly profile at fractional hours (cyclic).
    profile[h] is the mean level of the hour h:00–h:59, i.e. it sits at h + 0.5.
    Callers pass the centre of their interval (h + 0.5 for hourly data)."""
    p = np.asarray(profile, dtype=float)
    hours_frac = np.asarray(hours_frac, dtype=float) - 0.5
    h0 = np.floor(hours_frac).astype(int) % 24
    h1 = (h0 + 1) % 24
    w = hours_frac - np.floor(hours_frac)
    return p[h0] * (1 - w) + p[h1] * w


def fmt_ts(s: pd.Series) -> pd.Series:
    return s.dt.strftime(TS_FMT)


# ---------------------------------------------------------------- tagging
def tag(df: pd.DataFrame, mask, label: str, col: str = "_dq") -> None:
    if col not in df:
        df[col] = ""
    m = np.asarray(mask, dtype=bool)
    cur = df.loc[m, col]
    df.loc[m, col] = np.where(cur == "", label, cur + "|" + label)


def protect_mask(df: pd.DataFrame) -> np.ndarray:
    """Rows that belong to a hidden story stay free of random defects."""
    if "_story" not in df:
        return np.zeros(len(df), dtype=bool)
    return (df["_story"] != "").to_numpy()


def write_dataset(ctx: Ctx, name: str, df: pd.DataFrame, subdir: str | None = None) -> Path:
    """Strip hidden tag columns, record tagged rows in the instructor row log, write CSV."""
    df = df.reset_index(drop=True)
    for col, kind in (("_dq", "defect"), ("_story", "story")):
        if col in df:
            s = df[col]
            hit = s[s != ""]
            if len(hit):
                ex = hit.str.split("|").explode()
                ctx.rowlog.append(pd.DataFrame({"dataset": name, "row_index": ex.index, "kind": kind, "tag": ex.values}))
    out = df.drop(columns=[c for c in df.columns if c.startswith("_")])
    folder = ctx.data_dir if subdir is None else ctx.root / subdir
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.csv"
    out.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
    ctx.files[name] = path
    return path


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def real_local(ts: pd.Series) -> pd.Series:
    """Event tables come from DST-aware systems: move any time that falls in the non-existent
    spring-forward hour to the first real minute after it."""
    return ts.dt.tz_localize(TZ, nonexistent="shift_forward", ambiguous=True).dt.tz_localize(None)
