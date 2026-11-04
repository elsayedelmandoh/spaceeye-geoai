
# from chatbot.app.generation.query_understanding import understand_query
# from chatbot.app.retrieval.structured import (
#     get_compound_profile,
#     get_kpi,
# )
# from chatbot.app.retrieval.vector_store import search_documents


# DOCUMENT_TYPES = {
#     "published_statements": "published_statement",
#     "rules": "rule_summary",
#     "complaints": "synthetic_complaint",
#     "inspection_visits": "synthetic_visit",
# }


# def _build_where(
#     compound: str | None,
#     document_type: str | None = None,
# ) -> dict | None:
#     """Build ChromaDB metadata filters."""

#     conditions = []

#     if compound:
#         conditions.append({"compound": compound})

#     if document_type:
#         conditions.append({"document_type": document_type})

#     if len(conditions) == 2:
#         return {"$and": conditions}

#     if len(conditions) == 1:
#         return conditions[0]

#     return None


# def retrieve_hybrid(
#     query: str,
#     n_results: int = 5,
#     last_compound: str | None = None,
# ) -> dict:
#     """
#     Understand the user's question with Gemini, then retrieve
#     relevant structured data and textual evidence from SpaceEye.

#     Gemini decides what the user is asking for.
#     Python controls and executes data retrieval.
#     """

#     if not query or not query.strip():
#         raise ValueError("Query cannot be empty.")

#     # 1. Understand the question using Gemini.
#     understanding = understand_query(
#         question=query,
#         last_compound=last_compound,
#     )

#     intent = understanding["intent"]
#     sub_intent = understanding["sub_intent"]
#     compound = understanding["compound"]
#     rewritten_query = understanding["rewritten_query"]

#     # 2. Stop if the user needs to clarify the project.
#     if understanding["needs_clarification"]:
#         return {
#             "query": query,
#             "rewritten_query": rewritten_query,
#             "intent": intent,
#             "sub_intent": sub_intent,
#             "compound": compound,
#             "needs_clarification": True,
#             "clarification_question": understanding[
#                 "clarification_question"
#             ],
#             "structured_data": {
#                 "compound_profile": None,
#                 "latest_kpi": None,
#             },
#             "evidence": [],
#             "evidence_count": 0,
#             "understanding_mode": understanding["understanding_mode"],
#         }

#     # 3. Determine which data sources are needed.
#     search_targets = set(understanding["search_targets"])

#     # Project status, delay, latest data, and priority questions
#     # benefit from both structured data and supporting evidence.
#     if intent in ("project_info", "inspection_priority"):
#         search_targets.add("structured_data")

#     if intent == "project_info" and sub_intent in (
#         "status_inquiry",
#         "delay_assessment",
#         "latest_data",
#         "performance_comparison",
#     ):
#         search_targets.add("text_evidence")

#     if intent == "inspection_priority":
#         search_targets.add("text_evidence")

#     # 4. Retrieve structured data from DuckDB.
#     structured_data = {
#         "compound_profile": None,
#         "latest_kpi": None,
#     }

#     if compound and "structured_data" in search_targets:
#         structured_data["compound_profile"] = (
#             get_compound_profile(compound)
#         )
#         structured_data["latest_kpi"] = get_kpi(compound)

#     # 5. Retrieve textual evidence from ChromaDB.
#     evidence = []

#     if "text_evidence" in search_targets:
#         document_type = DOCUMENT_TYPES.get(intent)

#         # Priority questions may need more than one evidence type.
#         if intent == "inspection_priority":
#             document_type = None

#         where = _build_where(
#             compound=compound,
#             document_type=document_type,
#         )

#         evidence = search_documents(
#             query=rewritten_query,
#             n_results=n_results,
#             where=where,
#         )

#     # 6. Return the complete retrieval result.
#     return {
#         "query": query,
#         "rewritten_query": rewritten_query,
#         "intent": intent,
#         "sub_intent": sub_intent,
#         "compound": compound,
#         "search_targets": sorted(search_targets),
#         "structured_data": structured_data,
#         "evidence": evidence,
#         "evidence_count": len(evidence),
#         "needs_clarification": False,
#         "clarification_question": "",
#         "understanding_mode": understanding["understanding_mode"],
#     }


from chatbot.app.generation.query_understanding import understand_query
from chatbot.app.retrieval.structured import (
    get_compound_profile,
    get_kpi,
)
from chatbot.app.retrieval.vector_store import search_documents


DOCUMENT_TYPES = {
    "published_statements": "published_statement",
    "rules": "rule_summary",
    "complaints": "synthetic_complaint",
    "inspection_visits": "synthetic_visit",
    "knowledge": "external_knowledge",
}


def _build_where(
    compound: str | None,
    document_type: str | None = None,
) -> dict | None:
    """Build ChromaDB metadata filters."""

    conditions = []

    if compound:
        conditions.append({"compound": compound})

    if document_type:
        conditions.append({"document_type": document_type})

    if len(conditions) == 2:
        return {"$and": conditions}

    if len(conditions) == 1:
        return conditions[0]

    return None


