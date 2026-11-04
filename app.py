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
import pydeck as pdk
import streamlit as st

from src.dashboard.ops_visits import render_ops_visits_form  # T-NA-04

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

APP_DATA = Path(os.environ.get("SPACEEYE_APP_DATA", "app_data"))

BANNER_TEXT = "Synthetic - for training only"

ORIGIN_REAL = "🟢"       # real, as published
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
    "3 · Would it have warned?",
    "4 · Data trust",
    "5 · What if? (twin)",
]

# --------------------------------------------------------------------------- #
# Design tokens (UI only)
# --------------------------------------------------------------------------- #

PALETTE = {
    "bg": "#0A0E17",          # deep space
    "bg_alt": "#0D1220",      # sidebar
    "surface": "#121A2B",     # cards
    "surface_hi": "#182238",  # hover / inputs
    "border": "#223049",
    "text": "#E6EDF7",
    "muted": "#8A9BB8",
    "accent": "#38BDF8",      # Track A cyan
    "accent_b": "#FB923C",    # Track B amber
}


# --------------------------------------------------------------------------- #
# Stored-file access (no live computation) + no-names gate
# --------------------------------------------------------------------------- #

# Generated hand-off folders that sit under real/ (the v7 release): what-if results and the
# S1..S3 scenario tables. They are generated, so Track A must refuse them too.
GENERATED_PATH_RE = re.compile(r"(^|/)(what_if/|(tables|csv)/current/S\d\.)")


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


def load_table(rel_path: str, track: Track) -> pd.DataFrame | None:
    """Load a stored table. Returns None if the file does not exist yet."""
    if is_generated_path(rel_path) and not track.generated:
        raise PermissionError(
            f"Generated table '{rel_path}' must not be loaded in Track A."
        )
    path = APP_DATA / rel_path
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
    """Consistent screen title: icon chip + title + muted one-line subtitle."""
    sub = f'<div class="se-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="se-header">
          <div class="se-icon">{icon}</div>
          <div><div class="se-title">{title}</div>{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(icon: str, text: str) -> None:
    """Small uppercase section label used above cards."""
    st.markdown(
        f'<div class="se-section">{icon}&nbsp; {text}</div>',
        unsafe_allow_html=True,
    )


def inject_css() -> None:
    """Dark tech theme."""
    p = PALETTE
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

        html, body, [class*="css"], .stApp {{
            font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
        }}
        .stApp {{
            background:
              radial-gradient(1100px 500px at 85% -10%, rgba(56,189,248,0.08), transparent 60%),
              radial-gradient(900px 450px at -10% 0%, rgba(99,102,241,0.07), transparent 55%),
              {p['bg']};
            color: {p['text']};
        }}
        .block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1280px; }}
        header[data-testid="stHeader"] {{ background: transparent; }}
        #MainMenu, footer {{ visibility: hidden; }}
        h1, h2, h3, h4, p, label, span, li {{ color: {p['text']}; }}
        h2, h3 {{ letter-spacing: -0.01em; font-weight: 700; }}
        [data-testid="stCaptionContainer"], .stCaption {{ color: {p['muted']} !important; }}
        hr {{ border-color: {p['border']}; }}

        .se-header {{ display: flex; align-items: center; gap: 0.9rem; margin: 0 0 1.4rem 0; }}
        .se-icon {{
            width: 48px; height: 48px; border-radius: 14px; font-size: 1.5rem;
            display: flex; align-items: center; justify-content: center;
            background: linear-gradient(135deg, rgba(56,189,248,0.18), rgba(99,102,241,0.18));
            border: 1px solid {p['border']};
            box-shadow: 0 6px 20px rgba(0,0,0,0.35);
        }}
        .se-title {{ font-size: 1.7rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.15; }}
        .se-sub {{ color: {p['muted']}; font-size: 0.92rem; margin-top: 0.15rem; }}
        .se-section {{
            color: {p['muted']}; font-size: 0.74rem; font-weight: 700;
            letter-spacing: 0.12em; text-transform: uppercase; margin: 1.2rem 0 0.55rem 0;
        }}

        /* ضمان تساوي ارتفاع جميع الكاردز بنسبة 100% */
        [data-testid="stHorizontalBlock"] > div {{
            display: flex;
            flex-direction: column;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: linear-gradient(180deg, {p['surface']} 0%, {p['bg_alt']} 100%);
            border: 1px solid {p['border']} !important;
            border-radius: 16px;
            padding: 0.5rem 0.7rem;
            box-shadow: 0 8px 24px rgba(0,0,0,0.28);
            height: 100% !important;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        [data-testid="stMetric"] {{
            padding: 0.1rem 0.2rem;
            overflow: visible;
        }}
        [data-testid="stMetricLabel"] p {{
            color: {p['muted']} !important;
            font-size: 0.72rem !important;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            white-space: normal !important;
            word-break: break-word !important;
        }}
        [data-testid="stMetricValue"] div {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-weight: 700;
            color: {p['text']};
            font-size: clamp(1.1rem, 1.5vw, 1.5rem) !important;
            white-space: normal !important;
            word-break: break-word !important;
            line-height: 1.25 !important;
            overflow-wrap: break-word !important;
        }}

        [data-testid="stAlert"] {{
            background: {p['surface']}; border: 1px solid {p['border']};
            border-left: 4px solid {p['accent']}; border-radius: 12px;
            padding: 0.9rem 1.1rem; color: {p['text']};
        }}
        [data-testid="stAlert"] p {{ color: {p['text']}; }}

        [data-testid="stDataFrame"] {{
            border: 1px solid {p['border']}; border-radius: 14px; overflow: hidden;
            box-shadow: 0 6px 18px rgba(0,0,0,0.25);
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {p['bg_alt']} 0%, #090D16 100%);
            border-right: 1px solid {p['border']};
        }}
        [data-testid="stSidebar"] .block-container {{ padding-top: 1rem; }}
        [data-testid="stSidebar"] hr {{ margin: 1rem 0; border-color: {p['border']}; }}
        .se-brand {{ display: flex; align-items: center; gap: 0.7rem; margin: 0.2rem 0 0.4rem 0; }}
        .se-brand-logo {{
            width: 40px; height: 40px; border-radius: 12px; font-size: 1.3rem;
            display: flex; align-items: center; justify-content: center;
            background: linear-gradient(135deg, #38BDF8, #6366F1);
            box-shadow: 0 6px 18px rgba(56,189,248,0.35);
        }}
        .se-brand-name {{ font-weight: 800; font-size: 1.1rem; letter-spacing: -0.01em; }}
        .se-brand-sub {{ color: {p['muted']}; font-size: 0.72rem; letter-spacing: 0.1em; text-transform: uppercase; }}
        .se-side-label {{
            color: {p['muted']}; font-size: 0.7rem; font-weight: 700;
            letter-spacing: 0.14em; text-transform: uppercase; margin: 0.2rem 0 0.1rem 0;
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] > div {{
            background: {p['surface_hi']}; border: 1px solid {p['border']}; border-radius: 10px;
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] * {{ color: {p['text']}; }}
        [data-testid="stSidebar"] [role="radiogroup"] {{ gap: 0.25rem; }}
        [data-testid="stSidebar"] [role="radiogroup"] label {{
            background: transparent; border: 1px solid transparent; border-radius: 10px;
            padding: 0.45rem 0.7rem; transition: all 0.15s ease; width: 100%;
        }}
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
            background: {p['surface_hi']}; border-color: {p['border']};
        }}
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
            background: linear-gradient(90deg, rgba(56,189,248,0.16), rgba(56,189,248,0.04));
            border-color: rgba(56,189,248,0.45);
        }}
        .se-pill {{
            display: inline-block; padding: 0.22rem 0.65rem; border-radius: 999px;
            font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em;
            border: 1px solid {p['border']}; background: {p['surface']};
        }}
        .se-pill-a {{ color: {p['accent']}; border-color: rgba(56,189,248,0.45); }}
        .se-pill-b {{ color: {p['accent_b']}; border-color: rgba(251,146,60,0.55); }}

        .synthetic-banner {{
            position: sticky; top: 0.5rem; z-index: 1000;
            display: flex; align-items: center; justify-content: center; gap: 0.7rem;
            margin: 0 0 1.4rem 0; padding: 0.8rem 1.2rem;
            background: linear-gradient(100deg, #FF6A00 0%, #FF8A00 45%, #FFB300 100%);
            color: #1A0E00; font-weight: 800; font-size: 1.02rem;
            letter-spacing: 0.08em; text-transform: uppercase; text-align: center;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.35);
            box-shadow: 0 10px 28px rgba(255,122,0,0.38),
                        0 2px 6px rgba(0,0,0,0.45),
                        inset 0 1px 0 rgba(255,255,255,0.45);
            text-shadow: 0 1px 0 rgba(255,255,255,0.25);
        }}
        .synthetic-banner .dot {{
            width: 10px; height: 10px; border-radius: 50%; background: #1A0E00;
            box-shadow: 0 0 0 3px rgba(26,14,0,0.25); animation: se-pulse 1.8s ease-in-out infinite;
        }}
        @keyframes se-pulse {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.35; }} }}
        /* Floating SpaceEye Chat Button */
            .se-floating-chat {{
                position: fixed;
                right: 28px;
                bottom: 28px;
                width: 62px;
                height: 62px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                background: linear-gradient(135deg, #38BDF8, #6366F1);
                color: white !important;
                font-size: 28px;
                text-decoration: none !important;
                box-shadow: 0 8px 25px rgba(56, 189, 248, 0.4);
                z-index: 99999;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }}

        .se-floating-chat:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 30px rgba(56, 189, 248, 0.55);
            }}
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

