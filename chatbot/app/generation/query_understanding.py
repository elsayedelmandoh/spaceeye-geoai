
# import json
# import logging
# import os
# import re

# from google import genai
# from google.genai import types

# from chatbot.app.core.config import get_settings
# from chatbot.app.retrieval.router import route_query


# logger = logging.getLogger(__name__)

# DEFAULT_MODEL = "gemini-3.1-flash-lite"

# VALID_INTENTS = {
#     "project_info",
#     "inspection_priority",
#     "published_statements",
#     "rules",
#     "complaints",
#     "inspection_visits",
#     "project_overview",
#     "greeting",
#     "out_of_scope",
# }

# VALID_SEARCH_TARGETS = {
#     "structured_data",
#     "text_evidence",
# }

# QUERY_SCHEMA = {
#     "type": "OBJECT",
#     "properties": {
#         "intent": {
#             "type": "STRING",
#             "enum": sorted(VALID_INTENTS),
#         },
#         "sub_intent": {
#             "type": "STRING",
#         },
#         "compound": {
#             "type": ["STRING", "NULL"],
#         },
#         "rewritten_query": {
#             "type": "STRING",
#         },
#         "search_targets": {
#             "type": "ARRAY",
#             "items": {
#                 "type": "STRING",
#                 "enum": sorted(VALID_SEARCH_TARGETS),
#             },
#         },
#         "needs_clarification": {
#             "type": "BOOLEAN",
#         },
#         "clarification_question": {
#             "type": "STRING",
#         },
#     },
#     "required": [
#         "intent",
#         "sub_intent",
#         "compound",
#         "rewritten_query",
#         "search_targets",
#         "needs_clarification",
#         "clarification_question",
#     ],
#     "additionalProperties": False,
# }


# QUERY_UNDERSTANDING_INSTRUCTION = """
# أنت محرك فهم الأسئلة الخاص بنظام SpaceEye لمتابعة مشروعات
# التنمية العمرانية.

# مهمتك الوحيدة هي فهم سؤال المستخدم وتحديد البيانات التي
# يحتاج النظام إلى استرجاعها. لا تجب عن السؤال ولا تخترع بيانات.

# افهم اللغة العربية المصرية والعربية الفصحى والإنجليزية،
# وافهم الأسئلة المختصرة وأسئلة المتابعة والضمائر.

# قواعد تحديد النية:

# 1. project_info:
#    معلومات المشروع، حالته، آخر بياناته، مؤشرات الأداء،
#    مقارنة الفترات، أو تقييم التأخير.

# 2. inspection_priority:
#    مستوى أولوية التفتيش، سبب التصنيف، أو المؤشرات
#    التي أدت إلى تحديد أولوية المشروع.

# 3. published_statements:
#    التصريحات والإعلانات والمواعيد المنشورة والتقدم المعلن.

# 4. rules:
#    القواعد وملخصات اللوائح وحقوق المشتري وشروط التسليم.

# 5. complaints:
#    الشكاوى والمدفوعات والتظلمات.

# 6. inspection_visits:
#    الزيارات الميدانية ومحاضر التفتيش.

# 7. project_overview:
#    أسئلة عامة عن SpaceEye نفسه، وليس عن مشروع محدد.

# 8. greeting:
#    التحية والشكر والامتنان والردود الاجتماعية القصيرة،
#    مثل: أهلًا، صباح الخير، شكرًا، متشكرة، تسلم،
#    تمام، Thanks، Thank you، You're welcome.
#    لا تسترجع بيانات للمحادثات الاجتماعية القصيرة.

# 9. out_of_scope:
#    الأسئلة غير المرتبطة بوظائف النظام.

# قواعد تحديد المشروع:

# - استخرج كود المشروع فقط إذا ظهر صراحة في السؤال
#   أو كان واضحًا من سياق المتابعة السابق.
# - أكواد المشروعات تكون مثل C04 و C18.
# - إذا كان السؤال متابعة واضحة عن المشروع السابق،
#   استخدم الكود السابق.
# - لا تستخدم الكود السابق إذا انتقل المستخدم إلى موضوع
#   مختلف أو سأل سؤالًا عامًا.
# - لا تخترع كود مشروع.

# قواعد إعادة صياغة السؤال:

