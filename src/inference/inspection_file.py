"""Deterministic inspection-file builder and Markdown renderer.

The plain-data inputs are:
- ``kpis``: ``{"code", "quarter", "A", "K2", "K3", "K4", "K5_months",
  "K6", "level", "level_label", "level_word", "level_word_ar", "reason",
  "reason_ar", "may_be_complete", "origin", "run_id", "computed_at",
  "series": [{"quarter", "A", "K2", "K3", "K6", "level"}, ...]}``. The series
  is oldest first and unknown numbers are ``None``.
- ``facts``: ``[{"record_id", "kind", "subtype", "published_date", "detail",
  "link"}, ...]``, already cut at the requested quarter.
- ``images``: ``{"status": "missing" | "ok", "images": [{"path",
  "capture_date", "attribution"}, ...]}``.
- ``rules``: optional ``[{"article", "text"}, ...]`` legal-reference rows.
- ``llm``: optional ``{"paragraph": str, "questions": [str, str, str]}``.

No clock, network, or model call is used. Supplied generated text is isolated
in ``ai_paragraph`` and always requires review.
"""

from __future__ import annotations

import math
import re
from calendar import monthrange
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from typing import Any

from src.pipeline.kpis import LEVEL_WORD_AR

LEVEL_1_DUE_DAYS = 14
LEVEL_2_DUE_QUARTERS = 1
LEVEL_3_DUE_DAYS = 30
ROUTINE_DUE_QUARTERS = 1
WATCH_DUE_QUARTERS = 1
NOT_ASSESSABLE_DUE_QUARTERS = 1
MINIMUM_IMAGES = 6
K2_ESCALATION_QUARTERS = 4
K3_ESCALATION_MONTHS = 24
K6_ESCALATION_MONTHS = 24
COMPARISON_QUARTERS = 4

OWNER_PILLAR_LEAD = "Buildings & Facilities pillar lead"
OWNER_COMMITTEE = "inspection committee"
OWNER_OBSERVATORY = "observatory team"

_QUARTER_RE = re.compile(r"^\s*(\d{4})Q([1-4])\s*$")
_ORIGIN_MARKS = {
    "real": ("🟢 real", "🟢 حقيقي"),
    "public": ("🟢 real", "🟢 حقيقي"),
    "derived": ("🔵 derived", "🔵 مشتق"),
    "generated": ("🟠 generated", "🟠 مولد"),
}
_FORBIDDEN = (
    "distressed", "risk level", "high-risk", "completion %", "finishing %",
    "fined", "غرامة", "غرامات",
)


