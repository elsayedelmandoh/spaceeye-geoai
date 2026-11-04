
from typing import Any
from datetime import datetime
import re


def _value(data: dict | None, key: str, default="غير متاح"):
    if not data:
        return default
    value = data.get(key)
    return default if value is None else value


def _origin_label(origin: Any) -> str:
    labels = {
        "real": "بيانات منشورة",
        "derived": "مؤشر محسوب",
        "synthetic": "بيانات افتراضية",
        "generated": "بيانات مولّدة",
    }
    return labels.get(str(origin).lower(), str(origin or "غير محدد"))


def _extract_fields(document: str) -> dict:
    fields = {}
    for line in document.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip().lower()] = value.strip()
    return fields


def _format_profile(profile: dict | None) -> list[str]:
    if not profile:
        return ["لا تتوفر بيانات منظمة عن المشروع."]

    fields = [
        ("developer_code", "المطور", None, None),
        ("district", "المنطقة", None, None),
        ("land_area_m2", "مساحة الأرض (متر مربع)", "land_area_origin", None),
        ("units", "عدد الوحدات", "units_origin", None),
        ("floors_allowed", "الأدوار المسموح بها", "floors_origin", None),
        ("coverage_max", "الحد الأقصى لنسبة الغطاء (%)", None, "real"),
        ("cover_pct", "نسبة الغطاء (%)", None, "derived"),
        ("bua_m2", "مساحة المباني الإجمالية (متر مربع)", None, "derived"),
    ]

    lines = []

    for key, label, origin_key, fixed_origin in fields:
        value = profile.get(key)

        if value is None:
            continue

        origin = fixed_origin

        if origin_key:
            origin = profile.get(origin_key)

        suffix = f" ({_origin_label(origin)})" if origin else ""

        if key == "coverage_max":
            value = f"{float(value) * 100:.1f}"

        lines.append(f"- {label}: {value}{suffix}")

    return lines
def _format_kpi(kpi: dict | None) -> list[str]:
    if not kpi:
        return ["لا تتوفر مؤشرات KPI للمشروع."]

    fields = [
        ("quarter", "الفترة"),
        ("level", "مستوى أولوية التفتيش"),
        ("activity_prob", "درجة نشاط البناء"),
        ("K3", "أشهر تجاوز أول موعد تسليم معلن"),
        ("K5_months", "مدة K5 المحسوبة (شهر)"),
    ]

    lines = []
    for key, label in fields:
        value = kpi.get(key)
        if value is not None:
            if key == "activity_prob":
                value = f"{float(value) * 100:.1f}%"
            lines.append(f"- {label}: {value}")

    if kpi.get("reason_ar"):
        lines.append(f"- سبب التصنيف: {kpi['reason_ar']}")

    if kpi.get("K5_basis"):
        lines.append(f"- أساس حساب K5: {kpi['K5_basis']}")

    lines.append(
        "تنبيه: مؤشرات KPI محسوبة وفق المنهجية والافتراضات المستخدمة، "
        "وليست إثباتًا مستقلًا لحالة التسليم الفعلية."
    )
    return lines



def _statement_summary(item: dict) -> dict:
    metadata = item.get("metadata") or {}
    fields = _extract_fields(item.get("document") or "")

    statement_type = fields.get("type", "").lower()
    subtype = fields.get("subtype", "").lower()
    detail = fields.get("detail", "").lower()
    value = fields.get("value", "")
    qualifier = fields.get("qualifier", "").lower()
    period = fields.get("period", "")

    if statement_type == "event":
        if subtype == "delivery_complete":
            description = (
                "حدث منشور مصنف كاكتمال تسليم "
                "وفق التصريح"
            )
        else:
            description = "حدث منشور متعلق بالمشروع"

    elif statement_type == "promise":
        if "delivery" in subtype or "delivery" in detail:
            description = "موعد التسليم المعلن للمشروع"
        elif "start" in detail:
            description = "موعد بدء المرحلة الأولى"
        else:
            description = "تصريح متعلق بموعد المشروع"

        if period and period.lower() != "none to none":
            description += f": {period}"

    elif statement_type == "progress":
        description = "نسبة التقدم المعلنة"

        if value and value.lower() != "none":
            qualifier_text = {
                "about": "حوالي",
                "over": "أكثر من",
                "exact": "",
            }.get(qualifier, "")

            description += (
                f": {qualifier_text} {value}%"
            ).strip()

    else:
        description = "تصريح منشور"

    return {
        "id": metadata.get(
            "statement_id",
            item.get("id", ""),
        ),
        "date": metadata.get("published_date", ""),
        "description": description,
        "origin": metadata.get("origin", "unknown"),
        "url": metadata.get("source_url", ""),
    }


