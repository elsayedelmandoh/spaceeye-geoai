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

BANNER_TEXT = "بيانات مولّدة للتدريب فقط"

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


TRACK_A = Track("A", "المسار أ: صور الأقمار", generated=False)
TRACK_B = Track("B", "المسار ب: صور وأرقام مولّدة", generated=True)
TRACKS = {t.label: t for t in (TRACK_A, TRACK_B)}  # Track A first = default

SCREENS = [
    "1 · أولوية الزيارات",
    "2 · ملف الكمباوند",
    "3 · الفايدة",
    "4 · لو عدد الزيارات اتغير",
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
# Presentation helpers (headers, banner)
# --------------------------------------------------------------------------- #

def page_header(icon: str, title: str, subtitle: str = "") -> None:
    """Screen title + the question the screen answers. Text only: emoji icons are not shown."""
    sub = f'<div class="se-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="se-header"><div><div class="se-title">{title}</div>{sub}</div></div>',
                unsafe_allow_html=True)


def section_title(icon: str, text: str) -> None:
    """Section label above cards (the emoji argument is kept for call sites but not shown)."""
    st.markdown(f'<div class="se-section">{text}</div>', unsafe_allow_html=True)


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
        [data-testid="stDataFrame"] {{ border: 1px solid {p['border']}; border-radius: 3px; }}
        [data-testid="stMain"], [data-testid="stSidebar"] {{ direction: rtl; }}
        bdi {{ unicode-bidi: isolate; }}

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
    1: ("زيارة فورية", "#A8102C"),
    2: ("زيارة الدورة دي", "#E35D17"),
    3: ("مراجعة مستندات", "#D1A80C"),
    4: ("متابعة عادية", "#2E7D4F"),
}
NOT_ASSESSABLE: tuple[str, str] = ("مش قابل للتقييم", "#8A8F8B")  # grey

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
        df["K6"] = [("لا ينطبق" if status == "not_applicable_started" else "غير معروف") if _missing(k6)
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


WAYBACK_CREDIT = "الصور من Esri World Imagery Wayback، وبيانات كل صورة مطبوعة تحتها."


def level_number(level: object) -> int | None:
    try:
        return int(level) if int(level) in LEVELS else None
    except (TypeError, ValueError):
        return None


ARABIC_MONTHS = ("يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر",
                 "أكتوبر", "نوفمبر", "ديسمبر")
COUNT_NOUNS = {"شهر": ("أشهر", "شهرًا"), "ربع": ("أرباع", "ربعًا")}


def month_ar(value: object) -> str:
    stamp = pd.Timestamp(value)
    return f"{ARABIC_MONTHS[stamp.month - 1]} {stamp.year}"


def count_ar(n: int, noun: str) -> str:
    """Arabic counted noun after a digit: 3-10 take the plural, 11-99 the accusative singular."""
    few, many = COUNT_NOUNS[noun]
    rest = n % 100
    return few if 3 <= rest <= 10 else many if rest >= 11 else noun


def short_reason_ar(text: object) -> str:
    """An Arabic level reason without the level prefix, the activity score or the image count."""
    if _missing(text):
        return ""
    body = re.sub(r"\s*\(درجة النشاط [^)]*\)", "", str(text).split(": ", 1)[-1])
    body = re.sub(r"(\d+) (شهر|ربع)(?=\s|؛|$|\.)", lambda m: f"{m[1]} {count_ar(int(m[1]), m[2])}", body)
    body = re.sub(r"\((\d{4}-\d{2}-\d{2})\)", lambda m: f"({month_ar(m[1])})", body)
    clauses = [c.strip(" .") for c in body.split("؛") if c.strip(" .") and not c.strip().startswith("عدد الصور")]
    return "، ".join(clauses)


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
            "height_text": f"متوسط الارتفاع {height[0]:.0f} م ({height[1]})" if height else "مفيش ارتفاع مسجل",
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
                      "level_word": level_word(row["level"]), "why": short_reason_ar(row.get("reason_ar")),
                      "frames": frames_payload(item["code"]), "file": inspection_payload(item["code"], asof)})
    eligible = int(latest_df["level"].isin([1, 2, 3]).sum())
    payload = {"screen": "priority", "asof": asof, "total": len(latest_df), "cycle": items,
               "waiting": max(eligible - len(items), 0), "credit": WAYBACK_CREDIT, "map": False}
    # Track B keeps the map off: its tables start in a different quarter.
    mapped = None if track.generated else map_payload(latest_df, cycle)
    if mapped:
        payload.update(mapped, map=True, map_note=(
            "عرض 3D بيرفع كل كمباوند بمتوسط ارتفاع مبانيه (Google Open Buildings، "
            f"آخر سنة لحد {MAX_HEIGHT_YEAR})، مكبّر {MAP_HEIGHT_EXAGGERATION} مرات"))
    return payload


