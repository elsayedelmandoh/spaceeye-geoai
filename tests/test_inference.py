"""
tests/test_inference.py - Comprehensive Verification Suite for Verina's AI Pipeline (T-VE-01 -> T-VE-06)
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.inference.generate import generate_fallback_grounded_brief
from src.inference.inspection_template import generate_deterministic_report
from src.inference.render_reports import cycle_list_codes
from src.inference.tools import (
    build_inspection_context,
    get_facts,
    get_images,
    get_kpis,
    get_rules,
)
from src.inference.verify import (
    VERDICT_UNSUPPORTED,
    VERDICT_WRONG_NUMBER,
    verify_inspection_text,
)

REASON_ACTIVE = "المستوى 1: رصد نشاط بناء (درجة النشاط 0.53)؛ تجاوز أول موعد تسليم معلن (2021-12-31) بمقدار 57 شهر."
REASON_MAY_BE_COMPLETE = (
    "المستوى 4: رصد نشاط بناء (درجة النشاط 0.83)؛ يوجد إعلان تسليم منشور؛ "
    "قد يكون مكتملًا وفق إعلان التسليم أو الغطاء النباتي؛ يلزم تحقق ميداني."
)


def _context(**kpi_overrides):
    kpis = {
        "level": 1,
        "level_word_ar": "الأولى",
        "reason_ar": REASON_ACTIVE,
        "A": 0.53,
        "K2_stoppage_quarters": 0.0,
        "K3_delay_months": 57,
        "K5_fine_eligible_months": 45,
        "may_be_complete": False,
        "activity_history": [],
    }
    kpis.update(kpi_overrides)
    return {
        "compound_code": "C18",
        "quarter": "2026Q3",
        "facts": {
            "land_area_m2": 161874.0,
            "developer_code": "D14",
            "first_deadline": "2021-12-31",
            "cutoff_date": "2026-09-30",
        },
        "kpis": kpis,
        "complaints_summary": {"total_count": 3, "origin": "generated"},
        "images": {"status": "missing_image"},
    }


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
        self.assertIn(ctx["kpis"]["reason_ar"], html)
        self.assertNotIn("None", html)

    def test_active_compound_is_not_described_as_stalled(self):
        html = generate_deterministic_report(_context())
        self.assertIn("K2 = 0", html)
        for invented in ("ركود", "صب خرساني", "توقف إنشائي", "تعثر"):
            self.assertNotIn(invented, html)

    def test_may_be_complete_reason_is_kept_and_not_replaced(self):
        ctx = _context(level=4, level_word_ar="الرابعة", reason_ar=REASON_MAY_BE_COMPLETE, may_be_complete=True)
        html = generate_deterministic_report(ctx)
        self.assertIn("قد يكون مكتملًا", html)
        self.assertNotIn("النطاق الزمني والإنشائي الاعتيادي", html)

    def test_missing_k5_reads_as_no_published_deadline(self):
        html = generate_deterministic_report(_context(K5_fine_eligible_months=None))
        self.assertNotIn("None", html)
        self.assertIn("لا يوجد موعد تسليم منشور", html)
        shown = generate_deterministic_report(_context())
        self.assertIn("مؤشر فحص", shown)
        self.assertNotIn("مستحق", shown)

    def test_no_invented_verification_or_hard_coded_counts(self):
        html = generate_deterministic_report(_context(level=2, level_word_ar="الثانية"))
        for invented in ("27 صورة", "شهادة صلاحية الإشغال", "تم التحقق من عدم"):
            self.assertNotIn(invented, html)

    def test_reviewer_and_model_are_shown_only_when_real(self):
        template_only = generate_deterministic_report(_context())
        self.assertIn("لم تتم المراجعة بعد", template_only)
        self.assertIn("no AI model", template_only)
        self.assertNotIn("gemini", template_only)
        reviewed = generate_deterministic_report(
            _context(), ai_paragraph="نص", ai_questions=["س1", "س2", "س3"],
            reviewer_name="Review Team", model="fixture-model",
        )
        self.assertIn("Review Team", reviewed)
        self.assertIn("fixture-model", reviewed)

    def test_fallback_brief_uses_only_context_values(self):
        ctx = _context(level=2, level_word_ar="الثانية", K2_stoppage_quarters=2.0, A=0.35,
                       K3_delay_months=0, K5_fine_eligible_months=None)
        paragraph, questions = generate_fallback_grounded_brief(ctx)
        text = "\n".join([paragraph, *questions])
        self.assertNotIn("27", text)
        self.assertNotIn("None", text)
        res = verify_inspection_text(text, ctx, "C18", "2026Q3")
        self.assertEqual(res["flags"], [])

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

    def test_cycle_list_reports_exist(self):
        """T-VE-06: one inspection file per cycle-list compound, none for other compounds."""
        out_dir = root_dir / "app_data" / "files"
        codes = cycle_list_codes("2026Q3")
        self.assertEqual(codes, ["C18", "C07", "C14", "C03"])
        for code in codes:
            file_path = out_dir / f"{code}_2026Q3_inspection.html"
            self.assertTrue(file_path.exists(), f"Missing file: {file_path.name}")
            content = file_path.read_text(encoding="utf-8")
            self.assertTrue(len(content) > 5000)
            self.assertIn("لم تتم المراجعة بعد", content)
            self.assertNotIn("gemini-1.5-flash", content)
            self.assertNotIn("الزميل", content)
        stale = sorted(path.name for path in out_dir.glob("*_2026Q3_inspection.html"))
        self.assertEqual(stale, sorted(f"{code}_2026Q3_inspection.html" for code in codes))


if __name__ == "__main__":
    unittest.main()
