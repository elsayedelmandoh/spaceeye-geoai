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

from src.dashboard import insights
from src.dashboard.exports import export_csv
from src.dashboard.ops_visits import load_visits, render_ops_visits_form  # T-NA-04
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
    "3 · District view",
    "4 · Digital twin what if",
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
# Presentation helpers (banner, tiles)
# --------------------------------------------------------------------------- #

def metric_tile(label: str, value: object, unit: str, denominator: str,
                as_of: str, origin: str) -> None:
    """One KPI tile = value + unit + denominator + 'as of' + origin (section 9)."""
    with st.container(border=True):
        st.metric(label=f"{origin} {label}", value=f"{value} {unit}".strip())
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
        .se-card-head {{ display: flex; justify-content: space-between; align-items: center;
                         gap: 0.4rem; margin-top: 0.3rem; }}
        .se-card-why {{ color: {p['muted']}; font-size: 0.92rem; line-height: 1.45; margin-top: 0.35rem; }}
        [data-testid="stMetricValue"], [data-testid="stMetricValue"] > div {{ white-space: normal; overflow: visible; text-overflow: clip; line-height: 1.2; }}
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
    wanted =("cycle_rank", "code", "level_word", "reason", "K2", "K3", "K6")
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
            width="stretch",
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
    why = insights.short_reason(first.get("reason"))
    eligible = int(latest_df["level"].isin([1, 2, 3]).sum())
    waiting = eligible - len(cycle)
    rest = f" {waiting} more at levels 1-3 wait for the next cycle." if waiting > 0 else ""
    return (f"<b>Visit {', '.join(cycle['code'])} this cycle</b> ({len(cycle)} of {len(latest_df)} "
            f"compounds, {asof}). {cycle.iloc[0]['code']} comes first: {html.escape(why)}.{rest}")


def load_promises_ahead(latest_df: pd.DataFrame, asof: str) -> list[dict]:
    statements = load_table("real/statements.parquet", TRACK_A)
    if statements is None:
        return []
    return insights.upcoming_promises(statements, list(latest_df["code"].astype(str)), asof)


def render_summary_tiles(latest_df: pd.DataFrame, asof: str, promises: list[dict]) -> None:
    cycle = build_cycle_list(latest_df)
    months = latest_df["K5_months"].dropna() if "K5_months" in latest_df.columns else pd.Series(dtype=float)
    fined = months[months > 0]
    tiles = st.columns(4)
    with tiles[0]:
        metric_tile("To visit this cycle", len(cycle), "compound" if len(cycle) == 1 else "compounds", f"of {len(latest_df)}", asof, ORIGIN_DERIVED)
    with tiles[1]:
        metric_tile("At level 1", int((latest_df["level"] == 1).sum()),
                    "compound" if int((latest_df["level"] == 1).sum()) == 1 else "compounds",
                    f"of {len(latest_df)} assessed compounds", asof,
                    ORIGIN_DERIVED)
    with tiles[2]:
        metric_tile("Fine-eligible months", int(round(fined.sum())), "months",
                    f"in {len(fined)} compounds · the contract decides the fine", asof, ORIGIN_DERIVED)
    with tiles[3]:
        metric_tile("Promised dates ahead", len(promises), "dates",
                    f"in {len({p['code'] for p in promises})} compounds", asof, ORIGIN_DERIVED)


def visit_table(latest_df: pd.DataFrame, cycle: pd.DataFrame) -> pd.DataFrame:
    """The cycle list in visit order with the suggested action and the stored reason."""
    rows = latest_df.set_index("code").loc[cycle["code"]]
    return pd.DataFrame({
        "Rank": range(1, len(rows) + 1),
        "Compound": rows.index,
        "Level": rows["level"].map(level_word).to_numpy(),
        "Suggested action": [insights.suggested_action(r)[0] for _, r in rows.iterrows()],
        "Why": rows["reason"].map(insights.short_reason).to_numpy(),
    })


def render_visit_list(latest: tuple[pd.DataFrame, str] | None, track: Track) -> None:
    section_title("📋", "Visit list")
    if latest is None:
        st.info("Waiting for real/kpi_values.parquet.")
        return

    latest_df, asof = latest
    cycle = build_cycle_list(latest_df)
    if cycle.empty:
        st.info(f"No compounds in the cycle list for {asof}.")
        return

    st.caption("Suggested actions are proposals; the committee decides.")
    st.dataframe(visit_table(latest_df, cycle), hide_index=True, width="stretch",
                 column_config={"Why": st.column_config.TextColumn("Why", width="large")})

    # The inspection files quote simulated buyer complaints, so only the generated track serves them.
    files = []
    if track.generated:
        found = ((code, find_inspection_file(code, asof)) for code in sorted(latest_df["code"].astype(str)))
        files = [(code, path) for code, path in found if path is not None]
    buttons = st.columns(len(files) + 1)
    for column, (code, path) in zip(buttons, files):
        column.download_button(f"{ORIGIN_GENERATED} {code} inspection file (includes generated figures)",
                               data=path.read_bytes(), file_name=path.name,
                               mime="text/html", key=f"visit_file_{code}")
    export = cycle.rename(columns={"level_word": "level"})
    try:
        csv_data = export_csv(export, "cycle list")
    except ValueError as exc:
        buttons[-1].error(str(exc))
    else:
        buttons[-1].download_button(
            "⬇️ Cycle list (CSV)",
            data=csv_data,
            file_name=f"cycle_list_{asof}.csv",
            mime="text/csv",
        )


