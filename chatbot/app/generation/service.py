
# import json

# from chatbot.app.retrieval.hybrid import retrieve_hybrid
# from chatbot.app.generation.answer_builder import build_answer
# from chatbot.app.generation.gemini_client import generate_answer


# def answer_question(
#     question: str,
#     n_results: int = 5,
#     last_compound: str | None = None,
# ) -> dict:
#     """
#     Complete SpaceEye chatbot flow:

#     Gemini query understanding
#     -> Hybrid SQL + RAG retrieval
#     -> Evidence validation
#     -> Gemini answer generation
#     """

#     if not question or not question.strip():
#         raise ValueError("Question cannot be empty.")

#     # 1. Understand the question and retrieve SpaceEye data.
#     retrieval_result = retrieve_hybrid(
#         query=question,
#         n_results=n_results,
#         last_compound=last_compound,
#     )

#     intent = retrieval_result.get("intent")
#     sub_intent = retrieval_result.get("sub_intent")
#     compound = retrieval_result.get("compound")

#     structured_data = (
#         retrieval_result.get("structured_data") or {}
#     )

#     profile = structured_data.get("compound_profile")
#     kpi = structured_data.get("latest_kpi")
#     evidence = retrieval_result.get("evidence") or []

#     # 2. Handle clarification before generating an answer.
#     if retrieval_result.get("needs_clarification"):
#         clarification = (
#             retrieval_result.get("clarification_question")
#             or "من فضلك حددي كود المشروع الذي تريدين الاستفسار عنه."
#         )

#         return {
#             "question": question,
#             "answer": clarification,
#             "intent": intent,
#             "sub_intent": sub_intent,
#             "compound": compound,
#             "evidence_count": 0,
#             "generation_mode": "clarification",
#             "understanding_mode": retrieval_result.get(
#                 "understanding_mode"
#             ),
#         }

#     # 3. Detect an unknown project.
#     unknown_compound = (
#         compound is not None
#         and profile is None
#         and kpi is None
#         and intent in ("project_info", "inspection_priority")
#     )

#     # 4. Build a deterministic fallback answer.
#     fallback_answer = build_answer(retrieval_result)

#     if unknown_compound:
#         return {
#             "question": question,
#             "answer": fallback_answer,
#             "intent": intent,
#             "sub_intent": sub_intent,
#             "compound": compound,
#             "evidence_count": len(evidence),
#             "generation_mode": "local",
#             "understanding_mode": retrieval_result.get(
#                 "understanding_mode"
#             ),
#         }

#     # 5. Explain the actual retrieval limits to Gemini.
#     retrieval_limits = []

#     if sub_intent == "performance_comparison":
#         retrieval_limits.append(
#             "المتاح حاليًا هو أحدث KPI فقط. "
#             "لم يتم استرجاع KPI للربع السابق، لذلك لا يجوز "
#             "اختلاق مقارنة زمنية أو وصف تحسن أو تراجع."
#         )

#     if sub_intent == "delay_assessment":
#         retrieval_limits.append(
#             "لا تعتبر مؤشر K3 أو أي تصريح منفرد إثباتًا "
#             "نهائيًا للتأخير. وضّح الفرق بين تجاوز موعد معلن "
#             "وبين إثبات التأخير مقارنة بجدول زمني معتمد."
#         )

#     if sub_intent == "indicators_analysis":
#         retrieval_limits.append(
#             "اشرح المؤشرات الموجودة في البيانات المسترجعة فقط. "
#             "لا تخترع أوزانًا أو معايير أو أسباب تصنيف غير موجودة."
#         )

#     if not evidence:
#         retrieval_limits.append(
#             "لم يتم استرجاع أدلة نصية مرتبطة بالسؤال. "
#             "لا تنسب أي معلومة إلى تصريح أو مستند غير متاح."
#         )

#     if not profile and not kpi:
#         retrieval_limits.append(
#             "لم يتم استرجاع بيانات منظمة للمشروع."
#         )

