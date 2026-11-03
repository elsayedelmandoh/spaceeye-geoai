"""Real-corpus evaluation cases for document-chatbot retrieval and refusal."""

from __future__ import annotations

import pytest

from src.chatbot.answer import NOT_FOUND_ANSWER, answer_question
from src.chatbot.retrieve import TfidfRetriever, get_default_retriever


@pytest.fixture(scope="module")
def real_corpus_retriever() -> TfidfRetriever:
    """Return the cached real-corpus retriever for this evaluation module."""

    return get_default_retriever()


@pytest.mark.parametrize(
    ("question", "expected_path", "required_text", "forbidden_heading"),
    [
        pytest.param(
            "What does Article 54 of Law 119 require from the site supervisor?",
            "law-119-2008-building-law-art54-ar.md",
            None,
            None,
            id="article-54-supervisor",
        ),
        pytest.param(
            "What resolution is Dynamic World?",
            "dynamic-world-v1-en.md",
            "10 m",
            None,
            id="dynamic-world-resolution",
        ),
        pytest.param(
            "ما هي مدة السماح لتسليم الوحدة في قرار 2184 لسنة 2022؟",
            "decree-2184-2022-real-estate-sales-rules-ar.md",
            "اثنى عشر شهرًا",
            "قرار رئيس مجلس الوزراء رقم 2184 لسنة 2022",
            id="decree-delivery-grace",
        ),
        pytest.param(
            "What does SLA mean in this project?",
            "sla-and-kpi-note-team.md",
            None,
            None,
            id="project-sla",
        ),
        pytest.param(
            "What is ISO 37120?",
            "iso-37120-37122-city-indicators-en.md",
            None,
            None,
            id="iso-37120",
        ),
        pytest.param(
            "What does K5 measure?",
            "kpi-cards.md",
            "K5",
            None,
            id="k5-card",
        ),
        pytest.param(
            "What licence does Open Buildings use?",
            "open-buildings-temporal-v1-en.md",
            None,
            None,
            id="open-buildings-licence",
        ),
        pytest.param(
            "What are Esri's terms for exporting World Imagery tiles?",
            "esri-world-imagery-wayback-en.md",
            None,
            None,
            id="esri-export-terms",
        ),
        pytest.param(
            "When was ACUD founded?",
            "acud-public-site-en.md",
            None,
            None,
            id="acud-founded",
        ),
        pytest.param(
            "What penalty applies for breaking Article 54?",
            "law-119-2008-building-law-art54-ar.md",
            None,
            None,
            id="article-54-penalty",
        ),
        pytest.param(
            "Who won the 2022 World Cup?",
            None,
            None,
            None,
            id="refuse-world-cup",
        ),
        pytest.param(
            "Who is the president of France?",
            None,
            None,
            None,
            id="refuse-france-president",
        ),
        pytest.param(
            "What is the weather in Cairo tomorrow?",
            None,
            None,
            None,
            id="refuse-cairo-weather",
        ),
        pytest.param(
            "How do I cook koshari?",
            None,
            None,
            None,
            id="refuse-koshari",
        ),
        pytest.param(
            "What is the best smartphone to buy?",
            None,
            None,
            None,
            id="refuse-smartphone",
        ),
    ],
)
def test_real_corpus_retrieval_and_refusal_cases(
    question: str,
    expected_path: str | None,
    required_text: str | None,
    forbidden_heading: str | None,
    real_corpus_retriever: TfidfRetriever,
) -> None:
    """Retrieve the requested source or refuse an unsupported question."""

    answer = answer_question(question, real_corpus_retriever)

    if expected_path is None:
        assert answer.text == NOT_FOUND_ANSWER
        assert answer.citations == ()
        return

    assert answer.citations
    assert expected_path in answer.citations[0]
    ranked = real_corpus_retriever.search(question, top_k=3)
    top_cited = next(
        result
        for result in ranked
        if result.passage.citation == answer.citations[0]
    )
    if required_text is not None:
        assert required_text in top_cited.passage.text
    if forbidden_heading is not None:
        assert top_cited.passage.heading != forbidden_heading


def test_arabic_data_protection_question_never_returns_the_rubric(
    real_corpus_retriever: TfidfRetriever,
) -> None:
    """Answer the Arabic privacy-law question only from Law 151 or refuse it."""

    answer = answer_question(
        "ما هو قانون حماية البيانات الشخصية؟",
        real_corpus_retriever,
    )

    if answer.text == NOT_FOUND_ANSWER:
        assert answer.citations == ()
    else:
        assert answer.citations
        assert "law-151-2020-personal-data-protection-en.md" in answer.citations[0]