# - اجعل rewritten_query سؤالًا واضحًا ومكتملًا
#   يصلح للبحث في قاعدة البيانات.
# - أضف كود المشروع إذا كان معروفًا.
# - حافظ على المعنى الأصلي دون إضافة افتراضات.
# - لا تحوّل سؤال التأخير إلى تأكيد بوجود تأخير.
# - لا تعتبر مؤشر النشاط دليلًا على اكتمال التسليم.

# قواعد تحديد مصادر البحث:

# - structured_data: عندما يحتاج السؤال إلى بيانات SQL
#   أو مؤشرات أو ملف تعريف المشروع.
# - text_evidence: عندما يحتاج إلى تصريحات أو قواعد
#   أو شكاوى أو زيارات أو أدلة نصية.
# - يمكن اختيار المصدرين معًا.
# - لا تختر مصادر غير مرتبطة بالسؤال.

# إذا كان السؤال يحتاج كود مشروع محددًا ولا يوجد كود
# في السؤال أو سياق سابق، اجعل needs_clarification = true
# واطلب من المستخدم تحديد المشروع.

# أعد JSON مطابقًا للمخطط فقط.
# لا تكتب إجابة للمستخدم.
# """


# def _fallback_understanding(
#     question: str,
#     last_compound: str | None = None,
# ) -> dict:
#     """Use the existing keyword router if Gemini is unavailable."""

#     routing = route_query(
#         question,
#         last_compound=last_compound,
#     )

#     intent = routing["intent"]

#     search_targets = []

#     if intent not in ("greeting", "out_of_scope", "project_overview"):
#         search_targets = ["text_evidence"]

#     if intent in ("project_info", "inspection_priority"):
#         search_targets.append("structured_data")

#     return {
#         "intent": intent,
#         "sub_intent": "fallback",
#         "compound": routing["compound"],
#         "rewritten_query": question.strip(),
#         "search_targets": list(dict.fromkeys(search_targets)),
#         "needs_clarification": False,
#         "clarification_question": "",
#         "understanding_mode": "keyword_fallback",
#     }


# def _validate_result(
#     result: dict,
#     question: str,
#     last_compound: str | None = None,
# ) -> dict:
#     """Validate Gemini output before passing it to retrieval."""

#     intent = result.get("intent")

#     if intent not in VALID_INTENTS:
#         raise ValueError("Invalid intent returned by Gemini.")

#     compound = result.get("compound")

#     if compound is not None:
#         match = re.fullmatch(
#             r"C\d{2}",
#             str(compound).strip().upper(),
#         )

#         if not match:
#             compound = None
#         else:
#             compound = match.group(0)

#     # Do not accept a project code invented by the model.
#     explicit_code = re.search(
#         r"\bC\d{2}\b",
#         question,
#         re.IGNORECASE,
#     )

#     previous_code = (
#         last_compound.upper()
#         if last_compound
#         and re.fullmatch(r"C\d{2}", last_compound.upper())
#         else None
#     )

#     if explicit_code:
#         compound = explicit_code.group(0).upper()

#     elif intent not in (
#         "greeting",
#         "out_of_scope",
#         "project_overview",
#     ):
#         # Keep the previous project for follow-up questions.
#         compound = previous_code

#     else:
#         compound = None

#     rewritten_query = result.get("rewritten_query")

#     if not isinstance(rewritten_query, str) or not rewritten_query.strip():
#         rewritten_query = question.strip()

#     targets = result.get("search_targets", [])

#     if not isinstance(targets, list):
#         targets = []

#     targets = [
#         target
#         for target in targets
#         if target in VALID_SEARCH_TARGETS
#     ]

#     if intent in ("greeting", "out_of_scope", "project_overview"):
#         compound = None
#         targets = []

#     return {
#         "intent": intent,
#         "sub_intent": str(result.get("sub_intent", "general")),
#         "compound": compound,
#         "rewritten_query": rewritten_query.strip(),
#         "search_targets": list(dict.fromkeys(targets)),
#         "needs_clarification": bool(
#             result.get("needs_clarification", False)
#         ),
#         "clarification_question": str(
#             result.get("clarification_question", "")
#         ).strip(),
#         "understanding_mode": "gemini",
#     }


# def understand_query(
#     question: str,
#     last_compound: str | None = None,
# ) -> dict:
#     """
#     Understand the user's question using Gemini.

#     Gemini identifies the intent, project code, and retrieval needs.
#     Python validates the result before retrieval.
#     The existing router remains available as a fallback.
#     """

#     if not question or not question.strip():
#         raise ValueError("Question cannot be empty.")

