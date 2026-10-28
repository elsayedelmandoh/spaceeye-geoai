"""Invalid report observations must not masquerade as earlier available information."""

import pandas as pd

from src.analysis.ew_features import clean_complaints, clean_fin


def test_invalid_report_dates_are_removed_without_inventing_replacement_dates():
    fin = pd.DataFrame({"code": ["C01"] * 4, "month": ["2025-01", "2025-02", "2025-02", "2025-03"],
                        "reported_pct": [10.0, 20.0, 20.0, 30.0],
                        "report_date": pd.to_datetime(["2025-01-20", "2025-01-15", "2025-02-28", "2025-03-10"]),
                        "cover_balance_egp": [1000.0] * 4})
    mon, reports, fixed = clean_fin(fin)
    assert len(mon) == 3 and fixed == 0
    assert mon.loc[1, ["reported_pct", "report_date"]].isna().all()
    assert reports.reported_pct.tolist() == [10.0, 30.0]
    assert fin.reported_pct.notna().all()  # raw data preserved


def test_complaint_quarantine_never_uses_private_truth_and_masks_rejected_rows_too():
    raw = pd.DataFrame({"code": ["C01", "C99", "C01"], "created_at": ["2025-01-10", "2025-01-15", "2022-12-30"],
                        "text_ar": ["call 01012345678", "call 01012345678", None]})
    clean, rejected, masked = clean_complaints(raw, ["C01"], "2023-01-01", "2026-10-01")
    assert len(clean) == 1 and len(rejected) == 2 and masked == 2
    assert clean.text_ar.iloc[0] == "call [PHONE]"
    assert set(rejected.dq_reason) == {"unknown_code", "invalid_date"}
    assert "01012345678" not in rejected.text_ar.dropna().str.cat()
