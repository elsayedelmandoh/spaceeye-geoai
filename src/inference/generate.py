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
    kpis = context["kpis"]
    quarter = context["quarter"]

    activity = kpis["A"]
    k2 = kpis["K2_stoppage_quarters"]
    k3 = kpis["K3_delay_months"]
    k5 = kpis["K5_fine_eligible_months"]
    first_deadline = facts.get("first_deadline")

    if k2:
        activity_text = f"لم يُرصد نشاط بناء منذ {k2:g} ربع (K2)، وبلغت درجة النشاط {activity:.2f}."
    else:
        activity_text = f"لم تُسجَّل أرباع توقف (K2 = 0)، وبلغت درجة النشاط {activity:.2f}."
    if k3:
        delay_text = f"تجاوز أول موعد تسليم معلن ({first_deadline}) بمقدار {k3:g} شهراً (K3)."
    elif first_deadline:
        delay_text = f"لم يتجاوز موعد التسليم المعلن ({first_deadline}) (K3 = 0)."
    else:
        delay_text = "لا يوجد موعد تسليم معلن متاح (K3 = 0)."
    if k5 is None:
        exposure_text = "لا يوجد موعد منشور لاحتساب مدة التعرض للاشتراطات (K5)."
    else:
        exposure_text = f"مدة التعرض للاشتراطات K5 = {k5:g} شهراً (مؤشر فحص وليس غرامة مقدّرة)."
    completion_text = (
        " وقد يكون مكتملًا وفق إعلان التسليم أو الغطاء النباتي؛ يلزم تحقق ميداني."
        if kpis.get("may_be_complete")
        else ""
    )

    paragraph = (
        f"بحسب مؤشرات الرصد الفضائي حتى ربع {quarter}، صُنّف المركب {code} "
        f"في المستوى {kpis['level_word_ar']}. {activity_text} {delay_text} {exposure_text}"
        f"{completion_text} هذا الملخص يصف المؤشرات فقط، ويحدد التحقق الميداني الوضع الفعلي."
    )

    questions = [
        f"ما الموقف الفعلي للأعمال الإنشائية داخل موقع المركب {code} مقارنة بدرجة النشاط المرصودة فضائياً ({activity:.2f})؟",
        "هل توجد عمالة ومعدات نشطة بالموقع حالياً، وما الأعمال الجارية فيه؟",
        "ما الموقف الحالي لشبكات المرافق الداخلية والتشطيبات وموعد تسليم المرحلة الأولى للعملاء وفقاً لقرار مجلس الوزراء 2184 لسنة 2022؟",
    ]
    return paragraph, questions


def generate_inspection_brief(
    compound_id: str,
    quarter: str = "2026Q3",
) -> dict[str, Any]:
    """Generate, verify, and log one grounded inspection brief."""
    context = build_inspection_context(compound_id, quarter)
    draft = draft_narrative(context["kpis"], context["facts"])

    model = None
    if draft is None:
        paragraph, questions = generate_fallback_grounded_brief(context)
    else:
        paragraph = draft["paragraph"]
        questions = list(draft["questions"])
        model = str(load_ai_config()["gemini"]["model"])

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
        "model": model,
        "verification": verification,
        "log_path": log_path,
        "context": context,
    }


def run_batch_generation(model, tokenized_prompts: list, sampling_params: dict) -> list:
    """executes batch inference loop over input test prompts."""
    require_approved(load_ai_config())
    return []
