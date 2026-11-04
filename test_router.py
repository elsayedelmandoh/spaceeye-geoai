from chatbot.app.retrieval.router import route_query

tests = [
    "طب عايزة أعرف سبب إنه في المستوى الرابع",
    "ايه سبب انه ضمن المستوي الرابع",
    "ليه المشروع متصنف مستوى رابع",
    "ليه C04 في المستوى الرابع",
]

for question in tests:
    result = route_query(question, last_compound="C04")
    print("Intent:", result["intent"])
    print("Compound:", result["compound"])
    print("-" * 30)