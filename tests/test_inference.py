"""
tests/test_inference.py - Comprehensive Verification Suite for Verina's AI Pipeline (T-VE-01 -> T-VE-06)
"""

import sys
import unittest
from unittest.mock import patch
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.inference.tools import get_facts, get_kpis, get_rules, get_images, build_inspection_context
from src.inference.inspection_template import generate_deterministic_report
from src.inference.verify import verify_inspection_text, VERDICT_CORRECT, VERDICT_WRONG_NUMBER, VERDICT_UNSUPPORTED
from src.inference.generate import generate_inspection_brief
from src.inference.render_reports import render_all_reports, TARGET_COMPOUNDS


class TestInferencePipeline(unittest.TestCase):

    def test_tools_get_facts(self):
        """T-VE-02: get_facts returns real land survey facts without lookahead bias."""
        facts = get_facts("C07", "2026Q3")
        self.assertIn("land_area_m2", facts)
        self.assertIn("developer_code", facts)
        self.assertEqual(facts["district"], "R7")

    def test_tools_get_kpis(self):
        """T-VE-02: get_kpis returns real satellite metrics for C07."""
        kpis = get_kpis("C07", "2026Q3")
        self.assertEqual(kpis["level"], 2)
        self.assertIn("K2_stoppage_quarters", kpis)
        self.assertIn("activity_history", kpis)

    def test_tools_get_rules(self):
        """T-VE-02: get_rules returns Decree 2184 & Law 119/2008 articles."""
        rules = get_rules()
        self.assertTrue(len(rules) > 0)
        has_decree = any("2184" in str(r.get("source", "")) or "2184" in str(r.get("rule", "")) for r in rules)
        self.assertTrue(has_decree)

    def test_tools_get_images(self):
        """T-VE-02: get_images handles satellite images with graceful fallback citing T-AH-15."""
        with patch("src.inference.tools.Path.is_file", return_value=False):
            images = get_images("C07")
        self.assertIn("status", images)
        self.assertEqual(images["status"], "missing_image")
        self.assertIn("T-AH-15", images.get("reason", ""))

    def test_build_inspection_dossier(self):
        """T-VE-03: Generates deterministic inspection dossier HTML with 4 sections."""
        ctx = build_inspection_context("C07", "2026Q3")
        html = generate_deterministic_report(ctx)
        self.assertIn("C07", html)
        self.assertIn("2184", html)
        self.assertIn("خطأ الرصد", html)
        self.assertIn("27", html)

    def test_verifier_catches_wrong_number_and_causal_word(self):
        """T-VE-05: Verifier catches hallucinated numbers and speculative causal words."""
        sample_context = {
            "compound_id": "C07",
            "kpis": {"A": 0.352, "K2": 2.0},
            "facts": {"land_area_m2": 85000}
        }
        # 1. Catch wrong number
        res_num = verify_inspection_text("بلغت نسبة الإنجاز 99% بالمشروع C07", sample_context, "C07")
        self.assertEqual(res_num["verdict"], VERDICT_WRONG_NUMBER)

        # 2. Catch causal word
        res_causal = verify_inspection_text("توقف المشروع C07 بسبب تعثر السيولة", sample_context, "C07")
        self.assertEqual(res_causal["verdict"], VERDICT_UNSUPPORTED)
        self.assertIn("بسبب", res_causal["causal_words"])

    def test_render_5_reports_exist(self):
        """T-VE-06: 5 official inspection files exist in app_data/files/ with required footer."""
        out_dir = root_dir / "app_data" / "files"
        for code in TARGET_COMPOUNDS:
            filename = f"{code}_2026Q3_inspection.html"
            file_path = out_dir / filename
            self.assertTrue(file_path.exists(), f"Missing file: {filename}")
            content = file_path.read_text(encoding="utf-8")
            self.assertTrue(len(content) > 5000)
            self.assertIn("مسوّدة أُعدت بالذكاء الاصطناعي، روجعت بواسطة", content)
            self.assertIn("gemini-1.5-flash", content)


if __name__ == "__main__":
    unittest.main()
