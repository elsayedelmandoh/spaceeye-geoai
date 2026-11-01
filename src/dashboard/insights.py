"""Dashboard data builders: pure functions over stored tables, no Streamlit.

The screens in app.py only render what these return, so every number can be unit-tested.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

LEVEL_NUMBERS = (1, 2, 3, 4)

# Proposals for the committee to set, not stored rules: they only raise the suggested action.
WARNING_K3_MONTHS = 12
WARNING_K2_QUARTERS = 4
FINE_REVIEW_K5_MONTHS = 12

FRAME_NEAR_DAYS = 366  # a claim is paired with a picture only if one was captured within a year
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
PROMISE_WORDS = {
    "promised_delivery": "handover",
    "promised_delivery_start": "handover start",
    "promised_delivery_phase1": "phase 1 handover",
    "promised_delivery_phase2": "phase 2 handover",
    "promised_completion": "completion",
}
PROGRESS_WORDS = {"exact": "", "over": "over ", "about": "about "}

# The stored reasons are Arabic; these keep their counted nouns and dates readable.
ARABIC_MONTHS = ("يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر",
                 "أكتوبر", "نوفمبر", "ديسمبر")
COUNT_NOUNS = {"شهر": ("أشهر", "شهرًا"), "ربع": ("أرباع", "ربعًا")}
DUALS = {"شهر": "شهرين", "ربع": "ربعين"}


def is_missing(value: object) -> bool:
    return value is None or bool(pd.isna(value))


def level_number(level: object) -> int | None:
    try:
        return int(level) if int(level) in LEVEL_NUMBERS else None
    except (TypeError, ValueError):
        return None


def month_text(value: object) -> str:
    stamp = pd.Timestamp(value)
    return f"{MONTHS[stamp.month - 1]} {stamp.year}"


def month_ar(value: object) -> str:
    stamp = pd.Timestamp(value)
    return f"{ARABIC_MONTHS[stamp.month - 1]} {stamp.year}"


def count_ar(n: int, noun: str) -> str:
    """Arabic counted noun after a digit: 3-10 take the plural, 11-99 the accusative singular."""
    few, many = COUNT_NOUNS[noun]
    rest = n % 100
    return few if 3 <= rest <= 10 else many if rest >= 11 else noun


def count_phrase(n: int, noun: str) -> str:
    """A count inside running text: one and two are said in words, as Arabic does."""
    return f"{noun} واحد" if n == 1 else DUALS[noun] if n == 2 else f"{n} {count_ar(n, noun)}"


def short_reason_ar(text: object) -> str:
    """An Arabic level reason without the level prefix, the activity score or the image count."""
    if is_missing(text):
        return ""
    body = re.sub(r"\s*\(درجة النشاط [^)]*\)", "", str(text).split(": ", 1)[-1])
    body = re.sub(r"(\d+) (شهر|ربع)(?=\s|؛|$|\.)", lambda m: count_phrase(int(m[1]), m[2]), body)
    body = re.sub(r"\((\d{4}-\d{2}-\d{2})\)", lambda m: f"({month_ar(m[1])})", body)
    clauses = [c.strip(" .") for c in body.split("؛") if c.strip(" .") and not c.strip().startswith("عدد الصور")]
    return "، ".join(clauses)


def cycle_changes(kpis: pd.DataFrame, asof: str) -> dict | None:
    """Who joined and who left the visit list since the previous quarter, with the level before and now."""
    quarters = sorted(q for q in kpis["quarter"].astype(str).unique() if q < asof)
    if not quarters:
        return None
    before, now = (kpis[kpis["quarter"].astype(str) == q].set_index("code") for q in (quarters[-1], asof))
    on_before, on_now = set(before.index[before["cycle_rank"].notna()]), set(now.index[now["cycle_rank"].notna()])

    def moved(codes: set[str]) -> list[dict]:
        return [{"code": c, "was": level_number(before["level"].get(c)), "now": level_number(now["level"].get(c)),
                 "why": short_reason_ar(now["reason_ar"].get(c))} for c in sorted(codes)]
    return {"prev": quarters[-1], "joined": moved(on_now - on_before), "left": moved(on_before - on_now)}


def period_text(start: object, end: object) -> str:
    """A promised period in words: a month, a calendar year, a month range, or 'by' an end date."""
    if is_missing(end):
        return "with no date"
    end = pd.Timestamp(end)
    if is_missing(start):
        return f"by {month_text(end)}"
    start = pd.Timestamp(start)
    if start.month == 1 and end.month == 12 and start.year == end.year:
        return f"in {end.year}"
    if (start.year, start.month) == (end.year, end.month):
        return month_text(end)
    first = MONTHS[start.month - 1] if start.year == end.year else month_text(start)
    return f"{first}-{month_text(end)}"


def progress_amount(row: pd.Series) -> str:
    return f"{PROGRESS_WORDS.get(row['qualifier'], '')}{float(row['value']):.0f}%"


def claim_text(row: pd.Series) -> str:
    if row["kind"] == "progress":
        return f"progress {progress_amount(row)}"
    word = PROMISE_WORDS.get(row["subtype"], "handover")
    return f"promised {word} {period_text(row['period_start'], row['period_end'])}"


def _confirmed(statements: pd.DataFrame, asof: str) -> pd.DataFrame:
    """Confirmed claims published by the end of the quarter."""
    published = pd.to_datetime(statements["published_date"], errors="coerce")
    return statements[(statements["verdict"] == "CONFIRMED") & (published <= pd.Period(asof, "Q").end_time)]


def upcoming_promises(statements: pd.DataFrame, codes: list[str], asof: str) -> list[dict]:
    """Confirmed promised dates still ahead, soonest first: the next claims a visit can check."""
    confirmed = _confirmed(statements[statements["code"].isin(codes)], asof)
    ahead = confirmed[(confirmed["kind"] == "promise")
                      & (pd.to_datetime(confirmed["period_end"]) > pd.Period(asof, "Q").end_time)]
    rows = [{"code": str(r["code"]), "claim": claim_text(r), "said": month_text(r["published_date"]),
             "end": str(pd.Timestamp(r["period_end"]).date())} for _, r in ahead.iterrows()]
    return sorted(rows, key=lambda r: (r["end"], r["code"]))


def developer_groups(compounds: pd.DataFrame, latest: pd.DataFrame) -> list[dict]:
    """Developers with more than one compound: one meeting can cover all of them, most urgent first."""
    levels = dict(zip(latest["code"], latest["level"]))
    groups = []
    for developer, part in compounds.groupby("developer_code"):
        if len(part) < 2:
            continue
        items = sorted(({"code": c, "level": level_number(levels.get(c))} for c in part["code"]),
                       key=lambda i: (i["level"] or 9, i["code"]))
        groups.append({"developer": str(developer), "compounds": items})
    return sorted(groups, key=lambda g: (g["compounds"][0]["level"] or 9, -len(g["compounds"]), g["developer"]))


def timeline_frames(code: str, root: Path) -> list[tuple[str, Path]]:
    """The dated Wayback captures of one compound, oldest first, as (date, image path)."""
    pattern = re.compile(rf"{re.escape(code)}_\d+_(\d{{4}}-\d{{2}}-\d{{2}})\.jpg")
    hits = [(m[1], path) for path in (root / code).glob(f"{code}_*.jpg") if (m := pattern.fullmatch(path.name))]
    return sorted(hits)


def nearest_frame(frames: list[dict], when: pd.Timestamp) -> int | None:
    gaps = [abs((pd.Timestamp(f["date"]) - when).days) for f in frames]
    return None if not gaps or min(gaps) > FRAME_NEAR_DAYS else gaps.index(min(gaps))


def promise_rows(statements: pd.DataFrame, frames: list[dict], stages: dict[int, str], asof: str) -> list[dict]:
    """One compound's confirmed public claims, oldest first, each beside the nearest picture.

    `frames` are dicts with a capture `date`; `stages` maps a year to its construction stage.
    """
    now = pd.Period(asof, "Q").end_time
    rows = []
    for _, r in _confirmed(statements, asof).sort_values("published_date").iterrows():
        said = pd.Timestamp(r["published_date"])
        due = None
        if r["kind"] == "promise" and not is_missing(r["period_end"]):
            end = pd.Timestamp(r["period_end"])
            due = {"year": end.year, "passed": bool(end < now), "stage": stages.get(end.year) if end < now else None}
        near = nearest_frame(frames, said)
        capture = None if near is None else {
            "date": str(frames[near]["date"]), "stage": stages.get(int(str(frames[near]["date"])[:4]))}
        rows.append({"said": month_text(said), "claim": claim_text(r), "due": due, "capture": capture})
    return rows


def level_history(kpis: pd.DataFrame) -> pd.DataFrame:
    """Tidy code, quarter, level (NaN when not assessable), oldest quarter first."""
    out = kpis[["code", "quarter", "level"]].copy()
    out["quarter"] = out["quarter"].astype(str)
    out["level"] = out["level"].map(level_number).astype("float64")
    return out.sort_values(["code", "quarter"]).reset_index(drop=True)


def k3_text(row: pd.Series) -> str | None:
    """Why K3 is not shown as a number: no deadline, or a passed date on a compound that may be done."""
    if is_missing(row.get("k3_first_deadline")):
        return "no announced handover date"
    if not is_missing(row.get("may_be_complete")) and bool(row.get("may_be_complete")) and row.get("K3") == 0:
        return "date passed, may be handed over: confirm on site"
    return None


def _at_least(value: object, threshold: int) -> bool:
    return not is_missing(value) and float(value) >= threshold


def suggested_action(row: pd.Series) -> tuple[str, str]:
    """The next step the stored levels and clocks point to, as a suggestion for the committee."""
    level = level_number(row.get("level"))
    k2, k3, k5 = row.get("K2"), row.get("K3"), row.get("K5_months")
    if level is None:
        return "No action", "Not assessable this quarter."
    if level in (1, 2) and _at_least(k5, FINE_REVIEW_K5_MONTHS):
        return "Fine review", f"{int(k5)} fine-eligible months (proposal: {FINE_REVIEW_K5_MONTHS})."
    # A compound that may already be handed over is confirmed first: its quiet site is no stall.
    if level in (3, 4) and not is_missing(row.get("may_be_complete")) and bool(row.get("may_be_complete")):
        return ("Confirm handover on site", "The handover was announced and the compound may be complete.")             if level == 3 else ("Monitor", "Routine level; the compound may be complete.")
    if _at_least(k3, WARNING_K3_MONTHS):
        return "Written warning", f"{int(k3)} months past the first announced date (proposal: {WARNING_K3_MONTHS})."
    if _at_least(k2, WARNING_K2_QUARTERS):
        return "Written warning", f"{int(k2)} quarters without activity (proposal: {WARNING_K2_QUARTERS})."
    if level == 4:
        return "Monitor", "Routine level."
    if level == 3:
        return "Document review", "Check the file before spending a visit."
    if level == 2:
        return "Visit this cycle", "On the visit list this quarter."
    return "Visit now", "Highest priority this quarter."
