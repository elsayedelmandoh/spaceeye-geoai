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
    "bg": "#0E2235",          # survey plate: deep blueprint blue
    "bg_alt": "#0B1C2C",      # sidebar
    "surface": "#13304A",     # cards
    "surface_hi": "#1A3D5C",  # hover / inputs
    "border": "#2B4E6E",      # ruled lines
    "text": "#E9EFF5",
    "muted": "#9DB3C8",
    "accent": "#F2C14E",      # surveyor's chalk: Track A
    "accent_b": "#F28C38",    # generated data: Track B
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


def finding(text: str) -> None:
    """The screen's main finding in one plain sentence, built from the stored data."""
    st.markdown(f'<div class="se-finding">{text}</div>', unsafe_allow_html=True)


def how_to_read(points: list[str]) -> None:
    """Short reading guide, folded so it does not compete with the data."""
    with st.expander("How to read this screen"):
        st.markdown("\n".join(f"- {point}" for point in points))


def inject_css() -> None:
    """Survey-plate theme: flat ruled cards on blueprint blue, one type family for Arabic and Latin,
    tabular figures for numbers. The 3D priority map is the one bold element."""
    p = PALETTE
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
        html, body, [class*="css"], .stApp, button, input, textarea {{
            font-family: 'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, sans-serif;
        }}
        .stApp {{ background: {p['bg']}; color: {p['text']}; }}
        .block-container {{ padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1240px; }}
        header[data-testid="stHeader"] {{ background: transparent; }}
        #MainMenu, footer {{ visibility: hidden; }}
        h1, h2, h3, h4, p, label, span, li {{ color: {p['text']}; }}
        p, li {{ line-height: 1.6; }}
        [data-testid="stCaptionContainer"], .stCaption {{ color: {p['muted']} !important; }}
        hr {{ border-color: {p['border']}; }}
        :focus-visible {{ outline: 2px solid {p['accent']} !important; outline-offset: 2px; }}

        .se-header {{ display: flex; align-items: baseline; gap: 0.8rem; margin: 0 0 1.2rem 0;
                      padding-bottom: 0.8rem; border-bottom: 1px solid {p['border']}; }}
        .se-icon {{ font-size: 1.4rem; }}
        .se-title {{ font-size: 1.9rem; font-weight: 700; letter-spacing: -0.015em; line-height: 1.15; }}
        .se-sub {{ color: {p['muted']}; font-size: 1rem; margin-top: 0.2rem; }}
        .se-finding {{ border-left: 4px solid {p['accent']}; background: {p['surface']};
                       padding: 0.8rem 1rem; margin: 0 0 1rem 0; font-size: 1.08rem; line-height: 1.55; }}
        .se-section {{ color: {p['text']}; font-size: 1.02rem; font-weight: 600; margin: 1.3rem 0 0.5rem 0; }}

        [data-testid="stHorizontalBlock"] > div {{ display: flex; flex-direction: column; }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: {p['surface']};
            border: 1px solid {p['border']} !important;
            border-radius: 6px;
            padding: 0.45rem 0.65rem;
            height: 100% !important;
        }}
        [data-testid="stMetric"] {{ padding: 0.1rem 0.2rem; }}
        [data-testid="stMetricLabel"] p {{
            color: {p['muted']} !important; font-size: 0.86rem !important; font-weight: 500;
            white-space: normal !important;
        }}
        [data-testid="stMetricValue"] div {{
            font-variant-numeric: tabular-nums lining-nums;
            font-weight: 700; color: {p['text']};
            font-size: clamp(1.15rem, 1.6vw, 1.6rem) !important;
            white-space: normal !important; line-height: 1.25 !important;
        }}
        [data-testid="stAlert"] {{
            background: {p['bg_alt']}; border: 1px solid {p['border']};
            border-left: 3px solid {p['accent']}; border-radius: 4px; color: {p['text']};
        }}
        [data-testid="stAlert"] p {{ color: {p['text']}; }}
        [data-testid="stDataFrame"] {{ border: 1px solid {p['border']}; border-radius: 4px; }}
        [dir="auto"], .se-rtl {{ unicode-bidi: plaintext; }}
        .se-rtl {{ direction: rtl; text-align: right; font-size: 1.05rem; }}

        [data-testid="stSidebar"] {{ background: {p['bg_alt']}; border-right: 1px solid {p['border']}; }}
        [data-testid="stSidebar"] .block-container {{ padding-top: 1rem; }}
        [data-testid="stSidebar"] hr {{ margin: 0.9rem 0; border-color: {p['border']}; }}
        .se-brand {{ display: flex; align-items: center; gap: 0.6rem; margin: 0.2rem 0 0.3rem 0; }}
        .se-brand-logo {{ font-size: 1.4rem; }}
        .se-brand-name {{ font-weight: 700; font-size: 1.15rem; }}
        .se-brand-sub {{ color: {p['muted']}; font-size: 0.85rem; }}
        .se-side-label {{ color: {p['muted']}; font-size: 0.85rem; font-weight: 500; margin: 0.2rem 0 0.1rem 0; }}
        [data-testid="stSidebar"] [data-baseweb="select"] > div {{
            background: {p['surface']}; border: 1px solid {p['border']}; border-radius: 4px;
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] * {{ color: {p['text']}; }}
        [data-testid="stSidebar"] [role="radiogroup"] label {{
            border-left: 3px solid transparent; padding: 0.4rem 0.6rem; width: 100%;
        }}
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
            border-left-color: {p['accent']}; background: {p['surface']};
        }}
        .se-pill {{
            display: inline-block; padding: 0.15rem 0.6rem; border-radius: 999px;
            font-size: 0.85rem; font-weight: 500; border: 1px solid {p['border']};
        }}
        .se-pill-a {{ color: {p['accent']}; border-color: {p['accent']}; }}
        .se-pill-b {{ color: {p['accent_b']}; border-color: {p['accent_b']}; }}
        .se-move {{ padding: 0.6rem 0; border-bottom: 1px solid {p['border']}; }}
        .se-move-why {{ color: {p['muted']}; margin-top: 0.25rem; }}
        .synthetic-banner {{
            position: sticky; top: 0.5rem; z-index: 1000;
            display: flex; align-items: center; justify-content: center; gap: 0.6rem;
            margin: 0 0 1.2rem 0; padding: 0.6rem 1rem;
            background: {p['accent_b']}; color: #1F1102; font-weight: 700; font-size: 1rem;
            border-radius: 4px;
        }}
        .synthetic-banner .dot {{ width: 8px; height: 8px; border-radius: 50%; background: #1F1102; }}
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
    heights = latest_heights()

    features, points, labels = [], [], []
    counts = {word: 0 for word, _ in [*LEVELS.values(), NOT_ASSESSABLE]}
    for feat in geojson["features"]:
        code = feat["properties"]["code"]
        word, color = _level_style(levels.get(code))
        counts[word] += 1
        outline = _geo_points(feat["geometry"])
        points += outline
        if outline:
            top = heights.get(code, (0.0, 0))[0] * MAP_HEIGHT_EXAGGERATION + 40
            labels.append({"code": code, "position": [sum(x for x, _ in outline) / len(outline),
                                                      sum(y for _, y in outline) / len(outline), top]})
        features.append({
            "type": "Feature",
            "geometry": feat["geometry"],
            "properties": {"code": code, "level_word": word,
                           "fill_color": _hex_to_rgba(color),
                           # Flat when no height was measured (construction too recent).
                           "elevation": heights.get(code, (0.0, 0))[0],
                           "height_text": (f"mean height {heights[code][0]:.0f} m ({heights[code][1]})"
                                           if code in heights else "no height on file")},
        })

    with st.container(border=True):
        if not features:
            st.info("No R7 boundaries in the file.")
            return
        layer = pdk.Layer(
            "GeoJsonLayer",
            data={"type": "FeatureCollection", "features": features},
            get_fill_color="properties.fill_color",
            get_line_color=[232, 238, 244, 200],
            get_elevation="properties.elevation",
            elevation_scale=MAP_HEIGHT_EXAGGERATION,
            line_width_min_pixels=1,
            stroked=True, filled=True, extruded=True, wireframe=True, pickable=True,
        )
        codes = pdk.Layer("TextLayer", data=labels, get_position="position", get_text="code",
                          get_size=15, get_color=[233, 239, 245, 255], get_alignment_baseline="'bottom'",
                          billboard=True)
        view = pdk.data_utils.compute_view(points, view_proportion=0.9) if points else None
        if view is not None:
            view.pitch, view.bearing = 50, -18
        st.pydeck_chart(
            pdk.Deck(
                layers=[layer, codes],
                initial_view_state=view,
                map_style="dark",
                tooltip={"text": "{code}\n{level_word}\n{height_text}"},
            ),
            use_container_width=True,
        )
        legend = "".join(
            f'<span class="se-pill" style="border-color:{color};margin-right:0.4rem">'
            f'<span style="color:{color}">●</span> {word} · {counts[word]}</span>'
            for word, color in [*LEVELS.values(), NOT_ASSESSABLE]
        )
        st.markdown(legend, unsafe_allow_html=True)
        st.caption(f"{ORIGIN_DERIVED} derived · as of {asof} · colour = priority level, grey = not "
                   "assessable · block height = mean building height (Google Open Buildings, latest "
                   f"year to {MAX_HEIGHT_YEAR}), drawn {MAP_HEIGHT_EXAGGERATION}× taller · "
                   "right-drag to tilt or turn")


def cycle_headline(latest_df: pd.DataFrame, asof: str) -> str:
    """One sentence that states the cycle decision, built only from the stored level and reason."""
    cycle = build_cycle_list(latest_df)
    if cycle.empty:
        return f"No compound needs a visit this cycle ({asof})."
    first = latest_df[latest_df["code"] == cycle.iloc[0]["code"]].iloc[0]
    why = str(first.get("reason", "")).split(": ", 1)[-1].split("; observation")[0]
    eligible = int(latest_df["level"].isin([1, 2, 3]).sum())
    waiting = eligible - len(cycle)
    rest = f" {waiting} more at levels 1-3 wait for the next cycle." if waiting > 0 else ""
    return (f"<b>Visit {', '.join(cycle['code'])} this cycle</b> ({len(cycle)} of {len(latest_df)} "
            f"compounds, {asof}). {cycle.iloc[0]['code']} comes first: {html.escape(why)}.{rest}")


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

# Every K is computed from real inputs (K3 from a published date), so all are derived.
K_ORIGIN = {"A": ORIGIN_DERIVED, "K2": ORIGIN_DERIVED, "K3": ORIGIN_DERIVED,
            "K4": ORIGIN_DERIVED, "K5": ORIGIN_DERIVED, "K6": ORIGIN_DERIVED}
SERIES_COLORS = {"Activity score A": "#F2C14E", "Dynamic World built probability": "#7FB2DE"}
MARKER_COLOR = "#E9EFF5"


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


def load_images(code: str) -> dict[str, tuple[Path, str]]:
    """Before/after Wayback pair: the installed runtime pair (app_data/images) first, then the
    figures committed in the repo (data/imagery/figures). Capture dates come from each folder's index."""
    found: dict[str, tuple[Path, str]] = {}
    for folder, index_name in ((APP_DATA / "images", "images.csv"), (IMAGERY_DIR / "figures", "index.csv")):
        index_path = folder / index_name
        index = pd.read_csv(index_path) if index_path.exists() else None
        role_col = None if index is None else _find_col(index, ("role", "image_type"))
        for kind in ("before", "after"):
            path = folder / f"{code}_{kind}.jpg"
            if kind in found or not path.exists():
                continue
            captured, credit = "capture date n/a", "Esri World Imagery Wayback"
            if index is not None and role_col and "code" in index.columns:
                hit = index[(index["code"].astype(str) == code) & (index[role_col] == kind)]
                if not hit.empty:
                    row = hit.iloc[0]
                    if not _missing(row.get("capture_date")):
                        captured = f"captured {row['capture_date']}"
                    if not _missing(row.get("attribution")):
                        credit = str(row["attribution"])
            found[kind] = (path, f"{kind.capitalize()} · {captured} · {credit}")
    return found


def find_inspection_file(code: str, asof: str) -> Path | None:
    for files_dir in FILES_DIRS:
        for pattern in (f"{code}_{asof}.html", f"{code}_{asof}_*.html", f"{code}_*.html"):
            matches = sorted(files_dir.glob(pattern))
            if matches:
                return matches[-1]
    return None


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
                  "counted after the start: 4 active quarters or a published launch", asof, K_ORIGIN["K2"])
    with tiles[2]:
        _kpi_tile("K3 handover clock", get("K3"), "months",
                  "since first announced handover date", asof, K_ORIGIN["K3"])
    with tiles[3]:
        if _missing(get("K6")) and get("K6_status") == "not_applicable_started":
            metric_tile("K6 never started", "does not apply", "",
                        "construction start was observed", asof, K_ORIGIN["K6"])
        else:
            _kpi_tile("K6 never started", get("K6"), "months",
                      "since first launch/promise, no construction start", asof, K_ORIGIN["K6"])

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


def render_curves(code: str, history: pd.DataFrame | None, ann: pd.DataFrame | None,
                  row: pd.Series | None) -> None:
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

        # The same first deadline that K3 counts from (kpi_values.k3_first_deadline).
        first = None if row is None else row.get("k3_first_deadline")
        if not _missing(first):
            st.markdown(f"📌 **First announced handover date:** {pd.Timestamp(first):%b %Y} "
                        "(the date K3 counts from)")
        else:
            st.caption("📌 No announced handover date on file for this compound yet.")
        st.caption(f"{ORIGIN_DERIVED} derived · gaps = quarters not assessable · "
                   "dashed lines = quarter of a published developer statement")


STAGE_TABLE = REPO_DIR / "data" / "experiments" / "42_r7_stage_table" / "r7_stage_table.csv"
STAGE_WORDS = {"S0": "land or ground works", "S1": "under construction", "S2": "complete"}


def render_stage_strip(code: str) -> None:
    """Construction stage per year, read from the stored stage table (experiment 42)."""
    section_title("🏗️", "Construction stage by year")
    with st.container(border=True):
        if not STAGE_TABLE.exists():
            st.info("The stage table (data/experiments/42_r7_stage_table) is not in this checkout.")
            return
        table = enforce_no_names(_read_file(str(STAGE_TABLE)), "r7_stage_table.csv")
        mine = table.loc[table["code"] == code, ["year", "stage", "stage_source"]].copy()
        if mine.empty:
            st.info(f"No stage rows for {code}.")
            return
        mine["meaning"] = mine["stage"].map(STAGE_WORDS)
        chart = alt.Chart(mine).mark_rect(stroke=PALETTE["bg"], strokeWidth=2).encode(
            x=alt.X("year:O", title=None),
            color=alt.Color("meaning:N", title=None, legend=alt.Legend(orient="bottom"),
                            scale=alt.Scale(domain=list(STAGE_WORDS.values()),
                                            range=["#8A7A5C", PALETTE["accent"], "#46A758"])),
            tooltip=["year", "stage", "meaning", "stage_source"],
        )
        st.altair_chart(chart.properties(height=70), use_container_width=True)
        start = mine.loc[mine["stage"] != "S0", "year"]
        st.caption(f"{ORIGIN_DERIVED} derived · construction first seen in "
                   f"{int(start.min()) if not start.empty else 'no year yet'} · stages labelled by an AI "
                   "rater from Wayback figures, without a site visit · years without a figure use the "
                   "satellite and radar layer, which never marks a compound complete")


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
                            color=alt.value("#7FB2DE"),
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


def render_space_timeline(code: str) -> None:
    """The compound seen from space: one large frame chosen on a date slider, and the strip of all frames."""
    frames = space_frames(code)
    if not frames:
        render_images(code)
        return
    section_title("🛰️", "Seen from space")
    stages = stage_of_year(code)
    with st.container(border=True):
        dates = [date for date, _ in frames]
        chosen = st.select_slider("Capture date", options=dates, value=dates[-1], key=f"frame_{code}")
        stage = stages.get(int(chosen[:4]))
        big, grid = st.columns([3, 2])
        big.image(str(dict(frames)[chosen]), use_container_width=True,
                  caption=f"{code} · captured {chosen}" + (f" · {stage}" if stage else ""))
        with grid:
            for start in range(0, len(frames), 2):
                for col, (date, frame) in zip(st.columns(2), frames[start:start + 2]):
                    label = stages.get(int(date[:4]), "")
                    col.image(str(frame), caption=date + (f" · {label}" if label else ""),
                              use_container_width=True)
        st.caption("Esri World Imagery Wayback, single-capture frames with the same extent and zoom; cyan line = "
                   "reviewed working boundary, not a legal survey. Judged by eye: the images help plan the "
                   "visit, they are not a measurement. Stage words come from the stage table below.")


def render_images(code: str) -> None:
    section_title("🛰️", "Wayback images")
    images = load_images(code)
    with st.container(border=True):
        if not images:
            st.info(f"No Wayback before/after pair for {code} in app_data/images or data/imagery/figures.")
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
# Screen 3 data (T-NA-05): real-case backtest (Track A) + model metrics (Track B)
# --------------------------------------------------------------------------- #

# Frozen-clock backtest of the v7 release (one row per public case, with its explanation).
BACKTEST_DIR = "current/backtest"
METRICS_FILE = "docs/CURRENT_MODEL_METRICS.csv"
MODEL_METADATA_FILE = "docs/CURRENT_MODEL_METADATA.json"



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


def load_ready_json(rel_path: str) -> dict | None:
    path = READY_DATA / rel_path
    if not path.exists():
        return None
    data = _read_json(str(path), path.stat().st_mtime_ns)
    return data if isinstance(data, dict) else None


def _tag_numeric_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Orange tag on the headers of numeric columns of a generated table."""
    return df.rename(columns={c: f"{c} {ORIGIN_GENERATED}" for c in df.columns
                              if pd.api.types.is_numeric_dtype(df[c])})


# ---- Track A: frozen-clock table -------------------------------------------- #

def render_backtest_cases() -> None:
    path = READY_DATA / BACKTEST_DIR / "cases_explained.csv"
    summary = load_ready_json(f"{BACKTEST_DIR}/summary.json")
    if not path.exists() or summary is None:
        st.info(f"Waiting for {BACKTEST_DIR}/cases_explained.csv and summary.json of the v7 release "
                "(run python -m src.pipeline.setup_review).")
        return
    cases = enforce_no_names(_read_file(str(path)), "cases_explained.csv")
    total = summary["n_cases"]
    after_start = summary["after_start_reading"]["n"]
    point_in_time = summary["point_in_time_reading"]["n"]
    met = summary["after_start_reading"]["met"]

    finding(f"<b>The rule warned early in {after_start} of {total} public cases</b> (after construction "
            f"start), and in {point_in_time} of {total} on the freeze date itself. The success criterion "
            f"was {'met' if met else 'not met'}: {html.escape(summary['criterion'])}.")
    how_to_read([
        ("Each case is a real public R7 delay. The clock was frozen before the delay was known, and "
        "only data published by then was used."),
        ("'Warned after start' asks whether level 1 or 2 appeared at least 6 months before the first "
        "announced handover date."),
        "Open a case below for what happened, what the rule saw and the explanation that was tested and rejected.",
    ])
    section_title("🧊", "Frozen-clock backtest (real public cases)")
    tiles = st.columns(3)
    with tiles[0]:
        metric_tile("Warned after construction start", f"{after_start} of {total}", "cases",
                    "level 1-2 at least 6 months before the first announced handover date "
                    "(main reading)", "frozen clock", ORIGIN_DERIVED)
    with tiles[1]:
        metric_tile("Warned at the freeze date", f"{point_in_time} of {total}", "cases",
                    "level 1-2 on the freeze date itself, using only data published by then",
                    "frozen clock", ORIGIN_DERIVED)
    with tiles[2]:
        metric_tile("Success criterion", "Met" if met else "Not met", "",
                    f"{summary['criterion']} · fixed before any computation, not lowered",
                    "frozen clock", ORIGIN_DERIVED)

    table = pd.DataFrame({
        "Case": cases["code"].astype(str),
        "First announced handover": cases["first_deadline"].astype(str),
        "First level 1-2 alert": cases["first_alert_quarter"].fillna("none").astype(str),
        "Months before handover": cases["after_start_months_before"].map(lambda v: _fmt(v, 0)),
        "Warned after start": cases["after_start"].map(lambda v: _yes_no(_as_bool(v))),
        "Level at freeze date": cases["level_at_freeze"].map(_level_text),
        "Warned at freeze date": cases["point_in_time"].map(lambda v: _yes_no(_as_bool(v))),
    })
    with st.container(border=True):
        st.dataframe(table, use_container_width=True, hide_index=True)
        st.caption(f"{ORIGIN_DERIVED} derived from real public cases · counts only, no percentages "
                   "(small sample) · a later alert is not proof that the rule predicts delays")

    section_title("🔎", "Why, case by case")
    for _, r in cases.iterrows():
        with st.expander(f"{r['code']} · warned after start: {_yes_no(_as_bool(r['after_start']))}"):
            for column, heading in (("what_happened", "What happened"), ("this_case", "What the rule saw"),
                                    ("why", "Rule reading"), ("what_next", "What next")):
                if not _missing(r[column]):
                    st.markdown(f"**{heading}.** {r[column]}")
            if not _missing(r["competing_explanation"]):
                st.markdown(f"**Competing explanation.** {r['competing_explanation']} "
                            f"{'' if _missing(r['numeric_check']) else r['numeric_check']}")

    if not met:
        with st.container(border=True):
            st.markdown(
                "**What it means.** The rule catches stalls and passed dates. In the missed cases the "
                "sites looked active, so there was no stall to catch: the rule does not measure pace "
                "against the plan. Early warning of delay needs ACUD's data (supervisor reports, "
                "contractual dates, meters, escrow). The counts alone do not show why a delay happened.")


# ---- Track B: model metrics + B1-B5 ----------------------------------------- #

def render_model_metrics(track: Track) -> None:
    section_title("📐", "Binary classifier on generated data")
    metrics = load_table(METRICS_FILE, track, READY_DATA)  # generated: loaded only in Track B
    if metrics is None or metrics.empty:
        st.info(f"Waiting for {METRICS_FILE} of the v7 release (run python -m src.pipeline.setup_review).")
        return
    test = metrics[metrics["view"] == "time_test"].copy()
    test["n of m"] = [f"{_fmt(n)} of {_fmt(m)}" for n, m in zip(test["numerator"], test["denominator"])]
    test["value"] = test["value"].round(2)

    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown("**Recall per class (time test)**")
        recall = test[test["metric"] == "class_recall"].pivot(index="method", columns="class", values="n of m")
        st.dataframe(tag_generated_columns(recall.reset_index(), skip=("method",)),
                     use_container_width=True, hide_index=True)
    with right, st.container(border=True):
        st.markdown("**Macro-F1, two classes (time test)**")
        f1 = test[test["metric"] == "macro_f1_binary"][["method", "value", "denominator"]]
        f1 = f1.rename(columns={"value": "macro-F1", "denominator": "test rows"})
        st.dataframe(tag_generated_columns(f1, skip=("method",)), use_container_width=True, hide_index=True)

    at_4 = test[test["metric"] == "distressed_recall_at_4"][["method", "value", "n of m"]]
    random = (load_ready_json(MODEL_METADATA_FILE) or {}).get("random_at_4")
    if random:
        at_4 = pd.concat([at_4, pd.DataFrame([{
            "method": "random ranking (mean)", "value": round(random["mean"], 2),
            "n of m": f"{random['draws']:,} draws, range {random['low']:.2f}-{random['high']:.2f}"}])])
    with st.container(border=True):
        st.markdown("**Recall@4 for 'distressed' versus a random ranking (time test)**")
        chart = alt.Chart(at_4).mark_bar().encode(
            x=alt.X("value:Q", title="share of the distressed rows found in the top 4",
                    scale=alt.Scale(domain=[0, 1])),
            y=alt.Y("method:N", title=None, sort="-x"),
            color=alt.condition(alt.datum.method == "random ranking (mean)",
                                alt.value(PALETTE["muted"]), alt.value(PALETTE["accent_b"])),
            tooltip=["method", alt.Tooltip("value:Q", format=".2f"), "n of m"],
        )
        st.altair_chart(chart.properties(height=230), use_container_width=True)
        st.dataframe(tag_generated_columns(at_4, skip=("method",)), use_container_width=True, hide_index=True)

    holdout = metrics[(metrics["view"] == "developer_holdout") & (metrics["metric"] == "class_recall")
                      & (metrics["class"] == "distressed")]
    if not holdout.empty and (holdout["denominator"] == 0).all():
        st.caption("Developer holdout: it holds no 'distressed' row, so recall for that class is undefined there.")
    st.caption(f"{ORIGIN_GENERATED} Generated data: a diagnostic of the generator and model "
               "workflow, not real-world accuracy. The time test holds very few 'distressed' rows, "
               "so one row moves a recall value by a large step. Read the n of m.")


def render_b_signals(track: Track) -> None:
    section_title("🧾", "B1-B5 signals per compound")
    st.info("The v7 release does not store the B1-B5 trigger flags per compound, so they are not "
            "shown here. The model reads their generated inputs; see the training dictionary.")


# --------------------------------------------------------------------------- #
# Screen 4 data (T-NA-06): gates, coverage, facts counter, colour key
# --------------------------------------------------------------------------- #

COMPOUNDS_FILE = "real/compounds.parquet"                                                # contract: ahmed -> nada
STATEMENTS_FILE = "real/statements.parquet"  # published developer statements, one fact per row

# The 10 quality gates of 01-specs section 8 plus the vegetation pull check the pipeline logs:
# key, dimension, rule, owner role, if it fails.
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
    ("veg_pull_check", "Accuracy", "Pulled vegetation share equals the audited file (max diff 0.02)",
     "R3", "Flag"),
    ("no_names", "Privacy", "No compound or developer name in any output file", "R1", "Stop"),
)

_PASS = {"pass", "passed", "ok", "true", "1", "1.0", "yes"}
_FLAG = {"flag", "flagged", "warn", "warning", "stale", "review"}
_FAIL = {"fail", "failed", "false", "0", "0.0", "no", "stop", "stopped", "error"}
STATUS_WORD = {"Pass": "✅ Pass", "Flag": "⚠️ Flag", "Fail": "⛔ Fail", "unknown": "❔ not in log"}

# Dashboard-side audit: which stored tables are checked, and what must never appear in a real one.
AUDIT_REAL_FILES = (KPI_FILE, COMPOUNDS_FILE, "real/statements.parquet", "real/sat_yearly.parquet",
                    "real/sat_quarterly.parquet", "real/quality_checks_log.parquet")
AUDIT_GENERATED_FILES = (PREDICTIONS_FILE, METRICS_FILE, K5_EGP_FILE)
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
    """The quality log installed by setup_review, else the copy committed with the release."""
    for path in (APP_DATA / "real/quality_checks_log.parquet",
                 REPO_DIR / "releases/ready-data/review/real/quality_checks_log.parquet"):
        if path.exists():
            return pd.read_parquet(path)
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


def load_facts_count() -> tuple[int, int] | None:
    """(statements with a record_id and a review verdict, all statements) from the stored table."""
    statements = load_table(STATEMENTS_FILE, TRACK_A)
    if statements is None or not {"record_id", "verdict"} <= set(statements.columns):
        return None
    reviewed = statements["record_id"].notna() & statements["verdict"].notna()
    return int(reviewed.sum()), len(statements)


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
    path = next((root / rel for root in (APP_DATA, READY_DATA) if (root / rel).exists()), None)
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
                       facts: tuple[int, int] | None) -> None:
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
        if facts is None:
            metric_tile("Reviewed statements", "unknown", "", f"waiting for {STATEMENTS_FILE}",
                        "n/a", ORIGIN_REAL)
        else:
            reviewed, total = facts
            metric_tile("Reviewed statements", f"{reviewed:,} of {total:,}", "",
                        f"published statements with a record_id and a review verdict · "
                        f"{total - reviewed:,} without a verdict", "stored table", ORIGIN_REAL)


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
        chart = alt.Chart(per_q).mark_bar(color="#7FB2DE").encode(
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
         ("Numbers worked out from real data by a stated rule: activity score A, K2, K4, K6, "
         "priority levels, the height estimate."),
         "As good as its inputs. Read the 'as of' quarter and the gaps; unknown stays unknown."),
        (ORIGIN_GENERATED, "Generated", "stand-in for ACUD data",
         ("Simulated finance, complaints, classifier probabilities and scenarios. "
         "'Synthetic - for training only'."),
         ("For training and what-if only. Track B only, never on the map, never a statement "
         "about a real compound.")),
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
    if latest is not None:
        finding(cycle_headline(*latest))
    how_to_read([
        ("Each block is one coded R7 compound. Colour is the priority level; height is the mean "
        "building height seen from space."),
        ("The level is the worst of three clocks: K2 quarters without building activity, K3 months "
        "past the first announced handover date, K6 months since launch without a confirmed start."),
        "A compound that may be complete is capped at level 3 and must be confirmed on site.",
        "The cycle list takes up to 4 compounds from levels 1-3. The rule recommends; the committee decides.",
    ])
    render_map_slot(track, latest)
    render_cycle_list(latest)

    if track.generated:
        section_title("🧠", "Classifier probabilities: 'distressed' in the next 6 months")
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
    page_header("🗂️", "Compound file", "Why this one? Evidence behind the priority level.")
    how_to_read([
        "Pick a compound: the default is the first one on the cycle list. The Arabic sentence states why it has its level.",
        "The tiles show the three clocks that set the level; the table below them shows context that never sets it.",
        "The curves show building activity per quarter; dashed lines mark quarters with a published developer statement.",
        "The two Wayback images are judged by eye: they help plan the visit, they are not a measurement.",
        "Record the visit result at the bottom: real visit results are the ground truth this system still lacks.",
    ])

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
            st.markdown(f'<div class="se-rtl"><b>السبب:</b> {html.escape(str(reason))}</div>', unsafe_allow_html=True)

        render_space_timeline(code)
        render_kpi_tiles(row, asof)
        render_lineage(row, asof)
        render_curves(code, history, ann, row)
        render_stage_strip(code)
        render_context_charts(code)
        render_inspection_button(code, asof)
        render_track_b_extras(code, track)

        section_title("📝", "Visit form")
        render_ops_visits_form(codes, code)


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
    facts = _safe("statements", load_facts_count)

    if cov is not None and results:
        n_pass = sum(1 for status, _ in results.values() if status == "Pass")
        n_flag = sum(1 for status, _ in results.values() if status == "Flag")
        finding(f"<b>{cov['ok']} of {cov['total']} compounds can be assessed in {cov['asof']}</b>. "
                f"{n_pass} of {len(GATES)} quality gates passed and {n_flag} raised a flag for review.")
    how_to_read([
        ("Green numbers are published as they are, blue numbers are computed from them by a stated rule, "
        "orange numbers are generated for training only."),
        "A quality gate stops the run or flags it. A flag means a person should look, not that the data is wrong.",
        "A compound without enough images gets no level and stays grey on the map.",
    ])
    render_trust_tiles(cov, results, log, facts)
    render_gates_table(results, log)
    render_coverage(cov)
    render_dashboard_audit(track)
    render_colour_key()


# --------------------------------------------------------------------------- #
# Screen 5: What if? (twin)  -- T-NA-07
#
# Reads the stored v7 what-if hand-off (never recomputes):
#   ready-data/what_if/<S1|S2|S3>/who_moved_and_why.csv  (data/SCENARIO_CONTRACT_CURRENT.md)
# S1/S2: one row per compound and simulated month; the Track B hypothetical level and the
#        capacity-4 selection, baseline versus shock.
# S3:    one row per compound, quarter and capacity variant (2 or 6 versus 4); selection only,
#        levels never change.
# --------------------------------------------------------------------------- #

WHATIF_SCENARIOS = ("S1", "S2", "S3")
SCENARIO_NOTES = {
    "S1": "Cost shock · +30% on the imported cost component (FX-cost proxy)",
    "S2": "Collections drop · buyer payments −25% for six months",
    "S3": "Inspection capacity · 2 or 6 visits instead of 4 (re-rank only)",
}
LEVEL_NUMBER = {word.lower(): n for n, (word, _) in LEVELS.items()}   # word -> 1..4 (1 = most urgent)


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


def _in_list(flag: object) -> str:
    return "on the list" if _as_bool(flag) else "not on the list"


def whatif_view(raw: pd.DataFrame, scenario: str) -> tuple[pd.DataFrame, str]:
    """The latest period of one scenario: one row per compound, baseline versus scenario."""
    period = "quarter" if scenario == "S3" else "month"
    label = str(raw[period].max())
    latest = raw[raw[period].astype(str) == label]
    view = pd.DataFrame({"code": latest["code"].astype(str)})
    if scenario == "S3":
        view["level"] = latest["level"].map(_level_text)
        view["baseline list"] = latest["baseline_selected"].map(_in_list)
        view["list in scenario"] = latest["selected"].map(_in_list)
        view["change"] = [("joins the list" if _as_bool(s) else "leaves the list") if _as_bool(c) else "unchanged"
                          for s, c in zip(latest["selected"], latest["selection_changed"])]
    else:
        # Track B hypothetical levels (generated finance), not the real Track A levels of screen 1.
        view["baseline level (Track B)"] = latest["baseline_hypothetical_level"].map(_level_text)
        view["level in scenario (Track B)"] = latest["hypothetical_level"].map(_level_text)
        view["baseline list"] = latest["baseline_selected"].map(_in_list)
        view["list in scenario"] = latest["selected"].map(_in_list)
        changed = [bool(_as_bool(lv)) or bool(_as_bool(sel))
                   for lv, sel in zip(latest["level_changed"], latest["selection_changed"])]
        view["change"] = ["changes" if c else "unchanged" for c in changed]
    view["reason"] = latest["reason"].fillna("").astype(str)
    return view.reset_index(drop=True), label


def count_changed_rows(raw: pd.DataFrame) -> int:
    """Rows over the whole history whose level or list position differs from the baseline."""
    flags = [raw["selection_changed"]] + ([raw["level_changed"]] if "level_changed" in raw.columns else [])
    return sum(1 for values in zip(*flags) if any(_as_bool(v) for v in values))


def render_scenario_picker() -> tuple[str, str | None]:
    section_title("🎛️", "Choose a scenario")
    with st.container(border=True):
        chosen = st.radio("Scenario", WHATIF_SCENARIOS, horizontal=True, key="whatif_scenario",
                          format_func=lambda s: f"{s} · {SCENARIO_NOTES[s].split(' · ')[0]}",
                          label_visibility="collapsed")
        capacity = None
        if chosen == "S3":
            capacity = st.radio("Visits per cycle", ("capacity_minus_2", "capacity_plus_2"), horizontal=True,
                                key="whatif_capacity",
                                format_func=lambda c: "2 visits" if c.endswith("minus_2") else "6 visits")
        st.caption(f"{ORIGIN_GENERATED} {SCENARIO_NOTES[chosen]} · hypothetical, "
                   "the base run is never overwritten")
    return chosen, capacity


def render_whatif_tiles(raw: pd.DataFrame, view: pd.DataFrame, scenario: str, label: str) -> None:
    period_word = "quarter" if scenario == "S3" else "month"
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_tile("Compounds that change", f"{int((view['change'] != 'unchanged').sum())} of {len(view)}", "",
                    "join or leave the cycle list; levels never change in S3" if scenario == "S3"
                    else "level or cycle list, versus the baseline", label, ORIGIN_GENERATED)
    with c2:
        metric_tile(f"Changes over every {period_word}", f"{count_changed_rows(raw)} of {len(raw)}", "",
                    f"compound-{period_word} rows that differ from the baseline", "whole history",
                    ORIGIN_GENERATED)
    with c3:
        metric_tile("On the list in the scenario", f"{int((view['list in scenario'] == 'on the list').sum())} "
                    f"of {len(view)}", "", "compounds selected for visits", label, ORIGIN_GENERATED)


def render_whatif_moved(view: pd.DataFrame) -> None:
    section_title("🔀", "Who changes, and why")
    with st.container(border=True):
        changed = view[view["change"] != "unchanged"]
        if changed.empty:
            st.info("No compound changes level or list position in this scenario: the shock moves the "
                    "generated finances, but not across a rule threshold.")
            return
        rows = []
        for _, r in changed.iterrows():
            colour = "#34D399" if r["change"] == "leaves the list" else "#F87171"
            rows.append(
                f'<div class="se-move"><span style="color:{colour};font-weight:700">'
                f'{html.escape(r["code"])}</span> · {html.escape(r["change"])}'
                f'<div dir="auto" class="se-move-why">{html.escape(r["reason"])}</div></div>')
        st.markdown("".join(rows), unsafe_allow_html=True)


def screen_what_if(track: Track) -> None:
    page_header("🧪", "What if?", "Compound-level twin: who would change if conditions changed?")
    if not track.generated:
        st.warning("Scenarios use generated data. Switch to Track B in the sidebar to open them.")
        return
    # No map on this screen by design: generated numbers never sit on the real map.

    scenario, capacity = render_scenario_picker()
    rel = f"what_if/{scenario}/who_moved_and_why.csv"
    raw = _safe(rel, load_table, rel, track, READY_DATA)
    if raw is None or raw.empty:
        st.info(f"Scenario {scenario} is not installed: ready-data/{rel} is missing. "
                "Run python -m src.pipeline.setup_review.")
        return
    if capacity:
        raw = raw[raw["scenario_id"] == capacity]

    view, label = whatif_view(raw, scenario)
    moved = view[view["change"] != "unchanged"]
    finding(f"<b>{len(moved)} of {len(view)} compounds change in {scenario}</b> ({label})"
            + (": " + ", ".join(f"{c} {w}" for c, w in zip(moved["code"], moved["change"])) if len(moved) else
               ". The shock moves the generated finances, but no compound crosses a rule threshold")
            + ". Generated data: this shows sensitivity, not a forecast.")
    how_to_read([
        ("S1 and S2 shock the generated finances and re-apply the Track B rule; compare each level with "
        "its own baseline, not with the real levels of screen 1."),
        "S3 keeps every level and only changes how many compounds fit in one cycle (2 or 6 instead of 4).",
        "Nothing here is observed: no new satellite image or field visit enters a scenario.",
    ])
    render_whatif_tiles(raw, view, scenario, label)
    render_whatif_moved(view)
    section_title("📋", f"All compounds in {label}")
    with st.container(border=True):
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download this view (CSV)", data=view.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"what_if_{scenario}_{label}.csv", mime="text/csv", key="whatif_download")
    st.caption(f"{ORIGIN_GENERATED} {BANNER_TEXT}. Hypothetical interventions on generated data: they show "
               f"who would change in priority, not what will happen. Full history in ready-data/{rel}.")


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