def _level_move(change: dict) -> str:
    was = "none" if change["was"] is None else change["was"]
    return f"level {was} to {'none' if change['now'] is None else change['now']}"


def render_changes(asof: str) -> None:
    kpis = load_table(KPI_FILE, TRACK_A)
    changes = None if kpis is None or "cycle_rank" not in kpis.columns else insights.cycle_changes(kpis, asof)
    if changes is None:
        return
    section_title("🔄", f"Changes since {changes['prev']}")
    for column, (title, colour, key) in zip(st.columns(2), (
            ("Joined the list", "#F87171", "joined"), ("Left the list", "#34D399", "left"))):
        with column, st.container(border=True):
            st.markdown(f"**{title}**")
            if not changes[key]:
                st.markdown("No change.")
            for item in changes[key]:
                st.markdown(
                    f'<div class="se-move"><span style="color:{colour};font-weight:700">{html.escape(item["code"])}'
                    f'</span> · {_level_move(item)}'
                    f'<div dir="auto" class="se-move-why">{html.escape(item["why"])}</div></div>',
                    unsafe_allow_html=True)


def render_promises_ahead(promises: list[dict]) -> None:
    section_title("📅", "Promised dates ahead")
    if not promises:
        st.info("No promised date is still ahead.")
        return
    st.caption("A visit before these dates can check the developer's own promise.")
    table = pd.DataFrame(promises).rename(
        columns={"code": "Compound", "claim": "Promise", "said": "Said in", "end": "Due by"})
    st.dataframe(table, hide_index=True, width="stretch")


# --------------------------------------------------------------------------- #
# Screen 2 data
# --------------------------------------------------------------------------- #

KPI_FILE = "real/kpi_values.parquet"
ANNOUNCE_FILES = ("real/statements.parquet",)
# Inspection files: written by the pipeline into app_data, or the stored set committed in the repo.
FILES_DIRS = (APP_DATA / "files", REPO_DIR / "app_data" / "files")
IMAGERY_DIR = REPO_DIR / "data" / "imagery"

COL_A, COL_DW = "activity_prob", "built_prob_mean"
COL_HEIGHT, COL_YEAR = "height_mean_m", "year"
MAX_HEIGHT_YEAR = 2024

# Every K is computed from real inputs (K3 from a published date), so all are derived.
K_ORIGIN = {"K2": ORIGIN_DERIVED, "K3": ORIGIN_DERIVED, "K5": ORIGIN_DERIVED, "K6": ORIGIN_DERIVED}
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


def find_inspection_file(code: str, asof: str) -> Path | None:
    for files_dir in FILES_DIRS:
        for pattern in (f"{code}_{asof}.html", f"{code}_{asof}_*.html"):
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
        k3_text = None if row is None else insights.k3_text(row)
        if k3_text:
            metric_tile("K3 handover clock", k3_text, "", "since first announced handover date", asof,
                        K_ORIGIN["K3"])
        else:
            _kpi_tile("K3 handover clock", get("K3"), "months",
                      "since first announced handover date", asof, K_ORIGIN["K3"])
    with tiles[3]:
        if _missing(get("K6")) and get("K6_status") == "not_applicable_started":
            metric_tile("K6 never started", "does not apply", "",
                        "construction start was observed", asof, K_ORIGIN["K6"])
        else:
            _kpi_tile("K6 never started", get("K6"), "months",
                      "since first launch/promise, no construction start", asof, K_ORIGIN["K6"])
    k5, k5_status = get("K5_months"), get("K5_status")
    k5_text = ("no published deadline" if _missing(k5) and k5_status == "no_published_deadline"
               else "unknown" if _missing(k5) else f"{_fmt(k5, 0)} months")
    st.caption(f"{K_ORIGIN['K5']} Context, not a tile: K5 fine-eligible months {k5_text} · "
               f"the contract decides the fine · as of {asof}")


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
                            legend=alt.Legend(orient="bottom", labelLimit=0)),
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
        st.altair_chart(chart.properties(height=300), width="stretch")

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
            x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.value(0), y2=alt.value(34),
            color=alt.Color("meaning:N", title=None, legend=alt.Legend(orient="bottom"),
                            scale=alt.Scale(domain=list(STAGE_WORDS.values()),
                                            range=["#8A7A5C", PALETTE["accent"], "#46A758"])),
            tooltip=["year", "stage", "meaning", "stage_source"],
        )
        st.altair_chart(chart.properties(height=100), width="stretch")
        start = mine.loc[mine["stage"] != "S0", "year"]
        st.caption(f"Construction first seen in {int(start.min()) if not start.empty else 'no year yet'}.")


