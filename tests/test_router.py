import pytest

from chatbot.app.retrieval.router import route_query


@pytest.mark.parametrize(
    "question",
    [
        "طب عايزة أعرف سبب إنه في المستوى الرابع",
        "ايه سبب انه ضمن المستوي الرابع",
        "ليه المشروع متصنف مستوى رابع",
        "ليه C04 في المستوى الرابع",
    ],
)
def test_level_questions_route_to_inspection_priority_with_previous_compound(question):
    result = route_query(question, last_compound="C04")

    assert result["intent"] == "inspection_priority"
    assert result["compound"] == "C04"


@pytest.mark.parametrize(
    "question",
    ["ما هو قانون 151 لحماية البيانات الشخصية؟", "What is Dynamic World?"],
)
def test_source_document_questions_route_to_knowledge_without_compound(question):
    result = route_query(question, last_compound="C04")

    assert result["intent"] == "knowledge"
    assert result["where"] == {"document_type": "external_knowledge"}