def open_compound_file_from(key: str):
    """A front-end screen asked for a compound file: switch screens before the sidebar is drawn again."""
    def callback() -> None:
        code = (st.session_state.get(key) or {}).get("open")
        if code:
            st.session_state["compound_code"] = code
            st.session_state["screen"] = SCREENS[1]
    return callback


def render_cycle_download(latest: tuple[pd.DataFrame, str]) -> None:
    latest_df, asof = latest
    cycle = build_cycle_list(latest_df)
    if cycle.empty:
        return
    st.download_button("حمّل قائمة الزيارات (CSV)",
                       data=cycle.rename(columns={"level_word": "level"}).to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"cycle_list_{asof}.csv", mime="text/csv", key="cycle_download")


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


def inspection_payload(code: str, asof: str) -> dict | None:
    """The stored Arabic inspection file of this quarter, sent whole so the page can open and print it."""
    path = find_inspection_file(code, asof)
    return None if path is None else {"name": path.name, "html": path.read_text(encoding="utf-8")}


# ---- screen 2 renderers ----------------------------------------------------- #

STAGE_TABLE = REPO_DIR / "data" / "experiments" / "42_r7_stage_table" / "r7_stage_table.csv"
STAGE_WORDS = {"S0": "أرض أو أعمال حفر", "S1": "تحت الإنشاء", "S2": "مكتمل"}


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
        text = "غير معروف"
    return {"label": label, "rule": rule, "unit": None if text else count_ar(int(value), unit),
            "value": None if text else int(value), "text": text}


def _share(value: object) -> float | None:
    return None if _missing(value) else round(float(value), 3)