#     # Short greetings, thanks, and acknowledgements do not need database retrieval.
#     social_routing = route_query(question, last_compound=last_compound)
#     if social_routing["intent"] == "greeting":
#         return {
#             "intent": "greeting",
#             "sub_intent": "social",
#             "compound": None,
#             "rewritten_query": question.strip(),
#             "search_targets": [],
#             "needs_clarification": False,
#             "clarification_question": "",
#             "understanding_mode": "social_router",
#         }

#     settings = get_settings()

#     if not settings.gemini_api_key:
#         logger.warning(
#             "Gemini API key is unavailable. Using keyword fallback."
#         )
#         return _fallback_understanding(question, last_compound)

#     model = os.getenv(
#         "GEMINI_UNDERSTANDING_MODEL",
#         DEFAULT_MODEL,
#     )

#     prompt = f"""
# السؤال الحالي:
# {question}

# كود المشروع السابق في المحادثة:
# {last_compound or "لا يوجد"}

# حلل السؤال وفق التعليمات والمخطط المحدد.
# """

#     try:
#         with genai.Client(
#             api_key=settings.gemini_api_key
#         ) as client:

#             response = client.models.generate_content(
#                 model=model,
#                 contents=prompt,
#                 config=types.GenerateContentConfig(
#                     system_instruction=QUERY_UNDERSTANDING_INSTRUCTION,
#                     response_mime_type="application/json",
#                     response_json_schema=QUERY_SCHEMA,
#                     temperature=0.1,
#                     max_output_tokens=1000,
#                 ),
#             )

#         response_text = (response.text or "").strip()

#         if not response_text:
#             raise ValueError("Gemini returned an empty response.")

#         result = json.loads(response_text)

#         validated = _validate_result(
#             result=result,
#             question=question,
#             last_compound=last_compound,
#         )

#         logger.info(
#             "Query understood: intent=%s, compound=%s, mode=gemini",
#             validated["intent"],
#             validated["compound"],
#         )

#         return validated

#     except Exception:
#         logger.exception(
#             "Gemini query understanding failed. Using keyword fallback."
#         )

#         return _fallback_understanding(
#             question=question,
#             last_compound=last_compound,
#         )


import json
import logging
import re

from google import genai
from google.genai import types

from chatbot.app.core.budget import try_spend_gemini_call
from chatbot.app.core.config import get_settings
from chatbot.app.retrieval.router import route_query


logger = logging.getLogger(__name__)

VALID_INTENTS = {
    "project_info",
    "inspection_priority",
    "published_statements",
    "rules",
    "complaints",
    "inspection_visits",
    "knowledge",
    "project_overview",
    "greeting",
    "out_of_scope",
}

VALID_SEARCH_TARGETS = {
    "structured_data",
    "text_evidence",
}

PROJECT_CODE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])C\d{2}(?![A-Za-z0-9])",
    re.IGNORECASE,
)

GENERAL_SCENARIO_PATTERNS = [
    r"افترض",
    r"افتراضي",
    r"سيناريو",
    r"لو\s+مشروع",
    r"عندي\s+مشروع",
    r"أي\s+مشروع",
    r"مشروع\s+مفيهوش",
    r"مشروع\s+ليس\s+به",
    r"مفيش\s+نشاط",
    r"عدم\s+وجود\s+نشاط",
    r"النشاط\s+متوقف",
    r"موعد\s+التسليم\s+(?:عدى|فات|انتهى)",
    r"التسليم\s+متأخر",
    r"ماذا\s+لو",
    r"what\s+if",
    r"hypothetical",
    r"scenario",
]


QUERY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "intent": {
            "type": "STRING",
            "enum": sorted(VALID_INTENTS),
        },
        "sub_intent": {
            "type": "STRING",
        },
        "compound": {
            "type": ["STRING", "NULL"],
        },
        "compounds": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
        "rewritten_query": {
            "type": "STRING",
        },
        "search_targets": {
            "type": "ARRAY",
            "items": {
                "type": "STRING",
                "enum": sorted(VALID_SEARCH_TARGETS),
            },
        },
        "needs_clarification": {
            "type": "BOOLEAN",
        },
        "clarification_question": {
            "type": "STRING",
        },
    },
    "required": [
        "intent",
        "sub_intent",
        "compound",
        "compounds",
        "rewritten_query",
        "search_targets",
        "needs_clarification",
        "clarification_question",
    ],
    "additionalProperties": False,
}


