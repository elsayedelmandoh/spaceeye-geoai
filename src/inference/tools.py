"""Plain-Python data tools for cutoff-controlled inspection files."""

from __future__ import annotations

import json
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


class _FactRecords(list[dict[str, JsonValue]]):
    """Expose statement records with backward-compatible compound metadata."""

    def __init__(
        self,
        records: list[dict[str, JsonValue]],
        metadata: dict[str, JsonValue],
    ) -> None:
        super().__init__(records)
        self.metadata = metadata

    def __getitem__(self, key: int | slice | str) -> JsonValue | list[dict[str, JsonValue]]:
        if isinstance(key, str):
            return self.metadata[key]
        return super().__getitem__(key)

    def get(self, key: str, default: JsonValue = None) -> JsonValue:
        return self.metadata.get(key, default)

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str) and item in self.metadata:
            return True
        return super().__contains__(item)


_REAL_TABLES = ("statements", "kpi_values", "compounds")
_COMPOUND_FIELDS = (
    "developer_code",
    "district",
    "land_area_m2",
    "land_area_origin",
    "floors_allowed",
    "floors_origin",
    "units",
    "units_origin",
    "boundary_confidence",
)
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
    ("level_word_ar", "level_word_ar"),
    ("cycle_rank", "cycle_rank"),
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


def quarter_cutoff_date(quarter: str) -> pd.Timestamp:
    """Return the inclusive end of a quarter without reading the clock."""
    return qend(qindex(quarter)) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)


def _compound_row(
    tables: Mapping[str, pd.DataFrame], code: str
) -> pd.Series | None:
    """Return the matching compound row when compound data is available."""
    frame = tables.get("compounds")
    if frame is None:
        return None
    matching = frame.loc[frame["code"].eq(code)]
    return matching.iloc[0] if not matching.empty else None


def _deadline_fact(
    row: pd.Series | None, cutoff_date: object
) -> tuple[JsonValue, JsonValue]:
    """Return a deadline only when its publication was available by cutoff."""
    if row is None:
        return None, None
    published = pd.to_datetime(row.get("first_deadline_published"), errors="coerce")
    deadline = _json_value(row.get("first_deadline"))
    if pd.isna(published) or deadline is None or published.date() > cutoff_date:
        return None, None
    return deadline, _optional_text(row.get("first_deadline_published"))


def _compound_metadata(
    code: str,
    row: pd.Series | None,
    cutoff_date: object,
    statements: list[dict[str, JsonValue]],
) -> dict[str, JsonValue]:
    """Build code-safe compound metadata with unknown values left as None."""
    metadata: dict[str, JsonValue] = {field: None for field in _COMPOUND_FIELDS}
    if row is not None:
        for field in _COMPOUND_FIELDS:
            metadata[field] = _json_value(row.get(field))
    deadline, deadline_published = _deadline_fact(row, cutoff_date)
    metadata.update(
        {
            "code": code,
            "first_deadline": deadline,
            "first_deadline_published": deadline_published,
            "cutoff_date": cutoff_date.isoformat(),
            "published_statements_count": len(statements),
            "published_statements": statements,
        }
    )
    return metadata


def get_facts(
    code: str,
    quarter: str,
    tables: TablesSource = None,
) -> list[dict[str, JsonValue]]:
    """Return published statements available by the requested quarter-end."""
    resolved = _resolve_tables(tables)
    frame = _require_table(resolved, "statements")
    published = pd.to_datetime(frame["published_date"], format="mixed", errors="coerce")
    cutoff_date = quarter_cutoff_date(quarter).date()
    selected = frame.loc[frame["code"].eq(code) & published.dt.date.le(cutoff_date)].copy()
    selected["__published_at"] = published.loc[selected.index]
    sort_columns = ["__published_at"]
    if "record_id" in selected:
        sort_columns.append("record_id")
    statements = [
        _fact(row)
        for _, row in selected.sort_values(sort_columns, kind="stable").iterrows()
    ]
    metadata = _compound_metadata(
        code, _compound_row(resolved, code), cutoff_date, statements
    )
    return _FactRecords(statements, metadata)


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