LEVELS: dict[int, tuple[str, str]] = {
    1: ("Inspect now", "#EF4444"),
    2: ("Inspect this cycle", "#F97316"),
    3: ("Document review", "#EAB308"),
    4: ("Routine", "#22C55E"),
}
NOT_ASSESSABLE: tuple[str, str] = ("Not assessable", "#6B7280")  # grey

REQUIRED_KPI_COLUMNS = {"code", "quarter", "level"}


def _level_style(level: object) -> tuple[str, str]:
    try:
        return LEVELS[int(level)]
    except (TypeError, ValueError, KeyError):
        return NOT_ASSESSABLE


def level_word(level: object) -> str:
    return _level_style(level)[0]


def _hex_to_rgba(hex_color: str, alpha: int = 175) -> list[int]:
    h = hex_color.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)] + [alpha]


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
    wanted = ("cycle_rank", "code", "level_word", "reason_ar", "K2", "K3", "K6")
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


def render_map_slot(track: Track, latest: tuple[pd.DataFrame, str] | None) -> None:
    if track.generated:
        return
    section_title("🗺️", "Priority map")

    geojson = load_boundaries()
    if geojson is None:
        st.warning("real/compound_boundaries.geojson not found yet.")
        return
    if latest is None:
        st.info("Waiting for real/kpi_values.parquet.")
        return

    latest_df, asof = latest
    levels = dict(zip(latest_df["code"], latest_df["level"]))

    features, points = [], []
    counts = {word: 0 for word, _ in [*LEVELS.values(), NOT_ASSESSABLE]}
    for feat in geojson["features"]:
        code = feat["properties"]["code"]
        word, color = _level_style(levels.get(code))
        counts[word] += 1
        points += _geo_points(feat["geometry"])
        features.append({
            "type": "Feature",
            "geometry": feat["geometry"],
            "properties": {"code": code, "level_word": word,
                           "fill_color": _hex_to_rgba(color)},
        })

    with st.container(border=True):
        if not features:
            st.info("No R7 boundaries in the file.")
            return
        layer = pdk.Layer(
            "GeoJsonLayer",
            data={"type": "FeatureCollection", "features": features},
            get_fill_color="properties.fill_color",
            get_line_color=[255, 255, 255, 220],
            line_width_min_pixels=1,
            stroked=True, filled=True, pickable=True,
        )
        view = pdk.data_utils.compute_view(points, view_proportion=0.9) if points else None
        st.pydeck_chart(
            pdk.Deck(
                layers=[layer],
                initial_view_state=view,
                map_style="dark",
                tooltip={"text": "{code}\n{level_word}"},
            ),
            use_container_width=True,
        )
        legend = "".join(
            f'<span class="se-pill" style="border-color:{color};margin-right:0.4rem">'
            f'<span style="color:{color}">●</span> {word} · {counts[word]}</span>'
            for word, color in [*LEVELS.values(), NOT_ASSESSABLE]
        )
        st.markdown(legend, unsafe_allow_html=True)
        st.caption(f"{ORIGIN_DERIVED} derived · as of {asof} · grey = not assessable")


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
FILES_DIR = APP_DATA / "files"
PREDICTIONS_FILE = "ml/predictions.parquet"
K5_EGP_FILE, K5_EGP_COL = "ml/ml_dataset.parquet", "k5_egp"

COL_A, COL_DW = "activity_prob", "built_prob_mean"
COL_HEIGHT, COL_VEG, COL_YEAR = "height_mean_m", "veg_share", "year"
MAX_HEIGHT_YEAR = 2024
VEG_COMPLETE_THRESHOLD = 0.10

K_ORIGIN = {"A": ORIGIN_DERIVED, "K2": ORIGIN_DERIVED, "K3": ORIGIN_REAL,
            "K4": ORIGIN_REAL, "K5": ORIGIN_DERIVED, "K6": ORIGIN_DERIVED}
SERIES_COLORS = {"Activity score A": "#38BDF8", "Dynamic World built probability": "#818CF8"}
MARKER_COLOR = "#A78BFA"


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
    return kpis[kpis["code"] == code].sort_values("quarter").reset_index(drop=True)


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
    if "handover_date" in df.columns:
        df["handover_date"] = pd.to_datetime(df["handover_date"], errors="coerce")
    return df.sort_values("published_date").reset_index(drop=True)


def first_announced_date(ann: pd.DataFrame | None) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    if ann is None or "handover_date" not in ann.columns:
        return None
    dated = ann.dropna(subset=["handover_date"])
    if dated.empty:
        return None
    first = dated.iloc[0]
    return first["handover_date"], first["published_date"]


def load_images(code: str) -> dict[str, tuple[Path, str]]:
    """Smart image loader supporting both main and subfolder layouts."""
    imagery_dir = Path("data/imagery")
    images_sub = imagery_dir / "images"
    
    index_path = imagery_dir / "images.csv"
    if not index_path.exists():
        index_path = imagery_dir / "IMAGERY_MANIFEST.csv"

    index = None
    if index_path.exists():
        try:
            df = pd.read_csv(index_path)
            drop = [c for c in df.columns if c.lower() in FORBIDDEN_COLUMNS]
            if drop:
                df = df.drop(columns=drop)
            index = df
        except Exception:
            pass

    found: dict[str, tuple[Path, str]] = {}
    type_col = "image_type" if index is not None and "image_type" in index.columns else "kind"

    for kind in ("before", "after"):
        possible_paths = [
            images_sub / f"{code}_{kind}.jpg",
            images_sub / f"{code.lower()}_{kind}.jpg",
            imagery_dir / f"{code}_{kind}.jpg",
            imagery_dir / f"{code.lower()}_{kind}.jpg",
        ]
        
        path = next((p for p in possible_paths if p.exists()), None)
        if path is None:
            continue

        captured, credit = "capture date n/a", "Esri World Imagery Wayback"
        if index is not None and {"code", type_col} <= set(index.columns):
            hit = index[(index["code"].astype(str).str.upper() == code.upper()) & 
                        (index[type_col] == kind)]
            if not hit.empty:
                row = hit.iloc[0]
                if "capture_date" in index.columns and not _missing(row.get("capture_date")):
                    captured = f"captured {row['capture_date']}"
                if "attribution" in index.columns and not _missing(row.get("attribution")):
                    credit = str(row["attribution"])

        found[kind] = (path, f"{kind.capitalize()} · {captured} · {credit}")

    return found


def find_inspection_file(code: str, asof: str) -> Path | None:
    exact = FILES_DIR / f"{code}_{asof}.html"
    if exact.exists():
        return exact
    matches = sorted(FILES_DIR.glob(f"{code}_*.html"))
    return matches[-1] if matches else None


# ---- screen 2 renderers ----------------------------------------------------- #

def render_kpi_tiles(row: pd.Series | None, asof: str) -> None:
    section_title("📊", "Indicators")
    get = (lambda c: None) if row is None else (lambda c: row.get(c))

    tiles = st.columns(4)
    with tiles[0]:
        metric_tile("Priority level", level_word(get("level")), "",
                    "worst of K2, K3, K6", asof, ORIGIN_DERIVED)
    with tiles[1]:
        _kpi_tile("K2 no activity", get("K2"), "quarter(s)",
                  "counted only after construction started", asof, K_ORIGIN["K2"])
    with tiles[2]:
        _kpi_tile("K3 handover clock", get("K3"), "months",
                  "since first announced handover date", asof, K_ORIGIN["K3"])
    with tiles[3]:
        _kpi_tile("K6 never started", get("K6"), "months",
                  "since first launch/promise, no construction start", asof, K_ORIGIN["K6"])

    k4 = get("K4")
    k4_text = "unknown" if _missing(k4) else ("Yes" if k4 in (True, 1, "True", "Yes") else
                                             "No" if k4 in (False, 0, "False", "No") else str(k4))
    context = pd.DataFrame({
        "Indicator": ["A activity score", "K4 assessable", "K5 fine-eligible months"],
        "Value": [_fmt(get(COL_A), 2), k4_text, _fmt(get("K5"), 0)],
        "Unit": ["probability 0-1", "yes/no (≥ 6 images)", "months (real part)"],
        "Origin": [K_ORIGIN["A"], K_ORIGIN["K4"], K_ORIGIN["K5"]],
    })
    with st.container(border=True):
        st.caption("Context: shown, but they do not set the level.")
        st.dataframe(context, use_container_width=True, hide_index=True)


def render_lineage(row: pd.Series | None, asof: str) -> None:
    if row is None:
        return
    parts = [f"origin {row.get('origin', 'n/a')}", f"run_id {row.get('run_id', 'n/a')}"]
    if "computed_at" in row.index and not _missing(row["computed_at"]):
        parts.append(f"computed {row['computed_at']}")
    st.caption("🧬 Lineage · " + " · ".join(parts) + f" · as of {asof}")