def frame_stage(frame: dict, stages: dict[int, str]) -> str:
    return stages.get(int(frame["date"][:4]), "stage not on file")


def render_frame(frame: dict, stages: dict[int, str], caption: str = "") -> None:
    st.image(str(frame["path"]), caption=f"{caption}{frame['date']} · {frame_stage(frame, stages)}",
             width="stretch")


def render_frame_compare(code: str, frames: list[dict], stages: dict[int, str]) -> None:
    dates = [f["date"] for f in frames]
    pickers = st.columns(2)
    start = pickers[0].selectbox("Compare: from", dates, index=0, key=f"cmp_from_{code}")
    season = insights.season_of(start)
    same = [d for d in dates if d != start and insights.season_of(d) == season]
    if not same:
        st.info(f"No other {season} capture exists to compare with {start}; captures are compared within a season.")
        return
    chosen = [start, pickers[1].selectbox(f"Compare: to ({season} only)", same, index=len(same) - 1,
                                          key=f"cmp_to_{code}")]
    for column, date in zip(st.columns(2), chosen):
        with column:
            render_frame(frames[dates.index(date)], stages)


def render_images(code: str) -> None:
    section_title("🛰️", "Wayback timeline")
    frames, stages = space_frames(code), stage_of_year(code)
    with st.container(border=True):
        if not frames:
            st.info(f"No Wayback timeline for {code} in data/imagery/figures/timeline.")
            return
        dates = [f["date"] for f in frames]
        date = st.select_slider("Capture date", options=dates, value=dates[-1], key=f"timeline_{code}")
        shown = frames[dates.index(date)]
        big, side = st.columns([3, 1])
        with big:
            st.image(str(shown["path"]), width="stretch")
        with side:
            metric_tile("Captured", date, "", f"capture {dates.index(date) + 1} of {len(frames)}", date, ORIGIN_REAL)
            metric_tile(f"Stage in {date[:4]}", frame_stage(shown, stages), "",
                        "stage table, see the stage strip", date, ORIGIN_DERIVED)
            st.caption(f"{dates.index(date) + 1} of {len(frames)} captures")
        st.markdown("**Compare two captures**")
        render_frame_compare(code, frames, stages)


def render_inspection_button(code: str, asof: str) -> None:
    section_title("📄", "Inspection file")
    path = find_inspection_file(code, asof)
    if path is None:
        stored = sorted({p.name.split("_")[0] for d in FILES_DIRS for p in d.glob(f"C*_{asof}*.html")})
        st.button("📄 Inspection file (Arabic)", disabled=True, key=f"insp_{code}")
        st.caption(f"No inspection file stored for {code} in {asof}. Stored files cover: "
                   f"{', '.join(stored) if stored else 'none'}.")
        return
    st.download_button(f"{ORIGIN_GENERATED} Open inspection file (Arabic HTML, includes generated figures)",
                       data=path.read_bytes(), file_name=path.name, mime="text/html", key=f"insp_{code}")


def last_recorded_visit(code: str) -> dict | None:
    visits = load_visits()
    if visits is None or visits.empty:
        return None
    mine = visits[visits["code"] == code].sort_values("date")
    return None if mine.empty else {"date": str(mine.iloc[-1]["date"]), "result": str(mine.iloc[-1]["result"])}


def render_compound_header(row: pd.Series | None, code: str) -> None:
    """Level, suggested action and last recorded visit in one line."""
    if row is None:
        return
    action, why = insights.suggested_action(row)
    visit = last_recorded_visit(code)
    seen = "no visit recorded yet" if visit is None else f"{visit['date']} ({html.escape(visit['result'])})"
    number = insights.level_number(row.get("level"))
    level = level_word(row.get("level")) if number is None else f"Level {number} · {level_word(number)}"
    finding(f"<b>{level}.</b> Suggested action: <b>{action}</b>. {html.escape(why)} Last recorded visit: {seen}.")
    st.caption("The action is a suggestion; the committee decides.")


def level_scale() -> tuple[list[str], list[str]]:
    """Level words and their colours for charts, not assessable last."""
    return ([*(word for word, _ in LEVELS.values()), NOT_ASSESSABLE[0]],
            [*(colour for _, colour in LEVELS.values()), NOT_ASSESSABLE[1]])


