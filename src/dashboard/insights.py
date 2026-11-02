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


def cycle_changes(kpis: pd.DataFrame, asof: str) -> dict | None:
    """Who joined and who left the visit list since the previous quarter, with the level before and now."""
    quarters = sorted(q for q in kpis["quarter"].astype(str).unique() if q < asof)
    if not quarters:
        return None
    before, now = (kpis[kpis["quarter"].astype(str) == q].set_index("code") for q in (quarters[-1], asof))
    on_before, on_now = set(before.index[before["cycle_rank"].notna()]), set(now.index[now["cycle_rank"].notna()])

    def moved(codes: set[str]) -> list[dict]:
        return [{"code": c, "was": level_number(before["level"].get(c)), "now": level_number(now["level"].get(c)),
                 "why": short_reason(now["reason"].get(c))} for c in sorted(codes)]
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
    confirmed = statements["verdict"].astype(str).str.startswith("CONFIRMED")
    return statements[confirmed & (published <= pd.Period(asof, "Q").end_time)]


def upcoming_promises(statements: pd.DataFrame, codes: list[str], asof: str) -> list[dict]:
    """Confirmed promised dates still ahead, soonest first: the next claims a visit can check.

    A promise is dropped when a later-published confirmed promise of the same compound moves the date out.
    """
    confirmed = _confirmed(statements[statements["code"].isin(codes)], asof)
    promises = confirmed[confirmed["kind"] == "promise"].assign(
        published=lambda d: pd.to_datetime(d["published_date"]), ends=lambda d: pd.to_datetime(d["period_end"]))
    rows = []
    for _, r in promises[promises["ends"] > pd.Period(asof, "Q").end_time].iterrows():
        later = promises[(promises["code"] == r["code"]) & (promises["published"] > r["published"])]
        if (later["ends"] > r["ends"]).any():
            continue
        rows.append({"code": str(r["code"]), "claim": claim_text(r), "said": month_text(r["published_date"]),
                     "end": str(r["ends"].date())})
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

OUTCOME_WORDS = {
    "partial_delivery_late_completion_postponed": "partly handed over late, completion postponed",
    "postponed_twice_not_yet_delivered": "handover postponed twice, not yet delivered",
    "delivered_late": "handed over late",
}
BASELINE_LABEL = "Hypothetical baseline (generated finance)"
NUMBER_WORDS = ("No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten")


def _flag(value: object) -> bool:
    return not is_missing(value) and bool(value)


def outcome_text(outcome_type: object) -> str:
    if is_missing(outcome_type):
        return "outcome not on file"
    kind = str(outcome_type).strip()
    return OUTCOME_WORDS.get(kind, kind.replace("_", " "))


def short_reason(text: object) -> str:
    """A stored English level reason without the level prefix, the activity score or the image count."""
    if is_missing(text):
        return ""
    body = re.sub(r"\s*\(activity score [^)]*\)", "", str(text).split(": ", 1)[-1])
    body = re.sub(r"(\d+) quarter\(s\)", lambda m: f"{m[1]} quarter{'' if m[1] == '1' else 's'}", body)
    clauses = [c.strip(" .") for c in body.split(";") if c.strip(" .") and not c.strip().startswith("observation")]
    return "; ".join(clauses)


def what_space_saw(why: object) -> str:
    """`short_reason` as a sentence start."""
    text = short_reason(why)
    return text[:1].upper() + text[1:]


def warning_case(cases: pd.DataFrame) -> dict | None:
    """The public late case flagged earliest after construction started, from the frozen-clock backtest."""
    hits = cases[cases["after_start"].map(_flag)]
    if hits.empty:
        return None
    case = hits.sort_values("after_start_months_before", ascending=False).iloc[0]
    outcome, _, rest = str(case["what_happened"]).partition(";")
    reported = re.search(r"outcome date (\d{4}-\d{2}-\d{2})", rest)
    return {"code": str(case["code"]), "alert": str(case["first_alert_quarter"]),
            "months": int(case["after_start_months_before"]), "deadline": month_text(case["first_deadline"]),
            "saw": what_space_saw(case["why"]),
            "freeze": str(case["freeze_date"])[:10], "level_at_freeze": level_number(case["level_at_freeze"]),
            "outcome": outcome_text(outcome),
            "reported": month_text(reported[1]) if reported else ""}