def render_curves(code: str, history: pd.DataFrame | None, ann: pd.DataFrame | None) -> None:
    section_title("📈", "Satellite curves")
    with st.container(border=True):
        wanted = {COL_A: "Activity score A", COL_DW: "Dynamic World built probability"}
        if history is None or history.empty or not (set(wanted) & set(history.columns)):
            st.info(f"Waiting for the A / Dynamic World series of {code} in real/kpi_values.parquet.")
            return

        present = [c for c in wanted if c in history.columns]
        order = sorted(history["quarter"].astype(str).unique())
        long = (history[["quarter", *present]].rename(columns=wanted)
                .melt("quarter", var_name="series", value_name="value"))
        long["quarter"] = long["quarter"].astype(str)

        x = alt.X("quarter:N", sort=order, title=None, axis=alt.Axis(labelAngle=-45))
        lines = alt.Chart(long).mark_line(point=True).encode(
            x=x,
            y=alt.Y("value:Q", title="0-1", scale=alt.Scale(domain=[0, 1])),
            color=alt.Color("series:N", title=None,
                            scale=alt.Scale(domain=list(SERIES_COLORS),
                                            range=list(SERIES_COLORS.values())),
                            legend=alt.Legend(orient="bottom")),
            tooltip=["quarter", "series", alt.Tooltip("value:Q", format=".2f")],
        )
        chart = lines
        if ann is not None and not ann.empty and "published_date" in ann.columns:
            valid_ann = ann.dropna(subset=["published_date"])
            if not valid_ann.empty:
                marks = pd.DataFrame({
                    "quarter": valid_ann["published_date"].dt.to_period("Q").astype(str),
                    "label": "Developer statement published",
                })
                marks = marks[marks["quarter"].isin(order)].drop_duplicates("quarter")
                if not marks.empty:
                    rules = alt.Chart(marks).mark_rule(color=MARKER_COLOR, strokeDash=[4, 4]).encode(
                        x=alt.X("quarter:N", sort=order), tooltip=["quarter", "label"])
                    chart = lines + rules
        st.altair_chart(chart.properties(height=300), use_container_width=True)

        first = first_announced_date(ann)
        if first is not None:
            handover, published = first
            st.markdown(f"📌 **First announced handover date:** {handover:%b %Y} "
                        f"(published {published:%b %Y})")
        else:
            st.caption("📌 No announced handover date on file for this compound yet.")
        st.caption(f"{ORIGIN_DERIVED} derived · gaps = quarters not assessable · "
                   "dashed lines = quarter of a published developer statement")


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
                            color=alt.value("#38BDF8"),
                            tooltip=[COL_YEAR, alt.Tooltip(COL_HEIGHT, format=".1f"), "kind"],
                        ).properties(height=240),
                        use_container_width=True)
                st.caption(f"{ORIGIN_DERIVED} estimate · approved context through {MAX_HEIGHT_YEAR}")

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
                    line = alt.Chart(v).mark_line(point=True, color="#22C55E").encode(
                        x=alt.X(f"{COL_YEAR}:O", title=None),
                        y=alt.Y(f"{COL_VEG}:Q", title="share 0-1", scale=alt.Scale(domain=[0, 1])),
                        tooltip=[COL_YEAR, alt.Tooltip(COL_VEG, format=".2f")])
                    rule = alt.Chart(pd.DataFrame({"y": [VEG_COMPLETE_THRESHOLD]})).mark_rule(
                        color=MARKER_COLOR, strokeDash=[4, 4]).encode(y="y:Q")
                    st.altair_chart((line + rule).properties(height=240), use_container_width=True)
                st.caption(f"{ORIGIN_DERIVED} derived · dashed line = {VEG_COMPLETE_THRESHOLD:.2f}")


def render_images(code: str) -> None:
    section_title("🛰️", "Wayback images")
    images = load_images(code)
    with st.container(border=True):
        if not images:
            st.info("Waiting for Wayback images in data/imagery/.")
            return
        cols = st.columns(2)
        for col, kind in zip(cols, ("before", "after")):
            with col:
                if kind in images:
                    path, caption = images[kind]
                    st.image(str(path), caption=caption, use_container_width=True)
                else:
                    st.info(f"No '{kind}' image for {code} yet.")
        st.caption("Judged by eye: images support the visit, they are not a measurement.")


def render_inspection_button(code: str, asof: str) -> None:
    section_title("📄", "Inspection file")
    path = find_inspection_file(code, asof)
    if path is None:
        st.button("📄 Inspection file (Arabic)", disabled=True, key=f"insp_{code}")
        st.caption("Not ready yet: files/<code>_<quarter>.html arrives with T-EL-06.")
        return
    st.download_button("📄 Open inspection file (Arabic HTML)", data=path.read_bytes(),
                       file_name=path.name, mime="text/html", key=f"insp_{code}")
    st.caption("Drafted by AI from stored facts and reviewed before committee use.")


def render_track_b_extras(code: str, track: Track) -> None:
    if not track.generated:
        return
    section_title("🧠", "Generated-data model (Track B)")

    preds = load_table(PREDICTIONS_FILE, track)
    cols = st.columns(3)
    if preds is not None and {"code", "quarter"} <= set(preds.columns):
        mine = preds[preds["code"] == code]
        if not mine.empty:
            last = mine.sort_values("quarter").iloc[-1]
            with cols[0]:
                _kpi_tile("Probability: distressed", last.get("p_distressed"), "",
                          "generated label, next 6 months", str(last["quarter"]),
                          ORIGIN_GENERATED, digits=2)
            with cols[1]:
                _kpi_tile("Probability: not distressed", last.get("p_not_distressed"), "",
                          "generated label, next 6 months", str(last["quarter"]),
                          ORIGIN_GENERATED, digits=2)
        else:
            cols[0].info(f"No prediction row for {code}.")
    else:
        cols[0].info("Waiting for ml/predictions.parquet.")

    egp = load_table(K5_EGP_FILE, track)
    with cols[2]:
        if egp is not None and {"code", "quarter", K5_EGP_COL} <= set(egp.columns):
            mine = egp[egp["code"] == code].sort_values("quarter")
            if not mine.empty:
                last = mine.iloc[-1]
                _kpi_tile("K5 fine exposure", last[K5_EGP_COL], "EGP",
                          "eligible months × assumed rate × land value", str(last["quarter"]),
                          ORIGIN_GENERATED)
        else:
            st.info(f"Waiting for {K5_EGP_FILE}.")
    st.caption(f"{ORIGIN_GENERATED} Generated for training.")


# --------------------------------------------------------------------------- #
# Screen 3 data (T-NA-05): real-case backtest (Track A) + model metrics (Track B)
# --------------------------------------------------------------------------- #

BACKTEST_CASES_FILE = "releases/ready-data/backtest/cases.csv"        # Updated path
BACKTEST_SUMMARY_FILE = "releases/ready-data/backtest/summary.json"   # Updated path
METRICS_FILE = "ml/metrics.csv"                   # contract: elsayed -> nada (D3), generated
B_SIGNALS_FILE = "ml/ml_dataset.parquet"          # ASSUMED home of the stored B1-B5 columns

EARLY_WARNING_MONTHS = 6     # spec section 0: level 1-2 at least 6 months before the delay was public
SUCCESS_TARGET_DEFAULT = 5   # spec section 0; used only if summary.json carries no target

# Column / key aliases updated to match cases.csv structure
CASE_ALIASES = {
    "code": ("code", "compound_code", "case"),
    "outcome": ("outcome", "outcome_type", "event_type", "event", "first_deadline"),
    "event_date": ("event_date", "outcome_date", "public_date", "delay_public_date", "first_deadline"),
    "level": ("level_reached", "first_level", "best_level", "level_at_cutoff", "level", "level_at_freeze"),
    "months_early": ("months_early", "lead_months", "lead_time_months", "months_before", "after_start_months_before"),
    "warned": ("warned_early", "warned", "early_warning", "hit", "after_start"),
    "what": ("what_happened", "happened", "what", "literal"),
    "why": ("why", "why_explanation", "reason", "driver"),
    "next": ("what_next", "next_step", "next"),
    "competing": ("competing_explanation", "rejected_explanation", "competing"),
    "competing_n": ("competing_number", "rejected_number", "evidence_number"),
}
SUMMARY_ALIASES = {
    "warned": ("warned_early", "n_warned", "warned", "hits"),
    "total": ("n_cases", "cases", "total", "n_total", "n"),
    "frozen": ("warned_frozen", "warned_at_frozen_cutoff", "frozen_cutoff", "n_warned_frozen"),
    "target": ("target", "success_target", "target_cases"),
    "asof": ("asof", "as_of", "as_of_quarter", "run_id"),
}
DENOMINATOR_COLUMNS = ("n", "denominator", "support", "n_test", "n_rows", "of")


def _find_col(df: pd.DataFrame, aliases: tuple[str, ...]) -> str | None:
    lower = {str(c).lower(): c for c in df.columns}
    return next((lower[a] for a in aliases if a in lower), None)


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


def _as_int(value: object) -> int | None:
    try:
        return None if _missing(value) else int(float(value))
    except (TypeError, ValueError):
        return None


def _yes_no(flag: bool | None) -> str:
    return "unknown" if flag is None else ("Yes" if flag else "No")


@st.cache_data(show_spinner=False)
def _read_json(path_str: str, mtime_ns: int = 0) -> object:
    return json.loads(Path(path_str).read_text(encoding="utf-8"))


def load_backtest_summary() -> dict | None:
    path = APP_DATA.parent / BACKTEST_SUMMARY_FILE if not Path(BACKTEST_SUMMARY_FILE).exists() else Path(BACKTEST_SUMMARY_FILE)
    if not path.exists():
        path = Path(BACKTEST_SUMMARY_FILE)
    if not path.exists():
        return None
    try:
        data = _read_json(str(path), path.stat().st_mtime_ns)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _summary_value(summary: dict | None, aliases: tuple[str, ...]) -> object:
    """First matching key, searching nested objects too. Only numbers/labels are read:
    the raw JSON is never printed, so nothing unexpected can reach the screen."""
    queue = [summary] if summary else []
    while queue:
        node = queue.pop(0)
        for key, val in node.items():
            if str(key).lower() in aliases and not isinstance(val, (dict, list)):
                return val
        queue += [v for v in node.values() if isinstance(v, dict)]
    return None


def _level_text(value: object) -> str:
    if _missing(value):
        return "unknown"
    try:
        return level_word(int(float(value)))
    except (TypeError, ValueError):
        return str(value)  # already a word such as "Inspect now"


