"""Corpus-statistical word ranking and coverage checks for chatbot retrieval."""

from __future__ import annotations

import itertools
import math
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from src.chatbot.corpus import Passage

_TOKEN_PATTERN = re.compile(r"(?u)\b\w+\b")
_ARABIC_PATTERN = re.compile(r"[\u0600-\u06ff]")
_ARABIC_PREFIXES = ("وال", "فال", "بال", "كال", "لل")
_ENGLISH_STOP_WORDS = frozenset(ENGLISH_STOP_WORDS) | {
    "meaning",
    "mean",
    "means",
    "please",
    "tell",
}
_ARABIC_STOP_WORDS = frozenset(
    {
        "أو",
        "إلى",
        "التي",
        "الذي",
        "أثناء",
        "إن",
        "أن",
        "ثم",
        "كل",
        "كيف",
        "لماذا",
        "ما",
        "ماذا",
        "من",
        "هل",
        "و",
        "في",
        "عن",
        "على",
        "هذه",
        "هذا",
        "ذلك",
        "بين",
        "بعد",
        "قبل",
        "عند",
        "وقت",
        "أي",
        "كما",
        "لدى",
        "عبر",
        "هي",
    }
)

_BODY_WEIGHT = 1
_TITLE_WEIGHT = 3
_HEADING_WEIGHT = 4
_BM25_K1 = 1.5
_BM25_B = 0.75
_IDENTIFIER_BOOST = 3.0
_COMMON_SOURCE_RATIO = 0.35
_RARE_SOURCE_RATIO = 0.25
_MIN_COVERAGE = 0.75
_MIN_IDENTITY_COVERAGE = 0.40
_BIGRAM_PREFIX = "bigram:"


@dataclass(frozen=True)
class _QueryToken:
    """One normalized query term and its source-text shape."""

    term: str
    kind: str


@dataclass(frozen=True)
class _PassageFields:
    """Weighted retrieval fields and identity terms for one passage."""

    weighted_terms: tuple[str, ...]
    lexical_terms: frozenset[str]
    identity_terms: frozenset[str]


def _strip_arabic_prefix(token: str) -> str:
    """Remove common Arabic clitics without corrupting standalone words."""

    if token.startswith("ال") and len(token) > 2:
        return token[2:]
    for prefix in _ARABIC_PREFIXES:
        if token.startswith(prefix) and len(token) > len(prefix) + 1:
            return token[len(prefix) :]
    if token[0] in "وفكل" and len(token) >= 5:
        return token[1:]
    return token


def _normalize_token(token: str) -> str:
    """Normalize case and Arabic clitics while preserving identifier text."""

    normalized = token.casefold()
    if _ARABIC_PATTERN.search(normalized):
        normalized = _strip_arabic_prefix(normalized)
    return normalized


def _token_kind(token: str) -> str:
    """Classify a token without naming any domain-specific concept."""

    has_digit = any(character.isdigit() for character in token)
    has_letter = any(character.isalpha() for character in token)
    if has_digit and has_letter:
        return "mixed_identifier"
    if has_digit:
        return "numeric"
    if len(token) >= 2 and token.isalpha() and token.isupper():
        return "acronym"
    return "word"


def _raw_tokens(text: str) -> list[str]:
    """Return word-like raw tokens from text."""

    return _TOKEN_PATTERN.findall(text)


def _tokens(text: str) -> list[str]:
    """Return normalized word tokens from text."""

    return [_normalize_token(token) for token in _raw_tokens(text)]


def _content_tokens(text: str) -> list[str]:
    """Return normalized tokens that are meaningful for matching."""

    return [token for token in _tokens(text) if not _is_stop_word(token)]


def _bigrams(tokens: list[str]) -> list[str]:
    """Return adjacent word-pair tokens from a token sequence."""

    return [
        f"{_BIGRAM_PREFIX}{first}_{second}"
        for first, second in itertools.pairwise(tokens)
    ]


def _is_stop_word(token: str) -> bool:
    """Return whether a normalized token carries no question-specific meaning."""

    return token in _ENGLISH_STOP_WORDS or token in _ARABIC_STOP_WORDS


def _repeat(tokens: Iterable[str], weight: int) -> list[str]:
    """Repeat field tokens to model field importance in one BM25 document."""

    repeated: list[str] = []
    for token in tokens:
        repeated.extend([token] * weight)
    return repeated


def _weighted_field_terms(text: str, weight: int) -> list[str]:
    """Return weighted unigrams and word pairs from one passage field."""

    content_tokens = _content_tokens(text)
    return _repeat(_tokens(text), weight) + _repeat(
        _bigrams(content_tokens), weight
    )