#     # 6. Prepare the complete context for Gemini.
#     context_data = {
#         "original_question": question,
#         "understood_question": retrieval_result.get(
#             "rewritten_query",
#             question,
#         ),
#         "intent": intent,
#         "sub_intent": sub_intent,
#         "compound": compound,
#         "search_targets": retrieval_result.get(
#             "search_targets",
#             [],
#         ),
#         "structured_data": structured_data,
#         "evidence": evidence,
#         "retrieval_limits": retrieval_limits,
#         "data_provenance_guidelines": [
#             "البيانات المنشورة تختلف عن المؤشرات المحسوبة.",
#             "البيانات الافتراضية ليست سجلات تشغيلية حقيقية.",
#             "المؤشرات المحسوبة لا تمثل قياسات ميدانية مباشرة.",
#             "لا تعتبر درجة نشاط البناء احتمالًا للتسليم أو نسبة إنجاز.",
#             "لا تعتبر أولوية التفتيش حكمًا نهائيًا على المشروع.",
#         ],
#         "answer_guidelines": [
#             "أجب عن سؤال المستخدم مباشرة وبالعربية المصرية الواضحة، مع الحفاظ على المصطلحات الفنية عند الحاجة.",
#             "استخدم البيانات الموجودة في structured_data و evidence فقط. لا تضف حقائق من معرفتك العامة.",
#             "إذا لم تتوفر معلومة في السياق، قل بوضوح إنها غير متاحة في البيانات المسترجعة.",
#             "لا تستنتج أن المشروع متأخر أو مكتمل أو تم تسليمه إلا إذا كان ذلك مثبتًا صراحة في الأدلة.",
#             "اشرح أن activity_prob درجة نشاط مرصودة/محسوبة وليست احتمالًا أو نسبة إنجاز.",
#             "اعرض مستوى التفتيش باعتباره مستوى تصنيف، وليس ترتيبًا بين جميع المشروعات.",
#             "اذكر مصدر كل معلومة مهمة ونوعها: منشورة أو محسوبة أو افتراضية أو مولّدة، إذا كان المصدر متاحًا.",
#             "لا تعرض أسماء متغيرات البرمجة أو أعمدة قاعدة البيانات للمستخدم.",
#             "لا تعرض كل البيانات المتاحة دفعة واحدة؛ اختر فقط ما يجيب عن السؤال.",
#             "نسّق الإجابة بعناوين Markdown واضحة باستخدام ## للأقسام الرئيسية و### للعناوين الفرعية، مع نقاط قصيرة ومنظمة.",
#             "إذا كان الرد يعرض أكثر من مشروع، افصل كل مشروع في قسم مستقل يبدأ بعنوان ## المشروع Cxx حتى تعرض الواجهة كل مشروع في بطاقة منفصلة.",
#             "إذا كان الرد عن مشروع واحد ويحتوي مجموعات مختلفة من المعلومات، افصل بيانات المشروع ومؤشرات الأداء والتصريحات المنشورة بعناوين ## مستقلة لتظهر كل مجموعة في بطاقة منفصلة.",
#             "اجعل كل بطاقة تتناول موضوعًا واحدًا مترابطًا، ولا تقسّم كل معلومة صغيرة إلى بطاقة منفصلة.",
#             "لا تكتب رموز ‏\\n أو HTML entities كنص؛ استخدم أسطر Markdown عادية.",
#             "لا تكرر التحذيرات. أضف تنبيهًا واحدًا مختصرًا عندما يكون مهمًا.",
#             "إذا كان السؤال مقارنة زمنية ولم تتوفر بيانات الفترتين، وضّح ذلك ولا تخترع مقارنة.",
#             "إذا كان evidence فارغًا، لا تدّع وجود تصريح أو مستند مؤيد.",
#         ],
#     }

#     evidence_context = json.dumps(
#         context_data,
#         ensure_ascii=False,
#         default=str,
#         indent=2,
#     )

#     # 7. Keep only conversational/general intents local.
#     # Project and evidence questions must be answered by Gemini
#     # using the retrieved SQL + Chroma context above.
#     local_only_intents = (
#         "greeting",
#         "project_overview",
#         "out_of_scope",
#     )

#     if intent in local_only_intents:
#         answer = fallback_answer
#         generation_mode = "local"

#     else:
#         # 8. Gemini generates a natural, grounded answer.
#         answer = generate_answer(
#             question=question,
#             evidence_context=evidence_context,
#             fallback_answer=fallback_answer,
#         )

#         generation_mode = (
#             "gemini"
#             if answer != fallback_answer
#             else "local_fallback"
#         )

