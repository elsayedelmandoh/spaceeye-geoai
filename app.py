"""SpaceEye R7 Observatory - Streamlit dashboard (T-NA-01: skeleton + track switch).

Run with:  streamlit run app.py
"""

from __future__ import annotations

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

def is_generated_path(rel_path: str) -> bool:
    return rel_path.replace("\\", "/").startswith(GENERATED_PREFIXES)


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
def _read_file(path_str: str) -> pd.DataFrame:
    path = Path(path_str)
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".json":
        return pd.read_json(path)
    raise ValueError(f"Unsupported file type: {suffix}")


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
def _read_boundaries(path_str: str) -> tuple[dict, list[str]]:
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
    geojson, bad_codes = _read_boundaries(str(path))
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
    st.info("Skeleton page.")


def screen_data_trust(track: Track) -> None:
    page_header("🛡️", "Data trust", "How far can each number be trusted?")
    with st.container(border=True):
        st.markdown(
            f"**Colour key** &nbsp; {ORIGIN_REAL} real · {ORIGIN_DERIVED} derived · "
            f"{ORIGIN_GENERATED} generated"
        )
    st.info("Skeleton page.")


def screen_what_if(track: Track) -> None:
    page_header("🧪", "What if?", "Compound-level twin: who moves up if conditions change?")
    if not track.generated:
        st.warning(
            "Scenarios use generated data. Switch to Track B in the sidebar to open them."
        )
        return
    st.info("Skeleton page.")


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