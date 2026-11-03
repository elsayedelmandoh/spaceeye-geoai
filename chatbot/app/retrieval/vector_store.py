import chromadb

from chatbot.app.core.config import CHATBOT_DIR
from chatbot.app.retrieval.embeddings import (
    embed_documents,
    embed_query,
)


VECTOR_DB_PATH = CHATBOT_DIR / "vector_db"
COLLECTION_NAME = "spaceeye_evidence"


def get_vector_collection():
    client = chromadb.PersistentClient(
        path=str(VECTOR_DB_PATH)
    )

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def add_documents(
    ids: list[str],
    documents: list[str],
    metadatas: list[dict],
) -> None:
    if not (len(ids) == len(documents) == len(metadatas)):
        raise ValueError("IDs, documents and metadata lengths must match.")

    if not ids:
        return

    collection = get_vector_collection()

    embeddings = embed_documents(documents)

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )


def search_documents(
    query: str,
    n_results: int = 5,
    where: dict | None = None,
) -> list[dict]:
    collection = get_vector_collection()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_embeddings=[embed_query(query)],
        n_results=min(n_results, collection.count()),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    matches = []

    for i in range(len(results["ids"][0])):
        matches.append({
            "id": results["ids"][0][i],
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })

    return matches


def get_collection_count() -> int:
    return get_vector_collection().count()