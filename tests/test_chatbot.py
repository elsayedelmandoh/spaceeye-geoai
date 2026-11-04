"""Tests for the citations-first document Q&A chatbot."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.chatbot.answer import NOT_FOUND_ANSWER, AnswerOptions, answer_question
from src.chatbot.corpus import Passage, load_corpus, split_markdown
from src.chatbot.retrieve import TfidfRetriever, get_default_retriever
from src.inference.ai_config import load_ai_yaml_config


def test_shipped_chatbot_configuration_is_pending_with_zero_model_calls() -> None:
    config = load_ai_yaml_config(Path("configs/ai.yaml"))

    assert config["chatbot"] == {
        "approval": "pending",
        "max_calls_total": 0,
    }


def _write_document(root: Path, relative_path: str, text: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_passage_splitting_keeps_headings_and_file_path() -> None:
    text = (
        "# Inspection Capacity\n\n"
        + "inspection capacity review " * 40
        + "\n\n"
        + "## Selection Method\n\n"
        + "selection method review " * 40
    )

    passages = split_markdown("docs/fabricated-guide.md", text)

    assert [passage.heading for passage in passages] == [
        "Inspection Capacity",
        "Selection Method",
    ]
    assert [passage.path for passage in passages] == [
        "docs/fabricated-guide.md",
        "docs/fabricated-guide.md",
    ]
    assert passages[0].text.startswith("# Inspection Capacity")
    assert passages[1].text.startswith("## Selection Method")
    assert all(100 <= passage.word_count <= 200 for passage in passages)


def test_split_markdown_redacts_labeled_personal_values_but_keeps_codes() -> None:
    text = (
        "# Privacy Check\n\n"
        "Developer: C01\n\n"
        "Reviewer: PRIVATE IDENTIFIER\n"
    )

    passages = split_markdown("docs/privacy-check.md", text)

    assert "Developer: C01" in passages[0].text
    assert "PRIVATE IDENTIFIER" not in passages[0].text
    assert "[redacted]" in passages[0].text


def test_external_document_front_matter_is_loaded_as_metadata(
    tmp_path: Path,
) -> None:
    _write_document(
        tmp_path,
        "data/knowledge/external/fabricated-source.md",
        """---
title: Fabricated Public Source
source_url: https://example.test/source
retrieval_date: 2026-11-02
---

# Public Rules

This fabricated paragraph describes a public rule for the chatbot corpus test.
""",
    )

    passages = load_corpus(
        repo_root=tmp_path,
        project_paths=(),
        external_dir=tmp_path / "data" / "knowledge" / "external",
    )

    assert len(passages) == 1
    assert passages[0].title == "Fabricated Public Source"
    assert passages[0].source_url == "https://example.test/source"
    assert passages[0].retrieved == "2026-11-02"


def test_every_external_markdown_file_is_including_the_local_guide(
    tmp_path: Path,
) -> None:
    _write_document(
        tmp_path,
        "data/knowledge/external/README.md",
        """---
title: External Knowledge Guide
source_url: ""
retrieval_date: 2026-11-02
---

# External Knowledge Guide