def _format_evidence(evidence: list[dict]) -> list[str]:
    statements = []

    for item in evidence:
        metadata = item.get("metadata") or {}
        if metadata.get("document_type") == "published_statement":
            statements.append(_statement_summary(item))

    if not statements:
        return ["لم يتم العثور على تصريحات منشورة مرتبطة بالسؤال."]

    statements.sort(key=lambda item: item["date"] or "")
    lines = []

    for statement in statements:
        lines.append(
            f"- {statement['date']}: {statement['description']}"
        )
        lines.append(f"  رقم التصريح: {statement['id']}")
        lines.append(
            f"  طبيعة البيانات: {_origin_label(statement['origin'])}"
        )
        if statement["url"]:
            lines.append(f"  المصدر: {statement['url']}")

    return lines



def _format_complaints(evidence: list[dict]) -> list[str]:
    complaints = []

    channel_translation = {
        "phone": "الهاتف",
        "portal": "البوابة الإلكترونية",
        "email": "البريد الإلكتروني",
    }

    category_translation = {
        "quality": "جودة",
        "stoppage": "توقف العمل",
        "other": "أخرى",
        "delay": "تأخير",
        "payment": "السداد والمدفوعات",
    }

    for item in evidence:
        metadata = item.get("metadata") or {}

        if metadata.get("document_type") != "synthetic_complaint":
            continue

        fields = _extract_fields(item.get("document") or "")

        raw_date = fields.get("date", "")
        try:
            complaint_date = datetime.strptime(
                raw_date.split("T")[0], "%Y-%m-%d"
            ).strftime("%d-%m-%Y")
        except (ValueError, TypeError):
            complaint_date = "غير محدد"

        raw_channel = fields.get("channel", "").lower()
        raw_category = fields.get("category", "").lower()

        complaints.append({
            "id": metadata.get("complaint_id", item.get("id", "")),
            "date": complaint_date,
            "channel": channel_translation.get(
                raw_channel, raw_channel or "غير محدد"
            ),
            "category": category_translation.get(
                raw_category, raw_category or "غير محدد"
            ),
            "text": fields.get("complaint text", "نص الشكوى غير متاح"),
        })

    if not complaints:
        return ["لم يتم العثور على سجلات شكاوى مرتبطة بالسؤال."]

    lines = [
        "تنبيه: السجلات التالية افتراضية (Synthetic)، "
        "ومخصصة للاختبار والتدريب، وليست شكاوى عملاء حقيقية.",
        "",
    ]

    for complaint in complaints:
        lines.extend([
            f"- رقم الشكوى: {complaint['id']}",
            f"  التاريخ: {complaint['date']}",
            f"  قناة الاستقبال: {complaint['channel']}",
            f"  التصنيف: {complaint['category']}",
            f"  نص الشكوى: {complaint['text']}",
            "  مصدر البيانات: بيانات افتراضية",
            "",
        ])

    lines.append(
        f"عدد سجلات الشكاوى الافتراضية المسترجعة: {len(complaints)}"
    )

    return lines