def _tag_numeric_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Orange tag on the headers of numeric columns of a generated table."""
    return df.rename(columns={c: f"{c} {ORIGIN_GENERATED}" for c in df.columns
                              if pd.api.types.is_numeric_dtype(df[c])})


# ---- Track A: frozen-clock table -------------------------------------------- #

def render_backtest_cases() -> None:
    path = Path(BACKTEST_CASES_FILE)
    if not path.exists():
        path = APP_DATA.parent / BACKTEST_CASES_FILE
    
    cases = enforce_no_names(_read_file(str(path)), BACKTEST_CASES_FILE) if path.exists() else None
    summary = load_backtest_summary()
    if cases is None or cases.empty:
        st.info("Waiting for releases/ready-data/backtest/cases.csv.")
        return

    col = {field: _find_col(cases, names) for field, names in CASE_ALIASES.items()}
    flags = ([_as_bool(v) for v in cases[col["warned"]]] if col["warned"] else [None] * len(cases))

    total = _as_int(_summary_value(summary, SUMMARY_ALIASES["total"])) or len(cases)
    warned = _as_int(_summary_value(summary, SUMMARY_ALIASES["warned"]))
    if warned is None and col["warned"]:
        warned = sum(1 for f in flags if f)
    frozen = _as_int(_summary_value(summary, SUMMARY_ALIASES["frozen"]))
    target = _as_int(_summary_value(summary, SUMMARY_ALIASES["target"])) or SUCCESS_TARGET_DEFAULT
    asof = str(_summary_value(summary, SUMMARY_ALIASES["asof"]) or "stored run")
    met = None if warned is None else warned >= target

    section_title("🧊", "Frozen-clock backtest (real public cases)")
    tiles = st.columns(3 if frozen is not None else 2)
    with tiles[0]:
        metric_tile("Warned early", "unknown" if warned is None else f"{warned} of {total}",
                    "" if warned is None else "cases",
                    f"level 1-2 at least {EARLY_WARNING_MONTHS} months before the delay was public",
                    asof, ORIGIN_DERIVED)
    with tiles[1]:
        metric_tile("Success criterion",
                    "unknown" if met is None else ("Met" if met else "Not met"), "",
                    f"needs {target} of {total} cases · fixed before any computation",
                    asof, ORIGIN_DERIVED)
    if frozen is not None:
        with tiles[2]:
            metric_tile("At the frozen cutoff", f"{frozen} of {total}", "cases",
                        "using only data published before each quarter", asof, ORIGIN_DERIVED)

    # Per-case table: one row per case, level as a word, yes/no in words
    table = pd.DataFrame({"Case": cases[col["code"]].astype(str) if col["code"]
                          else [f"Case {i + 1}" for i in range(len(cases))]})
    for field, heading in (("outcome", "Outcome"), ("event_date", "Event date")):
        if col[field]:
            table[heading] = cases[col[field]].astype(str)
    if col["level"]:
        table["Level reached"] = cases[col["level"]].map(_level_text)
    if col["months_early"]:
        table["Months early"] = cases[col["months_early"]].map(lambda v: _fmt(v, 0))
    table["Warned early"] = [_yes_no(f) for f in flags]

    with st.container(border=True):
        st.dataframe(table, use_container_width=True, hide_index=True)
        st.caption(f"{ORIGIN_DERIVED} derived from real public cases · counts only, no percentages "
                   f"(small sample) · 'early' = level 1-2 at least {EARLY_WARNING_MONTHS} months "
                   "before the delay became public")

    # Why: per-case reasoning (what happened / why / what next / rejected explanation)
    section_title("🔎", "Why, case by case")
    for i, (_, r) in enumerate(cases.iterrows()):
        label = table.iloc[i]["Case"]
        with st.expander(f"{label} · warned early: {_yes_no(flags[i])}"):
            shown = False
            for field, heading in (("what", "What happened"), ("why", "Why"),
                                   ("next", "What next")):
                if col[field] and not _missing(r[col[field]]):
                    st.markdown(f"**{heading}.** {r[col[field]]}")
                    shown = True
            if col["competing"] and not _missing(r[col["competing"]]):
                number = ""
                if col["competing_n"] and not _missing(r[col["competing_n"]]):
                    number = f" ({r[col['competing_n']]})"
                st.markdown(f"**Competing explanation, rejected.** {r[col['competing']]}{number}")
                shown = True
            if not shown:
                st.caption("No explanation text in cases.csv for this case yet.")

    if met is False:
        with st.container(border=True):
            st.markdown(
                "**What it means.** Satellites tell 'building or not' well, but the saved rule did "
                "not raise early alerts in this small set of cases. Early warning of delay needs "
                "ACUD's data (supervisor reports, contractual dates, meters, escrow). The counts "
                "alone do not show why a delay happened.")


# ---- Track B: model metrics + B1-B5 ----------------------------------------- #

def render_model_metrics(track: Track) -> None:
    section_title("📐", "Binary classifier on generated data")
    metrics = load_table(METRICS_FILE, track)  # generated: loaded only in Track B
    if metrics is None or metrics.empty:
        st.info("Waiting for ml/metrics.csv (hand-off from elsayed, D3).")
        return

    m_col = _find_col(metrics, ("metric", "metric_name", "measure", "metric_key"))
    v_col = _find_col(metrics, ("value", "score", "result"))
    if m_col is None or v_col is None:
        st.warning("ml/metrics.csv has no 'metric' / 'value' columns: showing the raw table.")
        st.dataframe(_tag_numeric_headers(metrics), use_container_width=True, hide_index=True)
        return

    metrics = metrics.copy()
    metrics[v_col] = pd.to_numeric(metrics[v_col], errors="coerce").round(2)
    text = metrics[m_col].astype(str).str.lower()
    
    # Safe blob conversion preventing float/type aggregation issues
    blob = metrics.astype(str).fillna("").agg(lambda x: " ".join(x.astype(str)), axis=1).str.lower()
    
    # Updated filters matching metrics.csv structure (macro_f1_binary, distressed_recall_at_4, class_recall)
    is_macro = text.str.contains("macro|f1", regex=True)
    is_at_n = text.str.contains(r"@|_at_|recall_at|at_\d", regex=True)
    is_class = (text.str.contains("recall|class") & ~is_at_n & ~is_macro) | (text == "class_recall")
    is_random = blob.str.contains("random") | text.str.contains("random")

    def block(title: str, rows: pd.DataFrame, empty_msg: str) -> None:
        with st.container(border=True):
            st.markdown(f"**{title}**")
            if rows.empty:
                st.info(empty_msg)
            else:
                st.dataframe(_tag_numeric_headers(rows), use_container_width=True, hide_index=True)

    block("Per-class recall", metrics[is_class],
          "No per-class recall rows found in ml/metrics.csv.")
    block("Macro-F1 (two classes)", metrics[is_macro],
          "No macro-F1 rows found in ml/metrics.csv.")

    at_n = metrics[is_at_n | (is_random & text.str.contains("recall"))].copy()
    block("Recall@N for 'distressed' vs random ranking", at_n,
          "No recall@N rows found in ml/metrics.csv.")
    if not at_n.empty:
        group_cols = [c for c in at_n.columns if c not in (m_col, v_col)
                      and not pd.api.types.is_numeric_dtype(at_n[c])
                      and c.lower() not in DENOMINATOR_COLUMNS]
        at_n["compared"] = (at_n[group_cols].astype(str).agg(" · ".join, axis=1)
                            if group_cols else "model")
        at_n.loc[is_random.loc[at_n.index], "compared"] = "random ranking"
        enc = dict(x=alt.X("compared:N", title=None,
                           axis=alt.Axis(labelAngle=-20, labelLimit=240)),
                   y=alt.Y(f"{v_col}:Q", title="recall (0-1)", scale=alt.Scale(domain=[0, 1])),
                   color=alt.Color(f"{m_col}:N", title=None, legend=alt.Legend(orient="bottom")),
                   tooltip=["compared", m_col, alt.Tooltip(f"{v_col}:Q", format=".2f")])
        try:
            chart = alt.Chart(at_n).mark_bar().encode(xOffset=f"{m_col}:N", **enc)
        except Exception:  # older Altair without xOffset
            chart = alt.Chart(at_n).mark_bar().encode(**enc)
        with st.container(border=True):
            st.altair_chart(chart.properties(height=260), use_container_width=True)

    if _find_col(metrics, DENOMINATOR_COLUMNS) is None:
        st.warning("No denominator column (n) in ml/metrics.csv: every metric must show its n.")
    st.caption(f"{ORIGIN_GENERATED} Generated data: a diagnostic of the generator and model "
               "workflow, not real-world accuracy. The test split has very few 'distressed' rows, "
               "so one row can move a recall value by a large step: differences of one row are "
               "noise. Always compare with the random baseline and read the denominators.")


def render_b_signals(track: Track) -> None:
    section_title("🧾", "B1-B5 signals per compound")
    data = load_table(B_SIGNALS_FILE, track)  # generated: loaded only in Track B
    if data is None or not {"code", "quarter"} <= set(data.columns):
        st.info(f"Waiting for {B_SIGNALS_FILE} (B1-B5 columns).")
        return

    # خريطة البحث تشمل الأسماء المختصرة والأسماء الكاملة الموجودة في ملف الـ dataset
    labels = {
        1: "B1 escrow cover", 
        2: "B2 land arrears", 
        3: "B3 complaint rate",
        4: "B4 occupancy gap (context only)", 
        5: "B5 plan gap"
    }
    
    # الكلمات المفتاحية البديلة لكل مؤشر في الملف
    keywords = {
        1: ["b1", "escrow"],
        2: ["b2", "arrear"],
        3: ["b3", "complaint"],
        4: ["b4", "occupancy"],
        5: ["b5", "plan"]
    }

    found = {}
    for n, label in labels.items():
        match = None
        # البحث بالكلمات المفتاحية المرنة
        for col in data.columns:
            col_lower = str(col).lower()
            if any(kw in col_lower for kw in keywords[n]):
                match = col
                break
        if match:
            found[label] = match

    if not found:
        st.info(f"No B1-B5 columns found in {B_SIGNALS_FILE}.")
        return

    asof = str(data["quarter"].max())
    latest = data[data["quarter"] == data["quarter"].max()].sort_values("code")
    table = pd.DataFrame({"Code": latest["code"].astype(str).values})
    
    for label, source in found.items():
        values = latest[source]
        flags = [_as_bool(v) for v in values]
        known = values.dropna()
        name = str(source).lower()
        looks_like_amount = any(w in name for w in ("month", "pct", "pts", "point", "egp",
                                                    "kwh", "rate", "ratio", "count"))
        is_flag = (not known.empty and known.isin([0, 1, True, False]).all()
                   and (values.dtype == bool or any(w in name for w in ("flag", "trigger", "hit"))
                        or not looks_like_amount))
        if is_flag:
            word = "Gap" if label.startswith("B4") else "Triggered"
            table[f"{label} {ORIGIN_GENERATED}"] = [
                "unknown" if f is None else (word if f else "No") for f in flags]
        else:
            digits = 0 if (known % 1 == 0).all() else 1
            table[f"{label} {ORIGIN_GENERATED}"] = [_fmt(v, digits) for v in values]

    with st.container(border=True):
        st.dataframe(table, use_container_width=True, hide_index=True)
        st.caption(f"{ORIGIN_GENERATED} generated · {len(table)} compound(s) · as of {asof} · "
                   "B1, B2, B3, B5 raise the level to at least 2 when triggered; "
                   "B4 is context only. Missing stays 'unknown', never 'No'.")


# --------------------------------------------------------------------------- #
# Screen 4 data (T-NA-06): gates, coverage, facts counter, colour key
# --------------------------------------------------------------------------- #

QUALITY_LOG_FILES = (
    "releases/ready-data/review/real/quality_checks_log.parquet",
    "ready-data/review/real/quality_checks_log.parquet",
    "review/real/quality_checks_log.parquet",
    "real/quality_checks_log.parquet",
    "real/quality_checks_log.csv",
)  # contract: ahmed -> nada
COMPOUNDS_FILE = "real/compounds.parquet"                                                # contract: ahmed -> nada
FACTS_FILES = ("real/facts_register.parquet", "real/facts_register.csv",
               "real/facts.parquet", "real/facts.csv")                                   # ASSUMED (not in the contract)
DOCUMENTED_FACTS = (1009, 1026)  # 01-specs section 12 (slide 3). Fallback only: used when no facts register file exists

# The 10 quality gates (01-specs section 8): key, dimension, rule, owner role, if it fails.
GATES = (
    ("source", "Accuracy", "Every fact has a record_id and an accepted verdict", "R2", "Fix: excluded"),
    ("completeness", "Completeness", "At least 6 Dynamic World images in the quarter", "R3", "Flag: not assessable"),
    ("validity", "Validity", "Probabilities 0-1, counts ≥ 0, levels 1-4, valid dates", "R1", "Stop"),
    ("uniqueness", "Uniqueness", "(compound, quarter) and (compound, year) are unique", "R1", "Stop"),
    ("consistency", "Consistency", "Every code is in the register; row counts equal after joins", "R1", "Stop"),
    ("freshness", "Freshness", "Last quarter at most 1 quarter before computation", "R3", "Flag: stale"),
    ("separation", "Consistency", "No generated column in a real table; every column has an origin", "R1", "Stop"),
    ("data_or_city", "Accuracy", "More than 30% of compounds switch to 'no activity' in one quarter", "R4", "Flag and review"),
    ("stuck_series", "Accuracy", "Same value 4 quarters in a row", "R3", "Flag and review"),
    ("no_names", "Privacy", "No compound or developer name in any output file", "R1", "Stop"),
)

_PASS = {"pass", "passed", "ok", "true", "1", "1.0", "yes"}
_FLAG = {"flag", "flagged", "warn", "warning", "stale", "review"}
_FAIL = {"fail", "failed", "false", "0", "0.0", "no", "stop", "stopped", "error"}
STATUS_WORD = {"Pass": "✅ Pass", "Flag": "⚠️ Flag", "Fail": "⛔ Fail", "unknown": "❔ not in log"}

# Dashboard-side audit: which stored tables are checked, and what must never appear in a real one.
AUDIT_REAL_FILES = (KPI_FILE, COMPOUNDS_FILE, "real/statements.parquet", "real/sat_yearly.parquet",
                    "real/sat_quarterly.parquet", "real/quality_checks_log.parquet")
AUDIT_GENERATED_FILES = (PREDICTIONS_FILE, METRICS_FILE, B_SIGNALS_FILE,
                         "sim/fin_monthly.parquet", "sim/complaints.parquet")
GENERATED_COLUMN_HINTS = {  # columns that exist only in generated tables (spec sections 2, 5, 9)
    "p_distressed", "p_not_distressed", "k5_egp", "cover_balance_egp", "cover_required_egp",
    "planned_pct", "reported_pct", "land_months_late", "complaints", "kwh", "meters_active",
}


def _safe(label: str, fn, *args, default=None):
    """Run a loader; if a stored file is corrupt, say so and keep the screen alive.
    (st.stop() is not an Exception, so the no-names gate still stops the app.)"""
    try:
        return fn(*args)
    except Exception as exc:
        st.warning(f"{label}: could not be read ({type(exc).__name__}).")
        return default


def _norm(text: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")


def _gate_status(value: object) -> str:
    text = str(value).strip().lower()
    if text in _PASS:
        return "Pass"
    if text in _FLAG:
        return "Flag"
    if text in _FAIL:
        return "Fail"
    return "unknown"


def load_quality_log() -> pd.DataFrame | None:
    """Read the quality checks log from relative paths or directly from the project root."""
    possible_paths = [
        Path("releases/ready-data/review/real/quality_checks_log.parquet"),
        Path("ready-data/review/real/quality_checks_log.parquet"),
        Path("review/real/quality_checks_log.parquet"),
        APP_DATA / "real/quality_checks_log.parquet",
        APP_DATA / "quality_checks_log.parquet",
    ]
    for path in possible_paths:
        if path.exists():
            try:
                return pd.read_parquet(path)
            except Exception:
                pass
    return None


def gate_results(log: pd.DataFrame | None) -> dict[str, tuple[str, str]]:
    """{gate key: (Pass | Flag | Fail | unknown, impact/detail text)}; the latest row wins."""
    results: dict[str, tuple[str, str]] = {}
    if log is None:
        return results
    g_col = _find_col(log, ("gate", "check", "check_id", "gate_name", "check_name", "test"))
    s_col = _find_col(log, ("status", "result", "verdict", "outcome", "passed", "state"))
    if g_col is None or s_col is None:
        return results
    d_col = _find_col(log, ("impact_on_indicator", "impact", "detail", "details", "message", "note"))
    t_col = _find_col(log, ("computed_at", "checked_at", "timestamp"))
    ordered = log.sort_values(t_col) if t_col else log
    for _, row in ordered.iterrows():
        name = _norm(row[g_col])
        key = next((k for k, *_ in GATES if name == k or k in name), None)
        if key:
            detail = "" if d_col is None or _missing(row[d_col]) else str(row[d_col])
            results[key] = (_gate_status(row[s_col]), detail)
    return results


def load_facts_count() -> tuple[int, int, str, bool]:
    """(accepted, documented, source label, read from a stored file?).
    Reads a facts register when one exists; otherwise falls back to the figure
    documented in the spec, and says so. Nothing is invented."""
    register = _load_first(FACTS_FILES)
    if register is not None and not register.empty:
        v_col = _find_col(register, ("verdict", "status", "review_verdict"))
        id_col = _find_col(register, ("record_id",))
        if v_col:
            accepted = (register[v_col].astype(str).str.strip().str.lower()
                        .isin({"accepted", "accept", "ok", "verified", "true", "1"}))
            if id_col:
                accepted &= register[id_col].notna()
            return int(accepted.sum()), len(register), "facts register", True
    return DOCUMENTED_FACTS[0], DOCUMENTED_FACTS[1], "01-specs §12, not recomputed", False


def compute_coverage() -> dict | None:
    """Assessable vs not assessable, per quarter and now, from the stored kpi_values."""
    kpis = load_table(KPI_FILE, TRACK_A)
    if kpis is None or kpis.empty or not {"code", "quarter"} <= set(kpis.columns):
        return None
    k4_col = _find_col(kpis, ("k4", "k4_assessable", "assessable"))
    frame = kpis.copy()
    frame["quarter"] = frame["quarter"].astype(str)
    if k4_col:
        frame["_ok"] = frame[k4_col].map(_as_bool)  # True / False / None (unknown)
    elif "level" in frame.columns:  # fallback: no K4 column, infer from the level
        frame["_ok"] = frame["level"].notna().map(bool)
    else:
        return None
    asof = frame["quarter"].max()
    latest = frame[frame["quarter"] == asof]
    per_quarter = (frame.groupby("quarter")
                   .agg(total=("code", "nunique"),
                        assessable=("_ok", lambda s: int(sum(1 for x in s if x is True))))
                   .reset_index())
    codes = set(latest["code"].astype(str))
    geo = load_boundaries()
    boundary_codes = None if geo is None else {f["properties"]["code"] for f in geo["features"]}
    return {
        "asof": asof, "used_k4": k4_col is not None, "per_quarter": per_quarter,
        "total": len(latest),
        "ok": sum(1 for x in latest["_ok"] if x is True),
        "not_codes": sorted(latest.loc[[x is False for x in latest["_ok"]], "code"].astype(str)),
        "unknown": sum(1 for x in latest["_ok"] if x is None),
        "with_boundary": None if boundary_codes is None else len(codes & boundary_codes),
    }


def _audit_file(rel: str, track: Track) -> dict | None:
    """Non-stopping audit of one stored table (the live gate in load_table stops instead)."""
    # تحديد المسارات المحتملة للملف (سواء داخل app_data أو في مسارات الـ releases الخارجية)
    possible_paths = [
        APP_DATA / rel,
        Path(rel),
        Path("releases/ready-data/review") / rel,
        Path("ready-data/review") / rel,
    ]
    
    path = None
    for p in possible_paths:
        if p.exists():
            path = p
            break

    if path is None or path.suffix.lower() not in (".csv", ".parquet"):
        return None
        
    generated = is_generated_path(rel)
    if generated and not track.generated:
        return None  # separation: never opened in Track A
        
    df = _read_file(str(path))
    name_cols = [c for c in df.columns if str(c).lower() in FORBIDDEN_COLUMNS]
    bad = 0
    for col in df.columns:
        if str(col).lower() in CODE_COLUMNS:
            values = df[col].dropna().astype(str)
            bad += int((~values.str.match(CODE_PATTERN)).sum())
    stray = []
    if not generated:
        stray = sorted(c for c in df.columns if str(c).lower() in GENERATED_COLUMN_HINTS)
        origin = _find_col(df, ("origin",))
        if origin and df[origin].astype(str).str.lower().str.contains("generated").any():
            stray.append("origin = generated")
    ok = bad == 0 and not stray
    return {"File": rel, "Zone": f"{ORIGIN_GENERATED} generated" if generated else "real / derived",
            "Name-like columns dropped": len(name_cols), "Non-code values": bad,
            "Generated content in a real table": ", ".join(stray) if stray else "none",
            "Result": "✅ Pass" if ok else "⛔ Fail"}


def separation_guard_holds() -> bool:
    """Live self-test: opening a generated table as Track A must be refused."""
    try:
        load_table(PREDICTIONS_FILE, TRACK_A)
    except PermissionError:
        return True
    return False


# ---- screen 4 renderers ----------------------------------------------------- #

def render_trust_tiles(cov: dict | None, results: dict, log: pd.DataFrame | None,
                       facts: tuple[int, int, str, bool]) -> None:
    section_title("📊", "Trust at a glance")
    tiles = st.columns(4)

    with tiles[0]:
        if not results:
            metric_tile("Quality gates", "unknown", "",
                        "waiting for real/quality_checks_log (hand-off from ahmed, D3)",
                        "n/a", ORIGIN_DERIVED)
        else:
            n_pass = sum(1 for s, _ in results.values() if s == "Pass")
            n_flag = sum(1 for s, _ in results.values() if s == "Flag")
            n_fail = sum(1 for s, _ in results.values() if s == "Fail")
            run_col = _find_col(log, ("run_id",)) if log is not None else None
            run = str(log[run_col].iloc[-1]) if run_col else "stored log"
            metric_tile("Quality gates passed", f"{n_pass} of {len(GATES)}", "",
                        f"{len(results)} reported · {n_flag} flagged · {n_fail} failed",
                        run, ORIGIN_DERIVED)

    with tiles[1]:
        if cov is None:
            metric_tile("Assessable", "unknown", "", "waiting for real/kpi_values.parquet",
                        "n/a", ORIGIN_DERIVED)
        else:
            metric_tile("Assessable compounds", f"{cov['ok']} of {cov['total']}", "",
                        "K4 passed: at least 6 images and a reviewed boundary",
                        cov["asof"], ORIGIN_DERIVED)

    with tiles[2]:
        if cov is None:
            metric_tile("Not assessable", "unknown", "", "waiting for real/kpi_values.parquet",
                        "n/a", ORIGIN_DERIVED)
        else:
            extra = f" · {cov['unknown']} unknown" if cov["unknown"] else ""
            metric_tile("Not assessable compounds", f"{len(cov['not_codes'])} of {cov['total']}", "",
                        f"K4 failed: fix location/images first{extra}", cov["asof"], ORIGIN_DERIVED)

    with tiles[3]:
        accepted, documented, source, _ = facts
        metric_tile("Facts verified", f"{accepted:,} of {documented:,}", "",
                    f"documented facts with a record_id and an accepted verdict · "
                    f"{documented - accepted:,} excluded", source, ORIGIN_REAL)

    if not facts[3]:
        st.caption("ℹ️ Facts counter: no facts register file found in app_data/real/, so the "
                   "figure documented in 01-specs §12 is shown (not recomputed). It switches to "
                   "the stored register automatically once one exists.")


def render_gates_table(results: dict, log: pd.DataFrame | None) -> None:
    section_title("🚦", "Quality gates")
    rows = []
    for key, dimension, rule, owner, on_fail in GATES:
        status, detail = results.get(key, ("unknown", ""))
        rows.append({"Gate": key, "Dimension": dimension, "Rule": rule, "Owner": owner,
                     "If it fails": on_fail, "Result": STATUS_WORD[status], "Impact on indicator": detail})
    table = pd.DataFrame(rows)
    if not results:
        table = table.drop(columns=["Impact on indicator"])
    with st.container(border=True):
        if log is None:
            st.info("Waiting for real/quality_checks_log (hand-off from ahmed, D3): "
                    "the gates and rules are listed, results appear once the log exists.")
        st.dataframe(table, use_container_width=True, hide_index=True, column_config={
            "Gate": st.column_config.TextColumn(width="small"),
            "Dimension": st.column_config.TextColumn(width="small"),
            "Rule": st.column_config.TextColumn(width="large"),
            "Owner": st.column_config.TextColumn(width="small"),
            "If it fails": st.column_config.TextColumn(width="medium"),
            "Result": st.column_config.TextColumn(width="small"),
            "Impact on indicator": st.column_config.TextColumn(width="medium"),
        })
        st.caption(f"{ORIGIN_DERIVED} derived from the stored quality log · owners are roles · "
                   "'not in log' = the pipeline has not reported that gate yet")


def render_coverage(cov: dict | None) -> None:
    section_title("🛰️", "Coverage and not assessable")
    with st.container(border=True):
        if cov is None:
            st.info("Waiting for real/kpi_values.parquet (needs code, quarter and K4 or level).")
            return

        per_q = cov["per_quarter"]
        top = int(per_q["total"].max())
        chart = alt.Chart(per_q).mark_bar(color="#38BDF8").encode(
            x=alt.X("quarter:N", sort=list(per_q["quarter"]), title=None,
                    axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("assessable:Q", title=f"assessable compounds (of {top})",
                    scale=alt.Scale(domain=[0, top])),  # axis starts at 0 and ends at the total
            tooltip=["quarter", "assessable", "total"],
        )
        st.altair_chart(chart.properties(height=220), use_container_width=True)
        st.caption(f"{ORIGIN_DERIVED} derived · each bar = compounds assessable in that quarter, "
                   "out of the compounds on file that quarter · a change in coverage is shown, "
                   "never hidden")

        if cov["not_codes"]:
            codes = ", ".join(f"`{c}`" for c in cov["not_codes"])
            st.markdown(f"**Not assessable in {cov['asof']}:** {codes} · "
                        f"{len(cov['not_codes'])} of {cov['total']} compounds. "
                        "Action: fix location/images first. They stay grey on the map.")
        else:
            st.markdown(f"**All {cov['total']} compounds are assessable in {cov['asof']}.**")
        if cov["unknown"]:
            st.caption(f"{cov['unknown']} compound(s) have no K4 value: counted as unknown, "
                       "never as assessable.")
        if cov["with_boundary"] is not None:
            st.caption(f"Reviewed boundary on file for {cov['with_boundary']} of "
                       f"{cov['total']} compounds.")
        if not cov["used_k4"]:
            st.caption("K4 column not found: assessability is inferred from the level (a missing "
                       "level counts as not assessable).")


def render_dashboard_audit(track: Track) -> None:
    section_title("🔒", "Enforced by this dashboard")
    rows, missing = [], 0
    for rel in (*AUDIT_REAL_FILES, *(AUDIT_GENERATED_FILES if track.generated else ())):
        row = _safe(rel, _audit_file, rel, track)
        if row is None:
            missing += 1
        else:
            rows.append(row)
    guard = separation_guard_holds()

    with st.container(border=True):
        st.markdown(
            f"**no_names** · name-like columns are dropped on load and a non-code value in a code "
            f"column stops the screen ({len(FORBIDDEN_COLUMNS)} name-like column names watched).  \n"
            f"**separation** · opening a generated table as Track A is refused: "
            f"{'✅ confirmed just now' if guard else '⛔ NOT refused: fix load_table'}. "
            f"Generated tables load only in Track B, under the orange banner, tagged {ORIGIN_GENERATED}.")
        if rows:
            table = pd.DataFrame(rows)
            st.dataframe(table, use_container_width=True, hide_index=True)
            failed = int((table["Result"] != "✅ Pass").sum())
            st.caption(f"{len(rows)} stored table(s) checked now · {failed} with a finding"
                       + (f" · {missing} not on file yet" if missing else ""))
        else:
            st.info("No stored tables found yet to audit.")
        if not track.generated:
            st.caption("Generated tables are not opened in Track A, so they are not audited here.")


def render_colour_key() -> None:
    section_title("🎨", "Colour key and trust")
    cards = (
        (ORIGIN_REAL, "Real", "as published",
         "Published statements, registers and public records, used as published with their source.",
         "Highest trust. Each fact carries a record_id; still read the date it was published."),
        (ORIGIN_DERIVED, "Derived", "computed from real data",
         "Numbers worked out from real data by a stated rule: activity score A, K2, K4, K6, "
         "priority levels, the height estimate.",
         "As good as its inputs. Read the 'as of' quarter and the gaps; unknown stays unknown."),
        (ORIGIN_GENERATED, "Generated", "stand-in for ACUD data",
         "Simulated finance, complaints, classifier probabilities and scenarios. "
         "'Synthetic - for training only'.",
         "For training and what-if only. Track B only, never on the map, never a statement "
         "about a real compound."),
    )
    cols = st.columns(3)
    for col, (icon, name, short, what, trust) in zip(cols, cards):
        with col, st.container(border=True):
            st.markdown(f"### {icon} {name}")
            st.caption(short)
            st.markdown(what)
            st.markdown(f"**How far to trust.** {trust}")
    with st.container(border=True):
        st.markdown(
            f"**Trust order:** {ORIGIN_REAL} real → {ORIGIN_DERIVED} derived → {ORIGIN_GENERATED} "
            "generated. A figure that mixes origins carries the least trusted tag: K5 is "
            f"{ORIGIN_DERIVED} in months and {ORIGIN_GENERATED} in EGP.  \n"
            "**Reading rules:** a level is always written as a word (colour is never the only cue) · "
            "'unknown' is never shown as 0 · counts are 'n of m' · every tile shows its "
            "'as of' quarter and origin.")


# --------------------------------------------------------------------------- #
# Screens
# --------------------------------------------------------------------------- #

def screen_priority_map(track: Track) -> None:
    page_header("🛰️", "Priority map", "Whom should the committee visit first?")
    latest = load_latest_kpis()
    render_map_slot(track, latest)
    render_cycle_list(latest)

    if track.generated:
        section_title("🧠", "Classifier probabilities")
        preds = load_table("ml/predictions.parquet", track)
        if preds is None:
            st.info("Waiting for ml/predictions.parquet.")
        else:
            st.dataframe(tag_generated_columns(preds.head(10)),
                         use_container_width=True, hide_index=True)


def screen_compound_file(track: Track) -> None:
    page_header("🗂️", "Compound file", "Why this one? Evidence behind the priority level.")

    latest = load_latest_kpis()
    if latest is None:
        st.info("Waiting for real/kpi_values.parquet.")
    else:
        latest_df, asof = latest
        codes = sorted(latest_df["code"].dropna().astype(str).unique())
        levels = dict(zip(latest_df["code"], latest_df["level"]))

        default = 0
        if "cycle_rank" in latest_df.columns:
            ranked = latest_df.dropna(subset=["cycle_rank"]).sort_values("cycle_rank")
            if not ranked.empty and str(ranked.iloc[0]["code"]) in codes:
                default = codes.index(str(ranked.iloc[0]["code"]))

        pick, _ = st.columns([1, 2])
        code = pick.selectbox(
            "Compound", codes, index=default, key="compound_code",
            format_func=lambda c: f"{c} · {level_word(levels.get(c))}",
        )

        history = load_kpi_history(code)
        now = latest_df[latest_df["code"] == code]
        row = now.iloc[0] if not now.empty else None
        ann = load_announcements(code, asof)

        if row is None:
            st.warning(f"{code} has no KPI row for {asof}: shown as not assessable.")
        reason = None if row is None else row.get("reason_ar")
        if not _missing(reason) and str(reason).strip():
            st.markdown(f"**السبب:** {reason}")

        render_kpi_tiles(row, asof)
        render_lineage(row, asof)
        render_curves(code, history, ann)
        render_context_charts(code)
        render_images(code)
        render_inspection_button(code, asof)
        render_track_b_extras(code, track)

    section_title("📝", "Visit form")
    render_ops_visits_form()


def screen_backtest(track: Track) -> None:
    page_header("⏱️", "Would it have warned?", "Backtest and early-warning evidence.")
    if not track.generated:
        render_backtest_cases()  # Track A: real public cases, frozen clock
        return
    st.info("Real-case backtest (frozen clock): switch to Track A in the sidebar.")
    render_model_metrics(track)  # Track B: generated data only
    render_b_signals(track)


def screen_data_trust(track: Track) -> None:
    page_header("🛡️", "Data trust", "How far can each number be trusted?")
    log = _safe("quality_checks_log", load_quality_log)
    results = gate_results(log)
    cov = _safe("kpi_values", compute_coverage)
    facts = _safe("facts register", load_facts_count,
                  default=(*DOCUMENTED_FACTS, "01-specs §12, not recomputed", False))

    render_trust_tiles(cov, results, log, facts)
    render_gates_table(results, log)
    render_coverage(cov)
    render_dashboard_audit(track)
    render_colour_key()


# --------------------------------------------------------------------------- #
# Screen 5: What if? (twin)  -- T-NA-07
#
# Reads the stored v7 what-if hand-off (never recomputes):
#   real/SpaceEye_R7_READY_DATA_2026-10-31_v7/what_if/<S1|S2|S3>/who_moved_and_why.csv
#   real/SpaceEye_R7_READY_DATA_2026-10-31_v7/tables/current/<S>.parquet  (csv/current/<S>.csv as fallback)
#
# ASSUMPTIONS (change in one place):
#   * The columns of who_moved_and_why.csv are not documented here, so they are found by
#     tolerant aliases (WHATIF_ALIASES). Whatever the file holds is also shown unchanged
#     in the full table, so nothing is hidden if an alias misses.
#   * If a newer release folder (..._v8) is dropped in, the newest SpaceEye_R7_READY_DATA_*
#     folder that holds the file is used.
#   * Both folders are generated content. is_generated_path() treats them as generated,
#     so Track A refuses them even though they sit under real/.
#   * Scenario names come from the spec (section 9): S1 dollar shock, S2 collections drop,
#     S3 inspection capacity N ± 2 (re-rank only).
# --------------------------------------------------------------------------- #

WHATIF_RELEASE = "real/SpaceEye_R7_READY_DATA_2026-10-31_v7"
WHATIF_RELEASE_GLOB = "real/SpaceEye_R7_READY_DATA_*"
WHATIF_SCENARIOS = ("S1", "S2", "S3")
SCENARIO_NOTES = {
    "S1": "Dollar shock · USD/EGP +30%",
    "S2": "Collections drop · buyer payments −25% for 6 months",
    "S3": "Inspection capacity · N ± 2 (re-rank only, no generator re-run)",
}
WHATIF_ALIASES = {
    "code": ("code", "compound_code", "compound"),
    "before": ("level_base", "base_level", "baseline_level", "level_baseline", "level_before",
               "before_level", "before", "from_level", "level_from", "old_level", "level"),
    "after": ("level_scenario", "scenario_level", "level_after", "after_level", "after",
              "to_level", "level_to", "new_level"),
    "moved": ("selection_changed", "moved", "changed", "level_changed", "moves", "did_move"),  # <-- التعديل هنا
    "reason": ("reason", "why", "reason_text", "reason_en", "reason_ar", "explanation"),
}
LEVEL_NUMBER = {word.lower(): n for n, (word, _) in LEVELS.items()}   # word -> 1..4 (1 = most urgent)
MAX_MOVED_CARDS = 25


def _whatif_rel(scenario: str, tail: str) -> str | None:
    """Path (relative to the data folder) of a stored what-if file, newest release first."""
    candidates = [f"{WHATIF_RELEASE}/{tail.format(s=scenario)}"]
    releases = sorted(p.name for p in (APP_DATA / "real").glob("SpaceEye_R7_READY_DATA_*") if p.is_dir()) \
        if (APP_DATA / "real").exists() else []
    candidates += [f"real/{name}/{tail.format(s=scenario)}" for name in reversed(releases)]
    return next((c for c in candidates if (APP_DATA / c).exists()), None)


def _whatif_load(scenario: str, track: Track) -> dict:
    """All stored pieces for one scenario. Each load is isolated (one bad file never blanks the screen)."""
    out: dict = {"moved": None, "moved_rel": None, "table": None, "table_rel": None}
    rel = _whatif_rel(scenario, "what_if/{s}/who_moved_and_why.csv")
    if rel:
        out["moved_rel"] = rel
        out["moved"] = _safe(f"what_if/{scenario}/who_moved_and_why.csv", load_table, rel, track)
    for tail in ("tables/current/{s}.parquet", "csv/current/{s}.csv"):
        rel = _whatif_rel(scenario, tail)
        if rel:
            out["table_rel"] = rel
            out["table"] = _safe(f"{tail.format(s=scenario)}", load_table, rel, track)
            if out["table"] is not None:
                break
    return out


def _level_text(value: object) -> str:
    """A level always as a word. Unknown stays 'unknown' (never 0)."""
    if _missing(value) or str(value).strip() == "":
        return "unknown"
    text = str(value).strip()
    if text.lower() in LEVEL_NUMBER:
        return next(w for w, _ in LEVELS.values() if w.lower() == text.lower())
    try:
        number = int(float(text))
    except ValueError:
        return text
    return level_word(number) if number in LEVELS else "unknown"


def _level_number(word: str) -> int | None:
    return LEVEL_NUMBER.get(word.lower())


def _tagged_table(df: pd.DataFrame) -> pd.DataFrame:
    return _tag_numeric_headers(df)


def _prepare_moved(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Standard view of who_moved_and_why: code, before, in scenario, change, reason."""
    cols = {k: _find_col(raw, a) for k, a in WHATIF_ALIASES.items()}
    view = pd.DataFrame({"code": raw[cols["code"]].astype(str)}) if cols["code"] else pd.DataFrame(index=raw.index)
    if cols["before"]:
        view["before"] = raw[cols["before"]].map(_level_text)
    if cols["after"]:
        view["in scenario"] = raw[cols["after"]].map(_level_text)

    def change(i: int) -> str:
        if cols["before"] and cols["after"]:
            b, a = view.iloc[i]["before"], view.iloc[i]["in scenario"]
            nb, na = _level_number(b), _level_number(a)
            if nb is None or na is None:
                return "unknown"
            return "moves up" if na < nb else ("moves down" if na > nb else "unchanged")
        if cols["moved"]:
            flag = _as_bool(raw.iloc[i][cols["moved"]])
            return "unknown" if flag is None else ("changes level" if flag else "unchanged")
        return "listed as moved"   # the file only lists compounds that moved

    view["change"] = [change(i) for i in range(len(raw))]
    view["reason"] = raw[cols["reason"]].fillna("").astype(str) if cols["reason"] else ""
    return view, cols


