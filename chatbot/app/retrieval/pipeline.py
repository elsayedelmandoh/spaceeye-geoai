from chatbot.app.retrieval.router import route_query
from chatbot.app.retrieval.vector_store import search_documents


def retrieve_context(
    query: str,
    n_results: int = 5,
    last_compound: str | None = None,
) -> dict:
    """
    Route the question and retrieve relevant evidence.
    Use the previous compound for project-related follow-up questions.
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    # Route directly using the conversation context.
    routing = route_query(
        query,
        last_compound=last_compound,
    )

    intent = routing["intent"]

    # These intents do not require vector retrieval.
    if intent in ("out_of_scope", "project_overview", "greeting"):
        results = []
    else:
        results = search_documents(
            query=query,
            n_results=n_results,
            where=routing["where"],
        )

    return {
        "query": query,
        "intent": intent,
        "document_type": routing["document_type"],
        "compound": routing["compound"],
        "results": results,
        "results_count": len(results),
    }