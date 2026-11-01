"""
tests/test_verifier.py - Unit tests for Inspection Fact Verifier (T-VE-05)
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from src.inference.verify import (
    VERDICT_CORRECT,
    VERDICT_UNSUPPORTED,
    VERDICT_WRONG_NUMBER,
    log_verification_result,
    verify_inspection_text,
)


class TestInspectionVerifier(unittest.TestCase):

    def setUp(self):
        # Grounded factual context from C07 2026Q3
        self.sample_context = {
            "compound_id": "C07",
            "developer_id": "D12",
            "region": "R7",
            "quarter": "2026Q3",
            "kpis": {
                "A": 0.34,
                "K2": 0.28,
                "K3": 0.05,
                "K4": 0.12,
                "K5": 0.88,
                "K6": 0.00
            },
            "facts": {
                "contract_end": "2024-12-31",
                "area_sqm": 85000,
                "decree_law": "2184/2022"
            }
        }

    def test_valid_grounded_text(self):
        """Valid text referencing only factual context numbers and codes passes."""
        valid_text = (
            "وفقاً للبيانات المعتمدة للمشروع C07 بالمنطقة R7 حتى الربع 2026Q3، "
            "بلغت درجة النشاط المرصودة A نحو 0.34 مع استقرار مؤشر K2 عند 0.28 ومؤشر K4 عند 0.12."
        )
        res = verify_inspection_text(valid_text, self.sample_context, "C07", "2026Q3")
        self.assertEqual(res["verdict"], VERDICT_CORRECT)
        self.assertTrue(res["is_valid"])
        self.assertEqual(len(res["wrong_numbers"]), 0)
        self.assertEqual(len(res["causal_words"]), 0)

    def test_catches_wrong_number(self):
        """Verifier catches hallucinated or fabricated numbers."""
        invalid_num_text = (
            "المشروع C07 بلغت نسبة الإنجاز به 95% وتوقف العمل منذ 140 يوماً."
        )
        res = verify_inspection_text(invalid_num_text, self.sample_context, "C07", "2026Q3")
        self.assertEqual(res["verdict"], VERDICT_WRONG_NUMBER)
        self.assertFalse(res["is_valid"])
        self.assertIn("95", res["wrong_numbers"])

    def test_catches_causal_word_arabic(self):
        """Verifier flags causal words in Arabic requiring human inspection review."""
        causal_text = (
            "تأخر المشروع C07 بنسبة 0.34 بسبب نقص السيولة المالية للمطور."
        )
        res = verify_inspection_text(causal_text, self.sample_context, "C07", "2026Q3")
        self.assertEqual(res["verdict"], VERDICT_UNSUPPORTED)
        self.assertIn("بسبب", res["causal_words"])

    def test_catches_causal_word_english(self):
        """Verifier flags causal words in English."""
        causal_en = (
            "Compound C07 shows progress 0.34 because contractor suspended work."
        )
        res = verify_inspection_text(causal_en, self.sample_context, "C07", "2026Q3")
        self.assertEqual(res["verdict"], VERDICT_UNSUPPORTED)
        self.assertIn("because", res["causal_words"])

    def test_catches_unknown_entity_code(self):
        """Verifier flags ungrounded compound codes."""
        code_text = (
            "مقارنة بين المشروع C07 والمشروع C99 توضح الفارق."
        )
        res = verify_inspection_text(code_text, self.sample_context, "C07", "2026Q3")
        self.assertEqual(res["verdict"], VERDICT_UNSUPPORTED)
        self.assertIn("C99", res["wrong_codes"])

    def test_logging_verdict(self):
        """Logs verification results cleanly to CSV."""
        res = {
            "verdict": VERDICT_WRONG_NUMBER,
            "is_valid": False,
            "flags": ["Unverified numbers: 99"],
            "details": "Tested logger"
        }
        test_log = root_dir / "app_data" / "test_ai_verification_log.csv"
        if test_log.exists():
            test_log.unlink()
        path = log_verification_result(res, "C07", "2026Q3", "Preview text", test_log)
        self.assertTrue(Path(path).exists())
        test_log.unlink()

class TestFieldTiedChecks(unittest.TestCase):

    def setUp(self):
        self.context = {
            "compound_code": "C01",
            "kpis": {
                "level": 4,
                "A": 0.87,
                "K2": 0.0,
                "K2_stoppage_quarters": 0.0,
                "K3": 5,
                "K3_delay_months": 5,
                "series": [{"level": 2, "K2": 2.0}],
            },
        }

    def test_swapped_level_is_a_wrong_number(self):
        res = verify_inspection_text("المركب C01 في المستوى 2.", self.context, "C01", "2026Q3")
        self.assertEqual(res["verdict"], VERDICT_WRONG_NUMBER)
        self.assertIn("2", res["wrong_numbers"])
        ok = verify_inspection_text("المركب C01 في المستوى 4.", self.context, "C01", "2026Q3")
        self.assertEqual(ok["verdict"], VERDICT_CORRECT)

    def test_wrong_k2_number_is_caught_even_if_the_digit_exists_elsewhere(self):
        res = verify_inspection_text("توقف C01 لمدة 5 أرباع ودرجة النشاط 0.5.", self.context, "C01", "2026Q3")
        self.assertEqual(res["verdict"], VERDICT_WRONG_NUMBER)
        self.assertEqual(res["wrong_numbers"], ["5", "0.5"])

    def test_small_numbers_are_no_longer_whitelisted(self):
        res = verify_inspection_text("المركب C01 سجل 3 أرباع.", self.context, "C01", "2026Q3")
        self.assertEqual(res["verdict"], VERDICT_WRONG_NUMBER)
        self.assertIn("3", res["wrong_numbers"])
        res = verify_inspection_text("المركب C01 فيه 27 لقطة.", self.context, "C01", "2026Q3")
        self.assertIn("27", res["wrong_numbers"])

    def test_arabic_forbidden_word_is_flagged(self):
        res = verify_inspection_text("المركب C01 متعثر.", self.context, "C01", "2026Q3")
        self.assertEqual(res["verdict"], VERDICT_UNSUPPORTED)
        self.assertTrue(any("متعثر" in flag for flag in res["flags"]))

    def test_arabic_causal_word_is_flagged(self):
        res = verify_inspection_text("توقف العمل لأن التمويل نقص في C01.", self.context, "C01", "2026Q3")
        self.assertEqual(res["verdict"], VERDICT_UNSUPPORTED)
        self.assertIn("لأن", res["causal_words"])

    def test_named_compound_is_flagged(self):
        res = verify_inspection_text("المركب النخيل متأخر.", self.context, "C01", "2026Q3")
        self.assertEqual(res["verdict"], VERDICT_UNSUPPORTED)
        self.assertTrue(any("named" in flag for flag in res["flags"]))


if __name__ == "__main__":
    unittest.main()