def _render_whatif_waiting(scenario: str) -> None:
    st.info(
        f"Scenario {scenario} results are not stored yet. Waiting for "
        f"`{WHATIF_RELEASE}/what_if/{scenario}/who_moved_and_why.csv`. "
        "The screen fills in by itself once the file is in the data folder."
    )
    with st.container(border=True):
        st.markdown("#### 👀 Preview: what this screen will show")
        st.caption(f"{ORIGIN_GENERATED} expected shape (empty preview, no numbers invented)")
        st.dataframe(pd.DataFrame({"code": pd.Series(dtype="object"), "before": pd.Series(dtype="object"),
                                   "in scenario": pd.Series(dtype="object"),
                                   "change": pd.Series(dtype="object"), "reason": pd.Series(dtype="object")}),
                     use_container_width=True, hide_index=True)


def render_scenario_picker() -> str:
    section_title("🎛️", "Choose a scenario")
    with st.container(border=True):
        chosen = st.radio("Scenario", WHATIF_SCENARIOS, horizontal=True, key="whatif_scenario",
                          label_visibility="collapsed")
        st.caption(f"{ORIGIN_GENERATED} {SCENARIO_NOTES.get(chosen, '')} · hypothetical, "
                   "the base run is never overwritten")
    return chosen


def render_whatif_tiles(view: pd.DataFrame, total: int | None, asof: str) -> None:
    changed = view[view["change"].isin(["moves up", "moves down", "changes level", "listed as moved"])]
    n, up, down = len(changed), int((view["change"] == "moves up").sum()), int((view["change"] == "moves down").sum())
    unknown = int((view["change"] == "unknown").sum())
    of = f"{n} of {total}" if total else f"{n}"
    with_reason = int((changed["reason"].str.strip() != "").sum())
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_tile("Change level", of, "", "compounds whose level changes"
                    + (f" · {unknown} unknown" if unknown else "") + ("" if total else " · total not stored"),
                    asof, ORIGIN_GENERATED)
    directed = bool(view["change"].isin(["moves up", "moves down", "unchanged"]).any())
    with c2:
        metric_tile("Move up", f"{up} of {n}" if directed else "unknown", "",
                    "more urgent than in the base run" if directed else "direction not in the stored file",
                    asof, ORIGIN_GENERATED)
    with c3:
        metric_tile("Move down", f"{down} of {n}" if directed else "unknown", "",
                    "less urgent than in the base run" if directed else "direction not in the stored file",
                    asof, ORIGIN_GENERATED)
    with c4:
        metric_tile("With a reason", f"{with_reason} of {n}", "", "changed compounds that carry a reason",
                    asof, ORIGIN_GENERATED)


