"""Fabricated contract tests for guarded narrative drafting."""

from __future__ import annotations

from typing import Any

import pytest

from src.inference import narrative
from src.inference.ai_config import CallBudget
from src.inference.inspection_file import build_inspection_file
from src.inference.narrative import draft_narrative

_VALID_PARAGRAPH = "أوضح السجلات أن المركب C01 في الربع 2024Q2 يحتاج إلى تحقق ميداني."
_VALID_QUESTIONS = (
    "1. ما حالة أعمال البناء في الموقع؟\n"
    "2. ما السجلات المتاحة لتأكيد موعد التسليم؟\n"
    "3. ما الأدلة الميدانية التي يمكن توثيقها؟"
)
_EXPECTED_QUESTIONS = [
    "ما حالة أعمال البناء في الموقع؟",
    "ما السجلات المتاحة لتأكيد موعد التسليم؟",
    "ما الأدلة الميدانية التي يمكن توثيقها؟",
]


class FakeClient:
    """Return canned text and record each provider call."""

    def __init__(self, *responses: str, error: Exception | None = None) -> None:
        self.responses = list(responses)
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def generate(
        self,
        system: str,
        prompt: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        self.calls.append(
            {
                "system": system,
                "prompt": prompt,
                "model": model,
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            }
        )
        if self.error is not None:
            raise self.error
        return self.responses.pop(0)


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
        "series": [],
        "internal_note": "UNRELATED-KPI-DETAIL",
    }


def _facts() -> list[dict[str, Any]]:
    return [
        {
            "record_id": "F-001",
            "kind": "statement",
            "subtype": "delivery_promise",
            "published_date": "2023-12-15",
            "detail": "تفصيل مصطنع لاختبار حدود الأدلة.",
            "link": "https://example.test/records/F-001",
        }
    ]


def _config(approval: str = "approved") -> dict[str, Any]:
    return {
        "gemini": {
            "model": "fabricated-model",
            "temperature": 0.2,
            "max_output_tokens": 512,
            "max_calls_total": 30,
            "max_calls_per_file": 3,
            "approval": approval,
        }
    }