def first_frame_after(frames: list[dict], when: pd.Timestamp) -> int | None:
    return next((i for i, f in enumerate(frames) if pd.Timestamp(f["date"]) > when), None)


def frame_pair(frames: list[dict], index: int | None) -> list[dict]:
    """The frame at `index` and the latest one; just the latest when there is no index or they coincide."""
    if not frames:
        return []
    return [frames[index], frames[-1]] if index is not None and index != len(frames) - 1 else frames[-1:]


def flagged_early(latest: pd.DataFrame) -> list[dict]:
    """Visit-list compounds flagged with no handover date passed (none announced, or still ahead), leaving out
    those that may already be handed over."""
    on_list = latest[latest["cycle_rank"].notna()].sort_values("cycle_rank")
    early = on_list[(on_list["k3_first_deadline"].isna() | (on_list["K3"].fillna(0) == 0))
                    & ~on_list["may_be_complete"].map(_flag)]
    return [{"code": str(r["code"]), "level": level_number(r["level"]), "why": short_reason(r["reason"])}
            for _, r in early.iterrows()]


def strongest_claim(latest: pd.DataFrame, statements: pd.DataFrame, asof: str) -> dict | None:
    """The compound furthest past its first announced date among those with confirmed public claims."""
    confirmed = _confirmed(statements, asof)
    pool = latest[latest["code"].isin(confirmed["code"]) & latest["K3"].notna()]
    if pool.empty:
        return None
    row = pool.sort_values("K3", ascending=False).iloc[0]
    code = str(row["code"])
    last = pd.to_datetime(confirmed.loc[confirmed["code"] == code, "published_date"]).max()
    return {"code": code, "k3": int(row["K3"]), "deadline": month_text(row["k3_first_deadline"]), "last_claim": last}


def homes_waiting(compounds: pd.DataFrame, latest: pd.DataFrame) -> dict:
    """Real unit counts of compounds with fine-eligible months; generated unit counts are left out."""
    real = compounds.loc[compounds["units_origin"] == "real", ["code", "units"]]
    rows = real.merge(latest[["code", "level", "K5_months"]], on="code")
    rows = rows[rows["K5_months"] > 0].sort_values(["units", "code"], ascending=[False, True])
    items = [{"code": str(r["code"]), "units": int(r["units"]), "k5": int(r["K5_months"]),
              "level": level_number(r["level"])} for _, r in rows.iterrows()]
    return {"rows": items, "homes": sum(i["units"] for i in items), "compounds": len(items)}


def late_delays(outcomes: pd.DataFrame) -> dict:
    """Months each public case ran past its original promise, longest first, and the cases with no value yet."""
    known = outcomes.dropna(subset=["delay_months_vs_promise"]).sort_values(
        ["delay_months_vs_promise", "code"], ascending=[False, True])
    rows = [{"code": str(c), "months": int(m)} for c, m in zip(known["code"], known["delay_months_vs_promise"])]
    return {"rows": rows, "median": float(known["delay_months_vs_promise"].median()),
            "pending": sorted(outcomes.loc[outcomes["delay_months_vs_promise"].isna(), "code"].astype(str))}


def fine_months(latest: pd.DataFrame) -> dict:
    """Fine-eligible months per compound, most first; the contract decides whether a fine applies."""
    rows = latest[latest["K5_months"] > 0].sort_values(["K5_months", "code"], ascending=[False, True])
    items = [{"code": str(c), "months": int(m)} for c, m in zip(rows["code"], rows["K5_months"])]
    return {"rows": items, "total": sum(i["months"] for i in items), "compounds": len(items)}


def codes_by_current_level(history: pd.DataFrame) -> list[str]:
    """Compound codes with the most urgent current level first; not assessable last."""
    now = history[history["quarter"] == history["quarter"].max()].set_index("code")["level"].fillna(9)
    return sorted(history["code"].unique(), key=lambda c: (now.get(c, 9), c))


