"""
propose: write the data dictionaries (one markdown per table: column, type, unit/range, meaning, origin, how it is made).
input: nothing but the specs below. output: app_data/sim/dictionaries/{fin_monthly,complaints}.md and private/dictionaries/{answer_key,answer_key_complaints,defects_log}.md.
origin: generated (orange) = invented by the generator; derived (blue) = computed from other columns of the same table; key = identifier.
"""

from pathlib import Path

import pandas as pd

from src.generator.inputs import GEN
from src.pipeline.common import REAL

LABEL = GEN["label"]
GEN_, DER, KEY = "generated", "derived", "key"

FIN = [
    ("code", "str", "registered compound codes", "compound code (same codes as the real tables)", KEY, "from the current scoped register"),
    ("month", "str", f"YYYY-MM, {GEN['start']}..{GEN['end']}", "calendar month; the row is the state at the end of that month", KEY, "grid"),
    ("planned_pct", "float", "0-100 %", "contractual plan: Weibull S-curve divided by its value at the end, 100 % exactly at the contractual delivery month", GEN_,
     "deadline = end of the first real promise when one exists, else plan start + 30-42 months (finished work: the month it really finished)"),
    ("reported_pct", "float", "0-100 %, mostly empty", "supervisor-engineer progress report, only in months where a report arrived. in months with a real announced value it IS that value", GEN_,
     f"quarterly report of the true progress at quarter end; optimistic developers add 2-8 points; rounding probability {GEN['reports']['round5_share']:.0%} (final multiples-of-5 share is checked separately); 5 % missing (35 % while stalled)"),
    ("report_date", "date", "", "date of the report; 15-45 days after the quarter end (late-style developers up to 75); real publication date for announced values", GEN_, "see reported_pct"),
    ("units_sold", "int", "units / month", "units sold in the month", GEN_, "hazard (launch spike, slow tail) x demand (policy rate, Ramadan, post-float boom 2-4 months after 6 Mar 2024), negative-binomial noise"),
    ("avg_price_egp", "float", "EGP per unit", "average contract price of the units sold in the month (empty when none sold)", GEN_, "launch price per m2 = cost x U(1.4, 2.0); list jumps 15-40 % after the float; +0.5 %/month"),
    ("collections_egp", "float", "EGP / month", "buyer payments received in the month (all go into escrow)", GEN_,
     "8.5 % down payment at sale + equal monthly installments over 7-12 years x payment rate (3 % late, 8 % for 6 months after the float, weaker before a stall)"),
    ("cover_required_egp", "float", "EGP", "financial cover the decree requires: class % (20 or 15) x cost to complete, until certified progress passes 30 % / 25 % (art. 4)", DER,
     "cover_pct x cost_to_complete_egp"),
    ("cover_balance_egp", "float", "EGP", "escrow cash plus the cover the developer keeps posted (a guarantee; shrinks when the developer is in arrears)", GEN_,
     "releases only after a quarterly report: min(balance - 5 % refund reserve, certified cost so far x 1.05 - already released)"),
    ("cost_to_complete_egp", "float", "EGP", "build cost still to spend on the certified (reported) progress", DER,
     "total cost x (1 - certified %); total cost follows the real dollar (40 %) and the real rebar/cement index (60 %)"),
    ("land_due_egp", "float", "EGP", "land installment falling due in the month (0 in other months)", GEN_, "16 quarterly installments, land price 2,500-12,000 EGP/m2 x land area"),
    ("land_paid_egp", "float", "EGP", "land money paid in the month (a lump when arrears are cleared)", GEN_, "paid when cash covers it and a month of spending; arrears pay 1 %/month penalty"),
    ("land_months_late", "int", "months", "age of the oldest unpaid installment (0 when none)", DER, "month - due month of the oldest unpaid installment"),
    ("roads_paved_share", "float", "0-1", "share of internal roads paved", GEN_, "follows true progress above 35 % with a two-month lag, +-0.02 survey noise"),
    ("meters_active", "int", "meters", "residential meters with a contract (handed-over units with a contract)", GEN_, "handed-over units x contract rate rising from 0.5 to 0.92 in 12 months"),
    ("kwh", "float", "kWh / month", "electricity billed: occupied homes x 153 x temperature seasonality + standby of empty meters + the site meter while building; 4 % estimated reads", GEN_,
     "real monthly max temperature; site load follows the work done"),
    ("status_level", "str", "on_plan / behind / late / distressed", "level ACUD recorded at its last quarterly review", DER,
     "K3 > 24 or no reported progress for 6 months or land arrears with cover below the minimum -> distressed; K3 > 0 -> late; reported 10+ points under plan -> behind"),
    ("warning_issued", "bool", "", "a warning letter was issued in the month", GEN_, "12-month grace expired (decree art. 5), or 3 months with no reported progress at a quarterly review (every 6 months while it lasts)"),
]
CMP = [
    ("complaint_id", "str", "CMP-000001..", "complaint number (assigned in order of creation)", KEY, "sequence"),
    ("code", "str", "registered compound codes plus a planted unknown code", "compound code", KEY, "from the compound; defect 4 replaces it in the configured number of rows"),
    ("created_at", "datetime", "Africa/Cairo local time, no zone", "when the complaint was filed", GEN_, "uniform day, office-hours-heavy hour; defect 5 puts 5 rows before launch"),
    ("channel", "str", "phone / portal / visit", "filing channel", GEN_, "50 / 35 / 15 %; 5 % are the same buyer on a second channel within 7 days"),
    ("category", "str", "delay / stoppage / payment / quality / other", "category as filed by the complaint desk", GEN_, "from the causing event; 10-15 % filed under a wrong category on purpose"),
    ("text_ar", "str", "about 100 texts, the rest empty", "complaint text in Arabic written from templates (no LLM); 10 texts carry a planted fake phone number (defect 6)", GEN_, "templates by true cause, spelling slips, mixed topics"),
]
AK = [
    ("code, month", "str", "", "keys", KEY, ""), ("story", "str", "", "healthy / slow_late / partly_delivered / gradual_stall / stall_recovery / new_start", GEN_, "derived from the compound's real signals"),
    ("story_reason", "str", "", "which real signal gave the story", GEN_, ""), ("developer_strength, reporting_style", "str", "", "hidden developer traits", GEN_, ""),
    ("true_progress_pct", "float", "0-100", "hidden true progress (passes through the real anchors +-10)", GEN_, ""), ("true_cash_egp", "float", "EGP", "developer cash at month end", GEN_, ""),
    ("contractor_arrears_egp, bank_debt_egp", "float", "EGP", "unpaid contractor dues and bank line drawn", GEN_, ""), ("true_cost_to_complete_egp", "float", "EGP", "cost to complete on TRUE progress", GEN_, ""),
    ("escrow_cash_egp", "float", "EGP", "escrow cash (buyers' money)", GEN_, ""), ("handed_over_units, true_occupied_units", "float", "units", "handed over and really lived in", GEN_, ""),
    ("true_distress", "bool", "", "hidden distress this month", GEN_, "work stalled 6 months, or arrears > 2 months of burn, or land arrears with cover below minimum"),
    ("label_distress_next_6m", "bool", "", "true distress in any of the next 6 months (the training label)", DER, "label_censored marks months with fewer than 6 months left"),
]
AKC = [
    ("complaint_id", "str", "", "key", KEY, ""), ("true_code", "str", "", "code before defect 4", KEY, ""), ("true_category, true_cause", "str", "", "real category and the event behind the complaint (base, postponement, handover, price, stall, grace_expiry, stall_review, viral)", GEN_, ""),
    ("duplicate_of", "str", "", "complaint id this one duplicates (same buyer, second channel)", GEN_, ""), ("desk_category_wrong", "bool", "", "the desk filed it under a wrong category", GEN_, ""), ("has_text", "bool", "", "row carries an Arabic text", GEN_, ""),
]
DEF = [
    ("defect_id", "int", "1-6", "defect number", KEY, ""), ("table, column", "str", "", "where it was planted", KEY, ""), ("rows_affected", "int", "", "rows changed (duplicates: rows added)", GEN_, ""),
    ("description, expected_gate, detail", "str", "", "what was done, which gate should catch it, which compounds/months/ids", GEN_, ""),
]
SPECS = {"fin_monthly": ("fin_monthly: compound x month (+ duplicate-report rows from defect 2)", FIN),
         "complaints": ("complaints: one row per complaint", CMP), "answer_key": ("answer_key (private): compound x month hidden truth", AK),
         "answer_key_complaints": ("answer_key_complaints (private): true cause per complaint", AKC), "defects_log": ("defects_log (private): the six planted defects", DEF)}


def write(name: str, folder: Path) -> Path:
    title, cols = SPECS[name]
    if name == "fin_monthly":
        count = len(pd.read_parquet(REAL / "compounds.parquet"))
        months = len(pd.period_range(GEN["start"], GEN["end"], freq="M"))
        title = f"fin_monthly: compound x month, {count} x {months} = {count * months} base rows (+ logged duplicate-report rows from defect 2)"
    lines = [f"# {title}", "", f"**{LABEL}.** These operational records and hidden states are simulated, with selected supervisor observations anchored to published statements. They are not real company financial or complaint records. Origin: generated = produced by the generator, derived = computed from other columns, key = identifier.", "",
             "| column | type | unit / range | meaning | origin | how it is made |", "| --- | --- | --- | --- | --- | --- |"]
    lines += [f"| `{c}` | {t} | {u} | {m} | {o} | {h} |" for c, t, u, m, o, h in cols]
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / f"{name}.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p