#     return {
#         "question": question,
#         "answer": answer,
#         "intent": intent,
#         "sub_intent": sub_intent,
#         "compound": compound,
#         "evidence_count": len(evidence),
#         "generation_mode": generation_mode,
#         "understanding_mode": retrieval_result.get(
#             "understanding_mode"
#         ),
#     }


import json
import re

from chatbot.app.retrieval.hybrid import retrieve_hybrid
from chatbot.app.generation.answer_builder import build_answer
from chatbot.app.generation.gemini_client import generate_answer


# Query terms mapped to the type of information requested.
# These are checked against the actual retrieved context.
REQUESTED_FIELD_TERMS = {
    "workers": [
        "عامل",
        "عمال",
        "العمال",
        "عدد العاملين",
        "القوى العاملة",
        "workforce",
        "workers",
        "labor",
        "labour",
        "employees",
    ],
    "cost": [
        "تكلفة",
        "التكلفة",
        "تكاليف",
        "مصروفات",
        "المتبقي ماليًا",
        "التكلفة المتبقية",
        "تكلفة الاستكمال",
        "actual cost",
        "remaining cost",
        "completion cost",
        "budget",
        "expenditure",
    ],
}


def _normalize_text(value: str) -> str:
    """Normalize Arabic/English text for simple keyword matching."""
    return re.sub(r"\s+", " ", value.strip().lower())


def _requested_data_domains(question: str) -> list[str]:
    """Identify specific data domains explicitly requested by the user."""
    normalized = _normalize_text(question)
    requested = []

    for domain, terms in REQUESTED_FIELD_TERMS.items():
        if any(term.lower() in normalized for term in terms):
            requested.append(domain)

    return requested


def _flatten_context_values(value):
    """Yield searchable keys and values from nested dictionaries/lists."""
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key).lower()
            yield from _flatten_context_values(item)

    elif isinstance(value, list):
        for item in value:
            yield from _flatten_context_values(item)

    elif value is not None:
        yield str(value).lower()


def _domain_available(domain: str, structured_data: dict, evidence: list) -> bool:
    """
    Check whether the retrieved context contains data for a requested domain.

    A domain is considered available only if a matching field or explicit
    evidence is present. This avoids answering from unrelated project data.
    """
    context_values = list(_flatten_context_values(structured_data))

    for item in evidence:
        context_values.extend(_flatten_context_values(item))

    searchable = " ".join(context_values)

    domain_terms = {
        "workers": [
            "worker_count",
            "workers_count",
            "number_of_workers",
            "labor_count",
            "labour_count",
            "employee_count",
            "workforce",
            "عدد العمال",
            "عدد العاملين",
            "القوى العاملة",
        ],
        "cost": [
            "actual_cost",
            "remaining_cost",
            "completion_cost",
            "total_cost",
            "project_cost",
            "budget",
            "expenditure",
            "التكلفة الفعلية",
            "التكلفة المتبقية",
            "تكلفة الاستكمال",
            "تكلفة المشروع",
        ],
    }

    return any(
        term.lower() in searchable
        for term in domain_terms.get(domain, [])
    )


def _missing_domain_answer(domains: list[str]) -> str:
    """Build a concise answer when requested information is unavailable."""
    messages = []

    if "workers" in domains:
        messages.append(
            "عدد العمال الموجودين حاليًا غير متاح في البيانات "
            "المسترجعة لهذا المشروع."
        )

    if "cost" in domains:
        messages.append(
            "التكلفة الفعلية المتبقية لاستكمال المشروع غير متاحة "
            "في البيانات المسترجعة."
        )

    messages.append(
        "لا يمكن تحديد قيمة موثوقة دون سجل معتمد أو بيانات مالية "
        "أو تشغيلية تدعمها."
    )

    return "\n\n".join(messages)


