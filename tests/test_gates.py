# H1: final no_names scan covers repo data/ + docs/deliverables/quality-report.md
import tempfile
from pathlib import Path

from src.pipeline import gates


def test_final_name_scan_covers_repo_data_files():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        bad = tmp / "bad.csv"
        bad.write_text("compound_001\n")
        result = gates.g_no_names(root=tmp, extra=[str(bad)])
        assert result["status"] == "STOP", result