def render_level_history(code: str) -> None:
    section_title("🗓️", "Level history")
    kpis = load_table(KPI_FILE, TRACK_A)
    if kpis is None:
        return
    history = insights.level_history(kpis)
    mine = history[history["code"] == code].copy()
    mine["Level"] = mine["level"].map(level_word)
    words, colours = level_scale()
    chart = alt.Chart(mine).mark_rect(stroke=PALETTE["bg"], strokeWidth=2).encode(
        x=alt.X("quarter:O", title=None, sort=sorted(mine["quarter"].unique()), axis=alt.Axis(labelAngle=0, labelExpr="indexof(datum.value, 'Q1') > 0 ? slice(datum.value, 0, 4) : ''")),
        color=alt.Color("Level:N", title=None, legend=alt.Legend(orient="bottom"),
                        scale=alt.Scale(domain=words, range=colours)),
        y=alt.value(0), y2=alt.value(34),  # a fixed-height band: no y field to stretch
        tooltip=["quarter", "Level"],
    )
    with st.container(border=True):
        # Streamlit sizes the whole chart (axis and legend included) to this height.
        st.altair_chart(chart.properties(height=100), width="stretch")


def stage_of_year(code: str) -> dict[int, str]:
    if not STAGE_TABLE.exists():
        return {}
    table = enforce_no_names(_read_file(str(STAGE_TABLE)), "r7_stage_table.csv")
    mine = table[table["code"] == code]
    return {int(y): STAGE_WORDS.get(stage, stage) for y, stage in zip(mine["year"], mine["stage"])}


def space_frames(code: str) -> list[dict]:
    """The dated Wayback captures of one compound, oldest first, as {date, path} dicts."""
    frames = insights.timeline_frames(code, IMAGERY_DIR / "figures" / "timeline")
    return [{"date": date, "path": path} for date, path in frames]


def _due_text(due: dict | None) -> str:
    if due is None:
        return ""
    if not due["passed"]:
        return f"{due['year']} still ahead"
    return f"{due['year']} passed, space showed {due['stage']}" if due["stage"] else f"{due['year']} passed"


def render_claims(code: str, ann: pd.DataFrame | None, asof: str) -> None:
    section_title("📣", "Developer claims vs what space showed")
    rows = [] if ann is None or ann.empty or "verdict" not in ann.columns else insights.promise_rows(
        ann, space_frames(code), stage_of_year(code), asof)
    if not rows:
        st.info(f"No confirmed developer claim for {code}.")
        return
    st.dataframe(claims_table(rows), hide_index=True, width="stretch")


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


def _safe(label: str, fn, *args, default=None):
    """Run a loader; if a stored file is corrupt, say so and keep the screen alive.
    (st.stop() is not an Exception, so the no-names gate still stops the app.)"""
    try:
        return fn(*args)
    except Exception as exc:
        st.warning(f"{label}: could not be read ({type(exc).__name__}).")
        return default


# --------------------------------------------------------------------------- #
# Screens
# --------------------------------------------------------------------------- #

def render_cycle_cards(latest: tuple[pd.DataFrame, str] | None) -> None:
    """This cycle's visits as cards: the latest view from space, the level and the reason in one line."""
    if latest is None:
        return
    latest_df, _ = latest
    cycle = build_cycle_list(latest_df)
    if cycle.empty:
        return
    section_title("📋", "This cycle's visits")
    for col, (_, item) in zip(st.columns(len(cycle)), cycle.iterrows()):
        row = latest_df[latest_df["code"] == item["code"]].iloc[0]
        word, colour = _level_style(row["level"])
        frames = insights.timeline_frames(item["code"], IMAGERY_DIR / "figures" / "timeline")
        with col, st.container(border=True):
            if frames:
                st.image(str(frames[-1][1]), width="stretch")
            st.markdown(
                f'<div class="se-card-head"><b>{int(item["cycle_rank"])} · {item["code"]}</b>'
                f'<span class="se-pill" style="border-color:{colour};color:{colour}">{word}</span></div>'
                f'<div class="se-card-why">{html.escape(insights.short_reason(row.get("reason")))}</div>',
                unsafe_allow_html=True)
            if frames:
                st.caption(f"Wayback capture {frames[-1][0]}")


