"""Lightweight date semantics shared by imagery preparation and inspector tools."""

from datetime import date


def capture_age_months(captured: str, asof: str) -> int:
    """Completed calendar months since the latest capture in a mixed-date frame."""
    captured_date, cutoff = date.fromisoformat(captured), date.fromisoformat(asof)
    if captured_date > cutoff:
        raise ValueError("Capture is later than the as-of date")
    return 12 * (cutoff.year - captured_date.year) + cutoff.month - captured_date.month - int(cutoff.day < captured_date.day)