def compound_payload(code: str, row: pd.Series | None, history: pd.DataFrame | None,
                     ann: pd.DataFrame | None, asof: str) -> dict:
    """Screen 2 for the front end: frames to compare, the three clocks, the quarterly series, stages."""
    get = (lambda c: None) if row is None else row.get
    deadline = get("k3_first_deadline")
    k6_text = "لا ينطبق: الإنشاء بدأ" if (
        _missing(get("K6")) and get("K6_status") == "not_applicable_started") else None
    clocks = [
        _clock("K2 توقف النشاط", "أرباع متتالية من غير نشاط بناء، بعد البداية", get("K2"), "ربع"),
        _clock("K3 عدّاد التسليم", "أشهر من أول موعد تسليم معلن", get("K3"), "شهر",
               None if not _missing(deadline) else "مفيش موعد تسليم معلن"),
        _clock("K6 ما بدأش", "أشهر من الإطلاق أو الوعد من غير بداية إنشاء", get("K6"), "شهر", k6_text),
        _clock("K5 أشهر ممكن تتحسب عليها غرامة", "العقد هو اللي بيحدد الغرامة", get("K5_months"), "شهر",
               "مفيش موعد تسليم منشور" if _missing(get("K5_months")) and get("K5_status") == "no_published_deadline"
               else None),
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
        marker = {"q": str(first.to_period("Q")), "label": month_ar(first)}

    stages, stage_note = [], None
    if STAGE_TABLE.exists():
        table = enforce_no_names(_read_file(str(STAGE_TABLE)), "r7_stage_table.csv")
        mine = table.loc[table["code"] == code].sort_values("year")
        stages = [{"year": int(r["year"]), "stage": r["stage"], "word": STAGE_WORDS.get(r["stage"], r["stage"])}
                  for _, r in mine.iterrows()]
        start = mine.loc[mine["stage"] != "S0", "year"]
        stage_note = (f"أول إنشاء ظهر سنة {int(start.min())}." if not start.empty
                      else "لسه مفيش إنشاء ظاهر.")
    reason = short_reason_ar(get("reason_ar"))
    frames = frames_payload(code)
    return {
        "screen": "compound", "code": code, "asof": asof,
        "level": level_number(get("level")), "level_word": level_word(get("level")),
        "reason_ar": reason or None,
        "frames": frames, "file": inspection_payload(code, asof), "credit": WAYBACK_CREDIT,
        "clocks": clocks,
        "quarters": quarters, "statements": statements, "deadline": marker,
        "chart_note": None,
        "stages": stages, "stage_words": [{"stage": k, "word": v} for k, v in STAGE_WORDS.items()],
        "stage_note": stage_note,
        "stage_missing": "جدول المراحل مش موجود في النسخة دي.",
        "promises": promise_rows(code, ann, frames, asof),
    }


# ---- the developer said, space saw ------------------------------------------ #

PROMISE_WORDS = {
    "promised_delivery": "التسليم",
    "promised_delivery_start": "بداية التسليم",
    "promised_delivery_phase1": "تسليم المرحلة الأولى",
    "promised_delivery_phase2": "تسليم المرحلة التانية",
    "promised_completion": "الانتهاء من المشروع",
}
PROGRESS_WORDS = {"exact": "", "over": "أكتر من ", "about": "حوالي "}
FRAME_NEAR_DAYS = 366  # a claim is paired with a picture only if one was captured within a year


def period_ar(start: object, end: object) -> str:
    """A promised period in words: one month, a calendar year, a month range, or 'by' an end date."""
    end = pd.Timestamp(end)
    if _missing(start):
        return f"لحد {month_ar(end)}"
    start = pd.Timestamp(start)
    if start.month == 1 and end.month == 12 and start.year == end.year:
        return f"سنة {end.year}"
    if (start.year, start.month) == (end.year, end.month):
        return month_ar(end)
    first = ARABIC_MONTHS[start.month - 1] if start.year == end.year else month_ar(start)
    return f"{first}–{month_ar(end)}"


def claim_text(row: pd.Series) -> str:
    if row["kind"] == "progress":
        return f"نسبة التنفيذ {PROGRESS_WORDS.get(row['qualifier'], '')}{float(row['value']):.0f}%"
    return f"وعد ب{PROMISE_WORDS.get(row['subtype'], 'التسليم')} {period_ar(row['period_start'], row['period_end'])}"


def nearest_frame(frames: list[dict], when: pd.Timestamp) -> int | None:
    gaps = [abs((pd.Timestamp(f["date"]) - when).days) for f in frames]
    return None if not gaps or min(gaps) > FRAME_NEAR_DAYS else gaps.index(min(gaps))


def promise_rows(code: str, ann: pd.DataFrame | None, frames: list[dict], asof: str) -> list[dict]:
    """The developer's confirmed public claims, oldest first, each beside what space showed."""
    if ann is None or ann.empty or "verdict" not in ann.columns:
        return []
    stages = stage_of_year(code)
    now = pd.Period(asof, "Q").end_time
    rows = []
    for _, r in ann[ann["verdict"] == "CONFIRMED"].sort_values("published_date").iterrows():
        said = pd.Timestamp(r["published_date"])
        due = None
        if r["kind"] == "promise" and not _missing(r["period_end"]):
            end = pd.Timestamp(r["period_end"])
            due = {"year": end.year, "passed": bool(end < now), "stage": stages.get(end.year) if end < now else None}
        rows.append({"said": month_ar(said), "claim": claim_text(r), "stage": stages.get(said.year),
                     "frame": nearest_frame(frames, said), "due": due})
    return rows


def promise_example(latest_df: pd.DataFrame, asof: str) -> dict | None:
    """The compound whose first announced handover date passed longest ago (largest K3), among those
    with confirmed developer claims: its claims and two pictures (nearest the last claim, latest)."""
    for _, row in latest_df.sort_values("K3", ascending=False).iterrows():
        if _missing(row["K3"]) or row["K3"] <= 0:
            break
        code = str(row["code"])
        frames = frames_payload(code)
        claims = promise_rows(code, load_announcements(code, asof), frames, asof)
        if not claims or not frames:
            continue
        last = next((c for c in reversed(claims) if c["frame"] is not None), None)
        shown = [last["frame"], len(frames) - 1] if last and last["frame"] != len(frames) - 1 else [len(frames) - 1]
        return {"code": code, "k3": int(row["K3"]), "claims": claims,
                "frames": [{**frames[i], "caption": "بعد آخر تصريح" if i != len(frames) - 1 else "آخر صورة"}
                           for i in shown]}
    return None


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
    "partial_delivery_late_completion_postponed": "جزء منه اتسلّم متأخر، والاستكمال اتأجل",
    "postponed_twice_not_yet_delivered": "التسليم اتأجل مرتين ولسه ما اتسلمش",
    "delivered_late": "اتسلّم متأخر",
}
# The frozen-clock reasons are stored in English; their fixed clause patterns, in Arabic.
WHY_PATTERNS = (
    (r"no building activity for (\d+) quarter\(s\)", lambda m: f"لم يُرصد نشاط بناء منذ {m[1]} {count_ar(int(m[1]), 'ربع')}"),
    (r"building activity detected", lambda m: "رُصد نشاط بناء"),
    (r"first announced handover date \((\w+) (\d{4})\) is still ahead",
     lambda m: f"أول موعد تسليم معلن ({month_ar(f'{m[1]} {m[2]}')}) لم يحن بعد"),
    (r"no confirmed observed start for (\d+) months since the first known launch/promise",
     lambda m: f"ولم تتأكد بداية إنشاء بعد {m[1]} {count_ar(int(m[1]), 'شهر')} من أول إطلاق أو وعد"),
)


