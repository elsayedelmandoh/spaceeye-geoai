"""Plain-Python data tools for cutoff-controlled inspection files."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from src.pipeline.common import APP, CFG, REAL, SRC, qend, qindex, require_data_root

type FrameSource = pd.DataFrame | str | Path
type TablesSource = Mapping[str, FrameSource] | str | Path | None
type JsonValue = (
    None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)

_REAL_TABLES = ("statements", "kpi_values", "compounds")
_KPI_FIELDS = (
    ("A", "activity_prob"),
    ("K2", "K2"),
    ("K3", "K3"),
    ("K4", "K4"),
    ("K5_months", "K5_months"),
    ("K6", "K6"),
    ("level", "level"),
    ("level_label", "level_label"),
    ("level_word", "level_word"),
    ("reason", "reason"),
    ("reason_ar", "reason_ar"),
    ("may_be_complete", "may_be_complete"),
)
_LINK_COLUMNS = ("link", "source_link", "url")
_ARTICLE_COLUMNS = ("article_id", "article", "article_no", "article_number", "id")
_MISSING_IMAGES = {
    "status": "missing",
    "images": [],
    "reason": "Wayback images not prepared (T-AH-15)",
}


@lru_cache(maxsize=4)
def _tables(base: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Load the prepared real tables lazily from a real-table directory."""
    if base is None:
        require_data_root()
        base = REAL
    root = Path(base)
    return {
        name: pd.read_parquet(root / f"{name}.parquet")
        for name in _REAL_TABLES
    }


def _read_frame(source: str | Path) -> pd.DataFrame:
    """Read one CSV or Parquet table from a supplied path."""
    path = Path(source)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_parquet(path)


def _resolve_tables(tables: TablesSource) -> dict[str, pd.DataFrame]:
    """Resolve preloaded frames, table paths, or a real-table directory."""
    if tables is None:
        return _tables()
    if isinstance(tables, (str, Path)):
        return _tables(tables)
    return {
        name: source if isinstance(source, pd.DataFrame) else _read_frame(source)
        for name, source in tables.items()
    }


def _require_table(tables: Mapping[str, pd.DataFrame], name: str) -> pd.DataFrame:
    """Return a required table or fail with its missing name."""
    if name not in tables:
        raise KeyError(f"Required table '{name}' was not supplied")
    return tables[name]


def _json_value(value: object) -> JsonValue:
    """Convert a dataframe value to a JSON-safe value with unknown as None."""
    if value is None:
        return None
    missing = pd.isna(value)
    if isinstance(missing, (bool, np.bool_)) and bool(missing):
        return None
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value if isinstance(value, (bool, int, float, str)) else str(value)


def _optional_text(value: object) -> str | None:
    """Return non-empty text or None for an unknown value."""
    scalar = _json_value(value)
    if scalar is None:
        return None
    text = str(scalar).strip()
    return text or None


def _source_link(row: pd.Series) -> str | None:
    """Return the first populated source-link column without inventing one."""
    for column in _LINK_COLUMNS:
        if column in row:
            link = _optional_text(row[column])
            if link is not None:
                return link
    return None


def _fact(row: pd.Series) -> dict[str, JsonValue]:
    """Convert one statement row to a code-safe evidence record."""
    return {
        "record_id": _optional_text(row.get("record_id")),
        "kind": _optional_text(row.get("kind")),
        "subtype": _optional_text(row.get("subtype")),
        "published_date": _optional_text(row.get("published_date")),
        "period_start": _optional_text(row.get("period_start")),
        "period_end": _optional_text(row.get("period_end")),
        "detail": _optional_text(row.get("detail")),
        "link": _source_link(row),
    }


def get_facts(
    code: str,
    quarter: str,
    tables: TablesSource = None,
) -> list[dict[str, JsonValue]]:
    """Return published statements available by the requested quarter-end."""
    frame = _require_table(_resolve_tables(tables), "statements")
    published = pd.to_datetime(frame["published_date"], format="mixed", errors="coerce")
    cutoff_date = qend(qindex(quarter)).date()
    selected = frame.loc[frame["code"].eq(code) & published.dt.date.le(cutoff_date)].copy()
    selected["__published_at"] = published.loc[selected.index]
    sort_columns = ["__published_at"]
    if "record_id" in selected:
        sort_columns.append("record_id")
    selected = selected.sort_values(sort_columns, kind="stable")
    return [_fact(row) for _, row in selected.iterrows()]


def _is_false(value: object) -> bool:
    """Return whether a boolean field is explicitly false."""
    if value is False:
        return True
    return isinstance(value, str) and value.strip().casefold() == "false"


def _kpi_record(row: pd.Series) -> dict[str, JsonValue]:
    """Convert one KPI row to the public inspection-field contract."""
    record: dict[str, JsonValue] = {
        "quarter": _optional_text(row.get("quarter")),
    }
    for output_name, source_name in _KPI_FIELDS:
        record[output_name] = _json_value(row.get(source_name))
    if _is_false(record["K4"]):
        record["level_label"] = "not assessable"
        record["level_word"] = "not assessable"
    return record


