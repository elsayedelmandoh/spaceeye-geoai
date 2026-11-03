
import re
import unicodedata


COMPLAINT_KEYWORDS = [
    "شكوى", "شكاوى", "الشكاوي", "الشكاوى", "الشكوى",
    "تظلم", "سداد", "دفع", "مقدم الحجز",
    "محدش بيرد", "مفيش رد",
    "complaint", "complaints", "payment",
]

VISIT_KEYWORDS = [
    "زيارة تفتيش", "زيارات التفتيش", "محضر تفتيش",
    "المعاينة", "زيارة ميدانية",
    "inspection visit", "inspection visits", "site visit",
]

RULE_KEYWORDS = [
    "التأخير", "تأخر التسليم", "تأخير التسليم",
    "تأخر الاستلام", "حقوق المشتري", "حق المشتري",
    "حقوق العملاء", "فسخ العقد", "إلغاء التعاقد",
    "تعويض", "مستحقات", "شروط التسليم",
    "قواعد التسليم", "شروط التأخير", "مدة التأخير",
    "delay", "delivery delay", "late delivery",
    "handover delay", "delivery rules", "delivery conditions",
]

STATEMENT_KEYWORDS = [
    "ميعاد التسليم", "ميعاد تسليم",
    "موعد التسليم", "موعد تسليم",
    "تاريخ التسليم", "تاريخ تسليم",
    "وعد التسليم", "التسليم", "تسليم مشروع",
    "التقدم", "نسبة الإنجاز", "نسبة التقدم",
    "تصريح", "إعلان",
    "progress", "promise", "delivery date",
    "delivery progress", "announced delivery",
]

INSPECTION_PRIORITY_KEYWORDS = [
    "سبب المستوى",
    "سبب التصنيف",
    "سبب الأولوية",
    "سبب تحديد الأولوية",
    "ليه في المستوى",
    "ليه في مستوي",
    "ليه ضمن المستوى",
    "لماذا في المستوى",
    "لماذا في مستوي",
    "ضمن المستوى",
    "ضمن مستوي",
    "مستوى الأولوية",
    "مستوي الاولوية",
    "درجة الأولوية",
    "درجه الاولويه",
    "ترتيب الأولوية",
    "أولوية التفتيش",
    "اولويه التفتيش",
    "تصنيف التفتيش",
    "مستوى التفتيش",
    "سبب اختيار المشروع للتفتيش",
    "لماذا تم تصنيف المشروع",
    "ليه المشروع متصنف",
    "ليه المشروع في المستوى",
    "ليه المشروع في مستوي",
    "level 1", "level 2", "level 3", "level 4",
    "level one", "level two", "level three", "level four",
    "priority level",
    "inspection priority",
    "priority reason",
    "why level",
]

PROJECT_KEYWORDS = [
    "بيانات المشروع", "معلومات المشروع", "تفاصيل المشروع",
    "مساحة الأرض", "عدد الوحدات", "عدد الأدوار",
    "المطور", "المنطقة", "نسبة الغطاء",
    "مؤشرات الأداء",
    "kpi", "project details", "project information",
    "project profile", "latest kpi",
    "construction activity", "inspection priority",
]

PROJECT_OVERVIEW_KEYWORDS = [
    "spaceeye", "space eye",
    "ما هو المشروع", "ما هو سبيس آي",
    "ما هو سبيس اي",
    "عن المشروع", "نبذة عن المشروع",
    "تعريف المشروع", "هدف المشروع",
    "what is the project", "what is space eye",
    "about spaceeye", "about space eye",
    "project overview",
]

GREETING_PHRASES = [
    "اهلا", "اهلا وسهلا", "مرحبا", "مرحباً",
    "السلام عليكم", "السلام عليكم ورحمة الله",
    "صباح الخير", "مساء الخير",
    "hi", "hello", "hey",
    "good morning", "good evening",
    "شكرا", "شكرا جزيلا", "شكرا جدا", "شكرا ليك",
    "شكرا ليكي", "الف شكر", "متشكرة", "متشكرة جدا",
    "متشكر", "متشكر جدا", "تسلم", "تسلمي",
    "تسلم ايدك", "تسلم ايديك", "ربنا يخليك",
    "ممنون", "ممتن", "يعطيك العافية",
    "thanks", "thank you", "thank you so much",
    "thanks a lot", "many thanks", "appreciate it",
    "much appreciated", "great", "perfect",
    "تمام", "تمام شكرا", "تمام كده", "ماشي",
    "حلو", "جميل", "كويس",
]