def _kpi_aliases(record: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Return aliases used by the inspection-file context contract."""
    return {
        "level_word_ar": record["level_word_ar"],
        "K2_stoppage_quarters": record["K2"],
        "K3_delay_months": record["K3"],
        "K4_image_count_sufficient": record["K4"],
        "K5_fine_eligible_months": record["K5_months"],
        "K6_unstarted_months": record["K6"],
        "activity_history": record["series"],
    }


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
    result["code"] = code
    earlier = _previous_rows(frame, code, quarter).tail(history)
    result["series"] = [_kpi_record(row) for _, row in earlier.iterrows()]
    result.update(_kpi_aliases(result))
    result["origin"] = _json_value(current.get("origin"))
    result["run_id"] = _optional_text(current.get("run_id"))
    result["computed_at"] = _optional_text(current.get("computed_at"))
    return result


def _missing_images(status: str = "missing") -> dict[str, JsonValue]:
    """Return the explicit image-unavailable response."""
    return {**_MISSING_IMAGES, "status": status}


def _image_rows(frame: pd.DataFrame, code: str) -> list[pd.Series]:
    """Use an explicit chronological timeline, or the legacy before/after pair."""
    matching = frame.loc[frame["code"].eq(code)].copy()
    if "sequence" in matching:
        matching["sequence"] = pd.to_numeric(matching["sequence"], errors="coerce")
        matching = matching.dropna(subset=["sequence"]).sort_values("sequence", kind="stable")
        return [row for _, row in matching.drop_duplicates("image_type").iterrows()]
    selected = []
    for image_type in ("before", "after"):
        rows = matching.loc[matching["image_type"].astype(str).str.casefold().eq(image_type)]
        if not rows.empty:
            selected.append(rows.iloc[0])
    return selected


def get_images(
    code: str,
    images_path: str | Path | None = None,
    quarter: str | None = None,
) -> dict[str, JsonValue]:
    """Return dated imagery observations; release availability controls historical views."""
    path = Path(images_path) if images_path is not None else APP / "images" / "images.csv"
    missing_status = "missing_image" if images_path is None else "missing"
    if not path.is_file():
        return _missing_images(missing_status)
    frame = pd.read_csv(path)
    required = {"code", "image_type", "capture_date", "attribution", "path"}
    missing_columns = sorted(required.difference(frame.columns))
    if missing_columns:
        raise ValueError(f"Image table is missing columns: {', '.join(missing_columns)}")
    if "release_date" in frame:
        cutoff = qend(qindex(quarter or CFG["asof"]))
        released = pd.to_datetime(frame["release_date"], errors="coerce")
        frame = frame.loc[released.notna() & released.le(cutoff)]
        if "capture_date_max" in frame:
            captured = pd.to_datetime(frame["capture_date_max"], errors="coerce")
            frame = frame.loc[captured.notna() & captured.le(cutoff)]
    elif quarter is not None:
        return {"status": "missing", "images": [], "reason": "Historical image availability is unknown: release dates are absent"}
    rows = _image_rows(frame, code)
    if not rows:
        return _missing_images(missing_status)
    images = [
        {
            "image_type": _optional_text(row.get("image_type")),
            "capture_date": _optional_text(row.get("capture_date")),
            "attribution": _optional_text(row.get("attribution")),
            "path": _optional_text(row.get("path")),
        }
        for row in rows
    ]
    for image, row in zip(images, rows):
        for field in ("capture_date_min", "capture_date_max", "release_date", "source_url", "usage"):
            if field in frame:
                image[field] = _optional_text(row.get(field))
        if "capture_dates" in frame and _optional_text(row.get("capture_dates")):
            image["capture_dates"] = json.loads(str(row["capture_dates"]))
        if "mixed_capture_dates" in frame:
            image["mixed_capture_dates"] = bool(row["mixed_capture_dates"])
        if "sequence" in frame:
            image["sequence"] = int(row["sequence"])
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


def _default_rules_path() -> Path:
    """Return the prepared rules table or the configured canonical source."""
    prepared = REAL / "rules.parquet"
    if prepared.is_file():
        return prepared
    return SRC / CFG["sources"]["decree"]


def get_rules(
    query: str | None = None,
    articles: str | Sequence[str] | None = None,
    path: str | Path | None = None,
) -> list[dict[str, JsonValue]]:
    """Return matching rows from the prepared or configured rules table."""
    source_path = Path(path) if path is not None else _default_rules_path()
    if not source_path.is_file():
        raise FileNotFoundError(
            "Decree 2184 reference CSV for config key 'sources.decree' not found: "
            f"{source_path}. Mount F: under /mnt/f when using the configured path."
        )
    frame = _read_frame(source_path)
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


def _complaint_samples(frame: pd.DataFrame) -> list[dict[str, JsonValue]]:
    """Return recent complaint metadata without exposing complaint text."""
    return [
        {
            "complaint_id": _optional_text(row.get("complaint_id")),
            "category": _optional_text(row.get("category")),
            "created_at": _optional_text(row.get("created_at")),
        }
        for _, row in frame.tail(3).iterrows()
    ]


def get_complaints_summary(
    code: str,
    as_of_quarter: str = "2026Q3",
    complaints_path: str | Path | None = None,
) -> dict[str, JsonValue]:
    """Return synthetic complaint counts available by the requested quarter-end."""
    origin = "generated/synthetic operations — Synthetic - for training only"
    source_path = (
        Path(complaints_path)
        if complaints_path is not None
        else APP / "sim_clean" / "complaints.parquet"
    )
    if not source_path.is_file():
        return {"total_count": None, "recent_samples": None, "origin": origin}
    frame = _read_frame(source_path)
    created = pd.to_datetime(frame["created_at"], format="mixed", errors="coerce")
    cutoff_date = quarter_cutoff_date(as_of_quarter).date()
    selected = frame.loc[frame["code"].eq(code) & created.dt.date.le(cutoff_date)].copy()
    selected["__created_at"] = created.loc[selected.index]
    selected = selected.sort_values("__created_at", kind="stable")
    return {
        "total_count": len(selected),
        "recent_samples": _complaint_samples(selected),
        "origin": origin,
    }


def build_inspection_context(
    code: str, as_of_quarter: str = "2026Q3"
) -> dict[str, JsonValue]:
    """Build a cutoff-controlled inspection context from the public tools."""
    facts = get_facts(code, as_of_quarter)
    kpis = get_kpis(code, as_of_quarter)
    complaints = get_complaints_summary(code, as_of_quarter)
    images = get_images(code)
    rules = get_rules()
    relevant_rule_ids = {"R01", "R06", "R12", "R13", "R17", "R18"}
    applicable_rules = [
        rule for rule in rules if rule.get("rule_id") in relevant_rule_ids
    ]
    return {
        "compound_code": code,
        "quarter": as_of_quarter,
        "cutoff_date": facts.get("cutoff_date"),
        "facts": facts,
        "kpis": kpis,
        "complaints_summary": complaints,
        "images": images,
        "applicable_rules": applicable_rules,
    }