def _build_retrieval_limits(
    sub_intent: str,
    evidence: list,
    structured_data: dict,
    projects: list,
) -> list[str]:
    """Describe the limitations of the retrieved data."""

    limits = []

    if sub_intent == "performance_comparison":
        limits.append(
            "المتاح حاليًا هو أحدث KPI مسترجع لكل مشروع. "
            "لا تفترض وجود مقارنة زمنية ما لم تتوفر بيانات الفترات "
            "المطلوبة صراحة."
        )

    if sub_intent == "delay_assessment":
        limits.append(
            "لا تعتبر مؤشر K3 أو أي تصريح منفرد إثباتًا نهائيًا "
            "للتأخير. فرّق بين تجاوز موعد معلن وبين إثبات التأخير "
            "مقارنة بجدول زمني تعاقدي أو معتمد."
        )

    if sub_intent == "indicators_analysis":
        limits.append(
            "اشرح المؤشرات المسترجعة فقط. لا تخترع أوزانًا أو "
            "معايير أو أسباب تصنيف غير موجودة."
        )

    if not evidence:
        limits.append(
            "لم يتم استرجاع أدلة نصية مرتبطة بالسؤال. "
            "لا تنسب أي معلومة إلى تصريح أو مستند غير متاح."
        )

    if not structured_data.get("compound_profile") and not structured_data.get("latest_kpi") and not projects:
        limits.append(
            "لم يتم استرجاع بيانات منظمة للمشروع أو المشروعات."
        )

    if len(projects) > 1:
        limits.append(
            "هذه مقارنة بين عدة مشروعات. يجب فصل بيانات كل مشروع "
            "والتأكد من أن كل قيمة مرتبطة بكود المشروع الصحيح."
        )

    if sub_intent == "general_scenario":
        limits.append(
            "السؤال يصف سيناريو عامًا أو افتراضيًا، وليس بالضرورة "
            "حالة مشروع حقيقي في قاعدة البيانات. افصل بين التحليل "
            "العام والبيانات الفعلية المسترجعة."
        )

    return limits


