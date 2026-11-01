"""SpaceEye R7 Observatory - Streamlit dashboard (T-NA-01: skeleton + track switch).

Run with:  streamlit run app.py
"""

from __future__ import annotations

import html
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import altair as alt  # ships with Streamlit
import pandas as pd
import streamlit as st

from src.dashboard import front
from src.dashboard.ops_visits import render_ops_visits_form  # T-NA-04
from src.pipeline.common import APP as PIPELINE_APP_DATA

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

REPO_DIR = Path(__file__).resolve().parent
# Same folder that setup_review installs into (configs/data.yaml or SPACEEYE_DATA_ROOT);
# SPACEEYE_APP_DATA still overrides it.
APP_DATA = Path(os.environ.get("SPACEEYE_APP_DATA") or PIPELINE_APP_DATA)
# The unpacked v7 release sits next to app_data (setup_review): what-if, backtest, model outputs.
READY_DATA = APP_DATA.parent / "ready-data"

BANNER_TEXT = "Synthetic - for training only"

ORIGIN_DERIVED = "🔵"    # derived from real data
ORIGIN_GENERATED = "🟠"  # generated (stand-in for ACUD data)

# Folders under app_data/ whose content is generated (separation rule).
GENERATED_PREFIXES = ("sim/", "ml/", "scenarios/")

# Columns that could carry names: dropped before anything is rendered.
FORBIDDEN_COLUMNS = {
    "name", "compound_name", "developer_name", "developer", "project_name",
    "name_ar", "name_en",
}
CODE_COLUMNS = {"code", "compound_code", "compound", "developer_code"}
CODE_PATTERN = re.compile(r"^[CD]\d{2,3}$")


@dataclass(frozen=True)
class Track:
    key: str
    label: str
    generated: bool


TRACK_A = Track("A", "Track A: images", generated=False)
TRACK_B = Track("B", "Track B: images + numbers (generated)", generated=True)
TRACKS = {t.label: t for t in (TRACK_A, TRACK_B)}  # Track A first = default

SCREENS = [
    "1 · Priority map",
    "2 · Compound file",
    "3 · What it gives",
    "4 · Fewer or more visits",
]

# --------------------------------------------------------------------------- #
# Design tokens (UI only)
# --------------------------------------------------------------------------- #

PALETTE = {
    "bg": "#F1F2EE",          # light table: cool diffuser grey
    "bg_alt": "#E2E8E5",      # sidebar rail, tinted toward the boundary cyan
    "surface": "#FFFFFF",     # print mat
    "surface_hi": "#E6E9E3",  # hover
    "border": "#D3D7D0",      # hairline rules
    "text": "#1A1D1B",        # graphite ink
    "muted": "#4F5652",
    "accent": "#007C89",      # the cyan of the reviewed boundary: selection and actions
    "accent_b": "#B54708",    # generated data: Track B
}


# --------------------------------------------------------------------------- #
# Stored-file access (no live computation) + no-names gate
# --------------------------------------------------------------------------- #

# Generated parts of the v7 release: what-if results, current model outputs (tables/current),
# the training export and the model metrics. Track A must refuse them too.
GENERATED_PATH_RE = re.compile(r"(^|/)(what_if/|training/|(tables|csv)/current/|docs/CURRENT_MODEL_)")


def is_generated_path(rel_path: str) -> bool:
    path = rel_path.replace("\\", "/")
    return path.startswith(GENERATED_PREFIXES) or bool(GENERATED_PATH_RE.search(path))


