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


@pytest.mark.parametrize(
    ("question", "expected_citations", "allowed_paths", "required_terms"),
    [
        pytest.param(
            "اي هو SLA",
            (
                (
                    "data/knowledge/external/sla-and-kpi-note-team.md · "
                    "SLA (Service Level Agreement) in this project"
                ),
            ),
            (),
            (),
            id="arabic-sla-single-section",
        ),
        pytest.param(
            "What is SLA?",
            (
                (
                    "data/knowledge/external/sla-and-kpi-note-team.md · "
                    "SLA (Service Level Agreement) in this project"
                ),
            ),
            (),
            (),
            id="english-sla-single-section",
        ),
        pytest.param(
            "مين الكمبوندا اللي هزوره الاول",
            None,
            ("INSPECTION_DOSSIERS.md", "user-guide.md"),
            ("cycle list", "priority level", "visit list"),
            id="arabic-dialect-first-visit",
        ),
        pytest.param(
            "Which compound should the committee visit first?",
            None,
            ("INSPECTION_DOSSIERS.md", "user-guide.md"),
            ("cycle list", "priority level", "visit list"),
            id="english-first-visit",
        ),
    ],
)
def test_precision_cases_return_only_relevant_citations(
    question: str,
    expected_citations: tuple[str, ...] | None,
    allowed_paths: tuple[str, ...],
    required_terms: tuple[str, ...],
    real_corpus_retriever: TfidfRetriever,
) -> None:
    """Keep SLA precise and answer first-visit questions from project guidance."""

    answer = answer_question(question, real_corpus_retriever)

    if expected_citations is not None:
        assert answer.citations == expected_citations
        return

    assert answer.text != NOT_FOUND_ANSWER
    assert answer.citations
    assert any(
        allowed_path in citation
        for citation in answer.citations
        for allowed_path in allowed_paths
    )
    cited_passages = [
        result.passage
        for result in real_corpus_retriever.search(question, top_k=15)
        if result.passage.citation in answer.citations
    ]
    cited_text = "\n".join(passage.text for passage in cited_passages).casefold()
    assert any(term.casefold() in cited_text for term in required_terms)


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


@pytest.mark.parametrize(
    "question",
    [
        "مين الكمبوندا اللي هزوره الاول",
        "Which compound should the committee visit first?",
    ],
)
def test_first_visit_top_citation_states_the_visit_order(
    question: str,
    real_corpus_retriever: TfidfRetriever,
) -> None:
    """Lead with the cycle list or priority map, not a per-compound screen."""

    answer = answer_question(question, real_corpus_retriever)

    assert answer.text != NOT_FOUND_ANSWER
    assert any(
        marker in answer.citations[0]
        for marker in (
            "INSPECTION_DOSSIERS.md",
            "Screen 1: Priority map",
            "0. The plan on one page",
        )
    )


def test_inspection_capacity_question_cites_capacity_four(
    real_corpus_retriever: TfidfRetriever,
) -> None:
    """Answer the capacity question from a passage that states capacity 4."""

    answer = answer_question(
        "What is the inspection capacity?",
        real_corpus_retriever,
    )

    assert answer.text != NOT_FOUND_ANSWER
    assert "capacity 4" in answer.text.casefold()