This fabricated guide documents the external source format.
""",
    )

    passages = load_corpus(
        repo_root=tmp_path,
        project_paths=(),
        external_dir=tmp_path / "data" / "knowledge" / "external",
    )

    assert [passage.path for passage in passages] == [
        "data/knowledge/external/README.md"
    ]


def test_missing_fixed_document_is_skipped_with_a_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    missing = "docs/missing-fabricated-document.md"

    passages = load_corpus(
        repo_root=tmp_path,
        project_paths=(missing,),
        external_dir=tmp_path / "data" / "knowledge" / "external",
    )

    assert passages == []
    assert missing in caplog.text


def _retrieval_corpus() -> list[Passage]:
    return [
        Passage(
            path="docs/inspection-capacity.md",
            heading="Inspection Capacity",
            text=(
                "Inspection capacity is four priority inspections per cycle. "
                "The inspection team ranks candidates using published evidence."
            ),
            title="Inspection Capacity",
        ),
        Passage(
            path="docs/imagery.md",
            heading="Satellite Imagery",
            text=(
                "Satellite imagery provides vegetation indices and construction "
                "signals for the digital twin. Imagery is retrospective context."
            ),
            title="Satellite Imagery",
        ),
        Passage(
            path="docs/arabic-capacity.md",
            heading="سعة المعاينة",
            text=(
                "سعة المعاينة أربعة مواقع في كل دورة. يقوم فريق المعاينة "
                "بترتيب الأولويات باستخدام الأدلة المنشورة."
            ),
            title="سعة المعاينة",
        ),
    ]


def test_retrieval_ranks_the_right_passage_first_for_english() -> None:
    retriever = TfidfRetriever(_retrieval_corpus())

    results = retriever.search("How is inspection capacity prioritized?", top_k=2)

    assert results[0].passage.path == "docs/inspection-capacity.md"
    assert results[0].score > 0


def test_retrieval_ranks_the_right_passage_first_for_arabic() -> None:
    retriever = TfidfRetriever(_retrieval_corpus())

    results = retriever.search("ما سعة المعاينة؟", top_k=2)

    assert results[0].passage.path == "docs/arabic-capacity.md"
    assert results[0].score > 0


def test_answer_pruning_keeps_only_scored_directly_relevant_passages() -> None:
    shared_title = "SLA and how the project KPIs relate to it"
    retriever = TfidfRetriever(
        [
            Passage(
                path="docs/sla-note.md",
                heading="SLA definition",
                text=(
                    "SLA stands for Service Level Agreement (SLA). Work orders "
                    "use the agreed completion time."
                ),
                title=shared_title,
            ),
            Passage(
                path="docs/sla-note.md",
                heading="SLA timing",
                text=(
                    "SLA measures whether each work order is completed within "
                    "its agreed time."
                ),
                title=shared_title,
            ),
            Passage(
                path="docs/sla-note.md",
                heading="ISO",
                text=(
                    "ISO is the International Organization for Standardization "
                    "and publishes city indicator standards."
                ),
                title=shared_title,
            ),
            Passage(
                path="docs/operations.md",
                heading="Work-order timing",
                text=(
                    "Operations records work-order timing for audit purposes. "
                    + "The public note explains the operational background. " * 20
                    + "SLA appears once in this longer passage."
                ),
                title="Operations reference",
            ),
        ]
    )

    answer = answer_question(
        "What is SLA?",
        retriever,
        AnswerOptions(
            min_score=0.01,
            config={"chatbot": {"approval": "pending", "max_calls_total": 0}},
        ),
    )

    assert answer.citations == (
        "docs/sla-note.md · SLA definition",
        "docs/sla-note.md · SLA timing",
    )


def test_low_score_answer_is_not_found_without_citations() -> None:
    retriever = TfidfRetriever(_retrieval_corpus())

    answer = answer_question(
        "quantum xylophone nebula",
        retriever,
        AnswerOptions(
            min_score=0.08,
            config={"chatbot": {"approval": "pending", "max_calls_total": 0}},
        ),
    )

    assert answer.text == NOT_FOUND_ANSWER
    assert answer.citations == ()
    assert answer.used_model is False


def test_answer_citations_carry_the_repository_relative_file_path() -> None:
    retriever = TfidfRetriever(_retrieval_corpus())

    answer = answer_question(
        "How is inspection capacity prioritized?",
        retriever,
        AnswerOptions(
            min_score=0.01,
            config={"chatbot": {"approval": "pending", "max_calls_total": 0}},
        ),
    )

    assert answer.text
    assert answer.citations
    assert all(" · " in citation for citation in answer.citations)
    assert any(citation.startswith("docs/inspection-capacity.md · ") for citation in answer.citations)


class RecordingSummarizer:
    """Record optional model calls and return a fabricated summary."""

    def __init__(self) -> None:
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
        return "Fabricated grounded summary."


def test_model_path_is_not_called_when_approval_is_pending() -> None:
    summarizer = RecordingSummarizer()
    retriever = TfidfRetriever(_retrieval_corpus())

    answer = answer_question(
        "How is inspection capacity prioritized?",
        retriever,
        AnswerOptions(
            min_score=0.01,
            config={"chatbot": {"approval": "pending", "max_calls_total": 0}},
            summarizer=summarizer,
        ),
    )

    assert summarizer.calls == []
    assert answer.used_model is False


def test_approved_model_path_returns_a_summary_with_retrieved_citations() -> None:
    summarizer = RecordingSummarizer()
    retriever = TfidfRetriever(_retrieval_corpus())
    config = {
        "gemini": {
            "model": "fabricated-model",
            "temperature": 0,
            "max_output_tokens": 256,
        },
        "chatbot": {"approval": "approved", "max_calls_total": 1},
    }

    answer = answer_question(
        "How is inspection capacity prioritized?",
        retriever,
        AnswerOptions(
            min_score=0.01,
            config=config,
            summarizer=summarizer,
        ),
    )

    assert len(summarizer.calls) == 1
    assert answer.text == "Fabricated grounded summary."
    assert answer.used_model is True
    assert answer.citations


def test_real_corpus_refuses_an_off_topic_world_cup_question() -> None:
    answer = answer_question(
        "Who won the 2022 World Cup?",
        get_default_retriever(),
    )

    assert answer.text == NOT_FOUND_ANSWER
    assert answer.citations == ()


def test_real_corpus_ranks_law_119_article_54_first() -> None:
    answer = answer_question(
        "What does Article 54 of Law 119 require from the site supervisor?",
        get_default_retriever(),
    )

    assert answer.citations[0] == (
        "data/knowledge/external/law-119-2008-building-law-art54-ar.md · مادة (54)"
    )


def test_real_corpus_dynamic_world_answer_states_its_resolution() -> None:
    retriever = get_default_retriever()
    top_passage = retriever.search("What resolution is Dynamic World?", top_k=1)[0]

    answer = answer_question("What resolution is Dynamic World?", retriever)

    assert top_passage.passage.path == (
        "data/knowledge/external/dynamic-world-v1-en.md"
    )
    assert "10 m" in top_passage.passage.text
    assert answer.citations[0].startswith(
        "data/knowledge/external/dynamic-world-v1-en.md · "
    )


def test_real_corpus_decree_answer_uses_the_delivery_grace_article() -> None:
    retriever = get_default_retriever()
    question = "ما هي مدة السماح لتسليم الوحدة في قرار 2184 لسنة 2022؟"
    top_passage = retriever.search(question, top_k=1)[0]

    answer = answer_question(question, retriever)

    assert top_passage.passage.path == (
        "data/knowledge/external/decree-2184-2022-real-estate-sales-rules-ar.md"
    )
    assert top_passage.passage.heading == "المادة (5) التأخر فى التسليم"
    assert "اثنى عشر شهرًا" in top_passage.passage.text
    assert answer.citations[0].startswith(
        "data/knowledge/external/decree-2184-2022-real-estate-sales-rules-ar.md · "
    )


def test_real_corpus_keeps_the_project_sla_note_first() -> None:
    answer = answer_question(
        "What does SLA mean in this project?",
        get_default_retriever(),
    )

    assert answer.citations[0].startswith(
        "data/knowledge/external/sla-and-kpi-note-team.md · "
    )
