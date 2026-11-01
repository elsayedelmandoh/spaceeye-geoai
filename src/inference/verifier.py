"""Stricter replacement for verify.py with normalised token matching and token-only logs."""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
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
    "لأن",
    "لأنه",
    "لأنها",
    "جراء",
    "أدى إلى",
    "أدت إلى",
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
_LEVEL_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "الأولى": 1,
    "الأول": 1,
    "الثانية": 2,
    "الثاني": 2,
    "الثالثة": 3,
    "الثالث": 3,
    "الرابعة": 4,
    "الرابع": 4,
}
_LEVEL_VALUE = (
    r"(?P<level>[1-4](?!\.?\d)|(?:one|two|three|four)\b"
    r"|(?:الأولى|الأول|الثانية|الثاني|الثالثة|الثالث|الرابعة|الرابع)(?!\w))"
)
_LEVEL_PATTERNS = (
    re.compile(rf"\b(?:priority\s+)?level\b\s*(?:is|=|:)?\s*{_LEVEL_VALUE}", re.IGNORECASE),
    re.compile(rf"مستوى[^0-9]{{0,40}}?{_LEVEL_VALUE}"),
)
_NUM = r"\d+(?:\.\d+)?"
_FIELD_GAP = r"[^\d\n.؛;]{0,25}?"
_UNIT_NUM = rf"(?<![\w.,])(?P<num>{_NUM})(?P<gap>\s*\)?\s*)"
_LABEL_PATTERN = re.compile(
    rf"(?<![A-Za-z0-9_])(?P<label>K[2356])(?![A-Za-z0-9_])(?P<gap>{_FIELD_GAP})(?P<num>{_NUM})"
)
_ACTIVITY_PATTERN = re.compile(
    rf"(?:درجة\s+النشاط|مؤشر\s+النشاط|activity(?:\s+score)?)(?P<gap>{_FIELD_GAP})(?P<num>{_NUM})",
    re.IGNORECASE,
)
_QUARTERS_PATTERN = re.compile(rf"{_UNIT_NUM}(?:quarters?|أرباع|ارباع|ربع)", re.IGNORECASE)
_MONTHS_PATTERN = re.compile(rf"{_UNIT_NUM}(?:months?|أشهر|اشهر|شهر)", re.IGNORECASE)
# Source keys holding each KPI; contexts carry both the short and the long alias.
_FIELD_KEYS = {
    "K2": ("K2", "K2_stoppage_quarters"),
    "K3": ("K3", "K3_delay_months"),
    "K5": ("K5_months", "K5_fine_eligible_months"),
    "K6": ("K6", "K6_unstarted_months"),
    "activity": ("A", "activity_prob"),
}
_FORBIDDEN_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(?<!\w)distressed(?!\w)",
        r"risk level",
        r"high-risk",
        r"completion\s*%",
        r"(?<!\w)(?:ال)?متعثر\w*",
        r"نسبة\s+(?:ال)?[إا]نجاز",
        # "may be complete" is the data's own hedge; a bare claim of completion is not.
        r"(?<!\w)(?<!قد يكون )(?<!قد تكون )(?:ال)?مكتمل[ةًا]*(?!\w)",
    )
)
# A name is a quoted word, a Latin proper noun, or a definite Arabic noun ("ال...") after "compound".
# Adverbs and pronoun forms that follow it (e.g. "تلقائياً", "نفسه") are ordinary text, not names.
_NAMED_COMPOUND_PATTERN = re.compile(
    r"(?<!\w)(?:ال)?(?:مركب|كمبوند)\s+(?P<name>[«\"'][^»\"']+[»\"']|[A-Z][A-Za-z]+|ال[^\s،.؛:()]+)")
