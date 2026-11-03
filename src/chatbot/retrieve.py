"""Retrieve document passages with BM25 word ranking and character tie-breaks."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.chatbot.corpus import Passage, load_corpus
from src.chatbot.lexical import Bm25Ranker

_CHARACTER_VECTORIZER_OPTIONS = {
    "analyzer": "char_wb",
    "lowercase": True,
    "ngram_range": (3, 5),
    "sublinear_tf": True,
}


@dataclass(frozen=True)
class RetrievedPassage:
    """A passage paired with its BM25 relevance score and support flag."""

    passage: Passage
    score: float
    supported: bool = True


def _build_character_vectorizer() -> TfidfVectorizer:
    """Build the character analyzer used only to break equal word scores."""

    return TfidfVectorizer(**_CHARACTER_VECTORIZER_OPTIONS)


def _ranked_indices(
    word_scores: Sequence[float],
    character_scores: Sequence[float],
    passages: tuple[Passage, ...],
) -> list[int]:
    """Sort by word evidence, then character similarity and stable metadata."""

    return sorted(
        range(len(word_scores)),
        key=lambda index: (
            -word_scores[index],
            -character_scores[index],
            passages[index].path,
            passages[index].heading,
        ),
    )


class TfidfRetriever:
    """Rank passages using corpus-statistical BM25 word evidence.

    The historical class name is retained for API compatibility. Character
    n-grams are deliberately secondary and only distinguish equal word scores.
    """

    def __init__(self, passages: list[Passage] | tuple[Passage, ...]) -> None:
        self.passages = tuple(passages)
        self._character_vectorizer = _build_character_vectorizer()
        self._character_matrix = None
        self._ranker = Bm25Ranker(self.passages)
        if self.passages:
            passage_texts = [passage.text for passage in self.passages]
            self._character_matrix = self._character_vectorizer.fit_transform(
                passage_texts
            )

    def search(self, question: str, top_k: int = 3) -> list[RetrievedPassage]:
        """Return up to ``top_k`` passages ordered by descending relevance."""

        if top_k < 1:
            raise ValueError("top_k must be at least one")
        query = question.strip()
        if not query or not self.passages:
            return []
        return self._ranked_passages(query)[:top_k]

    def _ranked_passages(self, question: str) -> list[RetrievedPassage]:
        """Return every passage in BM25 order with character tie-breaks."""

        scored = self._ranker.score_all(question)
        word_scores = [score for score, _ in scored]
        support_flags = [supported for _, supported in scored]
        character_scores = self._character_scores(question)
        ranked_indices = _ranked_indices(
            word_scores,
            character_scores,
            self.passages,
        )
        return [
            RetrievedPassage(
                passage=self.passages[index],
                score=word_scores[index],
                supported=support_flags[index],
            )
            for index in ranked_indices
        ]

    def _character_scores(self, question: str) -> list[float]:
        """Return secondary character similarities for word-score ties."""

        if self._character_matrix is None:
            return [0.0] * len(self.passages)
        similarities = cosine_similarity(
            self._character_vectorizer.transform([question]),
            self._character_matrix,
        )[0]
        return [float(similarity) for similarity in similarities]


@lru_cache(maxsize=1)
def get_default_retriever() -> TfidfRetriever:
    """Build the repository corpus index once per process."""

    return TfidfRetriever(load_corpus())