QUERY_UNDERSTANDING_INSTRUCTION = """
أنت محرك فهم الأسئلة الخاص بنظام SpaceEye لمتابعة مشروعات
التنمية العمرانية.

مهمتك فهم السؤال وتحديد البيانات التي يحتاج النظام إلى استرجاعها.
لا تجب عن السؤال ولا تخترع بيانات.

افهم العربية المصرية والفصحى والإنجليزية، وأسئلة المتابعة والضمائر.

النيات:
- project_info: معلومات المشروع وحالته ومؤشرات الأداء والتأخير.
- inspection_priority: أولوية التفتيش وأسباب التصنيف.
- published_statements: التصريحات والإعلانات والمواعيد المنشورة.
- rules: القواعد وملخصات اللوائح وحقوق المشتري وشروط التسليم.
- complaints: الشكاوى والمدفوعات والتظلمات.
- inspection_visits: الزيارات الميدانية ومحاضر التفتيش.
- knowledge: المصادر المرجعية الخارجية: قانون البناء 119 وقرار 2184 وقانون حماية البيانات 151 ومعايير ISO 37120/37122 وDynamic World وOpen Buildings وEsri Wayback وموقع الهيئة وSLA.
- project_overview: أسئلة عامة عن نظام SpaceEye.
- greeting: التحية والشكر والردود الاجتماعية القصيرة.
- out_of_scope: الأسئلة غير المرتبطة بوظائف النظام.

تحديد المشروعات:
- استخرج كل أكواد المشروعات المذكورة صراحة، وليس أول كود فقط.
- ضع الأكواد في compounds، مثل ["C04", "C18"].
- استخدم compound إذا كان هناك مشروع واحد فقط.
- إذا كان السؤال متابعة واضحة عن مشروع سابق واحد، استخدم كوده.
- لا تستخدم كودًا سابقًا عند الانتقال إلى موضوع عام أو سيناريو افتراضي.
- لا تخترع أكواد مشروعات.

السيناريوهات العامة:
- إذا كان السؤال افتراضيًا أو يطلب تحليل حالة عامة دون تحديد مشروع،
  فلا تطلب كود مشروع.
- استخدم sub_intent = "general_scenario".
- يمكن اختيار structured_data أو text_evidence حسب طبيعة السؤال.
- لا تدّعِ أن السيناريو حدث بالفعل في مشروع حقيقي.

إعادة صياغة السؤال:
- اجعل rewritten_query واضحًا ومكتملًا.
- أضف أكواد المشروعات المعروفة.
- لا تضف افتراضات غير موجودة في السؤال.
- لا تحوّل السؤال عن التأخير إلى تأكيد بوجود تأخير.
- مؤشر النشاط ليس دليلًا على اكتمال التسليم.

مصادر البحث:
- structured_data لبيانات SQL والمؤشرات وملف تعريف المشروع.
- text_evidence للتصريحات والقواعد والشكاوى والزيارات والأدلة النصية.
- يمكن اختيار المصدرين معًا.

طلب التوضيح:
- اطلب كود المشروع فقط عندما يكون المستخدم يسأل عن بيانات مشروع حقيقي محدد
  ولا يوجد كود في السؤال أو سياق متابعة واضح.
- لا تطلب كودًا لتحليل سيناريو افتراضي أو شرح قاعدة عامة.
- إذا ذكر المستخدم أكثر من مشروع، لا تطلب منه اختيار مشروع واحد.

أعد JSON مطابقًا للمخطط فقط.
"""


def _extract_project_codes(text: str) -> list[str]:
    """Extract all explicit project codes, preserving their order."""
    if not text:
        return []

    codes = PROJECT_CODE_PATTERN.findall(text)

    return list(dict.fromkeys(
        code.upper() for code in codes
    ))


def _is_general_scenario(question: str) -> bool:
    """Detect hypothetical or general scenario questions."""
    normalized = question.strip().lower()

    return any(
        re.search(pattern, normalized, re.IGNORECASE)
        for pattern in GENERAL_SCENARIO_PATTERNS
    )