_COMPOUND_QUALIFIERS = frozenset(
    {"الذي", "التابع", "الحالي", "المذكور", "السكني", "نفسه", "المعني", "المستهدف"}
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
    start: int = -1


@dataclass(frozen=True)
class _Claim:
    token: str
    token_type: str
    verdict: str
    note: str


@dataclass(frozen=True)
class _Binding:
    """A stated value that must equal one named source field."""

    label: str
    token: str
    stated: Decimal
    allowed: frozenset[Decimal]
    is_word: bool = False


@dataclass
class _SourceTokens:
    numbers: set[Decimal] = field(default_factory=set)
    dates: set[str] = field(default_factory=set)
    codes: set[str] = field(default_factory=set)
    levels: set[int] = field(default_factory=set)
    record: Mapping[str, Any] | None = None


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
            extracted.append(_TextToken(token, "date", start=match.start()))
        elif match.lastgroup == "code":
            extracted.append(_TextToken(raw_token.upper(), "code", start=match.start()))
        else:
            number = Decimal(raw_token.replace(",", ""))
            digit_start = match.start() + (raw_token[0] in "+-")
            extracted.append(_TextToken(_format_decimal(number), "number", number, digit_start))
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


def _kpi_record(source: Any) -> Mapping[str, Any] | None:
    """Return the current-quarter KPI mapping, never the earlier-quarter series."""
    kpis = source.get("kpis") if isinstance(source, Mapping) else None
    return kpis if isinstance(kpis, Mapping) else None


def _collect_source_tokens(source: dict[str, Any] | list[Any]) -> _SourceTokens:
    source_tokens = _SourceTokens(record=_kpi_record(source))
    _walk_source(source, source_tokens)
    return source_tokens


def _field_values(record: Mapping[str, Any], label: str) -> frozenset[Decimal] | None:
    """Return the numeric values of one KPI, or None when the record lacks the field."""
    keys = [key for key in _FIELD_KEYS[label] if key in record]
    if not keys:
        return None
    values = {
        number
        for key in keys
        if isinstance(record[key], (int, float, Decimal)) and not isinstance(record[key], bool)
        if (number := _source_decimal(record[key])) is not None
    }
    return frozenset(values)


def _union_values(record: Mapping[str, Any], labels: tuple[str, ...]) -> frozenset[Decimal] | None:
    found = [values for label in labels if (values := _field_values(record, label)) is not None]
    return frozenset().union(*found) if found else None


def _matches_field(binding: _Binding) -> bool:
    """Compare at the precision the text states, so 0.35 matches an activity of 0.3515."""
    exponent = min(binding.stated.as_tuple().exponent, 0)
    step = Decimal(1).scaleb(exponent)
    return any(
        value.quantize(step, rounding=ROUND_HALF_UP) == binding.stated
        for value in binding.allowed
    )


def _level_value(stated: str) -> tuple[int, bool]:
    """Return the level number and whether the text spelled it as a word."""
    word = stated.casefold() if stated.isascii() else stated
    if word in _LEVEL_WORDS:
        return _LEVEL_WORDS[word], True
    return int(stated), False


def _bindings(text: str, record: Mapping[str, Any] | None) -> dict[int, _Binding]:
    """Map the start of each number tied to a level, KPI label or unit to its field.

    The nearest cue wins, so "K2 and activity 0.5" ties 0.5 to activity.
    """
    if record is None:
        return {}
    level = _normalise_level(record.get("level"))
    allowed_for = {
        "K2": _field_values(record, "K2"),
        "K3": _field_values(record, "K3"),
        "K5": _field_values(record, "K5"),
        "K6": _field_values(record, "K6"),
        "activity": _field_values(record, "activity"),
        "level": None if level is None else frozenset({Decimal(level)}),
        "quarters": _field_values(record, "K2"),
        "months": _union_values(record, ("K3", "K5", "K6")),
    }
    candidates: list[tuple[int, int, str, str, Decimal, bool]] = []
    for pattern, group_label in (
        (_LABEL_PATTERN, None),
        (_ACTIVITY_PATTERN, "activity"),
        (_QUARTERS_PATTERN, "quarters"),
        (_MONTHS_PATTERN, "months"),
    ):
        for match in pattern.finditer(text):
            label = group_label or match.group("label")
            gap = len(match.group("gap"))
            candidates.append(
                (match.start("num"), gap, label, match.group("num"), Decimal(match.group("num")), False)
            )
    for pattern in _LEVEL_PATTERNS:
        for match in pattern.finditer(text):
            value, is_word = _level_value(match.group("level"))
            candidates.append(
                (match.start("level"), 0, "level", match.group("level"), Decimal(value), is_word)
            )
    best: dict[int, tuple[int, _Binding]] = {}
    for start, distance, label, token, stated, is_word in candidates:
        allowed = allowed_for[label]
        if allowed is None or (start in best and best[start][0] <= distance):
            continue
        best[start] = (distance, _Binding(label, token, stated, allowed, is_word))
    return {start: binding for start, (_, binding) in best.items()}


def _mismatch_note(binding: _Binding) -> str:
    if not binding.allowed:
        return f"{binding.label} is not available in source but text states {binding.token}"
    source_values = ", ".join(_format_decimal(value) for value in sorted(binding.allowed))
    return f"text states {binding.label} {binding.token}; source {binding.label} is {source_values}"


def stated_value_mismatches(text: str, record: Mapping[str, Any] | None) -> list[tuple[str, str]]:
    """Return (token, note) for each stated level or KPI value that differs from its field."""
    bindings = _bindings(_normalise_digits(text), record)
    return [
        (binding.token, _mismatch_note(binding))
        for binding in bindings.values()
        if not _matches_field(binding)
    ]


def forbidden_terms(text: str) -> list[str]:
    """Return forbidden wording found in English or Arabic text."""
    return [match.group(0) for pattern in _FORBIDDEN_PATTERNS for match in pattern.finditer(text)]


def named_compounds(text: str) -> list[str]:
    """Return names written after the word compound; only C../D.. codes may identify one."""
    return [
        match.group("name")
        for match in _NAMED_COMPOUND_PATTERN.finditer(text)
        if match.group("name") not in _COMPOUND_QUALIFIERS
        and not re.fullmatch(_CODE_PATTERN, match.group("name"))
    ]


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
    binding: _Binding | None = None,
) -> _Claim:
    if binding is not None:
        if _matches_field(binding):
            return _Claim(token.token, token.token_type, "correct", "matched source value")
        return _Claim(token.token, token.token_type, "wrong number", _mismatch_note(binding))
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
    return any(pattern.search(normalised_text) for pattern in _LEVEL_PATTERNS)


def _token_claims(text: str, source_tokens: _SourceTokens) -> list[_Claim]:
    bindings = _bindings(_normalise_digits(text), source_tokens.record)
    return [
        _judge_token(
            token,
            source_tokens,
            bindings.get(token.start) if token.token_type == "number" else None,
        )
        for token in _extract_text_tokens(text)
    ]


def _level_word_claims(text: str, source_tokens: _SourceTokens) -> list[_Claim]:
    bindings = _bindings(_normalise_digits(text), source_tokens.record)
    return [
        _Claim(binding.token, "code", "wrong number", _mismatch_note(binding))
        for binding in bindings.values()
        if binding.is_word and not _matches_field(binding)
    ]


def _wording_claims(text: str) -> list[_Claim]:
    claims = [
        _Claim(term, "code", "unsupported claim", "forbidden wording")
        for term in forbidden_terms(text)
    ]
    claims.extend(
        _Claim(name, "code", "unsupported claim", "compound named without a code")
        for name in named_compounds(text)
    )
    return claims


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
    claims.extend(_level_word_claims(text, source_tokens))
    claims.extend(_wording_claims(text))
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