def screen_priority_map(track: Track) -> None:
    page_header("🛰️", "Priority map", "Whom should the committee visit first?")
    latest = load_latest_kpis()
    promises = []
    if latest is not None:
        finding(cycle_headline(*latest))
        promises = load_promises_ahead(*latest)
        render_summary_tiles(*latest, promises)
    render_cycle_cards(latest)
    render_map_slot(track, latest)
    render_visit_list(latest, track)
    if latest is not None:
        render_changes(latest[1])
        render_promises_ahead(promises)


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
        # A default index next to a value already in session state raises a Streamlit warning.
        start = {} if "compound_code" in st.session_state else {"index": default}
        code = pick.selectbox(
            "Compound", codes, key="compound_code", **start,
            format_func=lambda c: f"{c} · {level_word(levels.get(c))}",
        )

        history = load_kpi_history(code)
        now = latest_df[latest_df["code"] == code]
        row = now.iloc[0] if not now.empty else None
        ann = load_announcements(code, asof)

        if row is None:
            st.warning(f"{code} has no KPI row for {asof}: shown as not assessable.")
        render_compound_header(row, code)
        reason = None if row is None else insights.short_reason(row.get("reason"))
        if not _missing(reason) and str(reason).strip():
            st.markdown(f'<b>Why:</b> {html.escape(str(reason))}', unsafe_allow_html=True)

        render_kpi_tiles(row, asof)
        render_level_history(code)
        render_curves(code, history, ann, row)
        render_stage_strip(code)
        render_images(code)
        render_claims(code, ann, asof)
        if track.generated:
            render_inspection_button(code, asof)

        section_title("📝", "Visit form")
        render_ops_visits_form(codes, code)


# --------------------------------------------------------------------------- #
# Screen 3: district view (what the system gives the committee)
# --------------------------------------------------------------------------- #

BACKTEST_CASES = "current/backtest/cases_explained.csv"
LEVEL_CHART_HEIGHT_PER_COMPOUND = 30


def open_compound_file(code: str) -> None:
    st.session_state["compound_code"] = code
    st.session_state["screen"] = SCREENS[1]


def open_button(code: str, section: str, label: str = "") -> None:
    st.button(label or f"Open {code}", key=f"open_{section}_{code}", on_click=open_compound_file, args=(code,))


def level_text(level: int | None) -> str:
    return NOT_ASSESSABLE[0] if level is None else f"Level {level} · {level_word(level)}"


def render_season_pair(pair: list[dict], stages: dict[int, str], anchor_caption: str) -> None:
    """An anchor capture beside the latest one from the same season, or a note when there is none."""
    if not pair:
        st.caption("No later capture from the same season, so no image pair is shown.")
        return
    season = insights.season_of(pair[0]["date"])
    render_frame_row(pair, stages, [anchor_caption, f"Latest {season} capture"][-len(pair):])


def render_frame_row(frames: list[dict], stages: dict[int, str], captions: list[str]) -> None:
    for column, frame, caption in zip(st.columns(max(len(frames), 2)), frames, captions):
        with column:
            render_frame(frame, stages, f"{caption} · ")


def render_early_warning(case: dict | None) -> None:
    if case is None:
        section_title("⏰", "An early signal")
        st.info("No public late case in the backtest was flagged after construction started.")
        return
    code = case["code"]
    section_title("⏰", f"An early signal: {code}")
    frames, stages = space_frames(code), stage_of_year(code)
    pair = insights.frame_pair(frames, insights.first_frame_after(frames, pd.Period(case["alert"], "Q").end_time))
    with st.container(border=True):
        finding(f"<b>{code}</b> was first flagged in {case['alert']}, {case['months']} months before its first "
                f"handover date ({case['deadline']}).")
        st.markdown(f"**What space saw.** {html.escape(case['saw'])}.")
        if case["level_at_freeze"] is not None:
            st.markdown(f"By the freeze date ({case['freeze']}) it was back at level {case['level_at_freeze']} "
                        f"({level_word(case['level_at_freeze'])}).")
        reported = f", reported {case['reported']}" if case["reported"] else ""
        st.markdown(f"**What happened.** {html.escape(case['outcome'].capitalize())}{reported}.")
        render_season_pair(pair, stages, "First capture after the alert")


def render_flagged_early(rows: list[dict]) -> None:
    section_title("🚩", "Flagged now, before any handover date passed")
    with st.container(border=True):
        if not rows:
            st.markdown("No compound on the visit list is flagged before a handover date.")
            return
        for row in rows:
            code_col, level_col, why_col, open_col = st.columns([1, 2, 6, 2])
            code_col.markdown(f"**{row['code']}**")
            level_col.markdown(level_text(row["level"]))
            why_col.markdown(html.escape(row["why"]))
            with open_col:
                open_button(row["code"], "early")


