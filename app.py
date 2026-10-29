"""SpaceEye R7 Observatory - Streamlit dashboard (T-NA-01: skeleton + track switch).

Run with:  streamlit run app.py

Rules enforced here (01-specs.md sections 9 and 14):
  * Track A (images, real/derived) is the default.
  * Track B (images + numbers, GENERATED) shows a fixed orange banner
    "Synthetic - for training only", hides the map, and tags every
    generated number with the orange circle.
  * Everything is read from stored files (CSV / Parquet / JSON). No live compute.
  * Codes only (C01, D01, ...). Compound or developer names never reach the screen.

UI layer: a dark "mission control" theme injected as CSS (see `inject_css`).
The styling is presentation only; all data, gate and track logic is separate.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

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
    """Load a stored table. Returns None if the file does not exist yet.

    Separation rule: generated tables are never loaded in Track A.
    """
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
    with st.container(border=True):  # card styling comes from inject_css
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
    """Dark tech theme. Pure presentation: no data or logic lives here."""
    p = PALETTE
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

        /* ---------- base ---------- */
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

        /* ---------- screen header ---------- */
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

        /* ---------- cards (st.container(border=True)) ---------- */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: linear-gradient(180deg, {p['surface']} 0%, {p['bg_alt']} 100%);
            border: 1px solid {p['border']} !important;
            border-radius: 16px;
            padding: 0.35rem 0.5rem;
            box-shadow: 0 8px 24px rgba(0,0,0,0.28);
        }}

        /* ---------- metric tiles ---------- */
        [data-testid="stMetric"] {{ padding: 0.2rem 0.3rem; }}
        [data-testid="stMetricLabel"] p {{
            color: {p['muted']} !important; font-size: 0.78rem; font-weight: 600;
            letter-spacing: 0.06em; text-transform: uppercase;
        }}
        [data-testid="stMetricValue"] {{
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-weight: 600; color: {p['text']};
        }}

        /* ---------- alerts (placeholder / waiting messages) ---------- */
        [data-testid="stAlert"] {{
            background: {p['surface']}; border: 1px solid {p['border']};
            border-left: 4px solid {p['accent']}; border-radius: 12px;
            padding: 0.9rem 1.1rem; color: {p['text']};
        }}
        [data-testid="stAlert"] p {{ color: {p['text']}; }}

        /* ---------- dataframes ---------- */
        [data-testid="stDataFrame"] {{
            border: 1px solid {p['border']}; border-radius: 14px; overflow: hidden;
            box-shadow: 0 6px 18px rgba(0,0,0,0.25);
        }}

        /* ---------- sidebar ---------- */
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

        /* ---------- Track B sticky banner ---------- */
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


def render_map_slot(track: Track) -> None:
    """Map is Track A only. Track B must never draw generated numbers on a map."""
    if track.generated:
        return  # hidden completely, no placeholder
    section_title("🗺️", "Priority map")
    boundaries = APP_DATA / "real" / "compound_boundaries.geojson"
    if boundaries.exists():
        st.info("Map slot ready (rendered in T-NA-02 from compound_boundaries.geojson).")
    else:
        st.warning("real/compound_boundaries.geojson not found yet (hand-off from ahmed, D2).")


# --------------------------------------------------------------------------- #
# Screens (skeletons; content arrives in T-NA-02 .. T-NA-07)
# --------------------------------------------------------------------------- #

def screen_priority_map(track: Track) -> None:
    page_header("🛰️", "Priority map", "Whom should the committee visit first?")
    render_map_slot(track)

    section_title("📋", "Cycle list")
    kpis = load_table("real/kpi_values.parquet", TRACK_A)  # real/derived in both tracks
    if kpis is None:
        st.info("Waiting for real/kpi_values.parquet. Cycle list appears here (T-NA-02).")
    else:
        st.dataframe(kpis.head(10), use_container_width=True, hide_index=True)

    if track.generated:
        section_title("🧠", "Classifier probabilities")
        preds = load_table("ml/predictions.parquet", track)
        if preds is None:
            st.info("Waiting for ml/predictions.parquet (hand-off, D3).")
        else:
            st.dataframe(tag_generated_columns(preds.head(10)),
                         use_container_width=True, hide_index=True)


def screen_compound_file(track: Track) -> None:
    page_header("🗂️", "Compound file", "Why this one? Evidence behind the priority level.")
    st.info("Skeleton. Curves, images, K2-K6 and visit form arrive in T-NA-03 / T-NA-04.")
    if track.generated:
        st.caption(f"Track B adds binary probabilities and K5 in EGP, always tagged {ORIGIN_GENERATED}.")


def screen_backtest(track: Track) -> None:
    page_header("⏱️", "Would it have warned?", "Backtest and early-warning evidence.")
    st.info("Skeleton. Frozen-clock table and recall@N arrive in T-NA-05.")


def screen_data_trust(track: Track) -> None:
    page_header("🛡️", "Data trust", "How far can each number be trusted?")
    with st.container(border=True):
        st.markdown(
            f"**Colour key** &nbsp; {ORIGIN_REAL} real · {ORIGIN_DERIVED} derived · "
            f"{ORIGIN_GENERATED} generated"
        )
    st.info("Skeleton. Gates, coverage and the 1,009/1,026 facts arrive in T-NA-06.")


def screen_what_if(track: Track) -> None:
    page_header("🧪", "What if?", "Compound-level twin: who moves up if conditions change?")
    if not track.generated:
        st.warning(
            "Scenarios use generated data. Switch to Track B in the sidebar to open them."
        )
        return
    st.info("Skeleton. Scenarios S1-S3 arrive in T-NA-07.")


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
    # Brand block
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

    # Track switch is the first control; Track A is index 0 = default.
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
    render_banner(track)  # fixed orange banner on every screen in Track B
    SCREEN_FUNCTIONS[screen](track)


if __name__ == "__main__":
    main()