"""Dashboard data builders: pure functions over stored tables, no Streamlit.

The screens in app.py only render what these return, so every number can be unit-tested.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

LEVEL_NUMBERS = (1, 2, 3, 4)
LEVEL_WORDS = {1: "Inspect now", 2: "Inspect this cycle", 3: "Document review", 4: "Routine"}
NOT_ASSESSABLE_WORD = "Not assessable"

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


def level_word(level: object) -> str:
    """The stored priority level as a word, or the explicit not-assessable label."""
    number = level_number(level)
    return LEVEL_WORDS.get(number, NOT_ASSESSABLE_WORD) if number is not None else NOT_ASSESSABLE_WORD


def level_word_for_row(row: pd.Series) -> str:
    """The dashboard level word for one KPI row, preserving its stored no-level state."""
    if not is_missing(row.get("level")):
        return level_word(row.get("level"))
    for column in ("level_label", "level_word"):
        stored_state = row.get(column)
        if not is_missing(stored_state) and str(stored_state).strip():
            return str(stored_state).strip().capitalize()
    return NOT_ASSESSABLE_WORD


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


def visit_ranks(frame: pd.DataFrame) -> pd.Series:
    """Visit order for every compound of a quarter: the stored cycle list first, then the others by the
    pipeline's own order (level, K2 and K3 descending, then code), unassessed last."""
    in_cycle = frame["cycle_rank"].notna() if "cycle_rank" in frame.columns else pd.Series(False, index=frame.index)
    rest = frame[~in_cycle].assign(_level=lambda d: d["level"].map(lambda v: level_number(v) or 99),
                                   _k2=lambda d: d["K2"].fillna(0) if "K2" in d else 0,
                                   _k3=lambda d: d["K3"].fillna(0) if "K3" in d else 0)
    order = [*frame[in_cycle].sort_values("cycle_rank").index,
             *rest.sort_values(["_level", "_k2", "_k3", "code"], ascending=[True, False, False, True]).index]
    return pd.Series(range(1, len(order) + 1), index=order, dtype="Int64").reindex(frame.index)


def list_status(row: pd.Series) -> str:
    level = level_number(row.get("level"))
    if not is_missing(row.get("cycle_rank")):
        return "This cycle"
    if level is None:
        return "Not assessable"
    return "Monitor" if level == 4 else "Next in line"


HANDOVER_WORDS = {"delivery_complete": "handed over", "delivery_progress": "handover in progress",
                  "delivery_start": "handover started"}


def handover_status(statements: pd.DataFrame, code: str, asof: str) -> str:
    """The latest published handover event up to the quarter, with its scope and publication month."""
    events = statements[(statements["code"] == code) & statements["subtype"].isin(list(HANDOVER_WORDS))
                        & (pd.to_datetime(statements["published_date"]) <= pd.Period(asof, "Q").end_time)]
    if events.empty:
        return "none published"
    last = events.sort_values("published_date").iloc[-1]
    phase = re.fullmatch(r"phase(\d+)", str(last["scope"]))
    words = HANDOVER_WORDS[last["subtype"]]
    return f"{f'phase {phase[1]} ' if phase else ''}{words} (published {month_text(last['published_date'])})"


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


def capture_rows(frames: list[dict], stages: dict[int, str]) -> list[dict]:
    """Stored capture dates with their stored construction stage, oldest first."""
    rows = []
    for capture in sorted(frames, key=lambda stored_frame: str(stored_frame.get("date", ""))):
        date = str(capture.get("date", ""))
        try:
            year = int(date[:4])
        except (TypeError, ValueError):
            year = 0
        rows.append({"date": date, "stage": stages.get(year, "stage not on file")})
    return rows


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
        return "Fine review", (
            f"{int(k5)} months eligible for review under contract terms "
            f"(proposal: {FINE_REVIEW_K5_MONTHS})."
        )
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


def _count_with_unit(value: object, unit: str) -> str:
    if is_missing(value):
        return "unknown"
    number = float(value)
    amount = f"{int(number):,}" if number.is_integer() else f"{number:,.1f}"
    return f"{amount} {unit}{'' if abs(number) == 1 else 's'}"