def _is_delivery_verification(question: str) -> bool:
    """Detect questions about whether an announcement proves actual handover."""

    patterns = [
        r"إعلان\s+التسليم",
        r"اتسلّم\s+فعلي",
        r"تم\s+التسليم\s+فعلي",
        r"الاستلام\s+الفعلي",
        r"هل\s+.*التسليم.*(يعني|يثبت|معناه)",
        r"delivery\s+announcement",
        r"actual\s+handover",
        r"was\s+.*delivered",
    ]

    return any(
        re.search(pattern, question, re.IGNORECASE)
        for pattern in patterns
    )


def _is_project_comparison(question: str, codes: list[str]) -> bool:
    """Detect explicit comparisons between two or more projects."""

    comparison_terms = [
        "قارن",
        "مقارنة",
        "الفرق بين",
        "قارنلي",
        "compare",
        "comparison",
        "difference between",
    ]

    has_comparison_term = any(
        term in question.lower()
        for term in comparison_terms
    )

    return has_comparison_term and len(codes) >= 2

def _fallback_understanding(
    question: str,
    last_compound: str | None = None,
) -> dict:
    """Use the keyword router if Gemini is unavailable."""

    routing = route_query(
        question,
        last_compound=last_compound,
    )

    intent = routing["intent"]
    compounds = _extract_project_codes(question)

    if not compounds and last_compound:
        previous = _extract_project_codes(last_compound)
        compounds = previous

    if not compounds and routing.get("compound"):
        compounds = _extract_project_codes(
            str(routing["compound"])
        )

    if _is_general_scenario(question):
        sub_intent = "general_scenario"
    else:
        sub_intent = "fallback"

    search_targets = []

    if intent not in (
        "greeting",
        "out_of_scope",
        "project_overview",
    ):
        search_targets = ["text_evidence"]

    if intent in ("project_info", "inspection_priority"):
        search_targets.append("structured_data")

    if intent in ("greeting", "out_of_scope", "project_overview"):
        compounds = []

    return {
        "intent": intent,
        "sub_intent": sub_intent,
        "compound": compounds[0] if len(compounds) == 1 else None,
        "compounds": compounds,
        "rewritten_query": question.strip(),
        "search_targets": list(dict.fromkeys(search_targets)),
        "needs_clarification": False,
        "clarification_question": "",
        "understanding_mode": "keyword_fallback",
    }


def _validate_result(
    result: dict,
    question: str,
    last_compound: str | None = None,
) -> dict:
    """Validate Gemini output and apply deterministic intent corrections."""

    intent = result.get("intent")

    if intent not in VALID_INTENTS:
        raise ValueError("Invalid intent returned by Gemini.")

    explicit_codes = _extract_project_codes(question)
    previous_codes = _extract_project_codes(last_compound or "")

    general_scenario = _is_general_scenario(question)
    delivery_verification = _is_delivery_verification(question)
    project_comparison = _is_project_comparison(
        question,
        explicit_codes,
    )

    # 1. Resolve project codes.
    if explicit_codes:
        compounds = explicit_codes

    elif (
        intent not in (
            "greeting",
            "out_of_scope",
            "project_overview",
        )
        and len(previous_codes) == 1
        and not general_scenario
        and not delivery_verification
    ):
        compounds = previous_codes

    else:
        compounds = []

    # Keep valid model-provided codes only if no stronger source exists.
    if not compounds and not general_scenario and not delivery_verification:
        model_codes = result.get("compounds", [])

        if isinstance(model_codes, list):
            compounds = [
                code.strip().upper()
                for code in model_codes
                if isinstance(code, str)
                and re.fullmatch(
                    r"C\d{2}",
                    code.strip(),
                    re.IGNORECASE,
                )
            ]

        if not compounds:
            model_compound = result.get("compound")

            if isinstance(model_compound, str):
                compounds = _extract_project_codes(model_compound)

    compounds = list(dict.fromkeys(compounds))

    # 2. Deterministic intent corrections.
    if project_comparison:
        intent = "project_info"

    elif delivery_verification:
        intent = "published_statements"

    elif general_scenario:
        intent = "project_info"

    if intent in (
        "greeting",
        "out_of_scope",
        "project_overview",
    ):
        compounds = []

    compound = compounds[0] if len(compounds) == 1 else None

    # 3. Resolve sub-intent.
    sub_intent = str(result.get("sub_intent", "general"))

    if project_comparison:
        sub_intent = "performance_comparison"

    elif delivery_verification:
        sub_intent = "delivery_verification"

    elif general_scenario:
        sub_intent = "general_scenario"

    # 4. Rewrite the query.
    rewritten_query = result.get("rewritten_query")

    if not isinstance(rewritten_query, str) or not rewritten_query.strip():
        rewritten_query = question.strip()

    if project_comparison:
        rewritten_query = (
            f"قارن بين المشروعات {', '.join(compounds)} "
            f"من حيث البيانات المتاحة ومؤشرات الأداء للفترة المتاحة."
        )

    elif delivery_verification:
        rewritten_query = (
            "هل إعلان أو تصريح التسليم يثبت الاستلام الفعلي للمشروع؟ "
            "وضّح الفرق بين الإعلان المنشور وإثبات الاستلام الفعلي."
        )

    elif general_scenario:
        rewritten_query = question.strip()

    # 5. Resolve search targets.
    targets = result.get("search_targets", [])

    if not isinstance(targets, list):
        targets = []

    targets = [
        target
        for target in targets
        if target in VALID_SEARCH_TARGETS
    ]

    if project_comparison:
        targets = ["structured_data", "text_evidence"]

    elif delivery_verification:
        targets = ["text_evidence"]

    elif general_scenario:
        targets = ["text_evidence"]

    if intent == "inspection_priority":
        targets = list(set(targets + ["structured_data", "text_evidence"]))

    if intent == "knowledge":
        targets = ["text_evidence"]
        compounds = []
        compound = None

    if intent in (
        "greeting",
        "out_of_scope",
        "project_overview",
    ):
        targets = []
        compounds = []
        compound = None

    # 6. Resolve clarification.
    needs_clarification = bool(
        result.get("needs_clarification", False)
    )

    clarification_question = str(
        result.get("clarification_question", "")
    ).strip()

    # These questions do not need a project code.
    if (
        general_scenario
        or delivery_verification
        or project_comparison
    ):
        needs_clarification = False
        clarification_question = ""

    return {
        "intent": intent,
        "sub_intent": sub_intent,
        "compound": compound,
        "compounds": compounds,
        "rewritten_query": rewritten_query.strip(),
        "search_targets": list(dict.fromkeys(targets)),
        "needs_clarification": needs_clarification,
        "clarification_question": clarification_question,
        "understanding_mode": "gemini",
    }

