"""Deterministic Inspection File Generator (T-VE-03) - Print-Ready & Contract-Compliant.

Generates formal ACUD inspection briefings for R7 compounds using audited
facts, satellite KPIs, and statutory rules. Operates deterministically without
requiring an LLM, fulfilling the core requirement that the workflow operates
reliably offline.

Pipeline Integration Features:
1. Four Mandatory Report Sections:
   - ماذا حدث (What happened): Chronological facts, register parameters, and KPIs.
   - سبب التصنيف (Why: the stored level reason, no causal claims).
   - ما يعنيه ذلك (What it means): Priority level determination and operational risk.
   - خطة العمل (What we do): Specific action, owner, due date, and escalation trigger.
2. Hand-off Contract with Track A (T-AH-15):
   - Graceful fallback for satellite imagery: renders image box if available, or
     transparently marks 'missing_image' pending from AH-15.
3. Operational Complaints Summary:
   - Displays complaint counts filtered before cutoff, labeled 'generated simulation'.
4. Print-Ready A4 / PDF Styling:
   - Official ACUD header, print media stylesheets, avoiding page-break splits.
"""

import contextlib
import sys
from pathlib import Path

module_root = Path(__file__).resolve().parent.parent.parent
if str(module_root) not in sys.path:
    sys.path.insert(0, str(module_root))

from datetime import datetime
from typing import Any

from src.inference.tools import build_inspection_context

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(OSError, ValueError):
        sys.stdout.reconfigure(encoding="utf-8")


