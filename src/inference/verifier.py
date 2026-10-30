"""Stricter replacement for verify.py with normalised token matching and token-only logs."""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from src.pipeline.common import APP

DEFAULT_LOG_PATH = APP / "ai_verification_log.csv"

LOG_COLUMNS = (
    "file_id",
    "kind",
    "token",
    "token_type",
    "verdict",
    "note",
    "checked_on",
)
VERDICTS = ("correct", "wrong number", "unsupported claim", "missing context")

CAUSAL_WORDS_EN = (
    "because",
    "due to",
    "caused by",
    "therefore",
    "as a result",
)
CAUSAL_WORDS_AR = (
    "بسبب",
    "نتيجة",
    "لذلك",
    "ناتج عن",
    "يعود إلى",
)

_DIGIT_TRANSLATION = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩٫٬",
    "0123456789.,",
)
_DATE_PATTERN = (
    r"(?<![A-Za-z0-9_])"
    r"(?:\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])"
    r"|\d{4}[Qq][1-4])"
    r"(?![A-Za-z0-9_])"
)
_CODE_PATTERN = r"(?<![A-Za-z0-9_])[CDcd]\d{2}(?![A-Za-z0-9_])"
_NUMBER_PATTERN = (
    r"(?<![A-Za-z0-9_,])"
    r"[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)"
    r"(?![A-Za-z0-9_,]|\.\d)"
)
_TOKEN_PATTERN = re.compile(
    rf"(?P<date>{_DATE_PATTERN})"
    rf"|(?P<code>{_CODE_PATTERN})"
    rf"|(?P<number>{_NUMBER_PATTERN})"
)
_LEVEL_EN_PATTERN = re.compile(
    r"\b(?:priority\s+)?level\b\s*(?:is|=|:)?\s*"
    r"(?:[1-4]\b|one\b|two\b|three\b|four\b)",
    re.IGNORECASE,
)
_LEVEL_AR_PATTERN = re.compile(
    r"مستوى[^0-9]{0,40}(?:[1-4]\b|الأولى|الثانية|الثالثة|الرابعة)"
)
_CAUSAL_PATTERNS = tuple(
    (
        term,
        re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", re.IGNORECASE),
    )
    for term in CAUSAL_WORDS_EN + CAUSAL_WORDS_AR
)


@dataclass(frozen=True)
class _TextToken:
    token: str
    token_type: str
    number: Decimal | None = None


@dataclass(frozen=True)
class _Claim:
    token: str
    token_type: str
    verdict: str
    note: str


@dataclass
class _SourceTokens:
    numbers: set[Decimal] = field(default_factory=set)
    dates: set[str] = field(default_factory=set)
    codes: set[str] = field(default_factory=set)
    levels: set[int] = field(default_factory=set)


def _normalise_digits(text: str) -> str:
    return text.translate(_DIGIT_TRANSLATION)


def _format_decimal(number: Decimal) -> str:
    if number == number.to_integral_value():
        return format(number.to_integral_value(), "f")
    return format(number.normalize(), "f")


def _source_decimal(value: float | Decimal) -> Decimal | None:
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _extract_text_tokens(text: str) -> list[_TextToken]:
    normalised_text = _normalise_digits(text)
    extracted: list[_TextToken] = []
    for match in _TOKEN_PATTERN.finditer(normalised_text):
        raw_token = match.group(0)
        if match.lastgroup == "date":
            token = raw_token.upper() if "Q" in raw_token.upper() else raw_token
            extracted.append(_TextToken(token, "date"))
        elif match.lastgroup == "code":
            extracted.append(_TextToken(raw_token.upper(), "code"))
        else:
            number = Decimal(raw_token.replace(",", ""))
            extracted.append(_TextToken(_format_decimal(number), "number", number))
    return extracted