def why_ar(text: str) -> str:
    clauses = []
    for clause in text.split("; "):
        for pattern, words in WHY_PATTERNS:
            match = re.search(pattern, clause)
            if match:
                clauses.append(words(match))
                break
    return "، ".join(clauses)


def _safe(label: str, fn, *args, default=None):
    """Run a loader; if a stored file is corrupt, say so and keep the screen alive.
    (st.stop() is not an Exception, so the no-names gate still stops the app.)"""
    try:
        return fn(*args)
    except Exception as exc:
        st.warning(f"الملف {label} ما اتقراش ({type(exc).__name__}).")
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
        "deadline": month_ar(case["first_deadline"]),
        "why": why_ar(str(case["why"]).split(": ", 1)[-1]),
        "outcome": OUTCOME_WORDS.get(outcome.strip(), outcome.strip().replace("_", " ")),
        "reported": month_ar(reported) if reported else "",
        "frames": [{"date": d, "src": front.frame_uri(p, width=640), "foot": front.frame_uri(p, "foot", width=640)}
                   for d, p in shown],
    }


def value_payload(latest: tuple[pd.DataFrame, str]) -> dict:
    latest_df, asof = latest
    cycle = build_cycle_list(latest_df)
    on_list = latest_df[latest_df["code"].isin(cycle["code"])].set_index("code").loc[list(cycle["code"])]
    early = on_list[on_list["k3_first_deadline"].isna() | (on_list["K3"].fillna(0) == 0)]
    now = [{"code": code, "level": level_number(r["level"]), "level_word": level_word(r["level"]),
            "why": short_reason_ar(r.get("reason_ar"))} for code, r in early.iterrows()]

    fines = latest_df.dropna(subset=["K5_months"]).sort_values("K5_months", ascending=False)
    fine_rows = [{"code": c, "months": int(m)} for c, m in zip(fines["code"], fines["K5_months"])]

    return {"screen": "value", "asof": asof, "total": len(latest_df), "visits": len(cycle),
            "example": warning_example(), "now": now, "promise": promise_example(latest_df, asof),
            "fines": fine_rows, "fine_months": sum(r["months"] for r in fine_rows)}