def compound_panel_rows(row: pd.Series, asof: str, frames: list[dict],
                        stages: dict[int, str]) -> list[dict]:
    """The selected compound's sidebar details, built only from stored values."""
    captures = capture_rows(frames, stages)
    latest_capture = captures[-1] if captures else None
    if row.get("K6_status") == "not_applicable_started" and is_missing(row.get("K6")):
        k6 = "does not apply"
    else:
        k6 = _count_with_unit(row.get("K6"), "month")
    reason = row.get("reason_ar")
    return [
        {"label": "Code", "value": str(row.get("code", ""))},
        {"label": "Priority level", "value": level_word_for_row(row), "detail": f"as of {asof}"},
        {"label": "K2 no activity", "value": _count_with_unit(row.get("K2"), "quarter")},
        {"label": "K3 handover clock", "value": _count_with_unit(row.get("K3"), "month")},
        {"label": "K6 never started", "value": k6},
        {"label": "Reason", "value": "not stored" if is_missing(reason) else str(reason), "direction": "rtl"},
        {"label": "Suggested next action", "value": suggested_action(row)[0]},
        {"label": "Latest capture",
         "value": ("no capture stored" if latest_capture is None
                   else f"{latest_capture['date']} · {latest_capture['stage']}")},
    ]


def signal_history_table(kpis: pd.DataFrame, code: str) -> pd.DataFrame:
    """One compound's level and K2/K3/K6 by quarter, oldest quarter first."""
    columns = ["Quarter", "Level", "K2 (quarters)", "K3 (months)", "K6 (months)"]
    if not {"code", "quarter"} <= set(kpis.columns):
        return pd.DataFrame(columns=columns)
    compound_kpis = kpis[kpis["code"].astype(str) == str(code)].copy()
    compound_kpis["quarter"] = compound_kpis["quarter"].astype(str)
    compound_kpis = compound_kpis.sort_values("quarter")
    table = pd.DataFrame({"Quarter": compound_kpis["quarter"].to_numpy()})
    table["Level"] = [level_word_for_row(stored_row) for _, stored_row in compound_kpis.iterrows()]
    for source, target in (("K2", "K2 (quarters)"), ("K3", "K3 (months)"), ("K6", "K6 (months)")):
        table[target] = (pd.to_numeric(compound_kpis[source], errors="coerce").to_numpy()
                         if source in compound_kpis else [float("nan")] * len(compound_kpis))
    return table.reset_index(drop=True)


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


def short_reason(text: object, deadline_note: str | None = None) -> str:
    """A stored English level reason without the level prefix, the activity score or the image count.

    K2 counts quarters without new building change, so "no building activity" reads "no new building activity";
    `deadline_note` (see `first_deadline_note`) says when the first handover date was only for a phase.
    """
    if is_missing(text):
        return ""
    body = re.sub(r"\s*\(activity score [^)]*\)", "", str(text).split(": ", 1)[-1])
    body = re.sub(r"(\d+) quarter\(s\)", lambda m: f"{m[1]} quarter{'' if m[1] == '1' else 's'}", body)
    body = body.replace("no building activity", "no new building activity")
    if deadline_note:
        body = re.sub(r"first announced handover date \((\w+ \d{4})\)",
                      lambda m: f"first announced handover date ({m[1]}, {deadline_note})", body)
    clauses = [c.strip(" .") for c in body.split(";") if c.strip(" .") and not c.strip().startswith("observation")]
    return "; ".join(clauses)


