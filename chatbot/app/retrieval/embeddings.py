from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "intfloat/multilingual-e5-small"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_documents(texts: list[str]) -> list[list[float]]:
    prepared_texts = [f"passage: {text}" for text in texts]

    embeddings = get_embedding_model().encode(
        prepared_texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    embedding = get_embedding_model().encode(
        f"query: {query}",
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    return embedding.tolist()