"""Produce grounded extractive answers with optional, independently approved summaries."""

from __future__ import annotations

import logging
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from src.chatbot.retrieve import RetrievedPassage, TfidfRetriever
from src.inference.ai_config import CallBudget, require_chatbot_approved

NOT_FOUND_ANSWER = "Not found in the documents"
DEFAULT_MIN_SCORE = 0.08

_LOGGER = logging.getLogger(__name__)
_BUDGET_LOCK = threading.Lock()
_CHATBOT_BUDGET: CallBudget | None = None


class Summarizer(Protocol):
    """Provider boundary used only after chatbot approval and budget checks."""

    def generate(
        self,
        system: str,
        prompt: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str: ...


@dataclass(frozen=True)
class AnswerOptions:
    """Caller-controlled retrieval, threshold, and optional-summary settings."""

    top_k: int = 3
    min_score: float = DEFAULT_MIN_SCORE
    config: Mapping[str, Any] | None = None
    summarizer: Summarizer | None = None


@dataclass(frozen=True)
class ChatAnswer:
    """A grounded answer and the citations supporting it."""

    text: str
    citations: tuple[str, ...]
    used_model: bool = False


DEFAULT_ANSWER_OPTIONS = AnswerOptions()


def _quote_passages(ranked_passages: list[RetrievedPassage]) -> str:
    """Render retrieved passages as Markdown block quotes."""

    quoted: list[str] = []
    for ranked_passage in ranked_passages:
        quoted.append(
            "\n".join(f"> {line}" for line in ranked_passage.passage.text.splitlines())
        )
    return "\n\n".join(quoted)


def _unique_citations(ranked_passages: list[RetrievedPassage]) -> tuple[str, ...]:
    """Return citations in retrieval order without duplicates."""

    citations: list[str] = []
    for ranked_passage in ranked_passages:
        citation = ranked_passage.passage.citation
        if citation not in citations:
            citations.append(citation)
    return tuple(citations)


def _chatbot_call_limit(config: Mapping[str, Any] | None) -> int | None:
    """Return the approved chatbot call limit or ``None`` when model use is off."""

    if config is None:
        return None
    try:
        require_chatbot_approved(config)
    except RuntimeError:
        return None
    chatbot = config.get("chatbot")
    if not isinstance(chatbot, Mapping):
        return None
    max_calls_total = chatbot.get("max_calls_total")
    return max_calls_total if isinstance(max_calls_total, int) else None


def _spend_call_budget(max_calls_total: int) -> bool:
    """Spend one process-wide chatbot call when the configured budget permits."""

    global _CHATBOT_BUDGET

    with _BUDGET_LOCK:
        if (
            _CHATBOT_BUDGET is None
            or _CHATBOT_BUDGET.max_calls_total != max_calls_total
        ):
            _CHATBOT_BUDGET = CallBudget(
                max_calls_total=max_calls_total,
                max_calls_per_file=max_calls_total,
            )
        try:
            _CHATBOT_BUDGET.spend("chatbot")
        except RuntimeError:
            return False
    return True


def _provider_settings(config: Mapping[str, Any]) -> tuple[str, float, int] | None:
    """Read bounded provider settings from the existing Gemini configuration."""

    gemini = config.get("gemini")
    if not isinstance(gemini, Mapping):
        return None
    model = gemini.get("model")
    max_output_tokens = gemini.get("max_output_tokens")
    if not isinstance(model, str) or not model.strip():
        return None
    if (
        isinstance(max_output_tokens, bool)
        or not isinstance(max_output_tokens, int)
        or max_output_tokens <= 0
    ):
        return None
    temperature = gemini.get("temperature", 0)
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
        return None
    return model, float(temperature), max_output_tokens


def _default_summarizer() -> Summarizer | None:
    """Create the existing Gemini adapter without contacting a provider."""

    try:
        from src.inference.narrative import GeminiClient

        return GeminiClient()
    except ImportError as exc:
        _LOGGER.warning("Chatbot provider is unavailable (%s)", type(exc).__name__)
        return None


def _summary_prompt(
    question: str,
    ranked_passages: list[RetrievedPassage],
) -> tuple[str, str]:
    """Build the evidence-bounded provider instruction and prompt."""

    evidence = "\n\n".join(
        f"[{index}] {ranked_passage.passage.citation}\n{ranked_passage.passage.text}"
        for index, ranked_passage in enumerate(ranked_passages, start=1)
    )
    system = (
        "Answer the question using only the supplied document passages. "
        "Do not add facts, legal conclusions, names, or unsupported details."
    )
    prompt = f"Question:\n{question}\n\nDocument passages:\n{evidence}"
    return system, prompt


def _clean_summary(summary: str | None) -> str | None:
    """Return a non-empty provider summary or ``None``."""

    if not isinstance(summary, str) or not summary.strip():
        return None
    return summary.strip()


def _call_summarizer(
    summarizer: Summarizer,
    system: str,
    prompt: str,
    settings: tuple[str, float, int],
) -> str | None:
    """Call the provider and contain its failures at the external boundary."""

    model, temperature, max_output_tokens = settings
    try:
        summary = summarizer.generate(
            system, prompt, model, temperature, max_output_tokens
        )
    except Exception as exc:  # noqa: BLE001 - recover with the extractive answer
        _LOGGER.warning("Chatbot provider call failed (%s)", type(exc).__name__)
        return None
    return _clean_summary(summary)


def _model_summary(
    question: str,
    ranked_passages: list[RetrievedPassage],
    options: AnswerOptions,
) -> str | None:
    """Return a provider summary only after approval and budget checks pass."""

    max_calls_total = _chatbot_call_limit(options.config)
    if max_calls_total is None or not _spend_call_budget(max_calls_total):
        return None
    summarizer = options.summarizer or _default_summarizer()
    if summarizer is None or options.config is None:
        return None
    settings = _provider_settings(options.config)
    if settings is None:
        return None
    system, prompt = _summary_prompt(question, ranked_passages)
    return _call_summarizer(summarizer, system, prompt, settings)


def _supported_passages(
    question: str,
    retriever: TfidfRetriever,
    top_k: int,
) -> list[RetrievedPassage]:
    """Return the best supported passages from a wider candidate pool."""

    candidate_count = max(top_k * 5, top_k, 1)
    candidates = retriever.search(question, top_k=candidate_count)
    return [
        ranked_passage
        for ranked_passage in candidates
        if getattr(ranked_passage, "supported", True)
    ][:top_k]


def answer_question(
    question: str,
    retriever: TfidfRetriever,
    options: AnswerOptions = DEFAULT_ANSWER_OPTIONS,
) -> ChatAnswer:
    """Answer from retrieved passages, refusing when the best match is weak."""

    ranked_passages = _supported_passages(question, retriever, options.top_k)
    if not ranked_passages or ranked_passages[0].score < options.min_score:
        return ChatAnswer(text=NOT_FOUND_ANSWER, citations=())

    citations = _unique_citations(ranked_passages)
    summary = _model_summary(question, ranked_passages, options)
    if summary is not None:
        return ChatAnswer(text=summary, citations=citations, used_model=True)
    return ChatAnswer(text=_quote_passages(ranked_passages), citations=citations)