def first_deadline_note(statements: pd.DataFrame, code: str, deadline: object, asof: str) -> str | None:
    """"phase N; whole project <month>" when the stored first handover date is a phase date: a phase promise
    published by the quarter ends that month and no whole-project promise does. None otherwise."""
    if is_missing(deadline):
        return None
    promises = statements[(statements["code"] == code) & (statements["kind"] == "promise")
                          & statements["period_end"].notna()
                          & (pd.to_datetime(statements["published_date"]) <= pd.Period(asof, "Q").end_time)]
    month = pd.Timestamp(deadline).to_period("M")
    ends = pd.to_datetime(promises["period_end"]).dt.to_period("M")
    phase = promises[(ends == month) & promises["scope"].astype(str).str.fullmatch(r"phase\d+")]
    project = promises[promises["scope"] == "project"]
    if phase.empty or (ends[project.index] == month).any():
        return None
    note = f"phase {str(phase.iloc[0]['scope'])[5:]}"
    if not project.empty:
        note += f"; whole project {month_text(project.sort_values('published_date').iloc[0]['period_end'])}"
    return note


def finance_snapshot(fin: pd.DataFrame, code: str, asof: str) -> dict | None:
    """One compound's generated monthly money at the quarter's last month: collections over the last 12 months
    and the cover balance."""
    end = str(pd.Period(asof, "Q").asfreq("M", "end"))
    mine = fin[(fin["code"] == code) & (fin["month"].astype(str) <= end)].sort_values("month")
    if mine.empty:
        return None
    return {"month": str(mine.iloc[-1]["month"]), "collections_12m": float(mine.tail(12)["collections_egp"].sum()),
            "cover_balance": float(mine.iloc[-1]["cover_balance_egp"])}


def last_quarters(asof: str, n: int) -> list[str]:
    return [str(q) for q in pd.period_range(end=pd.Period(asof, "Q"), periods=n, freq="Q")]


def complaints_by_quarter(complaints: pd.DataFrame, code: str, asof: str) -> pd.DataFrame:
    created = pd.to_datetime(complaints["created_at"])
    mine = complaints[(complaints["code"] == code) & (created <= pd.Period(asof, "Q").end_time)]
    quarters = pd.to_datetime(mine["created_at"]).dt.to_period("Q").astype(str)
    return (mine.assign(quarter=quarters).groupby(["quarter", "category"]).size()
            .rename("complaints").reset_index())


def cycle_footprint(compounds: pd.DataFrame, codes: list[str], feddan_m2: float) -> dict:
    """Published homes and land, in feddan, of the listed compounds; generated counts and areas are left out,
    so each total says how many compounds it covers."""
    mine = compounds[compounds["code"].isin(codes)]
    homes, land = mine[mine["units_origin"] == "real"], mine[mine["land_area_origin"] == "real"]
    return {"homes": int(homes["units"].sum()), "homes_compounds": len(homes),
            "feddan": round(float(land["land_area_m2"].sum()) / feddan_m2, 1), "land_compounds": len(land)}


def activity_spread(latest: pd.DataFrame) -> dict:
    """District mean activity score and the compounds under half of it: what the average hides."""
    scores = latest.dropna(subset=["activity_prob"])
    mean = float(scores["activity_prob"].mean())
    low = scores[scores["activity_prob"] < mean / 2].sort_values("activity_prob")
    return {"mean": mean, "below_half": list(low["code"].astype(str))}


SOURCE_KINDS = {"event": "Event", "promise": "Promise", "progress": "Progress claim",
                "eval_outcome": "Outcome (check case)", "eval_promise": "Promise (check case)",
                "eval_revision": "Revised date (check case)", "eval_progress": "Progress (check case)"}


def source_rows(sources: pd.DataFrame, code: str) -> pd.DataFrame:
    """One compound's public sources, oldest first, for the names-and-sources screen."""
    mine = sources[sources["code"] == code].sort_values(["published_date", "record_id"])
    return pd.DataFrame({"Published": mine["published_date"].astype(str).str[:10],
                         "What": mine["kind"].map(lambda k: SOURCE_KINDS.get(k, str(k).replace("_", " "))),
                         "Publisher": mine["publisher"], "Says": mine["quote"], "Link": mine["url"],
                         "Record": mine["record_id"]}).reset_index(drop=True)