OUT_OF_SCOPE_KEYWORDS = [
    "weather", "الطقس", "درجة الحرارة",
    "recipe", "وصفة", "football", "كرة القدم",
    "translate", "ترجم",
]


def _normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"[إأآٱ]", "ا", text)
    text = re.sub(r"[؟?!.,،؛:]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_keywords(keywords: list[str]) -> list[str]:
    return [_normalize_text(keyword) for keyword in keywords]


def _contains_keyword(query: str, keywords: list[str]) -> bool:
    normalized_keywords = _normalize_keywords(keywords)
    return any(keyword in query for keyword in normalized_keywords)


def _is_greeting(query: str) -> bool:
    social_phrases = set(_normalize_keywords(GREETING_PHRASES))
    return query in social_phrases


def _extract_compound(query: str) -> str | None:
    match = re.search(r"\bC\d{2}\b", query, re.IGNORECASE)
    return match.group(0).upper() if match else None


def _is_inspection_priority_query(query: str) -> bool:
    if _contains_keyword(query, INSPECTION_PRIORITY_KEYWORDS):
        return True

    # Match ordinal levels, including the fourth level.
    level_pattern = (
        r"(?:المستوى|مستوى|المستوي|مستوي)\s*"
        r"(?:ال)?(?:اول|اولى|اول؟|ثاني|الثاني|ثانيه|"
        r"ثالث|الثالث|رابع|الرابع)"
    )

    has_level = re.search(level_pattern, query) is not None

    has_reason = any(
        word in query
        for word in (
            "سبب",
            "ليه",
            "لماذا",
            "تصنيف",
            "اولويه",
            "اولوية",
        )
    )

    return has_level and has_reason


def route_query(
    query: str,
    last_compound: str | None = None,
) -> dict:
    """
    Detect question intent and build ChromaDB metadata filters.
    Reuse the previous project code for relevant follow-up questions.
    """

    normalized_query = _normalize_text(query)

    if not normalized_query:
        intent = "out_of_scope"
        document_type = None
        compound = None

    else:
        compound = _extract_compound(query)

        if compound is None and last_compound:
            compound = last_compound.upper()

        if _is_greeting(normalized_query):
            intent = "greeting"
            document_type = None
            compound = None

        elif _contains_keyword(normalized_query, COMPLAINT_KEYWORDS):
            intent = "complaints"
            document_type = "synthetic_complaint"

        elif _contains_keyword(normalized_query, VISIT_KEYWORDS):
            intent = "inspection_visits"
            document_type = "synthetic_visit"

        elif _is_inspection_priority_query(normalized_query):
            intent = "inspection_priority"
            document_type = None

        elif _contains_keyword(normalized_query, RULE_KEYWORDS):
            intent = "rules"
            document_type = "rule_summary"

        elif _contains_keyword(normalized_query, STATEMENT_KEYWORDS):
            intent = "published_statements"
            document_type = "published_statement"

        elif _contains_keyword(normalized_query, PROJECT_KEYWORDS) or _extract_compound(query):
            intent = "project_info"
            document_type = None

        elif _contains_keyword(normalized_query, PROJECT_OVERVIEW_KEYWORDS):
            intent = "project_overview"
            document_type = None

        else:
            intent = "out_of_scope"
            document_type = None

    conditions = []

    if document_type:
        conditions.append({"document_type": document_type})

    if compound:
        conditions.append({"compound": compound})

    if len(conditions) == 2:
        where = {"$and": conditions}
    elif len(conditions) == 1:
        where = conditions[0]
    else:
        where = None

    return {
        "intent": intent,
        "document_type": document_type,
        "compound": compound,
        "where": where,
    }