@pytest.fixture(autouse=True)
def block_environment_backed_lookups(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure fabricated tests never read local credentials or default config."""

    def fail_lookup(*args: object, **kwargs: object) -> None:
        pytest.fail("tests must not use environment-backed AI lookups")

    monkeypatch.setattr(narrative, "get_api_key", fail_lookup)
    monkeypatch.setattr(narrative, "load_ai_config", fail_lookup)


def test_draft_narrative_returns_paragraph_and_three_parsed_questions() -> None:
    client = FakeClient(_VALID_PARAGRAPH, _VALID_QUESTIONS)

    result = draft_narrative(
        _kpis(),
        _facts(),
        client=client,
        budget=CallBudget(max_calls_total=3, max_calls_per_file=3),
        config=_config(),
    )

    assert result == {
        "paragraph": _VALID_PARAGRAPH,
        "questions": _EXPECTED_QUESTIONS,
    }
    assert len(client.calls) == 2
    assert client.calls[0]["model"] == "fabricated-model"
    assert client.calls[0]["temperature"] == 0.2
    assert client.calls[0]["max_output_tokens"] == 512


def test_draft_narrative_blocks_unapproved_calls() -> None:
    client = FakeClient(_VALID_PARAGRAPH, _VALID_QUESTIONS)

    result = draft_narrative(
        _kpis(),
        _facts(),
        client=client,
        budget=CallBudget(max_calls_total=3, max_calls_per_file=3),
        config=_config(approval="pending"),
    )

    assert result is None
    assert client.calls == []


def test_draft_narrative_returns_none_when_budget_is_exhausted() -> None:
    client = FakeClient(_VALID_PARAGRAPH, _VALID_QUESTIONS)

    result = draft_narrative(
        _kpis(),
        _facts(),
        client=client,
        budget=CallBudget(max_calls_total=1, max_calls_per_file=1),
        config=_config(),
    )

    assert result is None
    assert len(client.calls) == 1


def test_draft_narrative_returns_none_when_client_raises() -> None:
    client = FakeClient(error=RuntimeError("fabricated client failure"))

    result = draft_narrative(
        _kpis(),
        _facts(),
        client=client,
        budget=CallBudget(max_calls_total=3, max_calls_per_file=3),
        config=_config(),
    )

    assert result is None
    assert len(client.calls) == 1


@pytest.mark.parametrize(
    "questions",
    [
        "ما حالة الموقع؟\nما السجلات المتاحة؟",
        "ما حالة الموقع؟\nما السجلات المتاحة؟\nما الأدلة المتاحة؟\nما موعد التسليم؟",
    ],
)
def test_draft_narrative_rejects_anything_other_than_three_questions(
    questions: str,
) -> None:
    client = FakeClient(_VALID_PARAGRAPH, questions)

    result = draft_narrative(
        _kpis(),
        _facts(),
        client=client,
        budget=CallBudget(max_calls_total=3, max_calls_per_file=3),
        config=_config(),
    )

    assert result is None


@pytest.mark.parametrize(
    "invented_text",
    [
        "أوضح السجلات أن المركب C01 بلغ 99 ربعًا.",
        "أوضح السجلات أن المركب C01 بلغ في 2099-01-01.",
        "أوضح السجلات أن المركب C99 يحتاج إلى تحقق ميداني.",
    ],
)
def test_draft_narrative_rejects_an_invented_number_date_or_code(
    invented_text: str,
) -> None:
    client = FakeClient(invented_text, _VALID_QUESTIONS)

    result = draft_narrative(
        _kpis(),
        _facts(),
        client=client,
        budget=CallBudget(max_calls_total=3, max_calls_per_file=3),
        config=_config(),
    )

    assert result is None


@pytest.mark.parametrize(
    "forbidden_word",
    ["distressed", "risk level", "high-risk", "completion %"],
)
def test_draft_narrative_rejects_forbidden_wording(forbidden_word: str) -> None:
    client = FakeClient(
        f"The compound C01 is {forbidden_word}.",
        _VALID_QUESTIONS,
    )

    result = draft_narrative(
        _kpis(),
        _facts(),
        client=client,
        budget=CallBudget(max_calls_total=3, max_calls_per_file=3),
        config=_config(),
    )

    assert result is None


def test_draft_narrative_rejects_an_empty_paragraph() -> None:
    client = FakeClient("   ", _VALID_QUESTIONS)

    result = draft_narrative(
        _kpis(),
        _facts(),
        client=client,
        budget=CallBudget(max_calls_total=3, max_calls_per_file=3),
        config=_config(),
    )

    assert result is None


def test_prompts_include_only_the_attached_facts_and_display_context() -> None:
    client = FakeClient(_VALID_PARAGRAPH, _VALID_QUESTIONS)

    draft_narrative(
        _kpis(),
        _facts(),
        client=client,
        budget=CallBudget(max_calls_total=3, max_calls_per_file=3),
        config=_config(),
    )

    for call in client.calls:
        assert "تفصيل مصطنع لاختبار حدود الأدلة." in call["prompt"]
        assert "UNRELATED-KPI-DETAIL" not in call["prompt"]
        assert "UNRELATED-FACT-DETAIL" not in call["prompt"]
        assert "{{" not in call["prompt"]


def test_draft_narrative_result_can_be_passed_to_build_inspection_file() -> None:
    client = FakeClient(_VALID_PARAGRAPH, _VALID_QUESTIONS)

    draft = draft_narrative(
        _kpis(),
        _facts(),
        client=client,
        budget=CallBudget(max_calls_total=3, max_calls_per_file=3),
        config=_config(),
    )

    result = build_inspection_file(_kpis(), _facts(), llm=draft)

    assert result["ai_paragraph"] is not None
    assert result["ai_paragraph"]["text"] == _VALID_PARAGRAPH
    assert result["ai_paragraph"]["questions"] == _EXPECTED_QUESTIONS
    assert result["ai_paragraph"]["status"] == "draft - needs review"