def render_whatif_moved(view: pd.DataFrame) -> None:
    section_title("🔀", "Who changes level, and why")
    with st.container(border=True):
        changed = view[view["change"].isin(["moves up", "moves down", "changes level", "listed as moved"])]
        if changed.empty:
            st.info("No compound changes level in this scenario.")
            return
        arrow = {"moves up": "▲", "moves down": "▼"}
        color = {"moves up": "#F87171", "moves down": "#34D399"}   # up = more urgent = red
        rows = []
        for _, r in changed.head(MAX_MOVED_CARDS).iterrows():
            path = (f'{html.escape(r["before"])} → <b>{html.escape(r["in scenario"])}</b>'
                    if "before" in r and "in scenario" in r else html.escape(r["change"]))
            why = html.escape(r["reason"]) if r["reason"].strip() else '<i style="color:#8A9BB8">no reason stored</i>'
            c = color.get(r["change"], PALETTE["muted"])
            rows.append(
                f'<div style="padding:10px 0;border-bottom:1px solid {PALETTE["border"]}">'
                f'<span style="color:{c};font-weight:700">{arrow.get(r["change"], "●")} '
                f'{html.escape(str(r.get("code", "")))}</span> &nbsp;·&nbsp; {path}'
                f'<div dir="auto" style="color:{PALETTE["muted"]};margin-top:4px">{why}</div></div>')
        st.markdown("".join(rows), unsafe_allow_html=True)
        extra = len(changed) - MAX_MOVED_CARDS
        st.caption(f"{ORIGIN_GENERATED} ▲ moves up = more urgent to inspect · ▼ moves down = less urgent"
                   + (f" · {extra} more in the table below" if extra > 0 else ""))


