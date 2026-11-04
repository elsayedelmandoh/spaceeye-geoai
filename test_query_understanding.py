import json
from chatbot.app.generation.query_understanding import understand_query

questions = [
    "هل المشروع متأخر عن الجدول الزمني؟",
    "إيه المؤشرات اللي اعتمدت عليها في تحديد حالته؟",
    "إيه آخر بيانات متاحة عن المشروع؟",
    "قارن حالته بالربع السابق."
]

for question in questions:
    result = understand_query(
        question=question,
        last_compound="C04"
    )

    print("\nQUESTION:", question)
    print(json.dumps(result, ensure_ascii=False, indent=2))