def _unknown(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or value.__class__.__name__ == "NAType"


def _integer(value: Any) -> int | None:
    return None if _unknown(value) else int(value)


def _month_end(year: int, month: int) -> date:
    return date(year, month, monthrange(year, month)[1])


def _quarter_end(quarter: str) -> date:
    match = _QUARTER_RE.fullmatch(str(quarter))
    if match is None:
        raise ValueError(f"Invalid quarter label: {quarter!r}")
    year, number = int(match.group(1)), int(match.group(2))
    return _month_end(year, number * 3)


def _next_quarter_end(quarter: str) -> date:
    end = _quarter_end(quarter)
    month = end.month + 3
    year = end.year + (month - 1) // 12
    return _month_end(year, (month - 1) % 12 + 1)


def _origin_marks(origin: Any) -> tuple[str, str]:
    if _unknown(origin):
        return "unknown origin", "أصل غير معروف"
    return _ORIGIN_MARKS.get(str(origin), ("unknown origin", "أصل غير معروف"))


def _state(kpis: Mapping[str, Any]) -> str:
    if kpis.get("K4") is False:
        return "not assessable"
    level = _integer(kpis.get("level"))
    if level is not None and 1 <= level <= 4:
        return str(level)
    label = str(kpis.get("level_label") or "").lower()
    for state in ("not assessable", "start unknown", "not started"):
        if state in label:
            return state
    raise ValueError("KPI level is missing or unsupported")


def _plural(value: int, singular: str, plural: str) -> str:
    return f"{value} {singular if value == 1 else plural}"


def _what_happened(kpis: Mapping[str, Any], state: str) -> dict[str, Any]:
    origin = kpis.get("origin")
    mark_en, mark_ar = _origin_marks(origin)
    a, k2 = kpis.get("A"), _integer(kpis.get("K2"))
    k3, k5, k6 = (_integer(kpis.get(key)) for key in ("K3", "K5_months", "K6"))
    a_en = "unknown" if _unknown(a) else f"{float(a):.2f}"
    a_ar = "غير معروف" if _unknown(a) else f"{float(a):.2f}"
    k2_en = "unknown" if k2 is None else _plural(k2, "quarter", "quarters")
    k2_ar = "غير معروف" if k2 is None else _plural(k2, "ربع", "أرباع")
    k3_en = "unknown" if k3 is None else _plural(k3, "month", "months")
    k3_ar = "غير معروف" if k3 is None else _plural(k3, "شهر", "أشهر")
    k6_en = "unknown" if k6 is None else _plural(k6, "month", "months")
    k6_ar = "غير معروف" if k6 is None else _plural(k6, "شهر", "أشهر")
    k5_en = "unknown" if k5 is None else _plural(k5, "month", "months")
    k5_ar = "غير معروف" if k5 is None else _plural(k5, "شهر", "أشهر")

    metrics_en = [
        f"activity score A = {a_en}",
        f"consecutive quarters without building activity = {k2_en}",
        f"months since the first announced handover date was passed = {k3_en}",
        f"months since the first known launch or promise without a confirmed observed start = {k6_en}",
        f"screening exposure of {k5_en}, not a fine" if k5 is not None else "screening exposure = unknown, not a fine",
    ]
    metrics_ar = [
        f"درجة النشاط A = {a_ar}",
        f"عدد الأرباع المتتالية دون نشاط بناء = {k2_ar}",
        f"عدد الأشهر منذ تجاوز أول موعد تسليم معلن = {k3_ar}",
        f"عدد الأشهر منذ أول إعلان إطلاق أو وعد دون بداية مرصودة مؤكدة = {k6_ar}",
        f"مدة التعرض للاشتراطات = {k5_ar}، وهي مدة كشف فقط" if k5 is not None else "مدة التعرض للاشتراطات = غير معروفة، وهي مدة كشف فقط",
    ]
    if state in {"1", "2", "3", "4"}:
        word = str(kpis.get("level_word") or "unknown")
        word_ar = str(kpis.get("level_word_ar") or LEVEL_WORD_AR[int(state)])
        prefix_en = f"priority level {state} ({word})"
        prefix_ar = f"مستوى أولوية التفتيش {state} ({word_ar})"
    else:
        word = str(kpis.get("level_word") or state)
        word_ar = str(kpis.get("level_word_ar") or "غير معروف")
        prefix_en, prefix_ar = f"construction start status: {word}", f"حالة بداية التنفيذ: {word_ar}"
    return {
        "text_en": f"{prefix_en} ({mark_en}); " + "; ".join(f"{item} ({mark_en})" for item in metrics_en) + ".",
        "text_ar": f"{prefix_ar} ({mark_ar})؛ " + "؛ ".join(f"{item} ({mark_ar})" for item in metrics_ar) + ".",
        "reason": {
            "text_en": "unknown" if _unknown(kpis.get("reason")) else str(kpis.get("reason")),
            "text_ar": "غير معروف" if _unknown(kpis.get("reason_ar")) else str(kpis.get("reason_ar")),
            "origin": None if _unknown(origin) else origin,
        },
    }


def _year_over_year_series(kpis: Mapping[str, Any]) -> bool:
    series = kpis.get("series")
    if not isinstance(series, Sequence) or isinstance(series, (str, bytes)):
        return False
    labels = {str(row.get("quarter")) for row in series if isinstance(row, Mapping)}
    match = _QUARTER_RE.fullmatch(str(kpis.get("quarter")))
    return match is not None and f"{int(match.group(1)) - 1}Q{match.group(2)}" in labels


def _why(
    kpis: Mapping[str, Any], facts: Sequence[Mapping[str, Any]],
    rules: Sequence[Mapping[str, Any]] | None, state: str,
) -> dict[str, Any]:
    rejected: list[dict[str, Any]] = []
    n_images = _integer(kpis.get("n_images"))
    if state != "not assessable" and kpis.get("K4") is True and (n_images is None or n_images >= MINIMUM_IMAGES):
        # K4 is true only with at least the minimum images, so a missing count still supports the rejection
        count_en = str(n_images) if n_images is not None else f"at least {MINIMUM_IMAGES}"
        count_ar = str(n_images) if n_images is not None else f"ما لا يقل عن {MINIMUM_IMAGES}"
        rejected.append({
            "text_en": f"Poor image coverage is rejected as the explanation: {count_en} images are available in the quarter, meeting the minimum of {MINIMUM_IMAGES}.",
            "text_ar": f"يُستبعد ضعف تغطية الصور كتفسير: تتوفر {count_ar} صورة خلال الربع، وهو ما يحقق الحد الأدنى {MINIMUM_IMAGES}.",
            "basis": {"n_images": n_images, "minimum_images": MINIMUM_IMAGES},
        })
    k2 = _integer(kpis.get("K2"))
    if state != "not assessable" and k2 is not None and k2 >= 1 and _year_over_year_series(kpis):
        rejected.append({
            "text_en": f"Seasonal swing is rejected as the explanation: the comparison is year over year across {COMPARISON_QUARTERS} quarters, and K2 records {k2} consecutive quarters without building activity.",
            "text_ar": f"يُستبعد التذبذب الموسمي كتفسير: المقارنة بين سنة وسنة على {COMPARISON_QUARTERS} أرباع، ويوضح K2 مقدار {k2} أرباع متتالية دون نشاط بناء.",
            "basis": {"K2": k2, "comparison_quarters": COMPARISON_QUARTERS},
        })

    k3, k6 = _integer(kpis.get("K3")), _integer(kpis.get("K6"))
    level = _integer(kpis.get("level"))
    k3_drives = level in {1, 2, 3} and k3 is not None and k3 > 0
    k6_drives = level in {1, 2} and k6 is not None and k6 >= 13
    opened: list[dict[str, str]] = []
    if bool(kpis.get("may_be_complete")) or k3_drives or k6_drives:
        opened.append({
            "text_en": "Interior finishing is not visible from space; the visit decides.",
            "text_ar": "أعمال التشطيب الداخلي لا تظهر من الفضاء؛ الزيارة الميدانية تحدد الوضع.",
        })
    if k3_drives or k6_drives:
        opened.append({
            "text_en": "Images do not establish the cause of the handover clock; the supervisor report and visit decide.",
            "text_ar": "لا تثبت الصور سبب عدّاد موعد التسليم؛ تقرير المشرف والزيارة هما اللذان يحددان الوضع.",
        })
    return {
        "evidence": [fact.get("record_id") for fact in facts],
        "evidence_details": [{"record_id": fact.get("record_id"), "link": fact.get("link")} for fact in facts],
        "rejected_explanations": rejected,
        "open_explanations": opened,
        "rule_articles": [{"article": str(row.get("article"))} for row in (rules or []) if not _unknown(row.get("article"))],
    }


def _meaning(state: str) -> dict[str, str]:
    first = {
        "1": ("Priority level 1: visit first.", "مستوى أولوية التفتيش 1: الزيارة أولًا."),
        "2": ("Priority level 2: visit within this cycle.", "مستوى أولوية التفتيش 2: الزيارة خلال هذه الدورة."),
        "3": ("Priority level 3: request the supervisor report before deciding on a visit.", "مستوى أولوية التفتيش 3: طلب تقرير المشرف قبل اتخاذ قرار الزيارة."),
        "4": ("Priority level 4: routine monitoring in the next cycle.", "مستوى أولوية التفتيش 4: متابعة روتينية في الدورة التالية."),
        "not started": ("Construction start is not confirmed; watch through the next cycle.", "بداية التنفيذ غير مؤكدة؛ المتابعة حتى الدورة التالية."),
        "start unknown": ("The construction start is unknown; watch and collect evidence.", "بداية التنفيذ غير معروفة؛ المتابعة وجمع الأدلة."),
        "not assessable": ("The quarter is not assessable; fix the location or images first.", "الربع غير قابل للتقييم؛ إصلاح الموقع أو الصور أولًا."),
    }
    return {
        "text_en": f"{first[state][0]} The system recommends; the inspection committee decides.",
        "text_ar": f"{first[state][1]} يوصي النظام، وتقرر لجنة التفتيش.",
    }


def _action(state: str) -> dict[str, str]:
    action = {
        "1": ("Visit within two weeks and inform the Buildings & Facilities pillar lead.", "إجراء زيارة خلال أسبوعين وإعلام جهة «عمود المباني والخدمات»."),
        "2": ("Visit within the current cycle.", "إجراء زيارة خلال الدورة الحالية."),
        "3": ("Request the supervisor report.", "طلب تقرير المشرف."),
        "4": ("Continue routine monitoring in the next cycle.", "استمرار المتابعة الروتينية في الدورة التالية."),
        "not started": ("Watch the compound through the next cycle.", "متابعة المركب حتى الدورة التالية."),
        "start unknown": ("Watch and collect evidence before the next recomputation.", "المتابعة وجمع الأدلة قبل إعادة الحساب التالية."),
        "not assessable": ("Fix the location or images first.", "إصلاح الموقع أو الصور أولًا."),
    }
    return {"text_en": action[state][0], "text_ar": action[state][1]}


def _escalation(state: str, origin: Any) -> dict[str, str]:
    mark_en, mark_ar = _origin_marks(origin)
    threshold_en = f"if K2 reaches {K2_ESCALATION_QUARTERS} quarters ({mark_en}) or K3 passes {K3_ESCALATION_MONTHS} months ({mark_en}), reassess as priority level 1."
    threshold_ar = f"إذا بلغ K2 مقدار {K2_ESCALATION_QUARTERS} أرباع ({mark_ar}) أو تجاوز K3 مقدار {K3_ESCALATION_MONTHS} شهرًا ({mark_ar})، تُعاد الحالة إلى مستوى أولوية التفتيش 1."
    if state == "1":
        text_en = "If the visit is not completed by the due date, inform the Buildings & Facilities pillar lead."
        text_ar = "إذا لم تكتمل الزيارة بحلول تاريخ الاستحقاق، تُعلم جهة «عمود المباني والخدمات»."
    elif state in {"2", "3"}:
        item = "visit" if state == "2" else "supervisor report"
        item_ar = "الزيارة" if state == "2" else "تقرير المشرف"
        text_en = f"If the {item} is not completed by the due date, inform the Buildings & Facilities pillar lead; {threshold_en}"
        text_ar = f"إذا لم تكتمل {item_ar} بحلول تاريخ الاستحقاق، تُعلم جهة «عمود المباني والخدمات»؛ {threshold_ar}"
    elif state == "4":
        text_en, text_ar = threshold_en, threshold_ar
    elif state == "not started":
        text_en = f"If K3 passes {K3_ESCALATION_MONTHS} months ({mark_en}) or K6 passes {K6_ESCALATION_MONTHS} months ({mark_en}), reassess as priority level 1."
        text_ar = f"إذا تجاوز K3 مقدار {K3_ESCALATION_MONTHS} شهرًا ({mark_ar}) أو تجاوز K6 مقدار {K6_ESCALATION_MONTHS} شهرًا ({mark_ar})، تُعاد الحالة إلى مستوى أولوية التفتيش 1."
    elif state == "start unknown":
        text_en = "After the location or image gaps are resolved, recompute the priority level; " + threshold_en
        text_ar = "بعد معالجة فجوات الموقع أو الصور، يُعاد حساب مستوى الأولوية؛ " + threshold_ar
    else:
        text_en, text_ar = "Once the location or image coverage is fixed, recompute the priority level.", "بعد إصلاح الموقع أو تغطية الصور، يُعاد حساب مستوى الأولوية."
    return {"text_en": text_en, "text_ar": text_ar}


def _all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [text for item in value.values() for text in _all_strings(item)]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [text for item in value for text in _all_strings(item)]
    return []


def build_inspection_file(
    kpis: Mapping[str, Any], facts: Sequence[Mapping[str, Any]],
    images: Mapping[str, Any] | None = None, rules: Sequence[Mapping[str, Any]] | None = None,
    llm: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic, bilingual inspection file without any model call."""
    if not isinstance(kpis, Mapping) or not isinstance(facts, Sequence) or isinstance(facts, (str, bytes)):
        raise TypeError("kpis must be a mapping and facts must be a sequence")
    _ = images
    state = _state(kpis)
    quarter = str(kpis.get("quarter"))
    end = _quarter_end(quarter)
    due = end + timedelta(days=LEVEL_1_DUE_DAYS if state == "1" else LEVEL_3_DUE_DAYS if state == "3" else 0)
    if state not in {"1", "3"}:
        due = _next_quarter_end(quarter)
    ai_paragraph = None
    if llm is not None:
        ai_paragraph = {
            "text": str(llm.get("paragraph") or ""), "status": "draft - needs review",
            "questions": [str(question) for question in llm.get("questions") or []],
        }
    result = {
        "code": kpis.get("code"), "quarter": quarter, "origin": kpis.get("origin"), "run_id": kpis.get("run_id"),
        "sections": {
            "what_happened": _what_happened(kpis, state),
            "why": _why(kpis, facts, rules, state),
            "what_it_means": _meaning(state),
            "what_we_do": {
                "action": _action(state),
                "owner_role": OWNER_COMMITTEE if state in {"1", "2", "3", "4"} else OWNER_OBSERVATORY,
                "due_date": due.isoformat(),
                "escalation_trigger": _escalation(state, kpis.get("origin")),
            },
        },
        "evidence_ids": [fact.get("record_id") for fact in facts],
        "ai_paragraph": ai_paragraph,
        "language": {"committee": "ar", "log": "en"},
    }
    output = " ".join(_all_strings(result)).lower()
    forbidden = next((term for term in _FORBIDDEN if term in output), None)
    if forbidden is not None:
        raise ValueError(f"Forbidden output wording: {forbidden}")
    return result


def render_markdown(file: Mapping[str, Any], lang: str = "ar") -> str:
    """Render a committee-readable Arabic file or an English log version."""
    if lang not in {"ar", "en"}:
        raise ValueError("lang must be 'ar' or 'en'")
    suffix = "ar" if lang == "ar" else "en"
    sections = file["sections"]
    what, why, meaning, what_we_do = sections["what_happened"], sections["why"], sections["what_it_means"], sections["what_we_do"]
    if lang == "ar":
        title, happened, why_heading = "# ملف تفتيش", "## ما حدث", "## لماذا"
        evidence_heading, rejected_heading, opened_heading = "### الأدلة", "### تفسيرات مستبعدة", "### تفسيرات مفتوحة"
        meaning_heading, action_heading = "## ما الذي يعنيه ذلك", "## ما سنفعله"
        labels = ("الإجراء: ", "الدور المسؤول: ", "تاريخ الاستحقاق: ", "شرط التصعيد: ")
    else:
        title, happened, why_heading = "# Inspection file", "## What happened", "## Why"
        evidence_heading, rejected_heading, opened_heading = "### Evidence", "### Rejected explanations", "### Open explanations"
        meaning_heading, action_heading = "## What it means", "## What we do"
        labels = ("Action: ", "Owner role: ", "Due date: ", "Escalation trigger: ")
    links = {item["record_id"]: item.get("link") for item in why.get("evidence_details", [])}
    evidence = "\n".join(f"- {record_id}: {links.get(record_id) or 'link unavailable'}" for record_id in why.get("evidence", []))
    rejected = "\n".join(f"- {item['text_' + suffix]}" for item in why.get("rejected_explanations", []))
    opened = "\n".join(f"- {item['text_' + suffix]}" for item in why.get("open_explanations", []))
    reason = what.get("reason", {}).get(f"text_{suffix}", "")
    parts = [
        f"{title} {file.get('code')} — {file.get('quarter')}", happened, what[f"text_{suffix}"], reason,
        why_heading, evidence_heading, evidence, rejected_heading, rejected, opened_heading, opened,
        meaning_heading, meaning[f"text_{suffix}"], action_heading,
        f"{labels[0]}{what_we_do['action']['text_' + suffix]}",
        f"{labels[1]}{what_we_do['owner_role']}",
        f"{labels[2]}{what_we_do['due_date']}",
        f"{labels[3]}{what_we_do['escalation_trigger']['text_' + suffix]}",
    ]
    ai_paragraph = file.get("ai_paragraph")
    if ai_paragraph:
        parts.extend(["## مسودة الفقرة", str(ai_paragraph.get("text", ""))])
        parts.extend(f"- {question}" for question in ai_paragraph.get("questions", []))
        parts.append("Drafted by AI, reviewed by [name]")
    return "\n\n".join(part for part in parts if part).strip() + "\n"