def render_whatif_table(raw: pd.DataFrame, view: pd.DataFrame, scenario: str) -> None:
    section_title("📋", "Full table as stored")
    with st.container(border=True):
        st.dataframe(_tagged_table(raw), use_container_width=True, hide_index=True)
        st.caption(f"{ORIGIN_GENERATED} every column of who_moved_and_why.csv for {scenario}, unchanged")
        st.download_button("⬇️ Download this scenario (CSV)",
                           data=view.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"who_moved_{scenario}.csv", mime="text/csv", key="whatif_download")


def render_whatif_result_table(table: pd.DataFrame | None, scenario: str) -> None:
    if table is None:
        return
    with st.expander(f"Scenario {scenario} result table ({len(table):,} rows)"):
        st.dataframe(_tagged_table(table.head(500)), use_container_width=True, hide_index=True)
        st.caption(f"{ORIGIN_GENERATED} stored result of the scenario run"
                   + (" · first 500 rows shown" if len(table) > 500 else ""))


def screen_what_if(track: Track) -> None:
    page_header("🧪", "What if?", "Compound-level twin: who moves up if conditions change?")
    if not track.generated:
        st.warning(
            "Scenarios use generated data. Switch to Track B in the sidebar to open them."
        )
        return
    # No map on this screen by design: generated numbers never sit on the real map.

    scenario = render_scenario_picker()
    stored = _whatif_load(scenario, track)
    raw = stored["moved"]
    if raw is None:
        _render_whatif_waiting(scenario)
        render_whatif_result_table(stored["table"], scenario)
        return
    if raw.empty:
        st.info(f"Scenario {scenario}: who_moved_and_why.csv is stored but has no rows.")
        return

    view, cols = _prepare_moved(raw)
    if not cols["code"]:
        st.warning("who_moved_and_why.csv has no compound code column, so it cannot be shown by compound.")
        render_whatif_table(raw, view, scenario)
        return
    if not (cols["before"] and cols["after"] or cols["moved"]):
        st.caption("Level before/after columns were not recognised: every row is treated as a compound that moved.")

    table = stored["table"]
    total = None
    if table is not None:
        code_col = _find_col(table, WHATIF_ALIASES["code"])
        total = int(table[code_col].nunique()) if code_col else None
    elif cols["before"] and cols["after"]:
        total = len(view)
    asof = _find_col(raw, ("as_of", "asof", "quarter", "cutoff"))
    asof_text = str(raw[asof].dropna().astype(str).max()) if asof and raw[asof].notna().any() else "unknown"

    render_whatif_tiles(view, total, asof_text)
    render_whatif_moved(view)
    render_whatif_table(raw, view, scenario)
    render_whatif_result_table(table, scenario)
    st.caption(f"{ORIGIN_GENERATED} {BANNER_TEXT}. Hypothetical interventions on generated data: "
               "they show who would move up in priority, not what will happen.")