def claims_table(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame({
        "Published": [r["said"] for r in rows],
        "Claim": [r["claim"] for r in rows],
        "Promised year": [_due_text(r["due"]) for r in rows],
        "Nearest capture": ["none within a year" if r["capture"] is None else
                            f"{r['capture']['date']}: {r['capture']['stage'] or 'stage not on file'}"
                            for r in rows],
    })


def render_strongest_claim(latest_df: pd.DataFrame, asof: str) -> None:
    section_title("📣", "The developer said, space saw")
    statements = load_table("real/statements.parquet", TRACK_A)
    claim = None if statements is None else insights.strongest_claim(latest_df, statements, asof)
    if claim is None:
        st.info("No compound has a confirmed developer claim.")
        return
    code = claim["code"]
    frames, stages = space_frames(code), stage_of_year(code)
    rows = insights.promise_rows(statements[statements["code"] == code], frames, stages, asof)
    pair = insights.frame_pair(frames, insights.nearest_frame(frames, claim["last_claim"]))
    with st.container(border=True):
        finding(f"<b>{code}</b>: as of {asof}, {claim['k3']} months past the first announced handover date "
                f"({claim['deadline']}).")
        st.dataframe(claims_table(rows), hide_index=True, width="stretch")
        render_season_pair(pair, stages, "Nearest to the last claim")


def render_homes_waiting(compounds: pd.DataFrame, latest_df: pd.DataFrame, asof: str) -> None:
    section_title("🏠", "Homes in compounds with fine-eligible months")
    waiting = insights.homes_waiting(compounds, latest_df)
    if not waiting["rows"]:
        st.info("No compound with a published unit count has fine-eligible months.")
        return
    words, colours = level_scale()
    table = pd.DataFrame(waiting["rows"])
    table["Level"] = table["level"].map(level_word)
    table["label"] = table["k5"].astype(str) + " months"
    base = alt.Chart(table).encode(y=alt.Y("code:N", sort=list(table["code"]), title=None),
                                   x=alt.X("units:Q", title="Homes (published unit count)"))
    bars = base.mark_bar().encode(
        color=alt.Color("Level:N", title=None, legend=alt.Legend(orient="bottom"),
                        scale=alt.Scale(domain=words, range=colours)),
        tooltip=["code", "units", "k5", "Level"])
    labels = base.mark_text(align="left", dx=4, color=PALETTE["text"]).encode(text="label:N")
    with st.container(border=True):
        finding(f"{ORIGIN_DERIVED} <b>{waiting['homes']:,} homes</b> in {waiting['compounds']} compounds "
                f"with fine-eligible months, as of {asof}.")
        st.altair_chart((bars + labels).properties(height=34 * waiting["compounds"]), width="stretch")
        st.caption("Label = fine-eligible months of the compound.")


def render_late_promises(outcomes: pd.DataFrame) -> None:
    section_title("⌛", "How late R7 promises ran")
    delays = insights.late_delays(outcomes)
    if not delays["rows"]:
        st.info("No public case has a delay on file.")
        return
    table = pd.DataFrame(delays["rows"])
    median = delays["median"]
    base = alt.Chart(table).encode(y=alt.Y("code:N", sort=list(table["code"]), title=None))
    bars = base.mark_bar(color=PALETTE["accent"]).encode(x=alt.X("months:Q", title="Months after the promised date"),
                                                         tooltip=["code", "months"])
    labels = base.mark_text(align="left", dx=4, color=PALETTE["text"]).encode(x="months:Q", text="months:Q")
    rule = alt.Chart(pd.DataFrame({"median": [median]})).mark_rule(color=PALETTE["text"], strokeDash=[4, 4]).encode(
        x="median:Q")
    words = insights.NUMBER_WORDS[len(table)] if len(table) < len(insights.NUMBER_WORDS) else str(len(table))
    with st.container(border=True):
        finding(f"{words} R7 compounds began handing over {table['months'].min()}-{table['months'].max()} months after "
                f"the promised date (median {median:g}).")
        st.altair_chart((bars + labels + rule).properties(height=34 * len(table)), width="stretch")
        kinds = outcomes.set_index("code")["outcome_type"]
        for code in delays["pending"]:
            st.markdown(f"**{code}**: {insights.outcome_text(kinds.get(code))}.")
        st.caption("Dashed line = median.")


def render_fine_months(latest_df: pd.DataFrame, asof: str) -> None:
    section_title("⚖️", "Fine-eligible months")
    fines = insights.fine_months(latest_df)
    if not fines["rows"]:
        st.info("No compound has fine-eligible months.")
        return
    table = pd.DataFrame(fines["rows"])
    chart = alt.Chart(table).mark_bar(color=PALETTE["accent"]).encode(
        x=alt.X("code:N", sort=list(table["code"]), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("months:Q", title="Fine-eligible months"), tooltip=["code", "months"])
    with st.container(border=True):
        finding(f"{ORIGIN_DERIVED} <b>{fines['total']} fine-eligible months</b> over {fines['compounds']} "
                f"compounds, as of {asof}.")
        st.altair_chart(chart.properties(height=220), width="stretch")
        st.caption("The contract decides the fine.")


def render_developer_groups(compounds: pd.DataFrame, latest_df: pd.DataFrame) -> None:
    section_title("🏢", "Developers with several compounds")
    groups = insights.developer_groups(compounds, latest_df)
    if not groups:
        st.info("No developer has more than one compound.")
        return
    width = max(len(g["compounds"]) for g in groups)
    with st.container(border=True):
        for group in groups:
            cells = st.columns([1] + [2] * width)
            cells[0].markdown(f"**{group['developer']}**")
            for cell, item in zip(cells[1:], group["compounds"]):
                with cell:
                    open_button(item["code"], f"dev{group['developer']}", f"{item['code']} · {level_text(item['level'])}")


def render_district_levels() -> None:
    section_title("🗓️", "Level history, all compounds")
    kpis = load_table(KPI_FILE, TRACK_A)
    if kpis is None:
        return
    history = insights.level_history(kpis)
    history["Level"] = history["level"].map(level_word)
    order = insights.codes_by_current_level(history)
    words, colours = level_scale()
    chart = alt.Chart(history).mark_rect(stroke=PALETTE["bg"], strokeWidth=1).encode(
        x=alt.X("quarter:O", title=None, axis=alt.Axis(labelAngle=0, labelExpr="indexof(datum.value, 'Q1') > 0 ? slice(datum.value, 0, 4) : ''")),
        y=alt.Y("code:N", sort=order, title=None, axis=alt.Axis(labelOverlap=False)),
        color=alt.Color("Level:N", title=None, legend=alt.Legend(orient="bottom"),
                        scale=alt.Scale(domain=words, range=colours)),
        tooltip=["code", "quarter", "Level"])
    with st.container(border=True):
        st.altair_chart(chart.properties(height=LEVEL_CHART_HEIGHT_PER_COMPOUND * len(order)),
                        width="stretch")


def screen_district(track: Track) -> None:
    page_header("🏘️", "District view", "What does the system give the committee?")
    latest = load_latest_kpis()
    if latest is None:
        st.info("Waiting for real/kpi_values.parquet.")
        return
    latest_df, asof = latest
    cases = _safe(BACKTEST_CASES, load_table, BACKTEST_CASES, TRACK_A, READY_DATA)
    compounds = load_table("real/compounds.parquet", TRACK_A)
    outcomes = load_table("real/eval_outcomes.parquet", TRACK_A)
    render_early_warning(None if cases is None else insights.warning_case(cases))
    render_flagged_early(insights.flagged_early(latest_df))
    render_strongest_claim(latest_df, asof)
    if compounds is not None:
        render_homes_waiting(compounds, latest_df, asof)
    if outcomes is not None:
        render_late_promises(outcomes)
    render_fine_months(latest_df, asof)
    if compounds is not None:
        render_developer_groups(compounds, latest_df)
    render_district_levels()


# --------------------------------------------------------------------------- #
# Screen 4: fewer or more visits per cycle
#
# Reads the stored v7 capacity scenario (never recomputes):
#   ready-data/what_if/S3/who_moved_and_why.csv  (data/SCENARIO_CONTRACT_CURRENT.md)
# One row per compound, quarter and capacity variant (2 or 6 versus 4); selection only,
# levels never change.
# --------------------------------------------------------------------------- #

CAPACITY_FILE = "what_if/S3/who_moved_and_why.csv"
CAPACITY_VARIANTS = {"capacity_minus_2": "2 visits instead of 4", "capacity_plus_2": "6 visits instead of 4"}


def whatif_view(raw: pd.DataFrame, reasons: dict[str, str] | None = None) -> tuple[pd.DataFrame, str]:
    """The latest quarter of one capacity variant: one row per compound, baseline versus scenario,
    with each compound's stored English level reason for that quarter."""
    label = str(raw["quarter"].max())
    latest = raw[raw["quarter"].astype(str) == label]
    view = pd.DataFrame({"code": latest["code"].astype(str)})
    view["change"] = [("joins the list" if _as_bool(s) else "leaves the list") if _as_bool(c) else "unchanged"
                      for s, c in zip(latest["selected"], latest["selection_changed"])]
    view["reason"] = view["code"].map(reasons or {}).fillna("").map(insights.short_reason)
    return view.reset_index(drop=True), label


def render_capacity_variant(raw: pd.DataFrame, variant: str) -> None:
    part = raw[raw["scenario_id"] == variant]
    kpis = load_table(KPI_FILE, TRACK_A)
    quarter = str(part["quarter"].max())
    reasons = {} if kpis is None else dict(
        zip(kpis.loc[kpis["quarter"].astype(str) == quarter, "code"], kpis.loc[kpis["quarter"].astype(str) == quarter, "reason"]))
    view, label = whatif_view(part, reasons)
    moved = view[view["change"] != "unchanged"]
    with st.container(border=True):
        st.markdown(f"**{CAPACITY_VARIANTS[variant]}**")
        if moved.empty:
            st.markdown("The list does not change.")
        for _, r in moved.iterrows():
            colour = "#34D399" if r["change"] == "leaves the list" else "#F87171"
            st.markdown(
                f'<div class="se-move"><span style="color:{colour};font-weight:700">'
                f'{html.escape(r["code"])}</span> · {html.escape(r["change"])}'
                f'<div class="se-move-why">{html.escape(r["reason"])}</div></div>',
                unsafe_allow_html=True)
        st.caption(f"{ORIGIN_GENERATED} Generated · {label}")


SCENARIO_TABS = {"S1": "S1 · Cost shock", "S2": "S2 · Collections drop", "S3": "S3 · Capacity"}
SCENARIO_NOTES = {"S1": "Imported cost +30%.", "S2": "Collections -25% for six months."}


def hypothetical_text(level: float) -> str:
    return level_text(None if pd.isna(level) else int(level))


def render_scenario_moves(view: pd.DataFrame) -> None:
    moved = view[view["changed"]]
    if moved.empty:
        st.markdown("Nobody crosses a threshold: no compound changes level or list position.")
        return
    for _, r in moved.iterrows():
        change = (f"hypothetical baseline {hypothetical_text(r['baseline_level'])}, "
                  f"scenario {hypothetical_text(r['level'])}")
        if r["baseline_listed"] != r["listed"]:
            change += ", joins the list" if r["listed"] else ", leaves the list"
        st.markdown(
            f'<div class="se-move"><span style="color:{PALETTE["accent_b"]};font-weight:700">'
            f'{html.escape(r["code"])}</span> · {html.escape(change)}'
            f'<div dir="auto" class="se-move-why">{html.escape(r["reason"])}</div></div>',
            unsafe_allow_html=True)


def render_scenario_levels(view: pd.DataFrame) -> None:
    counts = insights.level_counts(view)
    counts["Level"] = counts["level"].map(level_word)
    words, _ = level_scale()
    chart = alt.Chart(counts).mark_bar().encode(
        x=alt.X("Level:N", sort=words, title=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("case:N", sort=[insights.BASELINE_LABEL, "Scenario"]),
        y=alt.Y("compounds:Q", title="Compounds", axis=alt.Axis(tickMinStep=1)),
        color=alt.Color("case:N", title=None, legend=alt.Legend(orient="bottom"),
                        scale=alt.Scale(domain=[insights.BASELINE_LABEL, "Scenario"],
                                        range=[PALETTE["muted"], PALETTE["accent_b"]])),
        tooltip=["case", "Level", "compounds"])
    st.altair_chart(chart.properties(height=200), width="stretch")


def render_finance_scenario(scenario: str, track: Track) -> None:
    rel = f"what_if/{scenario}/who_moved_and_why.csv"
    raw = _safe(rel, load_table, rel, track, READY_DATA)
    if raw is None or raw.empty:
        st.info(f"Waiting for ready-data/{rel}. Run python -m src.pipeline.setup_review.")
        return
    view, month = insights.scenario_view(raw)
    with st.container(border=True):
        st.caption(f"{ORIGIN_GENERATED} Generated · {SCENARIO_NOTES[scenario]} · {month}")
        render_scenario_moves(view)
        if view["changed"].any():
            render_scenario_levels(view)


PROGRESS_FILE = "what_if/progress_vs_baseline.csv"


def render_progress_vs_baseline(track: Track) -> None:
    """How far each finance shock moves progress against the baseline run (generated, same seed)."""
    raw = _safe(PROGRESS_FILE, load_table, PROGRESS_FILE, track, READY_DATA)
    section_title("📈", "Progress against the baseline run")
    if raw is None or raw.empty:
        st.info(f"Waiting for ready-data/{PROGRESS_FILE}. It is written by src/generator/twin_progress.py.")
        return
    view, month = insights.progress_view(raw)
    with st.container(border=True):
        st.caption(f"{ORIGIN_GENERATED} Generated · latest month {month} · the baseline and both shocks come from one run")
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.caption("Change in percent points of progress. A shock that moves no compound to another level "
                   "or visit-list place is a result, not a missing value.")


def screen_what_if(track: Track) -> None:
    page_header("🧪", "Digital twin what if", "Who would change if costs, collections or visit capacity changed?")
    if not track.generated:
        st.warning("Digital twin what if uses generated data. Switch to Track B in the sidebar to open it.")
        return
    render_progress_vs_baseline(track)
    tabs = st.tabs(list(SCENARIO_TABS.values()))
    for tab, scenario in zip(tabs[:2], ("S1", "S2")):
        with tab:
            render_finance_scenario(scenario, track)
    with tabs[2]:
        raw = _safe(CAPACITY_FILE, load_table, CAPACITY_FILE, track, READY_DATA)
        if raw is None or raw.empty:
            st.info(f"Waiting for ready-data/{CAPACITY_FILE}. Run python -m src.pipeline.setup_review.")
            return
        for column, variant in zip(st.columns(2), CAPACITY_VARIANTS):
            with column:
                render_capacity_variant(raw, variant)


SCREEN_FUNCTIONS = {
    SCREENS[0]: screen_priority_map,
    SCREENS[1]: screen_compound_file,
    SCREENS[2]: screen_district,
    SCREENS[3]: screen_what_if,
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