def _format_visits(evidence: list[dict]) -> list[str]:
    visits = []

    result_translation = {
        "stalled": "متعثر وفق السجل الافتراضي",
        "active": "نشط وفق السجل الافتراضي",
        "progressing": "جارٍ التقدم وفق السجل الافتراضي",
        "completed": "مكتمل وفق السجل الافتراضي",
        "not_done": "لم تُنفذ الزيارة",
    }

    note_translation = {
        "visit rescheduled; no observation recorded.":
            "تمت إعادة جدولة الزيارة، ولم تُسجل أي ملاحظات ميدانية.",
    }

    for item in evidence:
        metadata = item.get("metadata") or {}

        if metadata.get("document_type") != "synthetic_visit":
            continue

        fields = _extract_fields(item.get("document") or "")

        raw_date = fields.get("visit date", "")
        try:
            visit_date = datetime.strptime(
                raw_date.split("T")[0], "%Y-%m-%d"
            ).strftime("%d-%m-%Y")
        except (ValueError, TypeError):
            visit_date = "غير محدد"

        raw_result = fields.get("result", "").strip().lower()
        result = result_translation.get(
            raw_result, raw_result or "غير محدد"
        )

        raw_note = fields.get("note", "").strip()
        normalized_note = raw_note.lower()

        if "limited recent site progress" in normalized_note:
            note = (
                "تم افتراض محدودية التقدم الميداني مؤخرًا، "
                "مع طلب تقديم المقاول خطة عمل."
            )
        elif "ongoing site progress" in normalized_note:
            note = (
                "تم افتراض استمرار التقدم في الموقع، "
                "مع التوصية بمقارنة خطة العمل بتقرير المشرف."
            )
        else:
            note = note_translation.get(
                normalized_note, raw_note or "غير متاح"
            )

        raw_basis = fields.get("state basis", "").strip().lower()

        if "not a real field measurement" in raw_basis:
            basis = (
                "حالة تقديرية تم ترحيلها من نقطة القطع السابقة، "
                "وليست قياسًا ميدانيًا حقيقيًا."
            )
        else:
            basis = fields.get("state basis", "غير متاح")

        visits.append({
            "id": metadata.get("visit_id", item.get("id", "")),
            "date": visit_date,
            "quarter": fields.get("source quarter", "غير محدد"),
            "result": result,
            "note": note,
            "basis": basis,
        })

    if not visits:
        return ["لم يتم العثور على سجلات زيارات تفتيش مرتبطة بالسؤال."]

    lines = [
        "تنبيه: سجلات الزيارات التالية افتراضية (Synthetic)، "
        "ومخصصة للاختبار والتدريب، وليست زيارات ميدانية حقيقية.",
        "",
    ]

    for visit in visits:
        lines.extend([
            f"- رقم الزيارة: {visit['id']}",
            f"  تاريخ الزيارة: {visit['date']}",
            f"  الفترة: {visit['quarter']}",
            f"  نتيجة الزيارة: {visit['result']}",
            f"  ملاحظات الزيارة: {visit['note']}",
            f"  أساس الحالة: {visit['basis']}",
            "  مصدر البيانات: بيانات افتراضية",
            "",
        ])

    lines.append(
        f"عدد سجلات الزيارات الافتراضية المسترجعة: {len(visits)}"
    )

    return lines


def _format_knowledge(evidence: list[dict]) -> list[str]:
    lines = []

    for item in evidence:
        metadata = item.get("metadata") or {}

        if metadata.get("document_type") != "external_knowledge":
            continue

        heading = metadata.get("section") or ""
        title = metadata.get("title", "")
        # Chunk text starts with the "Source document" / "Section" header lines.
        text = (item.get("document") or "").split("\n", 2)[-1].strip()
        lines.extend([
            f"### {title}" + (f" - {heading}" if heading else ""),
            text[:800],
            f"المصدر: {metadata.get('source_url') or 'غير محدد'} "
            f"({metadata.get('file_path', '')})",
            "",
        ])

    return lines or ["لم يتم العثور على مصدر مرجعي مرتبط بالسؤال."]


