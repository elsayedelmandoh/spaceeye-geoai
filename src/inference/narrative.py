"""Generate an optional evidence-bounded inspection narrative."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from src.inference.ai_config import (
    CallBudget,
    get_api_key,
    load_ai_config,
    require_approved,
)
from src.inference.verifier import forbidden_terms, stated_value_mismatches

REPO_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT_PATH = REPO_ROOT / "prompts" / "system" / "inspection_agent.md"
PARAGRAPH_TEMPLATE_PATH = REPO_ROOT / "prompts" / "templates" / "inspection_paragraph.md"
QUESTIONS_TEMPLATE_PATH = REPO_ROOT / "prompts" / "templates" / "visit_questions.md"

_LOGGER = logging.getLogger(__name__)
_DIGIT_TOKEN_RE = re.compile(r"[^\W_]+(?:[-._:/][^\W_]+)*")
_QUESTION_PREFIX_RE = re.compile(r"^(?:[-*•‣▪◦]\s*|\(?\d+[.)]\s*)")


class _DraftFailure(Exception):
    """Carry a safe failure category without provider output or credentials."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class _Client(Protocol):
    """Provider boundary consumed by the narrative orchestrator."""

    def generate(
        self,
        system: str,
        prompt: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str: ...


@dataclass(frozen=True)
class _ProviderContext:
    """Settings and controls shared by both provider calls."""

    client: _Client
    system: str
    model: str
    temperature: float
    max_output_tokens: int
    config: Mapping[str, Any]
    budget: CallBudget
    file_id: str

    def _require_call_approval(self) -> None:
        try:
            require_approved(self.config)
        except Exception as exc:  # noqa: BLE001 - any failure must fall back to the template-only file
            raise _DraftFailure(f"approval check failed ({type(exc).__name__})") from None

    def _spend_call_budget(self) -> None:
        try:
            self.budget.spend(self.file_id)
        except Exception as exc:  # noqa: BLE001 - any failure must fall back to the template-only file
            raise _DraftFailure(f"call budget exhausted ({type(exc).__name__})") from None

    def generate(self, prompt: str) -> str:
        """Require approval, spend budget, and make one provider call."""
        self._require_call_approval()
        self._spend_call_budget()
        try:
            generated_text = self.client.generate(
                system=self.system,
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
            )
        except Exception as exc:  # noqa: BLE001 - any failure must fall back to the template-only file
            raise _DraftFailure(f"provider call failed ({type(exc).__name__})") from None

        if not isinstance(generated_text, str):
            raise _DraftFailure("provider returned non-text output")
        return generated_text


@dataclass(frozen=True)
class _Inputs:
    """Caller-provided data and provider dependencies."""

    kpis: dict
    facts: list[dict]
    client: _Client | None
    budget: CallBudget | None
    config: Mapping[str, Any] | None


@dataclass(frozen=True)
class _PromptContext:
    """Rendered prompts and the token set allowed in generated text."""

    system: str
    paragraph: str
    questions: str
    allowed_tokens: set[str]
    kpis: dict


class GeminiClient:
    """Small adapter around the installed provider SDK."""

    def generate(
        self,
        system: str,
        prompt: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        """Generate text with a lazily imported provider client."""
        from google import genai

        api_key = get_api_key()
        provider = genai.Client(api_key=api_key)
        response = provider.models.generate_content(
            model=model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            ),
        )
        generated_text = getattr(response, "text", "")
        return generated_text if isinstance(generated_text, str) else ""


def _render_template(path: Path, replacements: Mapping[str, str]) -> str:
    """Render a prompt template without interpreting JSON braces."""
    template = path.read_text(encoding="utf-8")
    for placeholder, replacement in replacements.items():
        template = template.replace(f"{{{{{placeholder}}}}}", replacement)
    return template


def _display(display_value: Any) -> str:
    """Return a display value while preserving an explicit unknown state."""
    if display_value is None:
        return "unknown"
    text = str(display_value).strip()
    return text or "unknown"


def _digit_tokens(text: str) -> set[str]:
    """Return alphanumeric tokens that contain at least one digit."""
    return {
        token
        for token in _DIGIT_TOKEN_RE.findall(text)
        if any(character.isdigit() for character in token)
    }


def _parse_questions(text: str) -> list[str] | None:
    """Parse exactly three non-empty question lines without list markers."""
    questions: list[str] = []
    for raw_line in text.splitlines():
        line = _QUESTION_PREFIX_RE.sub("", raw_line.strip(), count=1).strip()
        if line:
            questions.append(line)
    return questions if len(questions) == 3 else None


def _validate_text(text: str, prompts: _PromptContext) -> str | None:
    """Return a rejection reason when text violates the evidence boundary."""
    if forbidden_terms(text):
        return "forbidden wording"

    if _digit_tokens(text) - prompts.allowed_tokens:
        return "unsupported number, date, or code token"
    if stated_value_mismatches(text, prompts.kpis):
        return "stated level or KPI value differs from its source field"
    return None


def _require_valid_text(text: str, prompts: _PromptContext) -> None:
    """Reject generated text that exceeds the attached evidence."""
    rejection = _validate_text(text, prompts)
    if rejection is not None:
        raise _DraftFailure(rejection)


def _provider_context(inputs: _Inputs, system: str) -> _ProviderContext:
    """Resolve provider settings and the bounded call budget."""
    try:
        active_config = (
            load_ai_config() if inputs.config is None else inputs.config
        )
        gemini = active_config.get("gemini")
        if not isinstance(gemini, Mapping):
            raise TypeError("Missing provider configuration")
        active_budget = inputs.budget
        if active_budget is None:
            active_budget = CallBudget(
                max_calls_total=int(gemini["max_calls_total"]),
                max_calls_per_file=int(gemini["max_calls_per_file"]),
            )
        return _ProviderContext(
            client=inputs.client if inputs.client is not None else GeminiClient(),
            system=system,
            model=str(gemini["model"]),
            temperature=float(gemini["temperature"]),
            max_output_tokens=int(gemini["max_output_tokens"]),
            config=active_config,
            budget=active_budget,
            file_id=f"{inputs.kpis['code']}{inputs.kpis['quarter']}",
        )
    except Exception as exc:  # noqa: BLE001 - any failure must fall back to the template-only file
        raise _DraftFailure(f"configuration loading failed ({type(exc).__name__})") from None


def _prompt_context(inputs: _Inputs) -> _PromptContext:
    """Render both templates from attached facts and KPI display context."""
    kpis = inputs.kpis
    try:
        facts_json = json.dumps(inputs.facts, ensure_ascii=False)
        kpis_json = json.dumps(kpis, ensure_ascii=False, default=str)
        code = _display(kpis["code"])
        quarter = _display(kpis["quarter"])
        paragraph = _render_template(
            PARAGRAPH_TEMPLATE_PATH,
            {
                "facts_json": facts_json,
                "code": code,
                "quarter": quarter,
                "level_word": _display(kpis.get("level_word")),
                "reason_ar": _display(kpis.get("reason_ar")),
            },
        )
        questions = _render_template(
            QUESTIONS_TEMPLATE_PATH,
            {"facts_json": facts_json, "code": code, "quarter": quarter},
        )
        system = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 - any failure must fall back to the template-only file
        raise _DraftFailure(f"prompt preparation failed ({type(exc).__name__})") from None
    allowed_tokens = _digit_tokens(facts_json) | _digit_tokens(kpis_json)
    return _PromptContext(
        system=system,
        paragraph=paragraph,
        questions=questions,
        allowed_tokens=allowed_tokens,
        kpis=kpis,
    )


def _draft_paragraph(provider: _ProviderContext, prompts: _PromptContext) -> str:
    """Generate and validate the committee-facing paragraph."""
    paragraph = provider.generate(prompts.paragraph).strip()
    if not paragraph:
        raise _DraftFailure("empty paragraph")
    _require_valid_text(paragraph, prompts)
    return paragraph


def _draft_questions(provider: _ProviderContext, prompts: _PromptContext) -> list[str]:
    """Generate, parse, and validate exactly three visit questions."""
    questions = _parse_questions(provider.generate(prompts.questions))
    if questions is None:
        raise _DraftFailure("invalid question count")
    for question in questions:
        _require_valid_text(question, prompts)
    return questions


def draft_narrative(
    kpis: dict,
    facts: list[dict],
    client: _Client | None = None,
    budget: CallBudget | None = None,
    config: Mapping[str, Any] | None = None,
) -> dict | None:
    """Draft one paragraph and three visit questions from attached facts only.

    Any recoverable failure is logged by category and returns ``None`` so the
    deterministic inspection-file path remains available.
    """
    try:
        inputs = _Inputs(
            kpis=kpis,
            facts=facts,
            client=client,
            budget=budget,
            config=config,
        )
        prompts = _prompt_context(inputs)
        provider = _provider_context(inputs, prompts.system)
        paragraph = _draft_paragraph(provider, prompts)
        questions = _draft_questions(provider, prompts)
        return {"paragraph": paragraph, "questions": questions}
    except _DraftFailure as failure:
        _LOGGER.warning("Narrative generation failed: %s", failure.reason)
    except Exception as failure:  # noqa: BLE001 - any failure must fall back to the template-only file
        _LOGGER.warning(
            "Narrative generation failed: unexpected failure (%s)",
            type(failure).__name__,
        )
    return None