class Bm25Ranker:
    """Rank passages with corpus-derived BM25 evidence and query coverage."""

    def __init__(self, passages: tuple[Passage, ...]) -> None:
        self._passages = passages
        self._fields = tuple(self._build_fields(passage) for passage in passages)
        self._passage_df = self._build_passage_df(self._fields)
        self._source_terms = self._build_source_terms(self._fields, passages)
        self._source_df = Counter(
            term for terms in self._source_terms.values() for term in terms
        )
        self._source_idf = self._build_idf(self._source_df, len(self._source_terms))
        self._default_idf = max(self._source_idf.values(), default=1.0)
        self._average_length = self._build_average_length(self._fields)
        self._term_kinds = self._build_term_kinds(passages)
        self._rare_numeric_limit = max(
            2,
            math.floor(len(self._source_terms) * _RARE_SOURCE_RATIO),
        )

    @staticmethod
    def _build_fields(passage: Passage) -> _PassageFields:
        """Build weighted body, title, and heading fields for one passage."""

        body_tokens = _tokens(passage.text)
        title_tokens = _tokens(passage.title or "")
        heading_tokens = _tokens(passage.heading)
        weighted_terms = tuple(
            _weighted_field_terms(passage.text, _BODY_WEIGHT)
            + _weighted_field_terms(passage.title or "", _TITLE_WEIGHT)
            + _weighted_field_terms(passage.heading, _HEADING_WEIGHT)
        )
        return _PassageFields(
            weighted_terms=weighted_terms,
            lexical_terms=frozenset(body_tokens + title_tokens + heading_tokens),
            identity_terms=frozenset(
                title_tokens + heading_tokens + _tokens(passage.path)
            ),
        )

    @staticmethod
    def _build_passage_df(
        fields: tuple[_PassageFields, ...],
    ) -> Counter[str]:
        """Count passages containing each lexical term."""

        frequency: Counter[str] = Counter()
        for passage_fields in fields:
            frequency.update(set(passage_fields.weighted_terms))
        return frequency

    @staticmethod
    def _build_source_terms(
        fields: tuple[_PassageFields, ...],
        passages: tuple[Passage, ...],
    ) -> dict[str, frozenset[str]]:
        """Collect lexical terms for each source document."""

        source_terms: dict[str, set[str]] = {}
        for passage_fields, passage in zip(fields, passages, strict=True):
            source_terms.setdefault(passage.path, set()).update(
                passage_fields.lexical_terms
            )
        return {
            path: frozenset(terms) for path, terms in source_terms.items()
        }

    @staticmethod
    def _build_idf(frequency: Counter[str], document_count: int) -> dict[str, float]:
        """Build smoothed inverse-document-frequency values."""

        return {
            term: math.log(
                1 + (document_count - count + 0.5) / (count + 0.5)
            )
            for term, count in frequency.items()
        }

    @staticmethod
    def _build_average_length(fields: tuple[_PassageFields, ...]) -> float:
        """Return the mean weighted passage length."""

        if not fields:
            return 1.0
        return sum(len(passage_fields.weighted_terms) for passage_fields in fields) / len(
            fields
        )

    @staticmethod
    def _build_term_kinds(passages: tuple[Passage, ...]) -> dict[str, frozenset[str]]:
        """Collect observed token shapes across the corpus."""

        kinds: dict[str, set[str]] = {}
        for passage in passages:
            texts = (passage.text, passage.title or "", passage.heading)
            for text in texts:
                for raw_token in _raw_tokens(text):
                    term = _normalize_token(raw_token)
                    kinds.setdefault(term, set()).add(_token_kind(raw_token))
        return {term: frozenset(term_kinds) for term, term_kinds in kinds.items()}

    def _query_tokens(self, question: str) -> tuple[_QueryToken, ...]:
        """Extract unique meaningful query terms."""

        tokens: dict[str, _QueryToken] = {}
        for raw_token in _raw_tokens(question):
            term = _normalize_token(raw_token)
            if not term or _is_stop_word(term):
                continue
            query_token = _QueryToken(term=term, kind=_token_kind(raw_token))
            existing = tokens.get(term)
            if existing is None or query_token.kind != "word":
                tokens[term] = query_token
        return tuple(tokens.values())

    def _scoring_tokens(self, question: str) -> tuple[_QueryToken, ...]:
        """Return unigrams and adjacent word pairs for BM25 matching."""

        unigrams = self._query_tokens(question)
        query_bigrams = _bigrams(_content_tokens(question))
        return unigrams + tuple(
            _QueryToken(term=term, kind="word") for term in query_bigrams
        )

    def _is_identifier(self, token: _QueryToken) -> bool:
        """Return whether a term is an exact numeric or acronym identifier."""

        corpus_kinds = self._term_kinds.get(token.term, frozenset())
        return (
            token.kind in {"numeric", "mixed_identifier", "acronym"}
            or bool(corpus_kinds & {"numeric", "mixed_identifier", "acronym"})
        )

    def _is_rare_numeric(self, token: _QueryToken) -> bool:
        """Return whether a numeric identifier is uncommon across sources."""

        return (
            token.kind == "numeric"
            and self._source_df.get(token.term, 0) <= self._rare_numeric_limit
        )

    def _is_strong_anchor(self, token: _QueryToken) -> bool:
        """Return whether a term is a strong corpus-independent identifier."""

        corpus_kinds = self._term_kinds.get(token.term, frozenset())
        if "mixed_identifier" in corpus_kinds or token.kind == "mixed_identifier":
            return True
        if "acronym" in corpus_kinds or token.kind == "acronym":
            return True
        return self._is_rare_numeric(token)

    def _passage_idf(self, term: str) -> float:
        """Return the passage-level IDF for one term."""

        document_frequency = self._passage_df.get(term, 0)
        passage_count = len(self._fields)
        return math.log(
            1
            + (passage_count - document_frequency + 0.5)
            / (document_frequency + 0.5)
        )

    def _term_contribution(
        self,
        token: _QueryToken,
        frequency: int,
        passage_length: int,
    ) -> float:
        """Return one term's BM25 contribution to a passage score."""

        length_normalization = (
            1 - _BM25_B + _BM25_B * passage_length / self._average_length
        )
        contribution = (
            self._passage_idf(token.term)
            * frequency
            * (_BM25_K1 + 1)
            / (frequency + _BM25_K1 * length_normalization)
        )
        if self._is_identifier(token):
            contribution *= _IDENTIFIER_BOOST
        return contribution

    def _passage_score(
        self,
        tokens: tuple[_QueryToken, ...],
        passage_fields: _PassageFields,
    ) -> float:
        """Compute the word-level BM25 score for one passage."""

        frequencies = Counter(passage_fields.weighted_terms)
        passage_length = len(passage_fields.weighted_terms)
        return sum(
            self._term_contribution(
                token,
                frequencies.get(token.term, 0),
                passage_length,
            )
            for token in tokens
            if token.term in frequencies
        )

    def _is_common_source_term(self, token: _QueryToken) -> bool:
        """Return whether a term occurs in too many source documents."""

        source_count = len(self._source_terms)
        if not source_count:
            return False
        source_frequency = self._source_df.get(token.term, 0)
        return source_frequency / source_count > _COMMON_SOURCE_RATIO

    def _counts_for_coverage(self, token: _QueryToken) -> bool:
        """Return whether a query term contributes to coverage."""

        return not (
            self._is_common_source_term(token)
            and not self._is_strong_anchor(token)
        )

    def _coverage_weight(self, token: _QueryToken) -> float:
        """Return the source-level IDF weight for one query term."""

        return self._source_idf.get(token.term, self._default_idf)

    def _query_coverage(
        self,
        tokens: tuple[_QueryToken, ...],
        passage_fields: _PassageFields,
    ) -> float:
        """Return IDF-weighted coverage of meaningful query terms."""

        coverage_terms = [
            (token, self._coverage_weight(token))
            for token in tokens
            if self._counts_for_coverage(token)
        ]
        total_weight = sum(weight for _, weight in coverage_terms)
        matched_weight = sum(
            weight
            for token, weight in coverage_terms
            if token.term in passage_fields.lexical_terms
        )
        return matched_weight / total_weight if total_weight else 0.0

    def _has_identity_anchor(
        self,
        tokens: tuple[_QueryToken, ...],
        passage_fields: _PassageFields,
    ) -> bool:
        """Return whether a distinctive query term identifies the source."""

        return any(
            not self._is_common_source_term(token)
            and token.term in passage_fields.identity_terms
            for token in tokens
        )

    def _has_strong_anchor(
        self,
        tokens: tuple[_QueryToken, ...],
        passage_fields: _PassageFields,
    ) -> bool:
        """Return whether an exact identifier identifies the passage's source."""

        return any(
            self._is_strong_anchor(token)
            and token.term in passage_fields.identity_terms
            for token in tokens
        )

    def _is_supported(
        self,
        tokens: tuple[_QueryToken, ...],
        passage_fields: _PassageFields,
    ) -> bool:
        """Return whether lexical evidence covers enough of the question."""

        coverage = self._query_coverage(tokens, passage_fields)
        if coverage >= _MIN_COVERAGE:
            return True
        if self._has_strong_anchor(tokens, passage_fields):
            return True
        return (
            self._has_identity_anchor(tokens, passage_fields)
            and coverage >= _MIN_IDENTITY_COVERAGE
        )

    def score_all(self, question: str) -> list[tuple[float, bool]]:
        """Return BM25 scores and lexical-support flags for every passage."""

        query_tokens = self._query_tokens(question)
        scoring_tokens = self._scoring_tokens(question)
        return [
            (
                self._passage_score(scoring_tokens, passage_fields),
                self._is_supported(query_tokens, passage_fields),
            )
            for passage_fields in self._fields
        ]