SCREEN_FUNCTIONS = {
    SCREENS[0]: screen_priority_map,
    SCREENS[1]: screen_compound_file,
    SCREENS[2]: screen_backtest,
    SCREENS[3]: screen_data_trust,
    SCREENS[4]: screen_what_if,
}


# --------------------------------------------------------------------------- #
# Sidebar + entry point
# --------------------------------------------------------------------------- #

def render_sidebar() -> tuple[Track, str]:
    st.sidebar.markdown(
        """
        <div class="se-brand">
          <div class="se-brand-logo">🛰️</div>
          <div><div class="se-brand-name">SpaceEye</div>
          <div class="se-brand-sub">R7 · Observatory</div></div>
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
    else:
        st.sidebar.markdown(
            f'<span class="se-pill se-pill-a">{ORIGIN_REAL} REAL · {ORIGIN_DERIVED} DERIVED</span>',
            unsafe_allow_html=True,
        )
        st.sidebar.caption("Public and derived data only")
    st.sidebar.caption("🔒 Codes only: no compound or developer names.")
    return track, screen


def render_floating_chat_button() -> None:
    """Render a floating shortcut to the SpaceEye Hybrid RAG chatbot."""
    st.markdown(
        '<a href="http://127.0.0.1:8001/" target="_blank" '
        'rel="noopener noreferrer" class="se-floating-chat" '
        'title="Open SpaceEye AI Assistant" '
        'aria-label="Open SpaceEye AI Assistant">'
        '<span>💬</span></a>',
        unsafe_allow_html=True,
    )

def main() -> None:
    st.set_page_config(
        page_title="SpaceEye · R7 Observatory",
        page_icon="🛰️",
        layout="wide",
    )
    inject_css()
    render_floating_chat_button()
    track, screen = render_sidebar()
    render_banner(track)
    SCREEN_FUNCTIONS[screen](track)


if __name__ == "__main__":
    main()