def _previous_rows(frame: pd.DataFrame, code: str, quarter: str) -> pd.DataFrame:
    """Return the compound's earlier KPI rows in chronological order."""
    rows = frame.loc[frame["code"].eq(code)].copy()
    rows = rows.loc[rows["quarter"].astype(str).lt(str(quarter))]
    sort_column = "qi" if "qi" in rows else "quarter"
    return rows.sort_values(sort_column, kind="stable")


def get_kpis(
    code: str,
    quarter: str,
    tables: TablesSource = None,
    history: int = 8,
) -> dict[str, JsonValue]:
    """Return one compound-quarter KPI record and its earlier-quarter series."""
    if history < 0:
        raise ValueError("history must be zero or greater")
    frame = _require_table(_resolve_tables(tables), "kpi_values")
    rows = frame.loc[frame["code"].eq(code) & frame["quarter"].eq(quarter)]
    if rows.empty:
        raise LookupError(f"No KPI row for code '{code}' and quarter '{quarter}'")
    current = rows.iloc[0]
    result = _kpi_record(current)
    earlier = _previous_rows(frame, code, quarter).tail(history)
    result["series"] = [_kpi_record(row) for _, row in earlier.iterrows()]
    result["origin"] = _json_value(current.get("origin"))
    result["run_id"] = _optional_text(current.get("run_id"))
    result["computed_at"] = _optional_text(current.get("computed_at"))
    return result


def _missing_images() -> dict[str, JsonValue]:
    """Return the explicit image-unavailable response."""
    return dict(_MISSING_IMAGES)


def _image_rows(frame: pd.DataFrame, code: str) -> list[pd.Series]:
    """Return at most one source row for each image position."""
    matching = frame.loc[frame["code"].eq(code)].copy()
    selected = []
    for image_type in ("before", "after"):
        rows = matching.loc[matching["image_type"].astype(str).str.casefold().eq(image_type)]
        if not rows.empty:
            selected.append(rows.iloc[0])
    return selected


def get_images(
    code: str,
    images_path: str | Path | None = None,
) -> dict[str, JsonValue]:
    """Return source Wayback image metadata or an explicit missing status."""
    path = Path(images_path) if images_path is not None else APP / "images" / "images.csv"
    if not path.is_file():
        return _missing_images()
    frame = pd.read_csv(path)
    required = {"code", "image_type", "capture_date", "attribution", "path"}
    missing_columns = sorted(required.difference(frame.columns))
    if missing_columns:
        raise ValueError(f"Image table is missing columns: {', '.join(missing_columns)}")
    rows = _image_rows(frame, code)
    if not rows:
        return _missing_images()
    images = [
        {
            "image_type": _optional_text(row.get("image_type")),
            "capture_date": _optional_text(row.get("capture_date")),
            "attribution": _optional_text(row.get("attribution")),
            "path": _optional_text(row.get("path")),
        }
        for row in rows
    ]
    return {"status": "available", "images": images}


def _normalized_article(value: object) -> str:
    """Normalize an article identifier for conservative matching."""
    text = str(value).strip().casefold()
    text = re.sub(r"^(?:article|art)\s*", "", text)
    return re.sub(r"\s+", "", text)


def _article_matches(value: object, selector: str) -> bool:
    """Match an exact article or a parent article number."""
    target = _normalized_article(value)
    wanted = _normalized_article(selector)
    if target == wanted:
        return True
    return bool(re.fullmatch(r"\d+", wanted)) and target.startswith(f"{wanted}(")


def _rule_rows(frame: pd.DataFrame, articles: str | Sequence[str]) -> list[bool]:
    """Return one article-selection mask per dataframe row."""
    columns = [column for column in _ARTICLE_COLUMNS if column in frame]
    selectors = [articles] if isinstance(articles, str) else list(articles)
    if not columns or not selectors:
        return [False] * len(frame)
    return [
        any(
            _article_matches(row[column], selector)
            for column in columns
            for selector in selectors
        )
        for _, row in frame.iterrows()
    ]


def get_rules(
    query: str | None = None,
    articles: str | Sequence[str] | None = None,
    path: str | Path | None = None,
) -> list[dict[str, JsonValue]]:
    """Return matching rows from the Decree 2184 reference CSV."""
    source_path = Path(path) if path is not None else SRC / CFG["sources"]["decree"]
    if not source_path.is_file():
        raise FileNotFoundError(
            "Decree 2184 reference CSV for config key 'sources.decree' not found: "
            f"{source_path}. Mount F: under /mnt/f when using the configured path."
        )
    frame = pd.read_csv(source_path)
    selected = frame
    if articles is not None:
        mask = _rule_rows(selected, articles)
        selected = selected.loc[mask]
    if query is not None:
        needle = query.strip().casefold()
        mask = selected.apply(
            lambda row: any(
                needle in str(value).casefold()
                for value in row
                if isinstance(value, str)
            ),
            axis=1,
        )
        selected = selected.loc[mask]
    return [
        {str(column): _json_value(value) for column, value in row.items()}
        for _, row in selected.iterrows()
    ]