def generated_elsewhere(compound: pd.Series) -> list[str]:
    """What the other screens show for this compound from generated data, not from public sources."""
    items = [f"{name} ({col.split('_')[0]})" if col == "units_origin" else name
             for col, name in (("units_origin", "home count"), ("land_area_origin", "land area"))
             if compound.get(col) == "generated"]
    return items + ["land value and fine exposure", "collections and cover balance", "buyer complaints",
                    "inspection visits", "classifier probabilities and what-if scenarios"]


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


def caught_cases(cases: pd.DataFrame) -> tuple[int, int]:
    """Backtest cases flagged after construction started, out of all cases."""
    return int(cases["after_start"].map(_flag).sum()), len(cases)


def stall_codes(kpis: pd.DataFrame, k2_min: float) -> list[str]:
    """Compounds whose stall count K2 reached `k2_min` in at least one quarter."""
    peaks = kpis.groupby("code")["K2"].max()
    return sorted(peaks[peaks >= k2_min].index)


def alarm_tradeoff(visit_cost: float, missed_cost: float, false_alarms: float, missed: float) -> dict:
    """Yearly cost of wasted visits against late detections, and how many false alarms one miss is worth."""
    return {"false_alarms": visit_cost * false_alarms, "missed": missed_cost * missed,
            "total": visit_cost * false_alarms + missed_cost * missed,
            "break_even": missed_cost / visit_cost if visit_cost > 0 else None}


def first_frame_after(frames: list[dict], when: pd.Timestamp) -> int | None:
    return next((i for i, f in enumerate(frames) if pd.Timestamp(f["date"]) > when), None)


def frame_pair(frames: list[dict], index: int | None) -> list[dict]:
    """The frame at `index` beside the latest capture, in any season (owner decision, 3 November 2026).

    Just the latest frame when there is no index or the index is the latest."""
    if not frames:
        return []
    if index is None or index == len(frames) - 1:
        return frames[-1:]
    return [frames[index], frames[-1]]


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


def _prefix_match(values: pd.Series, search: str) -> pd.Series:
    return values.astype("string").str.lower().str.startswith(search).fillna(False).astype(bool)


def _at_or_above(values: pd.Series, minimum: float) -> pd.Series:
    """Unknown values pass only when the threshold is 0 (no filter)."""
    if minimum <= 0:
        return pd.Series(True, index=values.index)
    return (pd.to_numeric(values, errors="coerce") >= minimum).fillna(False).astype(bool)


def filter_compounds(df: pd.DataFrame, search: str = "", levels: tuple[int, ...] = (),
                     developers: tuple[str, ...] = (), k2_min: float = 0, k3_min: float = 0,
                     k6_min: float = 0, cycle_only: bool = False) -> pd.DataFrame:
    """Screen 1 filters. `search` is a case-insensitive prefix of the compound or developer code;
    empty `levels`/`developers` and a zero threshold mean no filter on that field."""
    keep = pd.Series(True, index=df.index)
    search = search.strip().lower()
    if search:
        hit = _prefix_match(df["code"], search)
        if "developer_code" in df.columns:
            hit |= _prefix_match(df["developer_code"], search)
        keep &= hit
    if levels:
        keep &= df["level"].map(level_number).isin(levels)
    if developers and "developer_code" in df.columns:
        keep &= df["developer_code"].astype("string").isin(developers).fillna(False).astype(bool)
    for column, minimum in (("K2", k2_min), ("K3", k3_min), ("K6", k6_min)):
        if column in df.columns:
            keep &= _at_or_above(df[column], minimum)
    if cycle_only:  # the same rule as the cycle list: stored rank, else levels 1-3
        keep &= df["cycle_rank"].notna() if "cycle_rank" in df.columns else df["level"].isin([1, 2, 3])
    return df[keep]


def picked_code(selection: dict | None, layer_id: str) -> str | None:
    """The compound code of the object clicked on a pydeck layer, or None."""
    objects = ((selection or {}).get("objects") or {}).get(layer_id) or []
    if not objects:
        return None
    props = objects[0].get("properties") or objects[0]
    code = props.get("code")
    return None if code is None else str(code)
