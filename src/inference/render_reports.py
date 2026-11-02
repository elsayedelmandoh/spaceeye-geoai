"""
src/inference/render_reports.py - Batch Render Arabic Inspection Dossiers (T-VE-06 / Deliverable 11)

Generates verified Arabic HTML inspection dossiers for presentation:
- Compounds: the stored cycle list of the quarter (cycle_rank not null).
- Integrates the executive brief + 3 Inspection Questions (T-VE-04).
- Verified facts and causal safety checks (T-VE-05).
- Footer: reviewer shown only when one is passed, model shown only when an LLM call happened.
- Stores outputs in app_data/files/.
"""

import sys
from pathlib import Path
from typing import Any

import pandas as pd

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.inference.generate import generate_inspection_brief
from src.inference.inspection_template import generate_deterministic_report
from src.pipeline.common import REAL

DEFAULT_QUARTER = "2026Q3"


def cycle_list_codes(quarter: str = DEFAULT_QUARTER) -> list[str]:
    """Return the quarter's cycle-list compounds in cycle order."""
    kpis = pd.read_parquet(REAL / "kpi_values.parquet", columns=["code", "quarter", "cycle_rank"])
    cycle = kpis.loc[kpis["quarter"].eq(quarter) & kpis["cycle_rank"].notna()]
    return cycle.sort_values("cycle_rank")["code"].tolist()


def render_all_reports(
    compounds: list[str] | None = None,
    quarter: str = DEFAULT_QUARTER,
    reviewer_name: str | None = None,
    output_dir: Path | None = None
) -> list[dict[str, Any]]:
    """
    Renders official inspection HTML dossiers for the cycle-list compounds.
    """
    if compounds is None:
        compounds = cycle_list_codes(quarter)

    if output_dir is None:
        output_dir = root_dir / "app_data" / "files"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    print(f"Generating {len(compounds)} official inspection files for quarter {quarter}...")

    for code in compounds:
        try:
            # 1. Generate Grounded AI Brief + 3 Questions (T-VE-04) and Verify (T-VE-05)
            brief_data = generate_inspection_brief(code, quarter)
            context = brief_data["context"]
            paragraph = brief_data["paragraph"]
            questions = brief_data["questions"]
            verdict = brief_data["verification"]["verdict"]

            # 2. Render Full Arabic HTML Dossier (T-VE-03 & T-VE-06)
            html_content = generate_deterministic_report(
                context=context,
                ai_paragraph=paragraph,
                ai_questions=questions,
                reviewer_name=reviewer_name,
                model=brief_data["model"],
            )

            # 3. Save to file
            filename = f"{code}_{quarter}_inspection.html"
            file_path = output_dir / filename
            file_path.write_text(html_content, encoding="utf-8")

            file_size_kb = round(file_path.stat().st_size / 1024, 1)
            print(f"  [OK] {filename} ({file_size_kb} KB) - Verifier verdict: {verdict}")

            results.append({
                "compound_id": code,
                "quarter": quarter,
                "file_path": str(file_path),
                "filename": filename,
                "size_kb": file_size_kb,
                "verdict": verdict,
                "status": "success"
            })
        except Exception as e:  # noqa: BLE001 - one failed compound is recorded and the batch continues
            print(f"  [ERROR] Failed rendering {code}: {e}")
            results.append({
                "compound_id": code,
                "quarter": quarter,
                "error": str(e),
                "status": "failed"
            })

    print(f"Batch generation completed: {len(results)} dossiers written to {output_dir}")
    return results


if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    rendered = render_all_reports()