def _format_rules(evidence: list[dict]) -> list[str]:
    rules = []

    arabic_descriptions = {
        "R13": "حق الاسترداد عند تجاوز مدة التأخير في التسليم 24 شهرًا.",
        "R12": "مهلة سماح بعد موعد التسليم المعلن مدتها 12 شهرًا.",
        "R15": (
            "تُصدر شهادة صلاحية الإشغال من المهندس المشرف بعد إتمام الأعمال، "
            "ولا يتم توصيل المرافق قبل إصدارها."
        ),
        "R16": (
            "يجب أن تتضمن عقود البيع والإيجار رقم الترخيص "
            "وعدد الأدوار والوحدات."
        ),
        "R11": (
            "تخصيص احتياطي للاسترداد بنسبة 5% "
            "من إجمالي تحصيلات كل مرحلة."
        ),
        "R06": (
            "يتعلق بإلغاء التغطية عند مستوى تقدم معين. "
            "والملخص يذكر حدًا قدره 30% من التقدم، "
            "لكن يلزم الرجوع للنص الأصلي لتحديد المقصود بدقة."
        ),
        "R07": (
            "يتعلق بإلغاء التغطية عند بلوغ مستوى معين من تقدم الأعمال. "
            "ويشير الملخص إلى الفئة الصغيرة، "
            "لكن يلزم مراجعة النص الأصلي لتحديد الشروط بدقة."
        ),
    }

    for item in evidence:
        metadata = item.get("metadata") or {}

        if metadata.get("document_type") != "rule_summary":
            continue

        rule_id = metadata.get("rule_id", item.get("id", ""))
        fields = _extract_fields(item.get("document") or "")

        article = fields.get("article", "غير محدد")
        description = arabic_descriptions.get(
            rule_id,
            "يتوفر ملخص لهذه القاعدة، لكن وصفها يحتاج إلى مراجعة النص الأصلي."
        )

        rules.append(
            f"- {rule_id} | {article}: {description}"
        )

    if not rules:
        return ["لم يتم العثور على قواعد مرتبطة بالسؤال."]

    return [
        "تنبيه: المعلومات التالية ملخصات للقواعد وليست النصوص القانونية الأصلية.",
        "",
        *rules,
        "",
        "يجب مراجعة المصدر القانوني الأصلي قبل اتخاذ أي إجراء رسمي.",
    ]
   