def scenario_view(raw: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """The latest month of one finance scenario: baseline versus scenario level and list membership."""
    month = str(raw["month"].max())
    latest = raw[raw["month"].astype(str) == month]
    view = pd.DataFrame({
        "code": latest["code"].astype(str).to_numpy(),
        "baseline_level": latest["baseline_hypothetical_level"].map(level_number).astype("float64").to_numpy(),
        "level": latest["hypothetical_level"].map(level_number).astype("float64").to_numpy(),
        "baseline_listed": latest["baseline_selected"].map(_flag).to_numpy(),
        "listed": latest["selected"].map(_flag).to_numpy(),
        "reason": latest["reason"].fillna("").astype(str).to_numpy(),
    })
    same_level = (view["baseline_level"] == view["level"]) | (view["baseline_level"].isna() & view["level"].isna())
    view["changed"] = ~same_level | (view["baseline_listed"] != view["listed"])
    return view, month


def progress_view(raw: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Latest month of the stored progress-vs-baseline table: baseline and each finance scenario, in percent points."""
    month = str(raw["month"].max())
    latest = raw[raw["month"].astype(str) == month]
    s1 = latest[latest["scenario_id"] == "S1"].set_index("code")
    s2 = latest[latest["scenario_id"] == "S2"].set_index("code").reindex(s1.index)
    view = pd.DataFrame({
        "Compound": s1.index.astype(str),
        "Baseline progress (% of whole project)": s1["baseline_progress_pct"].round(1).to_numpy(),
        "S1 cost shock (% of whole project)": s1["scenario_progress_pct"].round(1).to_numpy(),
        "S1 change (pp)": s1["delta_pp"].round(2).to_numpy(),
        "S2 collections drop (% of whole project)": s2["scenario_progress_pct"].round(1).to_numpy(),
        "S2 change (pp)": s2["delta_pp"].round(2).to_numpy(),
    })
    return view, month


def level_counts(view: pd.DataFrame) -> pd.DataFrame:
    """How many compounds sit at each hypothetical level (NaN = not assessable), baseline and scenario."""
    both = pd.concat([pd.DataFrame({"case": case, "level": view[column]})
                      for case, column in ((BASELINE_LABEL, "baseline_level"), ("Scenario", "level"))])
    return both.groupby(["case", "level"], dropna=False).size().rename("compounds").reset_index()


METRIC_COLUMNS = {  # stored metric/class -> column header (generated numbers carry the orange marker)
    ("class_recall", "distressed"): "🟠 Distressed recall",
    ("class_recall", "not_distressed"): "🟠 Not-distressed recall",
    ("macro_f1_binary", "all"): "🟠 Macro-F1",
    ("distressed_recall_at_4", "distressed"): "🟠 Distressed in top 4 (recall@4)",
}


def _metric_cell(row: pd.Series) -> str:
    if row["metric"] == "macro_f1_binary":
        return f"{row['value']:.3f} ({int(row['denominator'])} rows)"
    return f"{int(row['numerator'])} of {int(row['denominator'])}"


def model_metrics_table(metrics: pd.DataFrame, random_at_4: dict | None = None,
                        view: str = "time_test") -> pd.DataFrame:
    """One row per stored method for one evaluation view, each cell as stored ("n of m");
    the stored random recall@4 baseline is appended as its own row. Nothing is recomputed."""
    rows = metrics[metrics["view"] == view]
    table = pd.DataFrame({"Method": pd.unique(rows["method"])}).set_index("Method")
    for column in METRIC_COLUMNS.values():
        table[column] = "not stored"
    for _, row in rows.iterrows():
        column = METRIC_COLUMNS.get((row["metric"], row["class"]))
        if column:
            table.loc[row["method"], column] = _metric_cell(row)
    if random_at_4:
        random_row = dict.fromkeys(METRIC_COLUMNS.values(), "not stored")
        random_row["🟠 Distressed in top 4 (recall@4)"] = (
            f"{random_at_4['mean']:.3f} (mean of {int(random_at_4['draws']):,} random draws)")
        table.loc["random"] = random_row
    return table.reset_index()