def _retrieve_project_data(compound: str) -> dict:
    """Retrieve the structured profile and latest KPI for one project."""

    return {
        "compound": compound,
        "compound_profile": get_compound_profile(compound),
        "latest_kpi": get_kpi(compound),
    }


def _retrieve_evidence(
    query: str,
    compounds: list[str],
    document_type: str | None,
    n_results: int,
) -> list[dict]:
    """
    Retrieve evidence separately for each requested project.

    When no project code is supplied, perform a general unfiltered search.
    """

    evidence = []

    # General search: no compound filter.
    if not compounds:
        where = _build_where(
            compound=None,
            document_type=document_type,
        )

        return search_documents(
            query=query,
            n_results=n_results,
            where=where,
        )

    # Project-specific search: one Chroma query per project.
    for compound in compounds:
        where = _build_where(
            compound=compound,
            document_type=document_type,
        )

        matches = search_documents(
            query=query,
            n_results=n_results,
            where=where,
        )

        for match in matches:
            item = dict(match)
            metadata = dict(item.get("metadata") or {})

            item["compound"] = compound
            item["metadata"] = metadata

            # Keep the project code explicit even if the original metadata
            # does not contain it.
            item["metadata"]["compound"] = compound

            evidence.append(item)

    return evidence


def retrieve_hybrid(
    query: str,
    n_results: int = 5,
    last_compound: str | None = None,
) -> dict:
    """
    Understand the user's question, then retrieve structured data
    and textual evidence from DuckDB and ChromaDB.

    Supports:
    - One project
    - Multiple projects
    - General questions and hypothetical scenarios
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    # 1. Understand the question.
    understanding = understand_query(
        question=query,
        last_compound=last_compound,
    )

    intent = understanding["intent"]
    sub_intent = understanding["sub_intent"]
    compound = understanding["compound"]
    compounds = understanding.get("compounds") or (
        [compound] if compound else []
    )
    rewritten_query = understanding["rewritten_query"]

    # Remove duplicates and validate codes defensively.
    compounds = list(dict.fromkeys(
        code.upper()
        for code in compounds
        if isinstance(code, str)
        and len(code) == 3
        and code[0].upper() == "C"
        and code[1:].isdigit()
    ))

    # Keep the legacy singular field for existing code.
    compound = compounds[0] if len(compounds) == 1 else None

    # 2. Return early only when clarification is genuinely required.
    if understanding["needs_clarification"]:
        return {
            "query": query,
            "rewritten_query": rewritten_query,
            "intent": intent,
            "sub_intent": sub_intent,
            "compound": compound,
            "compounds": compounds,
            "needs_clarification": True,
            "clarification_question": understanding[
                "clarification_question"
            ],
            "search_targets": [],
            "structured_data": {
                "compound_profile": None,
                "latest_kpi": None,
                "projects": [],
            },
            "evidence": [],
            "evidence_count": 0,
            "understanding_mode": understanding["understanding_mode"],
        }

    # 3. Determine the required sources.
    search_targets = set(
        understanding.get("search_targets", [])
    )

    if intent in ("project_info", "inspection_priority"):
        search_targets.add("structured_data")

    if intent in ("project_info", "inspection_priority", "knowledge"):
        search_targets.add("text_evidence")

    # 4. Retrieve structured data.
    projects = []

    if "structured_data" in search_targets:
        for code in compounds:
            projects.append(
                _retrieve_project_data(code)
            )

    # Preserve the old response structure for existing single-project code.
    if len(projects) == 1:
        structured_data = {
            "compound_profile": projects[0]["compound_profile"],
            "latest_kpi": projects[0]["latest_kpi"],
            "projects": projects,
        }
    else:
        structured_data = {
            "compound_profile": None,
            "latest_kpi": None,
            "projects": projects,
        }

    # 5. Retrieve textual evidence.
    evidence = []

    if "text_evidence" in search_targets:
        document_type = DOCUMENT_TYPES.get(intent)

        # Priority analysis may require multiple evidence categories.
        if intent == "inspection_priority":
            document_type = None

        # Knowledge chunks carry no compound code, so never filter them by one.
        evidence = _retrieve_evidence(
            query=rewritten_query,
            compounds=[] if intent == "knowledge" else compounds,
            document_type=document_type,
            n_results=n_results,
        )

    # 6. Return the retrieval result.
    return {
        "query": query,
        "rewritten_query": rewritten_query,
        "intent": intent,
        "sub_intent": sub_intent,
        "compound": compound,
        "compounds": compounds,
        "search_targets": sorted(search_targets),
        "structured_data": structured_data,
        "evidence": evidence,
        "evidence_count": len(evidence),
        "needs_clarification": False,
        "clarification_question": "",
        "understanding_mode": understanding["understanding_mode"],
    }
