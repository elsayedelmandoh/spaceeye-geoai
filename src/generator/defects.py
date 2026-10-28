"""
propose: step 6. plant the 6 defects of the data plan on the clean tables and log them (private, with the row counts).
input: clean fin_monthly, complaints (with private helper columns), the simulated units, one random generator.
output: the defective copies and `defects_log` (defect, table, column, rows, description, gate that should catch it, detail).

  1  escrow balance entered in thousand EGP for one developer (owns exactly 2 compounds) for 4 months   -> accuracy / unit
  2  supervisor report entered twice with a different date (~1 % of the reports, at least 3)           -> uniqueness
  3  report date before the end of the quarter it covers (5 rows)                                      -> validity (date order)
  4  compound code that is not in the register inside the complaint feed (15 rows)                     -> consistency (foreign key)
  5  complaint dated before the compound launched (5 rows)                                             -> validity (date range)
  6  phone numbers typed inside the Arabic text (10 texts)                                             -> privacy masking test
"""

import re

import numpy as np
import pandas as pd

from src.generator.inputs import GEN, MONTHS, M_END, N, O0

D = GEN["defects"]
PHONE = re.compile(r"(?:\+?20|0)\s?1[0125][\s-]?\d{4}[\s-]?\d{4}")


def fake_phone(rng: np.random.Generator) -> str:
    d = f"01{rng.choice(['0', '1', '2', '5'])}{rng.integers(0, 10 ** 8):08d}"
    style = int(rng.integers(0, 3))
    return d if style == 0 else (f"{d[:3]} {d[3:7]} {d[7:]}" if style == 1 else f"+20{d[1:]}")


def plant(fin: pd.DataFrame, cmp_: pd.DataFrame, units: list, rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fin, cmp_ = fin.copy(), cmp_.copy()
    log = []
    # 1 thousand-EGP balance
    dev_count = pd.Series([u.sig.developer for u in units]).value_counts()
    dev = str(rng.choice(sorted(dev_count[dev_count == 2].index)))
    codes = sorted(u.sig.code for u in units if u.sig.developer == dev)
    start = int(rng.integers(MONTHS.get_loc(pd.Period("2024-09", "M")), MONTHS.get_loc(pd.Period("2026-01", "M")) + 1))
    months = [str(MONTHS[start + i]) for i in range(D["escrow_thousand_months"])]
    sel = fin.code.isin(codes) & fin.month.isin(months)
    fin.loc[sel, "cover_balance_egp"] = (fin.loc[sel, "cover_balance_egp"] / 1000).round(0)
    log.append((1, "fin_monthly", "cover_balance_egp", int(sel.sum()), f"balance in thousand EGP for {len(codes)} compounds of one developer for {len(months)} months",
                "accuracy (unit / jump of three orders of magnitude)", f"codes {','.join(codes)}; months {months[0]}..{months[-1]}"))
    # 3 report date before the end of the covered quarter (chosen first so duplicates do not copy it)
    reg = {(u.sig.code, str(MONTHS[m])): int(u.rep.covers[m]) for u in units for m in range(O0, N) if u.rep.regular[m]}
    cand = [i for i in fin.index[fin.report_date.notna()] if (fin.at[i, "code"], fin.at[i, "month"]) in reg]
    pick3 = sorted(rng.choice(cand, D["early_report_date_rows"], replace=False))
    for i in pick3:
        q_end = M_END[reg[(fin.at[i, "code"], fin.at[i, "month"])]]
        fin.at[i, "report_date"] = q_end - pd.Timedelta(days=int(rng.integers(5, 41)))
    log.append((3, "fin_monthly", "report_date", len(pick3), "report date earlier than the end of the quarter the report covers", "validity (date order)",
                ";".join(f"{fin.at[i, 'code']}@{fin.at[i, 'month']}" for i in pick3)))
    # 2 duplicate reports with a different date
    pool = [i for i in fin.index[fin.report_date.notna()] if i not in set(pick3)]
    k = max(3, int(round(D["duplicate_report_share"] * fin.report_date.notna().sum())))
    pick2 = sorted(rng.choice(pool, k, replace=False))
    dup = fin.loc[pick2].copy()
    dup["report_date"] = dup.report_date + pd.to_timedelta(rng.integers(3, 26, len(dup)), unit="D")
    fin = pd.concat([fin, dup]).sort_values(["code", "month"], kind="stable").reset_index(drop=True)
    log.append((2, "fin_monthly", "(row)", len(dup), "report entered twice, second copy carries a different date", "uniqueness (compound, month)",
                ";".join(f"{c}@{m}" for c, m in zip(dup.code, dup.month))))
    # 4 unknown code in the complaint feed
    rows4 = sorted(rng.choice(cmp_.index, D["unknown_code_rows"], replace=False))
    cmp_["_true_code"] = cmp_.code
    cmp_.loc[rows4, "code"] = D["unknown_code"]
    log.append((4, "complaints", "code", len(rows4), f"code {D['unknown_code']} is not in the compound register", "consistency (foreign key)", D["unknown_code"]))
    # 5 complaint before launch
    launch = {u.sig.code: u.st.launch for u in units}
    late = sorted([c for c in launch if launch[c] >= O0 + 5], key=lambda c: -launch[c])[:3] or sorted(launch, key=lambda c: -launch[c])[:3]
    pool5 = cmp_.index[cmp_._true_code.isin(late) & (cmp_.code != D["unknown_code"])]
    rows5 = sorted(rng.choice(pool5, D["before_launch_rows"], replace=False))
    for i in rows5:
        c = cmp_.at[i, "code"]
        lo = max(pd.Timestamp(GEN["start"] + "-01"), MONTHS[launch[c]].to_timestamp() - pd.DateOffset(months=6))
        hi = MONTHS[launch[c]].to_timestamp() - pd.Timedelta(days=5)
        cmp_.at[i, "created_at"] = lo + (hi - lo) * float(rng.random())
    log.append((5, "complaints", "created_at", len(rows5), "complaint dated before the compound launched", "validity (date range)", ",".join(sorted({cmp_.at[i, 'code'] for i in rows5}))))
    cmp_ = cmp_.sort_values(["created_at", "complaint_id"], kind="stable").reset_index(drop=True)
    # 6 phones in the text
    with_text = cmp_.index[cmp_.text_ar.notna()]
    rows6 = sorted(rng.choice(with_text, D["phone_texts"], replace=False))
    for i in rows6:
        cmp_.at[i, "text_ar"] = f"{cmp_.at[i, 'text_ar']} رقمي {fake_phone(rng)}"
    n6 = int(cmp_.text_ar.dropna().map(lambda t: bool(PHONE.search(t))).sum())
    log.append((6, "complaints", "text_ar", n6, "fake phone numbers typed inside the text", "privacy masking test (assert_zero_phones)", f"{n6} texts"))
    out = pd.DataFrame(sorted(log), columns=["defect_id", "table", "column", "rows_affected", "description", "expected_gate", "detail"])
    out["synthetic_label"] = GEN["label"]
    return fin, cmp_, out
