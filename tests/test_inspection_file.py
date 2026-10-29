"""Fabricated contract tests for the deterministic inspection file.

The input dictionaries deliberately mirror the plain-data boundary used by the
inspection tools:

* ``kpis`` contains ``code``, ``quarter``, ``A``, ``K2``, ``K3``, ``K4``,
  ``K5_months``, ``K6``, ``level``, ``level_label``, ``level_word``,
  ``level_word_ar``, ``reason``, ``reason_ar``, ``may_be_complete``, ``origin``,
  ``run_id``, ``computed_at``, and an oldest-first ``series``. Unknown values
  are ``None``.
* ``facts`` contains rows with ``record_id``, ``kind``, ``subtype``,
  ``published_date``, ``detail``, and ``link``.
* ``images`` contains ``status`` and an ``images`` list.
* ``rules`` contains Decree 2184 rows with ``article`` and ``text``.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.inference.inspection_file import build_inspection_file, render_markdown

ROLE_NAMES = {
    "Buildings & Facilities pillar lead",
    "inspection committee",
    "observatory team",
}


def _kpis(level: int | None = 1) -> dict[str, Any]:
    labels = {
        1: ("1", "first", "الأولى"),
        2: ("2", "second", "الثانية"),
        3: ("3", "third", "الثالثة"),
        4: ("4", "fourth", "الرابعة"),
        None: ("not started", "not started", "بداية غير مؤكدة"),
    }
    level_label, level_word, level_word_ar = labels[level]
    return {
        "code": "C07",
        "quarter": "2024Q2",
        "A": 0.12,
        "K2": 4,
        "K3": 27,
        "K4": True,
        "K5_months": 7,
        "K6": 25,
        "level": level,
        "level_label": level_label,
        "level_word": level_word,
        "level_word_ar": level_word_ar,
        "reason": (
            "Level 1: no building activity for 4 quarter(s) (activity score 0.12); "
            "first announced handover date passed by 27 months; observation complete."
        ),
        "reason_ar": (
            "المستوى 1: لم يرصد نشاط بناء منذ 4 ربع؛ تجاوز أول موعد تسليم معلن "
            "بمقدار 27 شهر؛ عدد الصور خلال الربع 14."
        ),
        "may_be_complete": False,
        "origin": "derived",
        "run_id": "fabricated-run",
        "computed_at": "2026-10-29",
        "n_images": 14,
        "series": [
            {"quarter": "2023Q2", "A": 0.40, "K2": 0, "K3": 0, "K6": None, "level": 4},
            {"quarter": "2023Q3", "A": 0.35, "K2": 0, "K3": 0, "K6": None, "level": 4},
            {"quarter": "2023Q4", "A": 0.30, "K2": 1, "K3": 0, "K6": None, "level": 3},
            {"quarter": "2024Q1", "A": 0.20, "K2": 2, "K3": 13, "K6": 13, "level": 2},
            {"quarter": "2024Q2", "A": 0.12, "K2": 4, "K3": 27, "K6": 25, "level": 1},
        ],
    }


def _facts() -> list[dict[str, Any]]:
    return [
        {
            "record_id": "F-001",
            "kind": "statement",
            "subtype": "delivery_promise",
            "published_date": "2023-12-15",
            "detail": "Fabricated delivery statement.",
            "link": "https://example.test/records/F-001",
        },
        {
            "record_id": "F-002",
            "kind": "event",
            "subtype": "launch",
            "published_date": "2023-01-10",
            "detail": "Fabricated launch event.",
            "link": "https://example.test/records/F-002",
        },
    ]


def _images() -> dict[str, Any]:
    return {
        "status": "ok",
        "images": [
            {
                "path": "images/C07-2023.jpg",
                "capture_date": "2023-06-01",
                "attribution": "Fabricated attribution.",
            }
        ],
    }


def _rules() -> list[dict[str, str]]:
    return [{"article": "3", "text": "Fabricated legal reference text."}]


def _all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _all_strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _all_strings(item)]
    return []


@pytest.mark.parametrize(
    ("state", "expected_action", "expected_due_date"),
    [
        (1, ("within two weeks", "pillar lead"), "2024-07-14"),
        (2, ("within the current cycle",), "2024-09-30"),
        (3, ("request the supervisor report",), "2024-07-30"),
        (4, ("routine", "next cycle"), "2024-09-30"),
        ("not started", ("watch",), "2024-09-30"),
        ("start unknown", ("watch", "collect evidence"), "2024-09-30"),
        ("not assessable", ("fix the location or images first",), "2024-09-30"),
    ],
)
def test_complete_file_has_required_sections_and_level_action(
    state: int | str,
    expected_action: tuple[str, ...],
    expected_due_date: str,
) -> None:
    kpis = _kpis(None if isinstance(state, str) else state)
    if state == "not started":
        kpis.update(K2=None, K3=0, K6=5)
        kpis["level_label"] = "not started"
        kpis["level_word"] = "not started"
        kpis["level_word_ar"] = "بداية غير مؤكدة"
    elif state == "start unknown":
        kpis.update(K2=None, K3=0, K6=None)
        kpis["level_label"] = "start unknown"
        kpis["level_word"] = "start unknown"
        kpis["level_word_ar"] = "بداية غير معروفة"
    elif state == "not assessable":
        kpis.update(A=0.10, K2=None, K3=0, K4=False, K5_months=None, K6=None, n_images=3)
        kpis["level_label"] = "not assessable"
        kpis["level_word"] = "not assessable"
        kpis["level_word_ar"] = "غير قابل للتقييم"

    result = build_inspection_file(kpis, _facts(), _images(), _rules())

    assert result["code"] == "C07"
    assert result["quarter"] == "2024Q2"
    assert result["origin"] == "derived"
    assert result["run_id"] == "fabricated-run"
    assert set(result["sections"]) == {
        "what_happened",
        "why",
        "what_it_means",
        "what_we_do",
    }
    assert result["language"] == {"committee": "ar", "log": "en"}
    assert result["ai_paragraph"] is None
    assert {"text_ar", "text_en"} <= set(result["sections"]["what_happened"])
    assert {"text_ar", "text_en"} <= set(result["sections"]["what_it_means"])

    what_we_do = result["sections"]["what_we_do"]
    assert what_we_do["owner_role"] in ROLE_NAMES
    assert what_we_do["due_date"] == expected_due_date
    action_text = what_we_do["action"]["text_en"].lower()
    for phrase in expected_action:
        assert phrase in action_text
    assert {"text_ar", "text_en"} <= set(what_we_do["action"])
    assert {"text_ar", "text_en"} <= set(what_we_do["escalation_trigger"])


def test_evidence_ids_and_links_are_carried_without_renaming_records() -> None:
    facts = _facts()

    result = build_inspection_file(_kpis(), facts, _images(), _rules())
    why = result["sections"]["why"]

    expected_ids = [fact["record_id"] for fact in facts]
    assert result["evidence_ids"] == expected_ids
    assert why["evidence"] == expected_ids
    assert why["evidence_details"] == [
        {"record_id": "F-001", "link": "https://example.test/records/F-001"},
        {"record_id": "F-002", "link": "https://example.test/records/F-002"},
    ]


def test_unknown_kpis_stay_unknown_and_are_not_replaced_with_zero() -> None:
    kpis = _kpis(4)
    kpis.update(A=None, K2=None, K3=None, K5_months=None, K6=None)

    result = build_inspection_file(kpis, _facts(), _images(), _rules())
    what_happened = result["sections"]["what_happened"]

    assert "unknown" in what_happened["text_en"]
    assert "غير معروف" in what_happened["text_ar"]
    assert "0 months" not in " ".join(_all_strings(result)).lower()
    assert "0 أشهر" not in " ".join(_all_strings(result))


def test_not_assessable_fixes_location_or_images_without_coverage_rejection() -> None:
    kpis = _kpis(None)
    kpis.update(A=0.10, K2=None, K3=0, K4=False, K5_months=None, K6=None, n_images=3)
    kpis["level_label"] = "not assessable"
    kpis["level_word"] = "not assessable"
    kpis["level_word_ar"] = "غير قابل للتقييم"

    result = build_inspection_file(kpis, _facts(), _images(), _rules())
    action = result["sections"]["what_we_do"]["action"]["text_en"]
    rejected = result["sections"]["why"]["rejected_explanations"]

    assert "fix the location or images first" in action.lower()
    assert not any("image coverage" in item["text_en"] for item in rejected)


def test_rejected_explanations_use_only_reproducible_input_numbers() -> None:
    result = build_inspection_file(_kpis(), _facts(), _images(), _rules())
    rejected = result["sections"]["why"]["rejected_explanations"]
    by_text = {item["text_en"]: item for item in rejected}

    coverage = next(item for item in rejected if "image coverage" in item["text_en"])
    assert "14 images" in coverage["text_en"]
    assert "minimum of 6" in coverage["text_en"]
    assert coverage["basis"] == {"n_images": 14, "minimum_images": 6}

    seasonal = next(item for item in rejected if "year over year" in item["text_en"])
    assert "4 quarters" in seasonal["text_en"]
    assert seasonal["basis"] == {"K2": 4, "comparison_quarters": 4}
    assert len(by_text) == len(rejected)


def test_llm_draft_is_isolated_from_factual_sections() -> None:
    llm = {
        "paragraph": "مسودة فقرة للمراجعة فقط.",
        "questions": ["ما حالة التنفيذ؟", "ما موعد التسليم؟", "ما الأدلة المتاحة؟"],
    }

    without_llm = build_inspection_file(_kpis(), _facts(), _images(), _rules())
    with_llm = build_inspection_file(_kpis(), _facts(), _images(), _rules(), llm=llm)

    assert with_llm["ai_paragraph"]["text"] == llm["paragraph"]
    assert with_llm["ai_paragraph"]["status"] == "draft - needs review"
    assert with_llm["ai_paragraph"]["questions"] == llm["questions"]
    assert {key: value for key, value in with_llm.items() if key != "ai_paragraph"} == {
        key: value for key, value in without_llm.items() if key != "ai_paragraph"
    }


def test_output_uses_screening_wording_and_contains_no_forbidden_claims() -> None:
    llm = {
        "paragraph": "مسودة إضافية للمراجعة.",
        "questions": ["سؤال أول؟", "سؤال ثانٍ؟", "سؤال ثالث؟"],
    }

    result = build_inspection_file(_kpis(), _facts(), _images(), _rules(), llm=llm)
    output = " ".join(_all_strings(result)).lower()

    for forbidden in (
        "distressed",
        "risk level",
        "high-risk",
        "completion %",
        "finishing %",
        "fined",
        "غرامة",
        "غرامات",
    ):
        assert forbidden not in output
    assert "screening exposure of 7 months, not a fine" in output
    assert "مدة كشف" in output


def test_builder_is_deterministic() -> None:
    first = build_inspection_file(_kpis(), _facts(), _images(), _rules())
    second = build_inspection_file(_kpis(), _facts(), _images(), _rules())

    assert first == second


def test_markdown_contains_all_evidence_ids_and_links() -> None:
    result = build_inspection_file(_kpis(), _facts(), _images(), _rules())

    markdown = render_markdown(result)

    for fact in _facts():
        assert fact["record_id"] in markdown
        assert fact["link"] in markdown
    assert "Drafted by AI, reviewed by [name]" not in markdown


def test_markdown_footer_is_present_only_for_an_optional_draft() -> None:
    result = build_inspection_file(
        _kpis(),
        _facts(),
        _images(),
        _rules(),
        llm={"paragraph": "مسودة فقرة.", "questions": ["أ؟", "ب؟", "ج؟"]},
    )

    markdown = render_markdown(result)

    assert "Drafted by AI, reviewed by [name]" in markdown


def test_coverage_rejection_works_when_the_image_count_is_not_in_the_kpis():
    kpis = {"code": "C01", "quarter": "2026Q3", "K4": True, "K2": 2, "K3": 5, "K6": None, "level": 2, "level_label": "2",
            "level_word": "second", "reason": "r", "reason_ar": "ر", "origin": "derived", "run_id": "R1", "A": 0.1}
    out = build_inspection_file(kpis, [])
    rejected = out["sections"]["why"]["rejected_explanations"]
    assert any("at least 6 images" in item["text_en"] for item in rejected)
