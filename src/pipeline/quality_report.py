"""Render the latest saved data-only gates as a team-facing quality report.

Reads saved checks only; does not rerun gates, change data or fit models.
"""

import csv
import hashlib
from collections import Counter

from src.pipeline.common import APP, BASE_DIR


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def main():
    source = APP / "data_completion" / "quality_checks.csv"
    with source.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("No saved checks; run src.pipeline.complete_data first")
    counts = Counter(row["status"] for row in rows)
    lines = [
        "# Track A quality report", "",
        "Task T-AH-12. Snapshot of saved data-only checks; rendering this report does not rerun them.", "",
        "Source: `app_data/data_completion/quality_checks.csv` (external configured input).",
        f"Source SHA256: `{hashlib.sha256(source.read_bytes()).hexdigest()}`.", "",
        "Results: " + ", ".join(f"{count} {status}" for status, count in sorted(counts.items())) + ".", "",
        "| Gate | Dimension | Status | Observed result | Owner role | On failure | Impact on the indicator |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    fields = ("gate", "dimension", "status", "value", "owner", "on_failure", "impact")
    lines += ["| " + " | ".join(cell(row[field]) for field in fields) + " |" for row in rows]
    lines += ["", "## Decisions and limits", "",
              "STOP blocks delivery. FIX requires correction and a gate rerun. FLAG stays visible and requires review; it is not a PASS.", "",
              "The 2019Q2 source-event FLAG remains unresolved. Review source coverage before interpreting that quarter as a physical construction change.", "",
              "Owner codes are pipeline roles, not evidence of a named teammate's review or sign-off. Freshness is relative to the configured computation date, not the report rendering date.", "",
              "These checks do not validate classifier accuracy, contractual fines, synthetic visits or actual field conditions. Historical backtest and model evaluations remain separate.", "",
              "Refresh checks: `uv run --locked --offline python -m src.pipeline.complete_data`. Then render: `uv run --locked --offline python -m src.pipeline.quality_report`."]
    target = BASE_DIR / "docs" / "deliverables" / "quality-report.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Quality report rendered from {len(rows)} saved checks; no gates rerun")


if __name__ == "__main__":
    main()