def generate_deterministic_report(
    context: dict[str, Any],
    ai_paragraph: str | None = None,
    ai_questions: list | None = None,
    reviewer_name: str | None = None,
    model: str | None = None,
) -> str:
    """Renders a complete, professional Arabic inspection report in HTML format.

    Every sentence is built from the context fields. The reviewer is shown only when
    one is passed, and the model only when an LLM call produced the paragraph.
    """
    code = context["compound_code"]
    quarter = context["quarter"]
    facts = context["facts"]
    kpis = context["kpis"]
    complaints = context.get("complaints_summary", {"total_count": 0, "origin": "generated"})
    images = context.get("images", {"status": "missing_image"})

    level = kpis.get("level", 4)
    level_word = kpis.get("level_word_ar", f"المستوى {level}")
    reason_ar = kpis.get("reason_ar", "لا توجد أسباب مسجلة")
    k2 = kpis.get("K2_stoppage_quarters")
    k3 = kpis.get("K3_delay_months")
    k5 = kpis.get("K5_fine_eligible_months")
    activity = kpis.get("A")
    land_area = facts.get("land_area_m2")
    dev_code = facts.get("developer_code") or "غير معلن"
    first_deadline = facts.get("first_deadline")
    cutoff_date = facts.get("cutoff_date", quarter)
    cmp_count = complaints.get("total_count")

    activity_text = f"، ودرجة النشاط ({activity:.2f})" if activity is not None else ""
    if k2:
        activity_sentence = f"لم يُرصد نشاط بناء منذ ({k2:g}) ربع (K2){activity_text}"
    else:
        activity_sentence = f"لم تُسجَّل أرباع توقف (K2 = 0){activity_text}"
    if first_deadline:
        delay_sentence = f"أما موعد التسليم الأول المنشور ({first_deadline})، فمؤشر التأخير K3 = ({k3:g}) شهراً"
    else:
        delay_sentence = f"لا يوجد موعد تسليم أول منشور في بيانات الأساس، ومؤشر التأخير K3 = ({k3:g}) شهراً"
    if k5 is None:
        exposure_sentence = "لا يوجد موعد تسليم منشور لاحتساب مدة التعرض للاشتراطات (K5)"
        k5_card = "لا يوجد موعد تسليم منشور"
    else:
        exposure_sentence = f"مدة التعرض للاشتراطات K5 = ({k5:g}) شهراً، وهي مؤشر فحص أولي وليست غرامة مقدّرة"
        k5_card = f"{k5:g} شهر"
    area_sentence = f"، بمساحة أرض معتمدة ({land_area:,.0f} م²)" if land_area is not None else ""
    complaints_sentence = (
        f" كما سُجّل عدد ({cmp_count}) شكوى تشغيلية (بيانات محاكاة) واردة على المشروع حتى تاريخ الأساس."
        if cmp_count is not None
        else ""
    )

    # 1. ماذا حدث (What happened)
    what_happened = (
        f"المشروع برمز ({code}) التابع للمطور ({dev_code}) في الحي السكني R7 بالعاصمة الإدارية{area_sentence}. "
        f"استناداً إلى سجلات المتابعة عبر الأقمار الصناعية (Sentinel-2) حتى تاريخ الأساس ({cutoff_date})، "
        f"{activity_sentence}. {delay_sentence}؛ {exposure_sentence}.{complaints_sentence}"
    )

    # 2. سبب التصنيف (the stored level reason; the file states indicators, not causes)
    why_text = (
        f"<strong>سبب التصنيف:</strong> {reason_ar.rstrip('.')}.<br>"
        "يصف هذا الملف المؤشرات المرصودة فقط ولا يحدد سبب الوضع الميداني؛ ويحدده التحقق الميداني."
    )

    # 3. ما يعنيه ذلك (What it means)
    if level == 1:
        what_it_means = (
            "يصنف المشروع ضمن <strong>الأولوية الأولى (عاجلة جداً)</strong> وفق سبب التصنيف أعلاه. "
            "يتطلب تدخلاً فورياً لمراجعة حساب الضمان البنكي طبقاً للقرار 2184 وتفعيل لجان التفتيش."
        )
    elif level == 2:
        what_it_means = (
            "يصنف المشروع ضمن <strong>الأولوية الثانية (تفتيش ومعاينة ميدانية)</strong>؛ يستوجب نزول لجنة تفتيش فنية إلى الموقع "
            "خلال مدة أقصاها 14 يوماً للتحقق من موقف الأعمال بالموقع."
        )
    elif level == 3:
        what_it_means = (
            "يصنف المشروع ضمن <strong>الأولوية الثالثة (مراجعة مستندية)</strong>؛ يتطلب استدعاء ممثل المطور لتقديم الموقف "
            "التنفيذي المحدث ومراجعة تراخيص البناء وجدول التسليمات."
        )
    else:
        what_it_means = "يصنف المشروع ضمن <strong>المتابعة الروتينية (الأولوية الرابعة)</strong> مع المراقبة الدورية للأقمار في الربع القادم."

    # 4. خطة العمل المعتمدة (What we do: Action, Owner, Due Date, Escalation)
    if level in [1, 2]:
        action_plan = {
            "action": "معاينة ميدانية هندسية وحصر شامل للأعمال المنجزة على أرض الواقع بالموقع",
            "owner": "إدارة الرقابة والمتابعة الميدانية - مهندس القطاع R7",
            "due_date": "خلال 14 يوماً من تاريخ صدور التقرير",
            "escalation": "في حال ثبوت توقف الأعمال دون مبرر قانوني: إحالة الملف للشؤون القانونية وتفعيل غرامات التأخير وإخطار الحاجزين طبقاً للقرار 2184."
        }
    else:
        action_plan = {
            "action": "طلب كشف موقف تنفيذي وجدول زمني معتمد للأعمال المتبقية",
            "owner": "وحدة المتابعة المستندية وتراخيص المطورين",
            "due_date": "خلال 30 يوماً من تاريخ التكليف",
            "escalation": "عدم الرد ينقل الكمبوند تلقائياً للأولوية الثانية في دورة المتابعة القادمة."
        }

    # Embed installed map files at the rendering boundary; plain tool/model
    # context contains paths and metadata only, never image base64 payloads.
    from src.inference.imagery_html import render_imagery_html
    imagery_html = render_imagery_html(images)

    # AI Section (if injected)
    ai_section_html = ""
    if ai_paragraph and ai_questions:
        ai_title = "إيجاز الذكاء الاصطناعي" if model else "ملخص آلي من قالب حتمي"
        ai_section_html = f"""
        <div class="ai-box">
            <div class="box-title">{ai_title} وأسئلة المعاينة الميدانية:</div>
            <p class="ai-text"><strong>الملخص الفني:</strong> {ai_paragraph}</p>
            <div class="questions-title"><strong>الأسئلة الفنية المقترحة للجنة التفتيش الميداني:</strong></div>
            <ol class="questions-list">
                {"".join(f"<li>{q}</li>" for q in ai_questions)}
            </ol>
        </div>
        """

    reviewer_text = f"روجع بواسطة: {reviewer_name}" if reviewer_name else "لم تتم المراجعة بعد (not reviewed yet)"
    if model:
        footer_statement = f"مسوّدة أُعدت بالذكاء الاصطناعي — الموديل: {model} — {reviewer_text}"
    else:
        footer_statement = f"قالب حتمي، دون نموذج ذكاء اصطناعي (deterministic template, no AI model) — {reviewer_text}"

    # HTML Document with Print Stylesheet
    html_content = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>ملف تفتيش ومعاينة كمبوند {code} - العاصمة الإدارية</title>
    <style>
        @page {{
            size: A4;
            margin: 15mm 12mm 15mm 12mm;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            margin: 0;
            padding: 24px;
            direction: rtl;
        }}
        .report-card {{
            max-width: 860px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.06);
            border: 1px solid #e2e8f0;
            padding: 28px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #0284c7;
            padding-bottom: 14px;
            margin-bottom: 20px;
        }}
        .gov-logo {{
            text-align: left;
            font-size: 11px;
            color: #64748b;
            font-weight: 600;
        }}
        .title-area h1 {{
            margin: 0;
            font-size: 22px;
            color: #0f172a;
        }}
        .subtitle {{
            color: #64748b;
            font-size: 13px;
            margin-top: 4px;
        }}
        .level-badge {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }}
        .level-1 {{ background-color: #fee2e2; color: #991b1b; border: 1px solid #f87171; }}
        .level-2 {{ background-color: #fef3c7; color: #92400e; border: 1px solid #fbbf24; }}
        .level-3 {{ background-color: #e0f2fe; color: #075985; border: 1px solid #7dd3fc; }}
        .level-4 {{ background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }}
        
        .grid-stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
        }}
        .stat-val {{
            font-size: 18px;
            font-weight: bold;
            color: #0284c7;
        }}
        .stat-lbl {{
            font-size: 11.5px;
            color: #64748b;
            margin-top: 2px;
        }}
        
        .section-box {{
            margin-bottom: 16px;
            padding: 14px 16px;
            border-radius: 8px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-right: 4px solid #0284c7;
            page-break-inside: avoid;
        }}
        .section-title {{
            font-weight: bold;
            font-size: 15px;
            margin-bottom: 6px;
            color: #0f172a;
        }}
        .section-content {{
            font-size: 13.5px;
            line-height: 1.7;
            color: #334155;
        }}
        
        .imagery-box {{
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 16px;
            page-break-inside: avoid;
        }}
        .imagery-box.placeholder {{
            background: #fafaf9;
            border: 1px dashed #a8a29e;
        }}
        .imagery-title {{
            font-weight: bold;
            font-size: 13.5px;
            color: #334155;
            margin-bottom: 8px;
        }}
        .placeholder-msg {{
            font-size: 12.5px;
            color: #57534e;
            line-height: 1.6;
        }}
        
        .plan-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
            font-size: 12.5px;
        }}
        .plan-table th, .plan-table td {{
            border: 1px solid #cbd5e1;
            padding: 7px 10px;
            text-align: right;
        }}
        .plan-table th {{
            background-color: #f1f5f9;
            color: #334155;
        }}
        
        .ai-box {{
            background: #f0fdf4;
            border: 1px solid #86efac;
            border-right: 4px solid #16a34a;
            border-radius: 8px;
            padding: 14px;
            margin: 16px 0;
            page-break-inside: avoid;
        }}
        .box-title {{
            font-weight: bold;
            color: #166534;
            font-size: 14px;
            margin-bottom: 6px;
        }}
        .questions-list {{
            margin: 6px 0 0 0;
            padding-right: 18px;
            font-size: 13px;
            color: #14532d;
        }}
        .questions-list li {{
            margin-bottom: 4px;
        }}
        
        .footer {{
            border-top: 1px solid #e2e8f0;
            margin-top: 24px;
            padding-top: 10px;
            font-size: 11px;
            color: #64748b;
            display: flex;
            justify-content: space-between;
        }}

        @media print {{
            body {{
                background-color: #ffffff;
                padding: 0;
            }}
            .report-card {{
                border: none;
                box-shadow: none;
                padding: 0;
                max-width: 100%;
            }}
            .section-box, .imagery-box, .plan-table, .ai-box {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-card">
        <div class="header">
            <div class="title-area">
                <h1>ملف تفتيش ومعاينة كمبوند {code}</h1>
                <div class="subtitle">شركة العاصمة الإدارية للتنمية العمرانية (ACUD) · قطاع الرقابة والتفتيش الميداني · الحي R7</div>
            </div>
            <div style="text-align: left;">
                <span class="level-badge level-{level}">{level_word}</span>
                <div class="gov-logo" style="margin-top: 6px;">كود المطور: {dev_code}</div>
            </div>
        </div>

        <div class="grid-stats">
            <div class="stat-card">
                <div class="stat-val">{k2:g} أرباع</div>
                <div class="stat-lbl">أرباع بلا نشاط بناء (K2)</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{k3:g} شهر</div>
                <div class="stat-lbl">تأخير التسليم (K3)</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{k5_card}</div>
                <div class="stat-lbl">مدة التعرض للاشتراطات (K5، مؤشر فحص)</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{"غير متاح" if cmp_count is None else f"{cmp_count} شكوى"}</div>
                <div class="stat-lbl">شكاوى المشترين (محاكاة)</div>
            </div>
        </div>

        <!-- 1. ماذا حدث -->
        <div class="section-box">
            <div class="section-title">1. ماذا حدث (الوقائع والمؤشرات المعتمدة)</div>
            <div class="section-content">{what_happened}</div>
        </div>

        <!-- 2. السبب والتفسير المستبعد -->
        <div class="section-box">
            <div class="section-title">2. سبب التصنيف (من مؤشرات الربع)</div>
            <div class="section-content">{why_text}</div>
        </div>

        <!-- Satellite Imagery Box (Contract with T-AH-15) -->
        {imagery_html}

        <!-- 3. ما يعنيه ذلك -->
        <div class="section-box">
            <div class="section-title">3. ما يعنيه ذلك (التصنيف والأولوية الرقابية)</div>
            <div class="section-content">{what_it_means}</div>
        </div>

        <!-- AI Generated Component (if present) -->
        {ai_section_html}

        <!-- 4. خطة العمل -->
        <div class="section-box">
            <div class="section-title">4. خطة العمل المعتمدة (ما نقوم به)</div>
            <table class="plan-table">
                <tr>
                    <th width="22%">الإجراء المعتمد</th>
                    <td>{action_plan["action"]}</td>
                </tr>
                <tr>
                    <th>الجهة المسؤولة (Owner)</th>
                    <td>{action_plan["owner"]}</td>
                </tr>
                <tr>
                    <th>التاريخ المستهدف</th>
                    <td>{action_plan["due_date"]}</td>
                </tr>
                <tr>
                    <th>محفز التصعيد القانوني</th>
                    <td>{action_plan["escalation"]}</td>
                </tr>
            </table>
        </div>

        <div class="footer">
            <div>{footer_statement}</div>
            <div>نظام SpaceEye-GeoAI · تاريخ الأساس: {cutoff_date} · وقت الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>
    </div>
</body>
</html>"""
    return html_content


def save_inspection_report(code: str, as_of_quarter: str = "2026Q3", output_dir: Path | None = None) -> Path:
    """Builds context, renders leak-free HTML report, and persists to disk."""
    if output_dir is None:
        module_root = Path(__file__).resolve().parent.parent.parent
        output_dir = module_root / "app_data" / "files"
    output_dir.mkdir(parents=True, exist_ok=True)

    ctx = build_inspection_context(code, as_of_quarter)
    html_str = generate_deterministic_report(ctx)

    out_file = output_dir / f"{code}_{as_of_quarter}_inspection.html"
    out_file.write_text(html_str, encoding="utf-8")
    print(f"Generated contract-compliant inspection report for {code} -> {out_file}")
    return out_file


if __name__ == "__main__":
    print("Testing Upgraded Contract-Compliant Inspection Template...")
    p = save_inspection_report("C07", "2026Q3")
    print(f"Successfully generated report at: {p}")