def enforce_no_names(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Drop name-like columns and stop the app if a code column holds a non-code."""
    drop = [c for c in df.columns if c.lower() in FORBIDDEN_COLUMNS]
    if drop:
        df = df.drop(columns=drop)
    for col in df.columns:
        if col.lower() in CODE_COLUMNS:
            bad = df[col].dropna().astype(str)
            bad = bad[~bad.str.match(CODE_PATTERN)]
            if not bad.empty:
                st.error(
                    f"no_names gate: '{source}' has {len(bad)} value(s) in "
                    f"'{col}' that are not codes. Display stopped."
                )
                st.stop()
    return df


@st.cache_data(show_spinner=False)
def _read_file_cached(path_str: str, mtime_ns: int) -> pd.DataFrame:
    path = Path(path_str)
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".json":
        return pd.read_json(path)
    raise ValueError(f"Unsupported file type: {suffix}")


def _read_file(path_str: str) -> pd.DataFrame:
    """Cached read. The file's modification time is part of the cache key, so a new
    hand-off (e.g. a fresh kpi_values.parquet) is picked up without restarting the app."""
    return _read_file_cached(path_str, Path(path_str).stat().st_mtime_ns)


def load_table(rel_path: str, track: Track, root: Path = APP_DATA) -> pd.DataFrame | None:
    """Load a stored table. Returns None if the file does not exist yet."""
    if is_generated_path(rel_path) and not track.generated:
        raise PermissionError(
            f"Generated table '{rel_path}' must not be loaded in Track A."
        )
    path = root / rel_path
    if not path.exists():
        return None
    return enforce_no_names(_read_file(str(path)), rel_path)


# --------------------------------------------------------------------------- #
# Presentation helpers (origin tags, banner, tiles)
# --------------------------------------------------------------------------- #

def tag_generated(value: object) -> str:
    """Every generated number carries the orange tag."""
    return f"{value} {ORIGIN_GENERATED}"


def tag_generated_columns(df: pd.DataFrame, skip: tuple[str, ...] = ("code", "quarter")) -> pd.DataFrame:
    """Append the orange tag to the headers of a generated table."""
    return df.rename(
        columns={c: f"{c} {ORIGIN_GENERATED}" for c in df.columns if c not in skip}
    )


def metric_tile(label: str, value: object, unit: str, denominator: str,
                as_of: str, origin: str) -> None:
    """One KPI tile = value + unit + denominator + 'as of' + origin (section 9)."""
    shown = tag_generated(value) if origin == ORIGIN_GENERATED else f"{value}"
    with st.container(border=True):
        st.metric(label=f"{origin} {label}", value=f"{shown} {unit}".strip())
        st.caption(f"{denominator} · as of {as_of}")


def page_header(icon: str, title: str, subtitle: str = "") -> None:
    """Screen title + the question the screen answers. Text only: emoji icons are not shown."""
    sub = f'<div class="se-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="se-header"><div><div class="se-title">{title}</div>{sub}</div></div>',
                unsafe_allow_html=True)


def section_title(icon: str, text: str) -> None:
    """Section label above cards (the emoji argument is kept for call sites but not shown)."""
    st.markdown(f'<div class="se-section">{text}</div>', unsafe_allow_html=True)


def how_to_read(points: list[str]) -> None:
    """Short reading guide, folded so it does not compete with the data."""
    with st.expander("How to read this screen"):
        st.markdown("\n".join(f"- {point}" for point in points))


def inject_css() -> None:
    """Light-table theme for the Streamlit parts (screens 3-5 and the lower half of 1-2). The font,
    Readex Pro for Arabic and Latin, is served from static/fonts through .streamlit/config.toml."""
    p = PALETTE
    st.markdown(
        f"""
        <style>
        .block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1320px; }}
        header[data-testid="stHeader"] {{ background: transparent; }}
        #MainMenu, footer {{ visibility: hidden; }}
        p, li {{ line-height: 1.6; }}
        ::selection {{ background: {p['accent']}; color: #fff; }}
        :focus-visible {{ outline: 2px solid {p['accent']} !important; outline-offset: 2px; }}
        [data-testid="stCaptionContainer"], .stCaption {{ color: {p['muted']} !important; }}

        .se-header {{ margin: 0 0 1.1rem 0; }}
        .se-title {{ font-size: 1.85rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1.15; }}
        .se-sub {{ color: {p['muted']}; font-size: 1rem; margin-top: 0.3rem; }}
        .se-section {{ font-size: 1rem; font-weight: 600; margin: 1.6rem 0 0.5rem 0; }}

        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: {p['surface']}; border: 1px solid {p['border']} !important; border-radius: 3px;
        }}
        [data-testid="stMetricLabel"] p {{
            color: {p['muted']} !important; font-size: 0.86rem !important; white-space: normal !important;
        }}
        [data-testid="stMetricValue"] div {{
            font-weight: 600; font-size: clamp(1.15rem, 1.6vw, 1.6rem) !important;
            white-space: normal !important; line-height: 1.25 !important;
        }}
        [data-testid="stDataFrame"] {{ border: 1px solid {p['border']}; border-radius: 3px; }}
        [dir="auto"], .se-rtl {{ unicode-bidi: plaintext; }}
        .se-rtl {{ direction: rtl; text-align: right; font-size: 1.05rem; }}

        [data-testid="stSidebar"] {{ border-right: 1px solid {p['border']}; }}
        .se-brand-name {{ font-weight: 600; font-size: 1.2rem; letter-spacing: -0.01em; }}
        .se-brand-sub {{ color: {p['muted']}; font-size: 0.85rem; }}
        .se-side-label {{ color: {p['muted']}; font-size: 0.85rem; margin: 0.2rem 0 0.1rem 0; }}
        [data-testid="stSidebar"] [role="radiogroup"] label {{ padding: 0.35rem 0.6rem; width: 100%; border-radius: 3px; }}
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{ background: {p['surface']}; font-weight: 600; }}
        .se-pill {{
            display: inline-block; padding: 0.1rem 0.6rem; border-radius: 999px;
            font-size: 0.85rem; font-weight: 500; border: 1px solid {p['border']}; background: {p['surface']};
        }}
        .se-pill-a {{ color: {p['accent']}; border-color: {p['accent']}; }}
        .se-pill-b {{ color: {p['accent_b']}; border-color: {p['accent_b']}; }}
        .se-move {{ padding: 0.6rem 0; border-bottom: 1px solid {p['border']}; }}
        .se-move-why {{ color: {p['muted']}; margin-top: 0.25rem; }}
        .synthetic-banner {{
            position: sticky; top: 0.5rem; z-index: 1000;
            display: flex; align-items: center; justify-content: center; gap: 0.6rem;
            margin: 0 0 1.2rem 0; padding: 0.55rem 1rem;
            background: {p['accent_b']}; color: #fff; font-weight: 600; border-radius: 3px;
        }}
        .synthetic-banner .dot {{ width: 7px; height: 7px; border-radius: 50%; background: #fff; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_banner(track: Track) -> None:
    if track.generated:
        st.markdown(
            f'<div class="synthetic-banner"><span class="dot"></span>'
            f'<span>{BANNER_TEXT}</span><span class="dot"></span></div>',
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------- #
# Screen 1 data
# --------------------------------------------------------------------------- #

# Print tones for a light ground, checked with the dataviz palette validator (CVD and contrast).
LEVELS: dict[int, tuple[str, str]] = {
    1: ("Inspect now", "#A8102C"),
    2: ("Inspect this cycle", "#E35D17"),
    3: ("Document review", "#D1A80C"),
    4: ("Routine", "#2E7D4F"),
}
NOT_ASSESSABLE: tuple[str, str] = ("Not assessable", "#8A8F8B")  # grey

REQUIRED_KPI_COLUMNS = {"code", "quarter", "level"}


def _level_style(level: object) -> tuple[str, str]:
    try:
        return LEVELS[int(level)]
    except (TypeError, ValueError, KeyError):
        return NOT_ASSESSABLE


def level_word(level: object) -> str:
    return _level_style(level)[0]


@st.cache_data(show_spinner=False)
def _read_boundaries(path_str: str, mtime_ns: int = 0) -> tuple[dict, list[str]]:
    data = json.loads(Path(path_str).read_text(encoding="utf-8"))
    features, bad_codes = [], []
    for feat in data.get("features", []):
        props = feat.get("properties") or {}
        code = next((str(v) for k, v in props.items() if k.lower() in CODE_COLUMNS), None)
        if code is None or not CODE_PATTERN.match(code):
            bad_codes.append(str(code))
            continue
        features.append({
            "type": "Feature",
            "geometry": feat.get("geometry"),
            "properties": {"code": code},
        })
    return {"type": "FeatureCollection", "features": features}, bad_codes


def load_boundaries() -> dict | None:
    path = APP_DATA / "real" / "compound_boundaries.geojson"
    if not path.exists():
        return None
    geojson, bad_codes = _read_boundaries(str(path), path.stat().st_mtime_ns)
    if bad_codes:
        st.error(
            f"no_names gate: compound_boundaries.geojson has {len(bad_codes)} "
            "feature(s) without a valid code. Display stopped."
        )
        st.stop()
    return geojson


def load_latest_kpis() -> tuple[pd.DataFrame, str] | None:
    kpis = load_table("real/kpi_values.parquet", TRACK_A)
    if kpis is None or kpis.empty:
        return None
    missing = REQUIRED_KPI_COLUMNS - set(kpis.columns)
    if missing:
        st.error(f"kpi_values.parquet is missing column(s): {', '.join(sorted(missing))}.")
        return None
    asof = kpis["quarter"].max()
    return kpis[kpis["quarter"] == asof].copy(), str(asof)


def build_cycle_list(latest_df: pd.DataFrame) -> pd.DataFrame:
    df = latest_df.copy()
    df["level_word"] = df["level"].map(level_word)
    if "cycle_rank" in df.columns:
        df = df[df["cycle_rank"].notna()].sort_values("cycle_rank")
    else:
        df = df[df["level"].isin([1, 2, 3])].sort_values(["level", "code"])
    if "K6_status" in df.columns:  # an empty K6 has a stated reason; show it instead of a blank
        df["K6"] = [("does not apply" if status == "not_applicable_started" else "unknown") if _missing(k6)
                    else str(int(k6)) for k6, status in zip(df["K6"], df["K6_status"])]
    wanted =("cycle_rank", "code", "level_word", "reason_ar", "K2", "K3", "K6")
    return df[[c for c in wanted if c in df.columns]].reset_index(drop=True)


def _geo_points(geometry: dict | None) -> list[list[float]]:
    points: list[list[float]] = []

    def walk(node: object) -> None:
        if isinstance(node, (list, tuple)) and node:
            if isinstance(node[0], (int, float)):
                points.append([float(node[0]), float(node[1])])
            else:
                for child in node:
                    walk(child)

    if geometry:
        walk(geometry.get("coordinates"))
    return points


MAP_HEIGHT_EXAGGERATION = 10  # 20-30 m buildings on 0.5-1 km plots would look flat at true scale


def latest_heights() -> dict[str, tuple[float, int]]:
    """{code: (mean building height in m, year)}: the latest approved year (to 2024) with a value."""
    yearly = load_table("real/sat_yearly.parquet", TRACK_A)
    if yearly is None or not {"code", COL_YEAR, COL_HEIGHT} <= set(yearly.columns):
        return {}
    known = yearly[(yearly[COL_YEAR] <= MAX_HEIGHT_YEAR) & yearly[COL_HEIGHT].notna()]
    last = known.sort_values(COL_YEAR).groupby("code").tail(1)
    return {r["code"]: (float(r[COL_HEIGHT]), int(r[COL_YEAR])) for _, r in last.iterrows()}


WAYBACK_CREDIT = "Imagery: Esri World Imagery Wayback, credits printed under each picture."


def level_number(level: object) -> int | None:
    try:
        return int(level) if int(level) in LEVELS else None
    except (TypeError, ValueError):
        return None


def short_reason(row: pd.Series) -> str:
    return str(row.get("reason", "")).split(": ", 1)[-1].split("; observation")[0]


def frames_payload(code: str) -> list[dict]:
    stages = stage_of_year(code)
    return [{"date": date, "stage": stages.get(int(date[:4]), ""), "src": front.frame_uri(path),
             "foot": front.frame_uri(path, "foot")} for date, path in space_frames(code)]


def map_payload(latest_df: pd.DataFrame, cycle: pd.DataFrame) -> dict | None:
    geojson = load_boundaries()
    if geojson is None:
        return None
    levels = dict(zip(latest_df["code"], latest_df["level"]))
    ranks = dict(zip(cycle["code"], cycle.index + 1))
    heights = latest_heights()
    compounds = []
    for feat in geojson["features"]:
        code = feat["properties"]["code"]
        outline = _geo_points(feat["geometry"])
        if not outline:
            continue
        height = heights.get(code)
        compounds.append({
            "code": code, "level": level_number(levels.get(code)), "level_word": level_word(levels.get(code)),
            "rank": ranks.get(code), "geometry": feat["geometry"],
            "center": [sum(x for x, _ in outline) / len(outline), sum(y for _, y in outline) / len(outline)],
            "height": height[0] if height else 0,
            "height_text": f"mean height {height[0]:.0f} m ({height[1]})" if height else "no height on file",
        })
    shown = [c["level"] for c in compounds]
    legend = [{"level": n, "word": word, "count": shown.count(n)} for n, (word, _) in LEVELS.items()]
    legend.append({"level": None, "word": NOT_ASSESSABLE[0], "count": shown.count(None)})
    return {"compounds": compounds, "legend": legend}


def priority_payload(track: Track, latest: tuple[pd.DataFrame, str]) -> dict:
    """Screen 1 for the front end: the cycle list with its frames and, on Track A, the map."""
    latest_df, asof = latest
    cycle = build_cycle_list(latest_df)
    items = []
    for _, item in cycle.iterrows():
        row = latest_df[latest_df["code"] == item["code"]].iloc[0]
        items.append({"rank": len(items) + 1, "code": item["code"], "level": level_number(row["level"]),
                      "level_word": level_word(row["level"]), "why": short_reason(row),
                      "frames": frames_payload(item["code"])})
    eligible = int(latest_df["level"].isin([1, 2, 3]).sum())
    payload = {"screen": "priority", "asof": asof, "total": len(latest_df), "cycle": items,
               "waiting": max(eligible - len(items), 0), "credit": WAYBACK_CREDIT, "map": False}
    # Track B keeps the map off: its tables start in a different quarter.
    mapped = None if track.generated else map_payload(latest_df, cycle)
    if mapped:
        payload.update(mapped, map=True, map_note=(
            "Tilt 3D raises each compound by its mean building "
            f"height (Google Open Buildings, latest year to {MAX_HEIGHT_YEAR}), drawn "
            f"{MAP_HEIGHT_EXAGGERATION}× taller"))
    return payload


def open_compound_file_from(key: str):
    """A front-end screen asked for a compound file: switch screens before the sidebar is drawn again."""
    def callback() -> None:
        code = (st.session_state.get(key) or {}).get("open")
        if code:
            st.session_state["compound_code"] = code
            st.session_state["screen"] = SCREENS[1]
    return callback


def render_cycle_list(latest: tuple[pd.DataFrame, str] | None) -> None:
    section_title("📋", "Cycle list")
    if latest is None:
        st.info("Waiting for real/kpi_values.parquet.")
        return

    latest_df, asof = latest
    cycle = build_cycle_list(latest_df)
    if cycle.empty:
        st.info(f"No compounds in the cycle list for {asof}.")
        return

    export = cycle.rename(columns={"level_word": "level"})
    with st.container(border=True):
        st.dataframe(
            export,
            use_container_width=True,
            hide_index=True,
            column_config={
                "cycle_rank": st.column_config.NumberColumn("Rank", width="small"),
                "code": st.column_config.TextColumn("Code", width="small"),
                "level": st.column_config.TextColumn("Priority level", width="medium"),
                "reason_ar": st.column_config.TextColumn("السبب (Arabic reason)", width="large"),
            },
        )
        left, right = st.columns([3, 1])
        left.caption(f"{ORIGIN_DERIVED} derived · {len(export)} compound(s) · as of {asof}")
        right.download_button(
            "⬇️ Download CSV",
            data=export.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"cycle_list_{asof}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# --------------------------------------------------------------------------- #
# Screen 2 data
# --------------------------------------------------------------------------- #

KPI_FILE = "real/kpi_values.parquet"
CONTEXT_FILES = ("real/sat_yearly.parquet", "real/sat_quarterly.parquet")
ANNOUNCE_FILES = ("real/statements.parquet",)
# Inspection files: written by the pipeline into app_data, or the stored set committed in the repo.
FILES_DIRS = (APP_DATA / "files", REPO_DIR / "app_data" / "files")
IMAGERY_DIR = REPO_DIR / "data" / "imagery"
# Current model outputs and the training export of the v7 release (under READY_DATA).
PREDICTIONS_FILE = "tables/current/ml_current.parquet"
K5_EGP_FILE, K5_EGP_COL = "training/ml_dataset_extended.parquet", "K5_egp"

COL_A, COL_DW = "activity_prob", "built_prob_mean"
COL_HEIGHT, COL_VEG, COL_YEAR = "height_mean_m", "veg_share", "year"
MAX_HEIGHT_YEAR = 2024
VEG_COMPLETE_THRESHOLD = 0.10


def _missing(value: object) -> bool:
    return value is None or bool(pd.isna(value))


def _fmt(value: object, digits: int = 0) -> str:
    return "unknown" if _missing(value) else f"{float(value):,.{digits}f}"


def _load_first(rel_paths: tuple[str, ...]) -> pd.DataFrame | None:
    for rel in rel_paths:
        df = load_table(rel, TRACK_A)
        if df is not None:
            return df
    return None


def _kpi_tile(label: str, value: object, unit: str, denominator: str,
              as_of: str, origin: str, digits: int = 0) -> None:
    shown = _fmt(value, digits)
    metric_tile(label, shown, "" if shown == "unknown" else unit, denominator, as_of, origin)


def load_kpi_history(code: str) -> pd.DataFrame | None:
    kpis = load_table(KPI_FILE, TRACK_A)
    if kpis is None or not {"code", "quarter"} <= set(kpis.columns):
        return None
    history = kpis[kpis["code"] == code]
    # The Dynamic World series lives in sat_quarterly, not in kpi_values.
    sat = load_table("real/sat_quarterly.parquet", TRACK_A)
    if sat is not None and COL_DW not in history.columns and {"code", "quarter", COL_DW} <= set(sat.columns):
        history = history.merge(sat.loc[sat["code"] == code, ["quarter", COL_DW]], on="quarter", how="left")
    return history.sort_values("quarter").reset_index(drop=True)


def load_announcements(code: str, asof: str) -> pd.DataFrame | None:
    df = _load_first(ANNOUNCE_FILES)
    if df is None or not {"code", "published_date"} <= set(df.columns):
        return None
    df = df[df["code"] == code].copy()
    df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")
    try:
        cutoff = pd.Period(asof, "Q").end_time
    except Exception:
        return None
    df = df[df["published_date"] <= cutoff]
    return df.sort_values("published_date").reset_index(drop=True)


def find_inspection_file(code: str, asof: str) -> Path | None:
    for files_dir in FILES_DIRS:
        for pattern in (f"{code}_{asof}.html", f"{code}_{asof}_*.html", f"{code}_*.html"):
            matches = sorted(files_dir.glob(pattern))
            if matches:
                return matches[-1]
    return None


# ---- screen 2 renderers ----------------------------------------------------- #

STAGE_TABLE = REPO_DIR / "data" / "experiments" / "42_r7_stage_table" / "r7_stage_table.csv"
STAGE_WORDS = {"S0": "land or ground works", "S1": "under construction", "S2": "complete"}


def render_context_charts(code: str) -> None:
    section_title("🏗️", "Height and vegetation")
    ctx = _load_first(CONTEXT_FILES)
    left, right = st.columns(2)

    with left, st.container(border=True):
        st.markdown("**Mean building height (m)**")
        if ctx is None or not {"code"} <= set(ctx.columns):
            st.info("Waiting for annual context (height).")
        else:
            has_year = COL_YEAR in ctx.columns
            has_height = COL_HEIGHT in ctx.columns
            if not (has_year and has_height):
                st.info("Height columns not found in context data.")
            else:
                h = ctx[(ctx["code"] == code) & (ctx[COL_YEAR] <= MAX_HEIGHT_YEAR)]
                h = h[[COL_YEAR, COL_HEIGHT]].copy()
                h["kind"] = h[COL_YEAR].map(lambda y: "estimate (v4)" if y == MAX_HEIGHT_YEAR else "observed")
                if h[COL_HEIGHT].notna().sum() == 0:
                    st.info("No height value for this compound.")
                else:
                    st.altair_chart(
                        alt.Chart(h).mark_bar().encode(
                            x=alt.X(f"{COL_YEAR}:O", title=None),
                            y=alt.Y(f"{COL_HEIGHT}:Q", title="m"),
                            opacity=alt.Opacity("kind:N", legend=alt.Legend(orient="bottom", title=None),
                                                scale=alt.Scale(domain=["observed", "estimate (v4)"],
                                                                range=[1.0, 0.5])),
                            color=alt.value("#2B59C3"),
                            tooltip=[COL_YEAR, alt.Tooltip(COL_HEIGHT, format=".1f"), "kind"],
                        ).properties(height=240),
                        use_container_width=True)
                st.caption(f"Latest year shown: {MAX_HEIGHT_YEAR}")

    with right, st.container(border=True):
        st.markdown("**Vegetation share (Sentinel-2)**")
        if ctx is None or not {"code"} <= set(ctx.columns):
            st.info("Waiting for annual context (vegetation).")
        else:
            has_year = COL_YEAR in ctx.columns
            has_veg = COL_VEG in ctx.columns
            if not (has_year and has_veg):
                st.info("Vegetation columns not found in context data.")
            else:
                v = ctx[ctx["code"] == code][[COL_YEAR, COL_VEG]]
                if v[COL_VEG].notna().sum() == 0:
                    st.info("No vegetation value for this compound.")
                else:
                    line = alt.Chart(v).mark_line(point=True, color="#2E7D4F").encode(
                        x=alt.X(f"{COL_YEAR}:O", title=None),
                        y=alt.Y(f"{COL_VEG}:Q", title="share 0-1", scale=alt.Scale(domain=[0, 1])),
                        tooltip=[COL_YEAR, alt.Tooltip(COL_VEG, format=".2f")])
                    rule = alt.Chart(pd.DataFrame({"y": [VEG_COMPLETE_THRESHOLD]})).mark_rule(
                        color=PALETTE["muted"], strokeDash=[4, 4]).encode(y="y:Q")
                    st.altair_chart((line + rule).properties(height=240), use_container_width=True)
                st.caption(f"Dashed line = {VEG_COMPLETE_THRESHOLD:.2f}")


def space_frames(code: str) -> list[tuple[str, Path]]:
    """The curated single-capture Wayback frames of one compound, oldest first: same extent and zoom,
    chosen for the presentation (data/imagery/figures/compare/<code>/<code>_<n>_<date>.jpg)."""
    folder = IMAGERY_DIR / "figures" / "compare" / code
    frames = []
    for path in sorted(folder.glob(f"{code}_*_*.jpg")):
        date = path.stem.rsplit("_", 1)[-1]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            frames.append((date, path))
    return frames


def stage_of_year(code: str) -> dict[int, str]:
    if not STAGE_TABLE.exists():
        return {}
    table = _read_file(str(STAGE_TABLE))
    mine = table[table["code"] == code]
    return {int(y): STAGE_WORDS.get(stage, stage) for y, stage in zip(mine["year"], mine["stage"])}


def _clock(label: str, rule: str, value: object, unit: str, text: str | None = None) -> dict:
    if text is None and _missing(value):
        text = "unknown"
    return {"label": label, "rule": rule, "unit": unit,
            "value": None if text else int(value), "text": text}


def _share(value: object) -> float | None:
    return None if _missing(value) else round(float(value), 3)


def compound_payload(code: str, row: pd.Series | None, history: pd.DataFrame | None,
                     ann: pd.DataFrame | None, asof: str) -> dict:
    """Screen 2 for the front end: frames to compare, the three clocks, the quarterly series, stages."""
    get = (lambda c: None) if row is None else row.get
    deadline = get("k3_first_deadline")
    k6_text = "does not apply: construction start observed" if (
        _missing(get("K6")) and get("K6_status") == "not_applicable_started") else None
    clocks = [
        _clock("K2 no activity", "quarters in a row, counted after the start", get("K2"), "quarters"),
        _clock("K3 handover clock", "months since the first announced handover date", get("K3"), "months",
               None if not _missing(deadline) else "no announced handover date"),
        _clock("K6 never started", "months since launch or promise, no construction start", get("K6"), "months",
               k6_text),
    ]
    quarters = []
    if history is not None and not history.empty:
        for _, h in history.iterrows():
            quarters.append({"q": str(h["quarter"]), "a": _share(h.get(COL_A)), "dw": _share(h.get(COL_DW))})
    seen = {q["q"] for q in quarters}
    statements = []
    if ann is not None and not ann.empty:
        published = ann["published_date"].dropna().dt.to_period("Q").astype(str)
        statements = sorted(set(published) & seen)
    marker = None
    if not _missing(deadline):
        first = pd.Timestamp(deadline)
        marker = {"q": str(first.to_period("Q")), "label": f"{first:%b %Y}"}

    stages, stage_note = [], None
    if STAGE_TABLE.exists():
        table = enforce_no_names(_read_file(str(STAGE_TABLE)), "r7_stage_table.csv")
        mine = table.loc[table["code"] == code].sort_values("year")
        stages = [{"year": int(r["year"]), "stage": r["stage"], "word": STAGE_WORDS.get(r["stage"], r["stage"])}
                  for _, r in mine.iterrows()]
        start = mine.loc[mine["stage"] != "S0", "year"]
        stage_note = (f"Construction first seen in {int(start.min())}." if not start.empty
                      else "No construction seen yet.")
    reason = get("reason_ar")
    return {
        "screen": "compound", "code": code, "asof": asof,
        "level": level_number(get("level")), "level_word": level_word(get("level")),
        "reason_ar": None if _missing(reason) or not str(reason).strip() else str(reason),
        "frames": frames_payload(code), "credit": WAYBACK_CREDIT, "clocks": clocks,
        "quarters": quarters, "statements": statements, "deadline": marker,
        "chart_note": None,
        "stages": stages, "stage_words": [{"stage": k, "word": v} for k, v in STAGE_WORDS.items()],
        "stage_note": stage_note,
        "stage_missing": "The stage table (data/experiments/42_r7_stage_table) is not in this checkout.",
    }


def render_context_table(row: pd.Series | None) -> None:
    """Indicators shown for context: they never set the level."""
    get = (lambda c: None) if row is None else row.get
    k4 = get("K4")
    k5, k5_status = get("K5_months"), get("K5_status")
    k5_text = (_fmt(k5, 0) if not _missing(k5) else
               "no published deadline" if k5_status == "no_published_deadline" else "unknown")
    k4_text = "unknown" if _missing(k4) else ("Yes" if k4 in (True, 1, "True", "Yes") else
                                             "No" if k4 in (False, 0, "False", "No") else str(k4))
    context = pd.DataFrame({
        "Indicator": ["A activity score", "K4 assessable", "K5 fine-eligible months"],
        "Value": [_fmt(get(COL_A), 2), k4_text, k5_text],
        "Unit": ["probability 0-1", "yes/no (≥ 6 images)", "months (screening, not a fine)"],
    })
    section_title("", "Context: shown, but it does not set the level")
    st.dataframe(context, use_container_width=True, hide_index=True)


def render_inspection_button(code: str, asof: str) -> None:
    section_title("📄", "Inspection file")
    path = find_inspection_file(code, asof)
    if path is None:
        stored = sorted({p.name.split("_")[0] for d in FILES_DIRS for p in d.glob("C*_*.html")})
        st.button("📄 Inspection file (Arabic)", disabled=True, key=f"insp_{code}")
        st.caption(f"No inspection file stored for {code}. Stored files cover: "
                   f"{', '.join(stored) if stored else 'none'}.")
        return
    st.download_button("📄 Open inspection file (Arabic HTML)", data=path.read_bytes(),
                       file_name=path.name, mime="text/html", key=f"insp_{code}")
    st.caption("Drafted by AI from stored facts and reviewed before committee use.")


def latest_predictions(preds: pd.DataFrame | None) -> pd.DataFrame | None:
    """One row per compound and method for the latest quarter. The release stores four methods
    and approves none as primary, so all four are shown side by side, never one picked silently."""
    if preds is None or not {"code", "quarter", "method", "p_distressed"} <= set(preds.columns):
        return None
    latest = preds[preds["quarter"] == preds["quarter"].max()]
    return latest.pivot_table(index="code", columns="method", values="p_distressed").round(2)


def render_track_b_extras(code: str, track: Track) -> None:
    if not track.generated:
        return
    section_title("🧠", "Generated-data model (Track B)")

    preds = load_table(PREDICTIONS_FILE, track, READY_DATA)
    table = latest_predictions(preds)
    left, right = st.columns([2, 1])
    with left, st.container(border=True):
        st.markdown("**Probability of 'distressed' in the next 6 months, by method**")
        if table is None or code not in table.index:
            st.info(f"No stored prediction for {code} in {PREDICTIONS_FILE}.")
        else:
            row = table.loc[[code]].reset_index(drop=True)
            st.dataframe(tag_generated_columns(row), use_container_width=True, hide_index=True)
            st.caption(f"{ORIGIN_GENERATED} as of {preds['quarter'].max()} · four methods, none approved as primary · "
                       "the rule, not these probabilities, selects the cycle list")

    egp = load_table(K5_EGP_FILE, track, READY_DATA)
    with right:
        if egp is not None and {"code", "quarter", K5_EGP_COL} <= set(egp.columns):
            mine = egp[egp["code"] == code].sort_values("quarter")
            if not mine.empty:
                last = mine.iloc[-1]
                _kpi_tile("K5 illustrative exposure", last[K5_EGP_COL], "EGP",
                          "K5 months × assumed rate × assumed land value; not a fine",
                          str(last["quarter"]), ORIGIN_GENERATED)
        else:
            st.info(f"Waiting for {K5_EGP_FILE}.")
    st.caption(f"{ORIGIN_GENERATED} Generated for training.")


# --------------------------------------------------------------------------- #
# Screen 3 data: what the committee gains
# --------------------------------------------------------------------------- #

# Frozen-clock backtest of the v7 release (one row per public case, with its explanation).
BACKTEST_DIR = "current/backtest"


def _as_bool(value: object) -> bool | None:
    """True / False / None (unknown). Missing never becomes False."""
    if _missing(value):
        return None
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "warned"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    try:  # 1.0 / 0.0 (a flag column that also holds missing values becomes float)
        number = float(text)
    except ValueError:
        return None
    return True if number == 1 else (False if number == 0 else None)


OUTCOME_WORDS = {
    "partial_delivery_late_completion_postponed": "part of it was delivered late and completion was postponed",
    "postponed_twice_not_yet_delivered": "the handover was postponed twice and is not yet delivered",
    "delivered_late": "it was delivered late",
}


def _safe(label: str, fn, *args, default=None):
    """Run a loader; if a stored file is corrupt, say so and keep the screen alive.
    (st.stop() is not an Exception, so the no-names gate still stops the app.)"""
    try:
        return fn(*args)
    except Exception as exc:
        st.warning(f"{label}: could not be read ({type(exc).__name__}).")
        return default


def warning_example() -> dict | None:
    """The public late case the rule flagged earliest after construction started (frozen-clock backtest)."""
    path = READY_DATA / BACKTEST_DIR / "cases_explained.csv"
    if not path.exists():
        return None
    cases = enforce_no_names(_read_file(str(path)), "cases_explained.csv")
    hits = cases[cases["after_start"].map(_as_bool).fillna(False).astype(bool)]
    if hits.empty:
        return None
    case = hits.sort_values("after_start_months_before", ascending=False).iloc[0]
    code, alert = str(case["code"]), str(case["first_alert_quarter"])
    outcome, _, rest = str(case["what_happened"]).partition(";")
    reported = rest.split("outcome date", 1)[-1].split(";")[0].strip() if "outcome date" in rest else ""
    frames = space_frames(code)
    alert_start = str(pd.Period(alert, "Q").start_time.date())
    after_alert = [f for f in frames if f[0] >= alert_start]
    shown = [after_alert[0], frames[-1]] if after_alert and after_alert[0] != frames[-1] else frames[-1:]
    return {
        "code": code, "alert": alert, "months": int(case["after_start_months_before"]),
        "deadline": f"{pd.Timestamp(case['first_deadline']):%b %Y}",
        "why": str(case["why"]).split(": ", 1)[-1].split("; observation")[0],
        "outcome": OUTCOME_WORDS.get(outcome.strip(), outcome.strip().replace("_", " ")),
        "reported": f"{pd.Timestamp(reported):%b %Y}" if reported else "",
        "frames": [{"date": d, "src": front.frame_uri(p, width=640), "foot": front.frame_uri(p, "foot", width=640)}
                   for d, p in shown],
    }


def value_payload(latest: tuple[pd.DataFrame, str]) -> dict:
    latest_df, asof = latest
    cycle = build_cycle_list(latest_df)
    on_list = latest_df[latest_df["code"].isin(cycle["code"])].set_index("code").loc[list(cycle["code"])]
    early = on_list[on_list["k3_first_deadline"].isna() | (on_list["K3"].fillna(0) == 0)]
    now = [{"code": code, "level": level_number(r["level"]), "level_word": level_word(r["level"]),
            "why": short_reason(r)} for code, r in early.iterrows()]

    fines = latest_df.dropna(subset=["K5_months"]).sort_values("K5_months", ascending=False)
    fine_rows = [{"code": c, "months": int(m)} for c, m in zip(fines["code"], fines["K5_months"])]

    watch = None
    sat = load_table("real/sat_quarterly.parquet", TRACK_A)
    if sat is not None and {"code", "quarter", "n_images"} <= set(sat.columns):
        sat = sat[sat["code"].isin(latest_df["code"])]
        grid = sat.pivot_table(index="code", columns="quarter", values="n_images", aggfunc="sum")
        watch = {"codes": list(grid.index), "quarters": [str(q) for q in grid.columns],
                 "values": [[None if pd.isna(v) else int(v) for v in row] for row in grid.to_numpy()],
                 "images": int(sat["n_images"].sum())}
    return {"screen": "value", "asof": asof, "total": len(latest_df), "visits": len(cycle),
            "example": warning_example(), "now": now,
            "fines": fine_rows, "fine_months": sum(r["months"] for r in fine_rows), "watch": watch}


# --------------------------------------------------------------------------- #
# Screens
# --------------------------------------------------------------------------- #

def screen_priority_map(track: Track) -> None:
    latest = load_latest_kpis()
    if latest is None:
        page_header("", "Priority map", "Whom should the committee visit first?")
        st.info("Waiting for real/kpi_values.parquet.")
        return
    front.mount(priority_payload(track, latest), key="front_priority", on_open=open_compound_file_from("front_priority"))
    how_to_read([
        "The list is the visit order. Pick a compound to see it from space; the dates under the picture flip it from the oldest to the latest capture.",
        ("The level is the worst of three clocks: K2 quarters without building activity, K3 months "
         "past the first announced handover date, K6 months since launch without a confirmed start."),
        "A compound that may be complete is capped at level 3 and must be confirmed on site.",
        "The cycle list takes up to 4 compounds from levels 1-3. The rule recommends; the committee decides.",
    ])
    with st.expander("Cycle list as a table, with the Arabic reasons"):
        render_cycle_list(latest)

    if track.generated:
        section_title("", "Classifier probabilities: 'distressed' in the next 6 months")
        preds = load_table(PREDICTIONS_FILE, track, READY_DATA)
        table = latest_predictions(preds)
        if table is None:
            st.info(f"Waiting for {PREDICTIONS_FILE}.")
        else:
            st.dataframe(tag_generated_columns(table.reset_index()), use_container_width=True, hide_index=True)
            st.caption(f"{ORIGIN_GENERATED} as of {preds['quarter'].max()} · {len(table)} compounds · "
                       "four methods, none approved as primary · the rule above, not these "
                       "probabilities, selects the cycle list")


def screen_compound_file(track: Track) -> None:
    latest = load_latest_kpis()
    if latest is None:
        page_header("", "Compound file", "Why this one? Evidence behind the priority level.")
        st.info("Waiting for real/kpi_values.parquet.")
        return
    latest_df, asof = latest
    codes = sorted(latest_df["code"].dropna().astype(str).unique())
    levels = dict(zip(latest_df["code"], latest_df["level"]))
    if st.session_state.get("compound_code") not in codes:
        cycle = build_cycle_list(latest_df)
        st.session_state["compound_code"] = cycle["code"].iloc[0] if not cycle.empty else codes[0]

    pick, _ = st.columns([1, 3])
    code = pick.selectbox("Compound", codes, key="compound_code",
                          format_func=lambda c: f"{c} · {level_word(levels.get(c))}")
    now = latest_df[latest_df["code"] == code]
    row = now.iloc[0] if not now.empty else None
    if row is None:
        st.warning(f"{code} has no KPI row for {asof}: shown as not assessable.")
    front.mount(compound_payload(code, row, load_kpi_history(code), load_announcements(code, asof), asof),
                key="front_compound")
    how_to_read([
        "Drag across the picture to compare two capture dates; the two lists under it choose the dates.",
        "The three clocks set the level; the table below shows context that never sets it.",
        "The curve shows building activity per quarter; the small marks on its top edge are quarters with a published developer statement.",
        "Record the visit result at the bottom: real visit results are the ground truth this system still lacks.",
    ])
    render_context_table(row)
    render_context_charts(code)
    render_inspection_button(code, asof)
    render_track_b_extras(code, track)

    section_title("", "Visit form")
    render_ops_visits_form(codes, code)


def screen_value(track: Track) -> None:
    latest = load_latest_kpis()
    if latest is None:
        page_header("", "What it gives", "What SpaceEye adds to the inspection cycle.")
        st.info("Waiting for real/kpi_values.parquet.")
        return
    front.mount(value_payload(latest), key="front_value", on_open=open_compound_file_from("front_value"))


# --------------------------------------------------------------------------- #
# Screen 4: fewer or more visits per cycle
#
# Reads the stored v7 capacity scenario (never recomputes):
#   ready-data/what_if/S3/who_moved_and_why.csv  (data/SCENARIO_CONTRACT_CURRENT.md)
# One row per compound, quarter and capacity variant (2 or 6 versus 4); selection only,
# levels never change.
# --------------------------------------------------------------------------- #

CAPACITY_FILE = "what_if/S3/who_moved_and_why.csv"
CAPACITY_VARIANTS = {"capacity_minus_2": "لو عندك زيارتين بس", "capacity_plus_2": "لو عندك 6 زيارات"}


def short_reason_ar(text: object) -> str:
    """An Arabic level reason without the level prefix, the activity score or the image count."""
    if _missing(text):
        return ""
    body = re.sub(r"\s*\(درجة النشاط [^)]*\)", "", str(text).split(": ", 1)[-1])
    clauses = [c.strip(" .") for c in body.split("؛") if c.strip(" .") and not c.strip().startswith("عدد الصور")]
    return "، ".join(clauses)


def whatif_view(raw: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """The latest quarter of one capacity variant: one row per compound, baseline versus scenario."""
    label = str(raw["quarter"].max())
    latest = raw[raw["quarter"].astype(str) == label]
    view = pd.DataFrame({"code": latest["code"].astype(str), "level": latest["level"].map(level_number)})
    view["change"] = [("joins" if _as_bool(s) else "leaves") if _as_bool(c) else "unchanged"
                      for s, c in zip(latest["selected"], latest["selection_changed"])]
    view["reason"] = latest["reason_ar"].map(short_reason_ar)
    return view.reset_index(drop=True), label


def render_capacity_variant(raw: pd.DataFrame, variant: str) -> None:
    view, label = whatif_view(raw[raw["scenario_id"] == variant])
    moved = view[view["change"] != "unchanged"]
    with st.container(border=True):
        st.markdown(f"**{CAPACITY_VARIANTS[variant]}**")
        if moved.empty:
            st.markdown("القائمة ما بتتغيرش.")
        for _, r in moved.iterrows():
            colour = "#A8102C" if r["change"] == "leaves" else "#2E7D4F"
            verb = "يطلع من القائمة" if r["change"] == "leaves" else "يدخل القائمة"
            st.markdown(
                f'<div class="se-move"><span style="color:{colour};font-weight:700">'
                f'<bdi>{html.escape(r["code"])}</bdi> {verb}</span> · المستوى <bdi>{r["level"]}</bdi>'
                f'<div class="se-move-why">{html.escape(r["reason"])}</div></div>', unsafe_allow_html=True)
        st.caption(f"الربع {label}")


def screen_what_if(track: Track) -> None:
    page_header("", "لو عدد الزيارات اتغير", "مين يدخل القائمة ومين يطلع لو عندك زيارات أقل أو أكتر من 4.")
    if not track.generated:
        st.warning("الشاشة دي بتقرا ملفات السيناريو، وهي متاحة في Track B من القائمة الجانبية.")
        return
    raw = _safe(CAPACITY_FILE, load_table, CAPACITY_FILE, track, READY_DATA)
    if raw is None or raw.empty:
        st.info(f"Waiting for ready-data/{CAPACITY_FILE} (run python -m src.pipeline.setup_review).")
        return
    for column, variant in zip(st.columns(2), CAPACITY_VARIANTS):
        with column:
            render_capacity_variant(raw, variant)


SCREEN_FUNCTIONS = {
    SCREENS[0]: screen_priority_map,
    SCREENS[1]: screen_compound_file,
    SCREENS[2]: screen_value,
    SCREENS[3]: screen_what_if,
}


# --------------------------------------------------------------------------- #
# Sidebar + entry point
# --------------------------------------------------------------------------- #

def render_sidebar() -> tuple[Track, str]:
    st.sidebar.markdown(
        """
        <div class="se-brand">
          <div class="se-brand-name">SpaceEye</div>
          <div class="se-brand-sub">R7 observatory · New Administrative Capital</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    st.sidebar.markdown('<div class="se-side-label">Data track</div>', unsafe_allow_html=True)
    label = st.sidebar.selectbox(
        "Track",
        options=list(TRACKS.keys()),
        index=0,
        key="track_label",
        label_visibility="collapsed",
        help="Track A: public/derived data. Track B: adds generated ACUD-style data.",
    )
    track = TRACKS[label]

    st.sidebar.divider()
    st.sidebar.markdown('<div class="se-side-label">Screens</div>', unsafe_allow_html=True)
    screen = st.sidebar.radio("Screen", SCREENS, key="screen", label_visibility="collapsed")

    st.sidebar.divider()
    if track.generated:
        st.sidebar.markdown(
            f'<span class="se-pill se-pill-b">{ORIGIN_GENERATED} GENERATED</span>',
            unsafe_allow_html=True,
        )
        st.sidebar.caption("Generated numbers tagged · map hidden")
    return track, screen


def main() -> None:
    st.set_page_config(
        page_title="SpaceEye · R7 Observatory",
        page_icon="🛰️",
        layout="wide",
    )
    inject_css()
    track, screen = render_sidebar()
    render_banner(track)
    SCREEN_FUNCTIONS[screen](track)


if __name__ == "__main__":
    main()