def answer_question(
    question: str,
    n_results: int = 5,
    last_compound: str | None = None,
) -> dict:
    """
    Complete SpaceEye chatbot flow:

    Gemini query understanding
    -> Hybrid SQL + RAG retrieval
    -> Retrieval validation
    -> Gemini grounded answer generation
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    # 1. Understand the question and retrieve data.
    retrieval_result = retrieve_hybrid(
        query=question,
        n_results=n_results,
        last_compound=last_compound,
    )

    intent = retrieval_result.get("intent")
    sub_intent = retrieval_result.get("sub_intent")
    compound = retrieval_result.get("compound")
    compounds = retrieval_result.get("compounds") or (
        [compound] if compound else []
    )

    structured_data = retrieval_result.get("structured_data") or {}
    projects = structured_data.get("projects") or []

    profile = structured_data.get("compound_profile")
    kpi = structured_data.get("latest_kpi")
    evidence = retrieval_result.get("evidence") or []

    common_result = {
        "question": question,
        "intent": intent,
        "sub_intent": sub_intent,
        "compound": compound,
        "compounds": compounds,
        "evidence_count": len(evidence),
        "understanding_mode": retrieval_result.get(
            "understanding_mode"
        ),
    }

    # 2. Handle clarification before generating an answer.
    if retrieval_result.get("needs_clarification"):
        clarification = (
            retrieval_result.get("clarification_question")
            or "من فضلك حددي كود المشروع الذي تريدين الاستفسار عنه."
        )

        return {
            **common_result,
            "answer": clarification,
            "generation_mode": "clarification",
        }

    # 3. Build a deterministic local answer.
    fallback_answer = build_answer(retrieval_result)

    # 4. Detect unknown requested projects.
    if compounds and intent in ("project_info", "inspection_priority"):
        known_codes = {
            str(project.get("compound", "")).upper()
            for project in projects
            if project.get("compound")
            and (
                project.get("compound_profile") is not None
                or project.get("latest_kpi") is not None
            )
        }

        # Backward compatibility for a single-project result.
        if not projects and compound and (profile is not None or kpi is not None):
            known_codes.add(compound.upper())

        unknown_codes = [
            code for code in compounds
            if code.upper() not in known_codes
        ]

        if unknown_codes and not known_codes:
            return {
                **common_result,
                "answer": fallback_answer,
                "generation_mode": "local",
            }

    # 5. Avoid answering unsupported specific-field questions
    # using unrelated project profile information.
    requested_domains = _requested_data_domains(question)

    missing_domains = [
        domain
        for domain in requested_domains
        if not _domain_available(
            domain=domain,
            structured_data=structured_data,
            evidence=evidence,
        )
    ]

    if missing_domains:
        return {
            **common_result,
            "answer": _missing_domain_answer(missing_domains),
            "generation_mode": "local_data_unavailable",
        }

    # 6. Explain retrieval limitations.
    retrieval_limits = _build_retrieval_limits(
        sub_intent=sub_intent,
        evidence=evidence,
        structured_data=structured_data,
        projects=projects,
    )

    # 7. Prepare complete context for Gemini.
    context_data = {
        "original_question": question,
        "understood_question": retrieval_result.get(
            "rewritten_query",
            question,
        ),
        "intent": intent,
        "sub_intent": sub_intent,
        "compound": compound,
        "compounds": compounds,
        "search_targets": retrieval_result.get(
            "search_targets",
            [],
        ),
        "structured_data": structured_data,
        "projects": projects,
        "evidence": evidence,
        "retrieval_limits": retrieval_limits,
        "data_provenance_guidelines": [
            "البيانات المنشورة تختلف عن المؤشرات المحسوبة.",
            "البيانات الافتراضية ليست سجلات تشغيلية حقيقية.",
            "المؤشرات المحسوبة لا تمثل قياسات ميدانية مباشرة.",
            "درجة النشاط ليست احتمالًا للتسليم أو نسبة إنجاز.",
            "أولوية التفتيش ليست حكمًا نهائيًا على المشروع.",
            "بيانات كل مشروع يجب أن تظل مرتبطة بكوده.",
            "تاريخ نشر إعلان التسليم لا يساوي بالضرورة تاريخ التسليم الفعلي.",
            "الموعد التعاقدي يختلف عن الموعد التقديري أو المفترض.",
        ],
        "answer_guidelines": [
            "أجب عن سؤال المستخدم مباشرة وبالعربية المصرية الواضحة.",
            "استخدم البيانات المسترجعة فقط، ولا تضف حقائق من معرفتك العامة.",
            "إذا لم تتوفر معلومة، قل بوضوح إنها غير متاحة.",
            "لا تعرض بيانات المشروع كاملة عندما يسأل المستخدم عن معلومة واحدة.",
            "لا تستنتج أن المشروع متأخر أو مكتمل أو تم تسليمه إلا بدليل صريح.",
            "اشرح أن activity_prob درجة نشاط محسوبة وليست احتمال تسليم أو نسبة إنجاز.",
            "اذكر مصدر المعلومة ونوعها: منشورة أو مشتقة أو افتراضية أو مولّدة متى توفر.",
            "لا تعرض أسماء متغيرات البرمجة أو أعمدة قاعدة البيانات للمستخدم.",
            "لا تخلط بيانات المشروعات عند المقارنة.",
            "في المقارنة، اعرض قسمًا مستقلًا لكل مشروع، ثم ملخصًا للفروق التي تدعمها البيانات.",
            "إذا كانت البيانات غير متاحة لأحد المشروعات، اذكر ذلك بدلًا من إكمال المقارنة بالتخمين.",
            "في السيناريو الافتراضي، اشرح طريقة التحليل وما يلزم للتحقق، ولا تنسب السيناريو إلى مشروع حقيقي.",
            "استخدم عناوين Markdown واضحة ومنظمة.",
            "إذا كان الرد يعرض أكثر من مشروع، اجعل لكل مشروع عنوانًا يبدأ بكود المشروع، مثل ## المشروع C04.",
            "لا تكرر التحذيرات أو المقدمات.",
            "لا تكتب رموز \\n كنص؛ استخدم أسطرًا فعلية.",
        ],
    }

    evidence_context = json.dumps(
        context_data,
        ensure_ascii=False,
        default=str,
        indent=2,
    )

    # 8. Keep conversational/general intents local.
    local_only_intents = (
        "greeting",
        "project_overview",
        "out_of_scope",
    )

    if intent in local_only_intents:
        answer = fallback_answer
        generation_mode = "local"

    else:
        # 9. Generate a grounded answer.
        answer = generate_answer(
            question=question,
            evidence_context=evidence_context,
            fallback_answer=fallback_answer,
        )

        generation_mode = (
            "gemini"
            if answer != fallback_answer
            else "local_fallback"
        )

    return {
        **common_result,
        "answer": answer,
        "generation_mode": generation_mode,
    }
