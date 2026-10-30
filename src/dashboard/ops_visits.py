"""ops_visits form (T-NA-04): record the result of each inspection visit.

Saves to app_data/ops_visits.csv (append-only) and lists past visits below
the form. Plain local file I/O, no live computation.

Integration (in app.py, e.g. inside screen_compound_file):
    from src.dashboard.ops_visits import render_ops_visits_form
    render_ops_visits_form()
"""

from __future__ import annotations

import csv
import os
import re
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

# Same data root as app.py (override with SPACEEYE_APP_DATA); default "app_data".
APP_DATA = Path(os.environ.get("SPACEEYE_APP_DATA", "app_data"))
OPS_VISITS_PATH = APP_DATA / "ops_visits.csv"

COLUMNS = ["code", "date", "result", "note"]
RESULT_OPTIONS = ["progressing", "stalled", "complete", "not done"]

# Project rule: codes only (C01, C12, D03 ...), never compound/developer names.
CODE_PATTERN = re.compile(r"^[CD]\d{2,3}$")


# --------------------------------------------------------------------------- #
# Logic (unchanged: no Streamlit calls here)
# --------------------------------------------------------------------------- #

def normalise_code(raw: str) -> str:
    """Trim spaces and upper-case, so ' c07 ' is stored as 'C07'."""
    return raw.strip().upper()


def validate_code(code: str) -> str | None:
    """Return an error message, or None when the code is acceptable."""
    if not code:
        return "Please enter a code before saving."
    if not CODE_PATTERN.match(code):
        return "Use a code such as C07 (codes only, no compound or developer names)."
    return None


def append_visit(record: dict[str, str]) -> None:
    """Append one row to ops_visits.csv; create the folder/file (with headers) if needed."""
    OPS_VISITS_PATH.parent.mkdir(parents=True, exist_ok=True)  # make sure app_data/ exists
    is_new = not OPS_VISITS_PATH.exists() or OPS_VISITS_PATH.stat().st_size == 0

    # BOM only when creating the file, so Excel opens Arabic notes correctly
    # without repeating the BOM on every appended row.
    encoding = "utf-8-sig" if is_new else "utf-8"
    with OPS_VISITS_PATH.open("a", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if is_new:
            writer.writeheader()
        writer.writerow({col: record[col] for col in COLUMNS})


def load_visits() -> pd.DataFrame | None:
    """Previously recorded visits, or None if nothing has been saved yet."""
    if not OPS_VISITS_PATH.exists():
        return None
    return pd.read_csv(OPS_VISITS_PATH, dtype=str, keep_default_na=False,
                       encoding="utf-8-sig")


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #

def _borderless_form(key: str):
    """st.form without its own border, so it does not double up inside the card.

    The `border` argument only exists in newer Streamlit versions; older ones
    simply keep the default form border.
    """
    try:
        return st.form(key, clear_on_submit=True, border=False)
    except TypeError:
        return st.form(key, clear_on_submit=True)


def _render_form_card() -> None:
    """The input card. Saving logic is exactly the same as before."""
    with st.container(border=True):
        st.markdown("#### 📝 Record a visit")
        st.caption("Codes only (e.g. C07). Do not write compound or developer names.")

        with _borderless_form("ops_visits_form"):
            # Row 1: code and date side by side
            col_code, col_date = st.columns(2)
            code = col_code.text_input("Code", placeholder="e.g. C07")
            visit_date = col_date.date_input("Date", value=date.today())

            # Row 2: result (half width, matches the column grid above)
            col_result, _ = st.columns(2)
            result = col_result.selectbox("Result", RESULT_OPTIONS)

            # Row 3: free-text note, full width
            note = st.text_area(
                "Note",
                placeholder="Optional: what was seen on site.",
                height=110,
            )

            submitted = st.form_submit_button("💾 Save visit", type="primary")

    if not submitted:
        return

    code = normalise_code(code)
    error = validate_code(code)
    if error:
        st.warning(error)
        return

    try:
        append_visit({
            "code": code,
            "date": visit_date.isoformat(),
            "result": result,
            "note": note.strip(),
        })
    except OSError as exc:  # e.g. file open in Excel, no write permission
        st.error(f"Could not save the visit: {exc}")
    else:
        st.success(f"Visit saved for {code} ({result}, {visit_date.isoformat()}).")


def _render_visits_card() -> None:
    """Metrics + table of recorded visits (newest first)."""
    # Read after the save, so the new row shows up immediately (not cached on purpose).
    visits = load_visits()
    if visits is None or visits.empty:
        return

    with st.container(border=True):
        st.markdown("#### 🗒️ Recorded visits")

        total = len(visits)
        last_date = visits["date"].max() if "date" in visits.columns else "-"
        stalled = int((visits["result"] == "stalled").sum())

        m_total, m_last, m_stalled = st.columns(3)
        m_total.metric("Total visits", total)
        m_last.metric("Latest visit", last_date)
        m_stalled.metric("Stalled", f"{stalled} of {total}")

        st.dataframe(
            visits.iloc[::-1],  # newest first
            use_container_width=True,
            hide_index=True,
            column_config={
                "code": st.column_config.TextColumn("Code", width="small"),
                "date": st.column_config.TextColumn("Date", width="small"),
                "result": st.column_config.TextColumn("Result", width="small"),
                "note": st.column_config.TextColumn("Note", width="large"),
            },
        )
        st.caption(f"Stored in {OPS_VISITS_PATH.as_posix()}")


def render_ops_visits_form() -> None:
    """Visit form card + recorded-visits card."""
    _render_form_card()
    _render_visits_card()