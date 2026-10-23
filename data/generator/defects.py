"""Generic defect injectors. Each one tags the rows it touches (hidden `_dq` column) and logs a summary."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import Ctx, protect_mask, tag


def dq1_missing(ctx: Ctx, name: str, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rng = ctx.rng(f"DQ1.{name}")
    lo, hi = ctx.cfg["defects"]["DQ1_missing_rate"]
    rate = float(rng.uniform(lo, hi))
    ok = ~protect_mask(df)
    if "_dq" in df:
        ok &= (df["_dq"] == "").to_numpy()
    cand = np.flatnonzero(ok)
    n = int(round(rate * len(df)))
    pick = rng.choice(cand, size=n, replace=False)
    which = rng.integers(0, len(cols), size=n)
    for j, c in enumerate(cols):
        rows = pick[which == j]
        df.loc[df.index[rows], c] = np.nan
    m = np.zeros(len(df), bool); m[pick] = True
    tag(df, m, "DQ1")
    ctx.note(id="DQ1", dataset=name, rows=n, rate=n / len(df), detail=f"one of {cols} set to empty in {n:,} random rows")
    return df


def dq2_outage(ctx: Ctx, name: str, df: pd.DataFrame, key: str, sensors: list[str], tcol: str = "timestamp") -> pd.DataFrame:
    """Remove contiguous blocks (3–48 h) of rows for the listed sensors: the device was offline."""
    rng = ctx.rng(f"DQ2.{name}")
    drop = np.zeros(len(df), bool)
    prot = protect_mask(df)
    blocks = []
    t = df[tcol]
    for s in sensors:
        for _ in range(int(rng.integers(2, 4))):         # 2–3 blocks per sensor
            for _try in range(50):
                hours = int(rng.choice([3, 5, 8, 12, 20, 30, 48]))
                start = ctx.start + pd.Timedelta(days=int(rng.integers(2, (ctx.end - ctx.start).days - 2)), hours=int(rng.integers(0, 24)))
                end = start + pd.Timedelta(hours=hours)
                m = (df[key] == s).to_numpy() & (t >= start).to_numpy() & (t < end).to_numpy()
                if not (m & prot).any() and not (m & drop).any():
                    break
            drop |= m
            blocks.append({"sensor": s, "start": start.strftime("%Y-%m-%d %H:%M"), "end": end.strftime("%Y-%m-%d %H:%M"), "hours": hours, "rows_removed": int(m.sum())})
    ctx.note(id="DQ2", dataset=name, rows=int(drop.sum()), rate=drop.mean(), detail=f"{len(blocks)} offline blocks (rows absent)", blocks=blocks)
    return df.loc[~drop].reset_index(drop=True)


def dq3_duplicates(ctx: Ctx, name: str, df: pd.DataFrame, sort_cols: list[str]) -> pd.DataFrame:
    rng = ctx.rng(f"DQ3.{name}")
    rate = ctx.cfg["defects"]["DQ3_duplicate_rate"]
    ok = np.flatnonzero(~protect_mask(df) & (df["_dq"] == "").to_numpy())
    n = int(round(rate * len(df)))
    pick = np.sort(rng.choice(ok, size=n, replace=False))
    dup = df.iloc[pick].copy()
    dup["_dq"] = np.where(dup["_dq"] == "", "DQ3", dup["_dq"] + "|DQ3")
    dup["_order"] = 1
    df = df.copy(); df["_order"] = 0
    out = pd.concat([df, dup]).sort_values(sort_cols + ["_order"], kind="stable").drop(columns="_order").reset_index(drop=True)
    ctx.note(id="DQ3", dataset=name, rows=n, rate=n / len(df), detail=f"{n:,} retransmitted rows inserted right after their original (exact copies)")
    return out


def dq5_spikes(ctx: Ctx, name: str, df: pd.DataFrame, fn) -> pd.DataFrame:
    """fn(df, idx, rng) mutates the chosen rows to impossible values and returns a description."""
    rng = ctx.rng(f"DQ5.{name}")
    rate = ctx.cfg["defects"]["DQ5_spike_rate"]
    ok = ~protect_mask(df) & (df["_dq"] == "").to_numpy()
    cand = np.flatnonzero(ok)
    n = int(round(rate * len(df)))
    pick = np.sort(rng.choice(cand, size=n, replace=False))
    desc = fn(df, df.index[pick], rng)
    m = np.zeros(len(df), bool); m[pick] = True
    tag(df, m, "DQ5")
    ctx.note(id="DQ5", dataset=name, rows=n, rate=n / len(df), detail=desc)
    return df


def dq4_dst(ctx: Ctx, name: str, df: pd.DataFrame, grid_mode: str, per_step: int) -> pd.DataFrame:
    if grid_mode == "phantom":
        m = df["_phantom"].to_numpy()
        tag(df, m, "DQ4")
        ctx.note(id="DQ4", dataset=name, rows=int(m.sum()), rate=m.mean(),
                 detail="rows stamped in the non-existent local hour 2025-04-25 00:00–00:59 (Cairo clocks jumped 00:00→01:00); gateway is not DST-aware")
    else:
        ctx.note(id="DQ4", dataset=name, rows=0, rate=0.0,
                 detail=f"gap: 2025-04-25 has no 00:00–00:59 rows (23-hour day, {per_step} fewer rows per device); correct local behaviour that breaks naive hourly resampling")
    return df.drop(columns=[c for c in ["_phantom", "_repeat"] if c in df])