def _normalise_level(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        number = _source_decimal(value)
    elif isinstance(value, str) and re.fullmatch(r"[1-4]", value.strip()):
        number = Decimal(value.strip())
    else:
        return None
    if number is None or number != number.to_integral_value():
        return None
    level = int(number)
    return level if level in {1, 2, 3, 4} else None


def _add_string_tokens(value: str, source_tokens: _SourceTokens) -> None:
    for token in _extract_text_tokens(value):
        if token.token_type == "number" and token.number is not None:
            source_tokens.numbers.add(token.number)
        elif token.token_type == "date":
            source_tokens.dates.add(token.token)
        else:
            source_tokens.codes.add(token.token)


def _walk_mapping(mapping: Mapping[Any, Any], source_tokens: _SourceTokens) -> None:
    for key, child in mapping.items():
        if str(key).casefold() == "level":
            level = _normalise_level(child)
            if level is not None:
                source_tokens.levels.add(level)
        _walk_source(child, source_tokens)


def _walk_source(node: Any, source_tokens: _SourceTokens) -> None:
    if isinstance(node, Mapping):
        _walk_mapping(node, source_tokens)
    elif isinstance(node, (list, tuple)):
        for child in node:
            _walk_source(child, source_tokens)
    elif isinstance(node, str):
        _add_string_tokens(node, source_tokens)
    elif isinstance(node, bool) or node is None:
        return
    elif isinstance(node, (int, float, Decimal)):
        number = _source_decimal(node)
        if number is not None:
            source_tokens.numbers.add(number)
    elif isinstance(node, datetime):
        source_tokens.dates.add(node.date().isoformat())
    elif isinstance(node, date):
        source_tokens.dates.add(node.isoformat())


def _collect_source_tokens(source: dict[str, Any] | list[Any]) -> _SourceTokens:
    source_tokens = _SourceTokens()
    _walk_source(source, source_tokens)
    return source_tokens


def _near_source_note(number: Decimal, source_numbers: set[Decimal]) -> str:
    if not source_numbers:
        return "number not found in source"
    nearest = min(source_numbers, key=lambda source_number: abs(number - source_number))
    difference = abs(number - nearest)
    if difference <= Decimal(1):
        return (
            "number not found in source; "
            f"source number {_format_decimal(nearest)} differs by "
            f"{_format_decimal(difference)} (within 1 unit)"
        )
    return "number not found in source"


def _judge_token(
    token: _TextToken,
    source_tokens: _SourceTokens,
) -> _Claim:
    if token.token_type == "number" and token.number in source_tokens.numbers:
        return _Claim(token.token, token.token_type, "correct", "matched source value")
    if token.token_type == "date" and token.token in source_tokens.dates:
        return _Claim(token.token, token.token_type, "correct", "matched source value")
    if token.token_type == "code" and token.token in source_tokens.codes:
        return _Claim(token.token, token.token_type, "correct", "matched source value")
    if token.token_type == "number" and token.number is not None:
        note = _near_source_note(token.number, source_tokens.numbers)
        return _Claim(token.token, token.token_type, "wrong number", note)
    if token.token_type == "date":
        return _Claim(token.token, token.token_type, "wrong number", "date not found in source")
    return _Claim(
        token.token,
        token.token_type,
        "unsupported claim",
        "code not found in source",
    )


def _extract_causal_words(text: str) -> list[tuple[int, str]]:
    matches: list[tuple[int, str]] = []
    for term, pattern in _CAUSAL_PATTERNS:
        matches.extend((match.start(), term) for match in pattern.finditer(text))
    return sorted(matches)


def _states_level(text: str) -> bool:
    normalised_text = _normalise_digits(text)
    return bool(
        _LEVEL_EN_PATTERN.search(normalised_text)
        or _LEVEL_AR_PATTERN.search(normalised_text)
    )


def _token_claims(text: str, source_tokens: _SourceTokens) -> list[_Claim]:
    return [_judge_token(token, source_tokens) for token in _extract_text_tokens(text)]


def _causal_claims(text: str) -> list[_Claim]:
    return [
        _Claim(
            causal_word,
            "code",
            "unsupported claim",
            "causal wording: manual review",
        )
        for _, causal_word in _extract_causal_words(text)
    ]


def _missing_context_claim(
    text: str,
    source_tokens: _SourceTokens,
) -> _Claim | None:
    if not source_tokens.levels or _states_level(text):
        return None
    source_levels = ", ".join(str(level) for level in sorted(source_tokens.levels))
    return _Claim(
        "level",
        "code",
        "missing context",
        f"source contains level {source_levels} but text states no level",
    )


def _claim_row(file_id: str, kind: str, claim: _Claim) -> dict[str, Any]:
    return {
        "file_id": file_id,
        "kind": kind,
        "token": claim.token,
        "token_type": claim.token_type,
        "verdict": claim.verdict,
        "note": claim.note,
    }


def verify_text(
    text: str,
    source: dict[str, Any] | list[Any],
    *,
    file_id: str,
    kind: str = "paragraph",
) -> list[dict[str, Any]]:
    """Return one deterministic verdict row for each token in generated text."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(source, (dict, list)):
        raise TypeError("source must be a dict or list")

    source_tokens = _collect_source_tokens(source)
    claims = _token_claims(text, source_tokens)
    claims.extend(_causal_claims(text))
    missing_context = _missing_context_claim(text, source_tokens)
    if missing_context is not None:
        claims.append(missing_context)
    return [_claim_row(file_id, kind, claim) for claim in claims]


def append_log(
    rows: Iterable[Mapping[str, Any]],
    path: str | Path = DEFAULT_LOG_PATH,
    *,
    checked_on: str,
) -> None:
    """Append token-only verification rows to a CSV using a supplied date."""
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not log_path.exists() or log_path.stat().st_size == 0
    with log_path.open("a", encoding="utf-8", newline="") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=LOG_COLUMNS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        for row in rows:
            logged_row = {column: row.get(column, "") for column in LOG_COLUMNS[:-1]}
            logged_row["checked_on"] = checked_on
            writer.writerow(logged_row)


def summarize(rows: Iterable[Mapping[str, Any]]) -> dict[str, int | bool]:
    """Count verdicts and identify whether any row requires manual review."""
    counts: dict[str, int] = {verdict: 0 for verdict in VERDICTS}
    needs_review = False
    for row in rows:
        verdict = str(row.get("verdict", ""))
        counts[verdict] = counts.get(verdict, 0) + 1
        needs_review = needs_review or verdict != "correct"
    counts["needs_review"] = needs_review
    return counts