# --------------------------------------------------------------------------- #
# Screens
# --------------------------------------------------------------------------- #

def screen_priority_map(track: Track) -> None:
    latest = load_latest_kpis()
    if latest is None:
        page_header("", "أولوية الزيارات", "اللجنة تزور مين الأول؟")
        st.info("في انتظار ملف real/kpi_values.parquet.")
        return
    front.mount(priority_payload(track, latest), key="front_priority", on_open=open_compound_file_from("front_priority"))
    render_cycle_download(latest)


def screen_compound_file(track: Track) -> None:
    latest = load_latest_kpis()
    if latest is None:
        page_header("", "ملف الكمباوند", "ليه الكمباوند ده؟")
        st.info("في انتظار ملف real/kpi_values.parquet.")
        return
    latest_df, asof = latest
    codes = sorted(latest_df["code"].dropna().astype(str).unique())
    levels = dict(zip(latest_df["code"], latest_df["level"]))
    if st.session_state.get("compound_code") not in codes:
        cycle = build_cycle_list(latest_df)
        st.session_state["compound_code"] = cycle["code"].iloc[0] if not cycle.empty else codes[0]

    pick, _ = st.columns([1, 3])
    code = pick.selectbox("الكمباوند", codes, key="compound_code",
                          format_func=lambda c: f"{c} · {level_word(levels.get(c))}")
    now = latest_df[latest_df["code"] == code]
    row = now.iloc[0] if not now.empty else None
    if row is None:
        st.warning(f"مفيش بيانات لـ {code} في {asof}، فهو معروض كـ مش قابل للتقييم.")
    front.mount(compound_payload(code, row, load_kpi_history(code), load_announcements(code, asof), asof),
                key="front_compound")

    section_title("", "نتيجة الزيارة")
    render_ops_visits_form(codes, code)


def screen_value(track: Track) -> None:
    latest = load_latest_kpis()
    if latest is None:
        page_header("", "الفايدة", "SpaceEye بيضيف إيه لدورة التفتيش.")
        st.info("في انتظار ملف real/kpi_values.parquet.")
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
        st.warning("الشاشة دي بتقرا ملفات السيناريو، وهي متاحة في المسار ب من القائمة الجانبية.")
        return
    raw = _safe(CAPACITY_FILE, load_table, CAPACITY_FILE, track, READY_DATA)
    if raw is None or raw.empty:
        st.info(f"في انتظار ملف ready-data/{CAPACITY_FILE}.")
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
          <div class="se-brand-sub">مرصد R7 · العاصمة الإدارية الجديدة</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    st.sidebar.markdown('<div class="se-side-label">مسار البيانات</div>', unsafe_allow_html=True)
    label = st.sidebar.selectbox(
        "Track",
        options=list(TRACKS.keys()),
        index=0,
        key="track_label",
        label_visibility="collapsed",
        help="المسار أ: بيانات عامة ومشتقة منها. المسار ب: بيضيف بيانات مولّدة شبه بيانات الشركة.",
    )
    track = TRACKS[label]

    st.sidebar.divider()
    st.sidebar.markdown('<div class="se-side-label">الشاشات</div>', unsafe_allow_html=True)
    screen = st.sidebar.radio("Screen", SCREENS, key="screen", label_visibility="collapsed")

    st.sidebar.divider()
    if track.generated:
        st.sidebar.markdown(
            f'<span class="se-pill se-pill-b">{ORIGIN_GENERATED} بيانات مولّدة للتدريب</span>',
            unsafe_allow_html=True,
        )
        st.sidebar.caption("الخريطة مخفية في المسار ده")
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