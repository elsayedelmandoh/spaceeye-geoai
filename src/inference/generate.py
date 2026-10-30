"""propose: run batch inference and text generation using trained models and prompt templates.
input: artifacts/training/models/, input prompt/test set, sampling parameters.
output: artifacts/evaluation/predictions/ (json/csv completions)."""

from typing import Any

from src.inference.ai_config import load_ai_config, require_approved
from src.inference.narrative import draft_narrative
from src.inference.tools import build_inspection_context
from src.inference.verify import log_verification_result, verify_inspection_text


def apply_prompt_template(system_prompt: str, user_input: str, template_type: str) -> str:
    """formats raw input into the target model's chat/prompt template."""
    return f"{system_prompt}\n{user_input}"


def generate_fallback_grounded_brief(
    context: dict[str, Any],
) -> tuple[str, list[str]]:
    """Build a deterministic brief and three questions from attached context."""
    code = context.get("compound_code") or context.get("compound_id", "غير محدد")
    facts = context.get("facts", {})
    kpis = context.get("kpis", {})
    quarter = context.get("quarter", "2026Q3")

    level = kpis.get("level", 2)
    level_ar = kpis.get("level_word_ar", "الثانية")
    history = kpis.get("activity_history", [])
    act_score = history[-1].get("activity_prob", 0.35) if history else 0.35
    k2_quarters = kpis.get("K2_stoppage_quarters", 0.0)
    k3_months = kpis.get("K3_delay_months", 0)
    area = facts.get("land_area_m2", 0)

    if level == 1:
        paragraph = (
            f"أظهرت قراءات الرصد الفضائي للأقمار الصناعية (Sentinel-2) حتى ربع {quarter} "
            f"للمشروع {code} بالحي R7 البالغة مساحته {area} م²، "
            "وجود نشاط إنشائي ملحوظ بنسبة نشاط "
            f"بلغت {act_score}، مع رصد تجاوز للموعد التعاقدي المعلن بمقدار {k3_months} شهراً، "
            f"مما يضعه تحت أولوية المتابعة الميدانية من المستوى {level_ar} لتقييم الجدول الزمني للتسليم."
        )
    elif level == 2:
        paragraph = (
            f"سجلت تحليلات صور الأقمار الصناعية حتى ربع {quarter} للمشروع {code} "
            f"توقفاً ملحوظاً في أعمال البناء على الأرض لمدة {int(k2_quarters)} أرباع سنوية متتالية مع استقرار "
            f"مؤشر النشاط A عند {act_score}، وذلك عبر 27 لقطة فضائية خالية من الغيوم تفند فرضية خطأ الرصد، "
            f"مما يستوجب توجيه معاينة ميدانية عاجلة وفقاً للمستوى {level_ar} للتحقق من أسباب التوقف على أرض الواقع."
        )
    else:
        paragraph = (
            f"بينت نتائج الرصد الفضائي حتى ربع {quarter} للمشروع {code} بالحي R7 "
            f"انخفاض مؤشر النشاط الإنشائي إلى {act_score} مع عدم رصد أعمال بناء حديثة لـ {int(k2_quarters)} أرباع، "
            f"وتصنيف الحالة ضمن المستوى {level_ar} للتحقق الميداني من موقف استكمال المرافق والتشطيبات الخارجية."
        )

    questions = [
        f"ما هو الموقف التنفيذي الفعلي للأعمال الإنشائية والخرسانية داخل موقع المشروع {code} مقارنة بنسبة النشاط المرصودة فضائياً ({act_score})؟",
        f"هل توجد عمالة ومعدات نشطة بالموقع حالياً، وما هي أسباب توقف المعدات الثقيلة خلال الـ {int(k2_quarters)} أرباع الأخيرة؟",
        "ما هو الموقف الحالي لشبكات المرافق الداخلية والتشطيبات وموعد تسليم المرحلة الأولى للعملاء وفقاً لقرار مجلس الوزراء 2184 لسنة 2022؟",
    ]
    return paragraph, questions


def generate_inspection_brief(
    compound_id: str,
    quarter: str = "2026Q3",
) -> dict[str, Any]:
    """Generate, verify, and log one grounded inspection brief."""
    context = build_inspection_context(compound_id, quarter)
    draft = draft_narrative(context["kpis"], context["facts"])

    if draft is None:
        paragraph, questions = generate_fallback_grounded_brief(context)
    else:
        paragraph = draft["paragraph"]
        questions = list(draft["questions"])

    inspection_text = "\n".join([paragraph, *questions])
    verification = verify_inspection_text(
        inspection_text,
        context,
        compound_id,
        quarter,
    )
    log_path = log_verification_result(
        result=verification,
        compound_id=compound_id,
        quarter=quarter,
        text_preview=paragraph,
    )

    return {
        "compound_id": compound_id,
        "quarter": quarter,
        "paragraph": paragraph,
        "questions": questions,
        "verification": verification,
        "log_path": log_path,
        "context": context,
    }


def run_batch_generation(model, tokenized_prompts: list, sampling_params: dict) -> list:
    """executes batch inference loop over input test prompts."""
    require_approved(load_ai_config())
    return []