def build_answer(result: dict) -> str:
    """Build a deterministic Arabic fallback answer."""

    structured = result.get("structured_data") or {}
    profile = structured.get("compound_profile")
    kpi = structured.get("latest_kpi")
    evidence = result.get("evidence") or []

    intent = result.get("intent")
    sub_intent = result.get("sub_intent")
    compound = (
        result.get("compound")
        or (profile or {}).get("code")
    )

    # Unknown project code.
    if (
        intent in ("project_info", "inspection_priority")
        and compound
        and not profile
        and not kpi
    ):
        return (
            f"كود المشروع {compound} غير موجود ضمن البيانات "
            "المنظمة المتاحة حاليًا في SpaceEye."
        )

    # Greeting, thanks, and short social acknowledgements.
    if intent == "greeting":
        query = str(result.get("query") or "").strip().lower()
        normalized = re.sub(r"[\u064B-\u065F\u0670]", "", query)
        normalized = re.sub(r"[إأآٱ]", "ا", normalized)
        for char in "؟?!.,،؛:":
            normalized = normalized.replace(char, " ")
        normalized = " ".join(normalized.split())

        thanks_phrases = (
            "شكرا", "شكرا جزيلا", "شكرا جدا", "شكرا ليك",
            "شكرا ليكي", "الف شكر", "متشكرة", "متشكرة جدا",
            "متشكر", "متشكر جدا", "تسلم", "تسلمي",
            "تسلم ايدك", "تسلم ايديك", "ربنا يخليك",
            "ممنون", "ممتن", "يعطيك العافية",
            "thanks", "thank you", "thank you so much",
            "thanks a lot", "many thanks", "appreciate it",
            "much appreciated",
        )
        acknowledgement_phrases = (
            "تمام", "تمام شكرا", "ماشي", "حلو", "جميل",
            "great", "perfect",
        )

        if any(phrase in normalized for phrase in thanks_phrases):
            return (
                "العفو، تحت أمرك! 😊\n\n"
                "لو محتاج أي معلومة عن مشروعات SpaceEye أنا معاك."
            )

        if normalized in acknowledgement_phrases:
            return "تمام، أنا معاك. 😊"

        if any(
            phrase in normalized
            for phrase in ("ازيك", "عامل ايه", "كيف حالك", "how are you")
        ):
            return (
                "الحمد لله، شكرًا لسؤالك! 😊\n\n"
                "أقدر أساعدك في إيه بخصوص مشروعات SpaceEye؟"
            )

        return (
            "أهلًا بيك! 👋\n\n"
            "أنا مساعد SpaceEye الذكي، أقدر أساعدك في "
            "بيانات ومؤشرات مشروعات التنمية العمرانية.\n\n"
            "أقدر أساعدك إزاي؟"
        )

    # SpaceEye overview.
    if intent == "project_overview":
        return "\n".join([
            "مرحبًا بك في SpaceEye.",
            "",
            "SpaceEye هو نظام لمتابعة وتحليل مشروعات "
            "التنمية العمرانية، مع التركيز على مشروعات "
            "منطقة R7 بالعاصمة الإدارية الجديدة.",
            "",
            "يتيح النظام:",
            "- عرض بيانات المشروعات والمطورين.",
            "- متابعة مؤشرات الأداء وأولوية التفتيش.",
            "- البحث في التصريحات ومواعيد التسليم المعلنة.",
            "- الاطلاع على ملخصات القواعد واللوائح المتاحة.",
            "- استعراض سجلات الشكاوى وزيارات التفتيش الافتراضية.",
            "",
            "مهم: السجلات الافتراضية ليست بيانات تشغيلية "
            "أو ميدانية حقيقية.",
        ])

    # Out of scope.
    if intent == "out_of_scope":
        return (
            "السؤال خارج نطاق المعلومات المتاحة في SpaceEye. "
            "يمكنك سؤالي عن بيانات المشروعات أو مؤشرات الأداء "
            "أو التصريحات أو القواعد أو سجلات التفتيش."
        )

    # Sourced knowledge documents.
    if intent == "knowledge":
        return "\n".join([
            "المصادر المرجعية المرتبطة بالسؤال:",
            "",
            *_format_knowledge(evidence),
        ])

    # Rules.
    if intent == "rules":
        return "\n".join([
            "القواعد واللوائح المرتبطة بالسؤال:",
            "",
            *_format_rules(evidence),
        ])

    # Complaints.
    if intent == "complaints":
        return "\n".join([
            "سجلات الشكاوى:",
            "",
            *_format_complaints(evidence),
        ])

    # Inspection visits.
    if intent == "inspection_visits":
        return "\n".join([
            "سجلات زيارات التفتيش:",
            "",
            *_format_visits(evidence),
        ])

    # Inspection priority.
    if intent == "inspection_priority":
        if not compound:
            return "من فضلك حددي كود المشروع المطلوب."

        lines = [
            f"مؤشرات أولوية التفتيش للمشروع {compound}",
            "",
            *_format_kpi(kpi),
            "",
            "ملاحظات:",
            "- المؤشرات المحسوبة تساعد في تحديد أولوية المراجعة.",
            "- لا تمثل هذه المؤشرات إثباتًا نهائيًا لحالة المشروع.",
        ]

        return "\n".join(lines)

    # Project information.
    if intent == "project_info":
        if not compound:
            return "من فضلك حددي كود المشروع المطلوب."

        lines = [
            f"ملخص المشروع {compound}",
            "",
            "أولًا: بيانات المشروع",
            *_format_profile(profile),
            "",
            "ثانيًا: مؤشرات الأداء",
            *_format_kpi(kpi),
        ]

        if sub_intent in (
            "status_inquiry",
            "delay_assessment",
            "latest_data",
        ):
            lines.extend([
                "",
                "ثالثًا: التصريحات المنشورة المرتبطة بالسؤال",
                *_format_evidence(evidence),
            ])

        if sub_intent == "performance_comparison":
            lines.extend([
                "",
                "لا تتوفر في نتيجة الاسترجاع الحالية بيانات "
                "الربع السابق اللازمة لإجراء مقارنة زمنية موثوقة.",
            ])

        if sub_intent == "delay_assessment":
            lines.extend([
                "",
                "تنبيه: تجاوز موعد تسليم معلن لا يكفي وحده "
                "لإثبات التأخير مقارنة بجدول زمني معتمد.",
            ])

        lines.extend([
            "",
            "ملاحظات مهمة:",
            "- بعض بيانات المشروع قد تكون مشتقة أو مولّدة.",
            "- أولوية التفتيش مؤشر للمراجعة وليست حكمًا نهائيًا.",
        ])

        return "\n".join(lines)

    # Published statements.
    if intent == "published_statements":
        return "\n".join([
            "التصريحات والأدلة المنشورة:",
            "",
            *_format_evidence(evidence),
            "",
            "موعد التسليم المعلن لا يثبت وحده أن المشروع "
            "لم يتم تسليمه.",
        ])

    return (
        "لم أتمكن من تحديد نوع السؤال أو العثور على "
        "إجابة مناسبة من البيانات المتاحة."
    )
