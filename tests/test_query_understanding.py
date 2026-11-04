import pytest

from chatbot.app.generation import query_understanding
from chatbot.app.generation.query_understanding import understand_query

QUESTIONS = [
    "هل المشروع متأخر عن الجدول الزمني؟",
    "إيه المؤشرات اللي اعتمدت عليها في تحديد حالته؟",
    "إيه آخر بيانات متاحة عن المشروع؟",
    "قارن حالته بالربع السابق.",
]


@pytest.fixture(autouse=True)
def no_gemini(monkeypatch):
    """Keep these tests offline: no key, so the keyword fallback is used."""
    monkeypatch.setattr(
        query_understanding,
        "get_settings",
        lambda: type("S", (), {"gemini_api_key": "", "gemini_model": "m"})(),
    )


@pytest.mark.parametrize("question", QUESTIONS)
def test_understand_query_returns_valid_structure_without_model(question):
    result = understand_query(question=question, last_compound="C04")

    assert result["intent"] in query_understanding.VALID_INTENTS
    assert result["understanding_mode"] == "keyword_fallback"
    assert result["rewritten_query"]


def test_empty_question_is_rejected():
    with pytest.raises(ValueError):
        understand_query(question="  ")
