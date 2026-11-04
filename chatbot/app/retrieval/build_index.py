"""Rebuild the vector store: python -m chatbot.app.retrieval.build_index [--knowledge-only].

Upserts by chunk id, so it is safe to re-run and never deletes an existing store.
"""

import argparse

from chatbot.app.retrieval.ingestion import build_documents
from chatbot.app.retrieval.knowledge import build_knowledge_chunks
from chatbot.app.retrieval.vector_store import add_documents, get_collection_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--knowledge-only",
        action="store_true",
        help="index only chatbot/knowledge/external/*.md (no ready-data contexts needed)",
    )
    args = parser.parse_args()

    chunks = build_knowledge_chunks() if args.knowledge_only else build_documents()
    add_documents(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["document"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
    )
    print(f"Upserted {len(chunks)} chunks; collection now holds {get_collection_count()}.")


if __name__ == "__main__":
    main()
