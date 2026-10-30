"""Contract tests for the guarded Arabic inspection-report path."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.inference import inspection_report
from src.inference.ai_config import CallBudget
from src.inference.inspection_file import build_inspection_file
from src.inference.inspection_report import build_report, main, render_report_html

REVIEWER_PLACEHOLDER = "[اسم المراجع / reviewer name]"


def _kpis() -> dict[str, Any]:
    return {
        "code": "C01",
        "quarter": "2024Q2",
        "A": 0.12,
        "K2": 4,
        "K3": 27,
        "K4": True,
        "K5_months": 7,
        "K6": 25,
        "level": 1,
        "level_label": "1",
        "level_word": "first",
        "level_word_ar": "الأولى",
        "reason": "Fabricated reason.",
        "reason_ar": "سبب مصطنع للاختبار.",
        "may_be_complete": False,
        "origin": "derived",
        "run_id": "fabricated-run",
        "computed_at": "2026-10-29",
        "n_images": 14,
        "series": [],
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
        }
    ]


def _file(*, with_ai: bool = False) -> dict[str, Any]:
    narrative = None
    if with_ai:
        narrative = {
            "paragraph": "مسودة اختبارية للمركب C01 في الربع 2024Q2.",
            "questions": ["ما حالة البناء؟", "ما الأدلة المتاحة؟", "ما الخطوة التالية؟"],
        }
    inspection_file = build_inspection_file(
        _kpis(),
        _facts(),
        images={"status": "missing", "images": []},
        llm=narrative,
    )
    inspection_file["facts"] = _facts()
    return inspection_file


def test_footer_keeps_reviewer_placeholder_unless_explicitly_supplied() -> None:
    default_footer = render_report_html(
        _file(),
        generated_at="2026-10-30T12:00:00+00:00",
        model="fixture-model",
    )
    reviewed_footer = render_report_html(
        _file(),
        generated_at="2026-10-30T12:00:00+00:00",
        model="fixture-model",
        reviewer="Review Team",
    )

    assert REVIEWER_PLACEHOLDER in default_footer
    assert "Prepared by code, reviewed by [اسم المراجع / reviewer name]" in default_footer
    assert "أُعدّ الملف بواسطة كود" in default_footer
    assert "Drafted by AI, reviewed by" not in default_footer
    assert "Review Team" not in default_footer
    assert REVIEWER_PLACEHOLDER not in reviewed_footer
    assert "Prepared by code, reviewed by Review Team" in reviewed_footer
    assert "أُعدّ الملف بواسطة كود" in reviewed_footer
    assert "Drafted by AI, reviewed by" not in reviewed_footer
    assert "Review Team" in reviewed_footer


def test_footer_shows_model_and_time_only_for_an_ai_draft() -> None:
    generated_at = "2026-10-30T12:00:00+00:00"
    template_only = render_report_html(
        _file(),
        generated_at=generated_at,
        model="fixture-model",
    )
    with_draft = render_report_html(
        _file(with_ai=True),
        generated_at=generated_at,
        model="fixture-model",
    )

    assert "fixture-model" not in template_only
    assert generated_at not in template_only
    assert "Filled by code without a model" in template_only
    assert "fixture-model" in with_draft
    assert generated_at in with_draft
    assert "Drafted by AI, reviewed by [اسم المراجع / reviewer name]" in with_draft
    assert "Prepared by code, reviewed by" not in with_draft
    assert "Filled by code without a model" not in with_draft


def test_ai_text_appears_only_in_the_labelled_draft_block() -> None:
    paragraph = "مسودة اختبارية للمركب C01 في الربع 2024Q2."
    question = "ما الخطوة التالية؟"
    html = render_report_html(
        _file(with_ai=True),
        generated_at="2026-10-30T12:00:00+00:00",
        model="fixture-model",
    )

    assert html.count(paragraph) == 1
    assert html.count(question) == 1
    assert "AI draft" in html
    assert "needs review" in html
    assert "Synthetic - for training only" in html


def test_missing_images_are_explicit_and_never_fabricated() -> None:
    html = render_report_html(
        _file(),
        generated_at="2026-10-30T12:00:00+00:00",
        model=None,
        images={"status": "missing", "images": []},
    )

    assert "الصور غير متاحة" in html
    assert "Images are unavailable" in html
    assert "data:image" not in html


def test_fact_detail_is_html_escaped() -> None:
    inspection_file = _file()
    inspection_file["facts"][0]["detail"] = "<script>alert('x')</script>"

    html = render_report_html(
        inspection_file,
        generated_at="2026-10-30T12:00:00+00:00",
        model=None,
    )

    assert "<script>" not in html
    assert "&" + "lt;script" + "&" + "gt;" in html


def test_report_avoids_forbidden_wording_and_labels_k5_as_screening_exposure() -> None:
    html = render_report_html(
        _file(),
        generated_at="2026-10-30T12:00:00+00:00",
        model=None,
    ).lower()

    for forbidden in ("distressed", "risk level", "high-risk", "completion %"):
        assert forbidden not in html
    assert "screening exposure" in html
    assert "مدة كشف" in html
    assert html.count("يوصي النظام، وتقرر لجنة التفتيش.") == 1


def test_build_report_writes_named_html_without_embedded_pixels(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    images = {
        "status": "ok",
        "images": [
            {
                "path": "images/C01_before.jpg",
                "capture_date": "2025-05-01",
                "attribution": "Fabricated source attribution.",
            }
        ],
    }
    monkeypatch.setattr(inspection_report, "get_kpis", lambda code, quarter: _kpis())
    monkeypatch.setattr(inspection_report, "get_facts", lambda code, quarter: _facts())
    monkeypatch.setattr(inspection_report, "get_images", lambda code, quarter: images)

    output_path = build_report(
        "C01",
        "2024Q2",
        generated_at="2026-10-30T12:00:00+00:00",
        out_dir=tmp_path,
    )

    assert output_path == tmp_path / "C01_2024Q2.html"
    html = output_path.read_text(encoding="utf-8")
    assert "data:image" not in html
    assert "images/C01_before.jpg" in html
    assert "2025-05-01" in html
    assert "Fabricated source attribution." in html


class FakeClient:
    """Return controlled narrative text without a network boundary."""

    def __init__(self, responses: tuple[str, str]) -> None:
        self.responses = list(responses)
        self.calls = 0

    def generate(
        self,
        system: str,
        prompt: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        self.calls += 1
        return self.responses.pop(0)


def test_build_report_uses_a_fake_client_and_keeps_draft_verifiable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeClient(
        (
            "مسودة اختبارية للمركب C01 في الربع 2024Q2.",
            "ما حالة البناء؟\nما الأدلة المتاحة؟\nما الخطوة التالية؟",
        )
    )
    config = {
        "gemini": {
            "model": "fixture-model",
            "temperature": 0.2,
            "max_output_tokens": 512,
            "max_calls_total": 3,
            "max_calls_per_file": 3,
            "approval": "approved",
        }
    }
    monkeypatch.setattr(inspection_report, "get_kpis", lambda code, quarter: _kpis())
    monkeypatch.setattr(inspection_report, "get_facts", lambda code, quarter: _facts())
    monkeypatch.setattr(
        inspection_report,
        "get_images",
        lambda code, quarter: {"status": "missing", "images": []},
    )
    monkeypatch.setattr(inspection_report, "load_ai_config", lambda: config)

    output_path = build_report(
        "C01",
        "2024Q2",
        generated_at="2026-10-30T12:00:00+00:00",
        use_model=True,
        client=client,
        budget=CallBudget(max_calls_total=3, max_calls_per_file=3),
        out_dir=tmp_path,
        log_path=tmp_path / "verification.csv",
    )
    html = output_path.read_text(encoding="utf-8")

    assert client.calls == 2
    assert "مسودة اختبارية للمركب C01" in html
    assert "fixture-model" in html
    assert (tmp_path / "verification.csv").is_file()


def test_build_report_does_not_draft_without_explicit_model_use(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(inspection_report, "get_kpis", lambda code, quarter: _kpis())
    monkeypatch.setattr(inspection_report, "get_facts", lambda code, quarter: _facts())
    monkeypatch.setattr(
        inspection_report,
        "get_images",
        lambda code, quarter: {"status": "missing", "images": []},
    )

    def unexpected_draft(*args: object, **kwargs: object) -> None:
        pytest.fail("drafting must not run without --use-model")

    monkeypatch.setattr(inspection_report, "draft_narrative", unexpected_draft)

    build_report(
        "C01",
        "2024Q2",
        generated_at="2026-10-30T12:00:00+00:00",
        out_dir=tmp_path,
    )


def test_cli_skips_an_unknown_code_and_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_build_report(code: str, quarter: str, **kwargs: object) -> Path:
        if code == "C99":
            raise LookupError("No KPI row for unknown code")
        output_path = tmp_path / f"{code}_{quarter}.html"
        output_path.write_text("fixture", encoding="utf-8")
        return output_path

    monkeypatch.setattr(inspection_report, "build_report", fake_build_report)

    exit_code = main(
        [
            "--quarter",
            "2024Q2",
            "--codes",
            "C01",
            "C99",
            "--generated-at",
            "2026-10-30T12:00:00+00:00",
            "--out-dir",
            str(tmp_path),
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 0
    assert "C99" in output.err
    assert "skipped" in output.err.lower()
    assert (tmp_path / "C01_2024Q2.html").is_file()


def test_cli_returns_non_zero_when_no_report_is_written(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_report(code: str, quarter: str, **kwargs: object) -> Path:
        raise LookupError(f"No KPI row for {code}")

    monkeypatch.setattr(inspection_report, "build_report", missing_report)

    exit_code = main(
        [
            "--quarter",
            "2024Q2",
            "--codes",
            "C99",
            "--generated-at",
            "2026-10-30T12:00:00+00:00",
            "--out-dir",
            str(tmp_path),
        ]
    )

    assert exit_code != 0


def test_fixed_generated_at_produces_deterministic_html(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(inspection_report, "get_kpis", lambda code, quarter: _kpis())
    monkeypatch.setattr(inspection_report, "get_facts", lambda code, quarter: _facts())
    monkeypatch.setattr(
        inspection_report,
        "get_images",
        lambda code, quarter: {"status": "missing", "images": []},
    )

    first = build_report(
        "C01",
        "2024Q2",
        generated_at="2026-10-30T12:00:00+00:00",
        out_dir=tmp_path / "first",
    ).read_text(encoding="utf-8")
    second = build_report(
        "C01",
        "2024Q2",
        generated_at="2026-10-30T12:00:00+00:00",
        out_dir=tmp_path / "second",
    ).read_text(encoding="utf-8")

    assert first == second