def understand_query(
    question: str,
    last_compound: str | None = None,
) -> dict:
    """
    Understand the user's question using Gemini.

    Python validates project codes and prevents invented codes.
    The keyword router remains available as a fallback.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    social_routing = route_query(
        question,
        last_compound=last_compound,
    )

    if social_routing["intent"] == "greeting":
        return {
            "intent": "greeting",
            "sub_intent": "social",
            "compound": None,
            "compounds": [],
            "rewritten_query": question.strip(),
            "search_targets": [],
            "needs_clarification": False,
            "clarification_question": "",
            "understanding_mode": "social_router",
        }

    settings = get_settings()

    if not settings.gemini_api_key:
        logger.warning(
            "Gemini API key is unavailable. Using keyword fallback."
        )
        return _fallback_understanding(
            question,
            last_compound,
        )

    if not try_spend_gemini_call():
        return _fallback_understanding(
            question,
            last_compound,
        )

    model = settings.gemini_model

    prompt = f"""
السؤال الحالي:
{question}

أكواد المشروعات السابقة في المحادثة:
{last_compound or "لا يوجد"}

حلل السؤال وفق التعليمات والمخطط المحدد.
إذا ذكر السؤال أكثر من مشروع، ضع جميع الأكواد في compounds.
إذا كان السؤال سيناريو افتراضيًا، فلا تطلب كود مشروع.
"""

    try:
        with genai.Client(
            api_key=settings.gemini_api_key
        ) as client:

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=QUERY_UNDERSTANDING_INSTRUCTION,
                    response_mime_type="application/json",
                    response_json_schema=QUERY_SCHEMA,
                    temperature=0.1,
                    max_output_tokens=1200,
                ),
            )

        response_text = (response.text or "").strip()

        if not response_text:
            raise ValueError("Gemini returned an empty response.")

        result = json.loads(response_text)

        validated = _validate_result(
            result=result,
            question=question,
            last_compound=last_compound,
        )

        logger.info(
            "Query understood: intent=%s, compounds=%s, mode=gemini",
            validated["intent"],
            validated["compounds"],
        )

        return validated

    except Exception:
        logger.exception(
            "Gemini query understanding failed. Using keyword fallback."
        )

        return _fallback_understanding(
            question=question,
            last_compound=last_compound,
        )
