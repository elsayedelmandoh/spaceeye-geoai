"""Render guarded Arabic inspection reports and prepare local presentation files.

The HTML is self-contained and can be printed to A4 PDF with a browser's
``Print to PDF`` command. No PDF dependency or external browser invocation is
required. Reports with embedded imagery stay on the local machine.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from src.inference.ai_config import load_ai_config
from src.inference.imagery_html import render_imagery_html
from src.inference.inspection_file import build_inspection_file
from src.inference.narrative import draft_narrative
from src.inference.tools import get_facts, get_images, get_kpis
from src.inference.verifier import append_log, summarize, verify_text

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "app_data" / "files"
REVIEWER_PLACEHOLDER = "[اسم المراجع / reviewer name]"
SYNTHETIC_MARK = "Synthetic - for training only"


def _escaped(value: object, fallback: str = "") -> str:
    """Escape one display value and preserve an explicit unknown state."""
    if value is None:
        text = fallback
    else:
        text = str(value)
    return escape(text, quote=True)


def _mapping(value: object) -> Mapping[str, Any]:
    """Return a mapping view for a report subsection."""
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[Any]:
    """Return a list view without treating strings as sequences of items."""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _localised_text(value: object, fallback: str = "غير معروف") -> str:
    """Return Arabic text from a bilingual mapping, with an English fallback."""
    item = _mapping(value)
    text = item.get("text_ar") or item.get("text_en")
    return str(text) if text else fallback


def _safe_link(value: object) -> str | None:
    """Allow only complete HTTP(S) links in evidence references."""
    if value is None:
        return None
    url = str(value).strip()
    parsed = urlsplit(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return url
    return None


def _missing_images_html() -> str:
    """Return the explicit bilingual unavailable-image notice."""
    return (
        '<div class="image-notice" role="note">'
        "<strong>الصور غير متاحة.</strong> "
        "<span dir=\"ltr\">Images are unavailable; no image is fabricated.</span>"
        "</div>"
    )


def _metadata_images_html(images: Mapping[str, Any]) -> str:
    """Render share-safe image metadata without embedding pixels."""
    rows = [item for item in _sequence(images.get("images")) if isinstance(item, Mapping)]
    if not rows:
        return _missing_images_html()
    cards: list[str] = []
    for row in rows:
        cards.append(
            "<li>"
            f"<span class=\"label\">المسار:</span> <code dir=\"ltr\">{_escaped(row.get('path'))}</code><br>"
            f"<span class=\"label\">تاريخ الالتقاط:</span> {_escaped(row.get('capture_date'), 'غير معروف')}<br>"
            f"<span class=\"label\">الإسناد:</span> {_escaped(row.get('attribution'), 'غير متاح')}"
            "</li>"
        )
    return (
        '<div class="image-metadata"><h3>بيانات الصور (بدون تضمين البكسلات)</h3>'
        f"<ul>{''.join(cards)}</ul></div>"
    )


def _images_html(images: dict | None) -> str:
    """Render imagery through the existing local renderer when requested."""
    if not isinstance(images, Mapping):
        return _missing_images_html()
    if images.get("_metadata_only"):
        return _metadata_images_html(images)
    status = str(images.get("status") or "").casefold()
    if status not in {"ok", "available"}:
        return _missing_images_html()
    payload = dict(images)
    payload["status"] = "available"
    rendered = render_imagery_html(payload)
    if "data:image" not in rendered:
        return rendered + _missing_images_html()
    return rendered


def _evidence_html(file: Mapping[str, Any]) -> str:
    """Render evidence identifiers, details, and safe source links."""
    sections = _mapping(file.get("sections"))
    why = _mapping(sections.get("why"))
    details = [item for item in _sequence(why.get("evidence_details")) if isinstance(item, Mapping)]
    facts = [item for item in _sequence(file.get("facts")) if isinstance(item, Mapping)]
    facts_by_id = {
        str(item.get("record_id")): item
        for item in facts
        if item.get("record_id") is not None
    }
    evidence_ids = _sequence(why.get("evidence"))
    if not evidence_ids:
        evidence_ids = _sequence(file.get("evidence_ids"))
    entries: list[str] = []
    for raw_id in evidence_ids:
        record_id = str(raw_id)
        detail_item = facts_by_id.get(record_id, {})
        linked_item = next(
            (item for item in details if str(item.get("record_id")) == record_id),
            {},
        )
        link = _safe_link(linked_item.get("link") or detail_item.get("link"))
        link_html = (
            f' — <a href="{_escaped(link)}" rel="noopener noreferrer" '
            f'dir="ltr">{_escaped(link)}</a>'
            if link
            else " — رابط غير متاح"
        )
        detail = detail_item.get("detail")
        detail_html = f"<p>{_escaped(detail)}</p>" if detail else ""
        entries.append(
            f'<li><strong>{_escaped(record_id)}</strong>{link_html}{detail_html}</li>'
        )
    if not entries:
        return "<p>لا توجد أدلة منشورة متاحة لهذا الربع.</p>"
    return f'<ul class="evidence-list">{"".join(entries)}</ul>'


def _explanations_html(items: object) -> str:
    """Render a list of bilingual explanations."""
    entries = [item for item in _sequence(items) if isinstance(item, Mapping)]
    if not entries:
        return "<p>لا توجد تفسيرات إضافية في هذا الربع.</p>"
    rendered = [
        f"<li>{_escaped(_localised_text(item))}</li>"
        for item in entries
    ]
    return f'<ul>{"".join(rendered)}</ul>'


def _verification_html(verification: dict | None) -> str:
    """Render verifier verdict counts when a summary is supplied."""
    if not isinstance(verification, Mapping) or not verification:
        return ""
    items = [
        f"<li>{_escaped(key)}: {_escaped(value)}</li>"
        for key, value in verification.items()
    ]
    return (
        '<section class="section verification"><h2>ملخص التحقق</h2>'
        f'<ul>{"".join(items)}</ul></section>'
    )


def render_report_html(
    file: dict,
    *,
    generated_at: str,
    model: str | None,
    reviewer: str | None = None,
    images: dict | None = None,
    verification: dict | None = None,
) -> str:
    """Render one self-contained RTL Arabic inspection report.

    Every value taken from ``file`` is HTML-escaped. Optional draft text is
    shown only in a labelled review block. When ``images`` is supplied with an
    available status, the existing imagery renderer embeds attributed pixels;
    such output is local-only and must not be published or committed.
    """
    sections = _mapping(file.get("sections"))
    what_happened = _mapping(sections.get("what_happened"))
    why = _mapping(sections.get("why"))
    meaning = _mapping(sections.get("what_it_means"))
    what_we_do = _mapping(sections.get("what_we_do"))
    action = _mapping(what_we_do.get("action"))
    escalation = _mapping(what_we_do.get("escalation_trigger"))
    reason = _mapping(what_happened.get("reason"))

    ai_paragraph = _mapping(file.get("ai_paragraph"))
    has_ai_draft = bool(ai_paragraph)
    reviewer_value = reviewer.strip() if isinstance(reviewer, str) and reviewer.strip() else REVIEWER_PLACEHOLDER
    reviewer_display = _escaped(reviewer_value)

    draft_html = ""
    if has_ai_draft:
        questions = [
            str(question)
            for question in _sequence(ai_paragraph.get("questions"))
            if str(question).strip()
        ]
        question_html = (
            '<ol class="questions">'
            + "".join(f"<li>{_escaped(question)}</li>" for question in questions)
            + "</ol>"
            if len(questions) == 3
            else ""
        )
        draft_html = (
            '<section class="section ai-draft"><h2>مسودة الذكاء الاصطناعي — تحتاج إلى مراجعة</h2>'
            '<p class="draft-label" dir="ltr"><strong>AI draft</strong> — needs review</p>'
            f'<p class="draft-paragraph">{_escaped(ai_paragraph.get("text"))}</p>'
            f"{question_html}"
            f'<p class="synthetic">{SYNTHETIC_MARK}</p>'
            "</section>"
        )

    origin = _escaped(file.get("origin"), "غير معروف")
    run_id = _escaped(file.get("run_id"), "غير معروف")
    origin_is_generated = str(file.get("origin") or "").casefold() in {
        "generated",
        "synthetic",
    }
    synthetic_line = f'<p class="synthetic">{SYNTHETIC_MARK}</p>' if origin_is_generated else ""

    if has_ai_draft:
        provenance = (
            '<div class="provenance">'
            f"<p><strong>النموذج:</strong> <span dir=\"ltr\">{_escaped(model, 'غير متاح')}</span></p>"
            f"<p><strong>وقت الإعداد:</strong> <span dir=\"ltr\">{_escaped(generated_at)}</span></p>"
            "</div>"
        )
    else:
        provenance = (
            '<div class="provenance">'
            "<p>تم تعبئة الملف بواسطة كود ثابت دون استخدام نموذج.</p>"
            '<p dir="ltr">Filled by code without a model.</p>'
            "</div>"
        )

    if has_ai_draft:
        footer_statement = (
            f"<p>مسوّدة أُعدت بالذكاء الاصطناعي، روجعت بواسطة: {reviewer_display}</p>"
            f'<p dir="ltr">Drafted by AI, reviewed by {reviewer_display}</p>'
        )
    else:
        footer_statement = (
            f"<p>أُعدّ الملف بواسطة كود، ثم روجع بواسطة: {reviewer_display}</p>"
            f'<p dir="ltr">Prepared by code, reviewed by {reviewer_display}</p>'
        )

    css = """
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    body { margin: 0; background: #f4f6f8; color: #17212b; font-family: Tahoma, Arial, sans-serif; line-height: 1.75; }
    main { width: min(100%, 210mm); margin: 24px auto; padding: 14mm 16mm; background: #fff; box-shadow: 0 2px 14px #0002; }
    h1, h2, h3 { line-height: 1.4; color: #123a5a; }
    h1 { font-size: 1.65rem; margin-top: 0; }
    h2 { font-size: 1.25rem; border-bottom: 2px solid #c8d6e2; padding-bottom: 0.25rem; margin-top: 0; }
    h3 { font-size: 1.05rem; }
    .meta, .lineage, .provenance { color: #445463; font-size: 0.92rem; }
    .section { margin: 1.2rem 0; padding: 1rem 1.1rem; border: 1px solid #d6dee5; border-radius: 8px; break-inside: avoid; }
    .section p { margin: 0.45rem 0; }
    .ai-draft { border: 2px dashed #9a6b00; background: #fffaf0; }
    .draft-label { color: #7a5200; font-weight: 700; }
    .draft-paragraph { font-size: 1.05rem; }
    .questions { padding-inline-start: 1.6rem; }
    .synthetic { direction: ltr; text-align: left; font-weight: 700; color: #7a3d00; }
    .k5-note { background: #eef5fb; padding: 0.65rem; border-inline-start: 4px solid #39779e; }
    .decision { font-weight: 700; color: #244f35; }
    .evidence-list li, .image-metadata li { margin-bottom: 0.65rem; overflow-wrap: anywhere; }
    .label { font-weight: 700; }
    .image-notice { padding: 0.75rem; background: #fff4e5; border: 1px solid #e3b872; border-radius: 6px; }
    .image-metadata { margin: 0.8rem 0; }
    .imagery-box, .sat-img { max-width: 100%; }
    .sat-img { height: auto; display: block; margin: 0.5rem 0; }
    .img-caption { font-size: 0.85rem; color: #4b5563; }
    footer { margin-top: 1.5rem; padding: 1rem; border-top: 3px double #657786; font-size: 0.9rem; }
    footer p { margin: 0.25rem 0; }
    @page { size: A4; margin: 14mm; }
    @media print {
      body { background: #fff; font-size: 10.5pt; }
      main { width: auto; margin: 0; padding: 0; box-shadow: none; }
      .section { border-color: #bbb; }
      a { color: #000; }
    }
    """

    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ملف تفتيش {_escaped(file.get('code'))} — {_escaped(file.get('quarter'))}</title>
<style>{css}</style>
</head>
<body>
<main>
<header>
  <h1>ملف تفتيش المركب {_escaped(file.get('code'))}</h1>
  <p class="meta">الربع: <span dir="ltr">{_escaped(file.get('quarter'))}</span></p>
  <p class="lineage">سلسلة المصدر: الأصل: <span dir="ltr">{origin}</span> — معرّف التشغيل: <span dir="ltr">{run_id}</span></p>
  {synthetic_line}
</header>

<section class="section">
  <h2>ما حدث</h2>
  <p>{_escaped(_localised_text(what_happened))}</p>
  <p><strong>السبب:</strong> {_escaped(_localised_text(reason))}</p>
  <p class="k5-note">مدة التعرض للاشتراطات (screening exposure) هي مدة كشف فقط، ولا تمثل حكماً مالياً.</p>
</section>

<section class="section">
  <h2>لماذا</h2>
  <h3>الأدلة</h3>
  {_evidence_html(file)}
  <h3>التفسيرات المستبعدة</h3>
  {_explanations_html(why.get('rejected_explanations'))}
  <h3>التفسيرات المفتوحة</h3>
  {_explanations_html(why.get('open_explanations'))}
</section>

<section class="section">
  <h2>ما الذي يعنيه ذلك</h2>
  <p>{_escaped(_localised_text(meaning))}</p>
</section>

<section class="section">
  <h2>ما سنفعله</h2>
  <p><strong>الإجراء:</strong> {_escaped(_localised_text(action))}</p>
  <p><strong>الدور المسؤول:</strong> {_escaped(what_we_do.get('owner_role'), 'غير محدد')}</p>
  <p><strong>تاريخ الاستحقاق:</strong> <span dir="ltr">{_escaped(what_we_do.get('due_date'), 'غير معروف')}</span></p>
  <p><strong>شرط التصعيد:</strong> {_escaped(_localised_text(escalation))}</p>
</section>

{draft_html}
{_verification_html(verification)}

<section class="section">
  <h2>الصور</h2>
  {_images_html(images)}
</section>

<footer>
  {footer_statement}
  {provenance}
</footer>
</main>
</body>
</html>
"""


def _draft_with_model(
    kpis: dict,
    facts: list[dict],
    *,
    client: Any,
    budget: Any,
) -> tuple[dict | None, str | None]:
    """Return an optional draft and its model name without hidden writes."""
    try:
        config = load_ai_config()
    except (OSError, RuntimeError, TypeError, ValueError, KeyError):
        return None, None
    gemini = config.get("gemini")
    if not isinstance(gemini, Mapping):
        return None, None
    model = gemini.get("model")
    draft = draft_narrative(
        kpis,
        facts,
        client=client,
        budget=budget,
        config=config,
    )
    if not isinstance(draft, Mapping):
        return None, None
    return dict(draft), str(model) if model is not None else None


def build_report(
    code: str,
    quarter: str,
    *,
    generated_at: str,
    use_model: bool = False,
    client: Any = None,
    budget: Any = None,
    reviewer: str | None = None,
    out_dir: str | Path | None = None,
    embed_images: bool = False,
    log_path: str | Path | None = None,
) -> Path:
    """Build and write one Arabic HTML inspection report.

    The default output is the repository-local ``app_data/files`` directory.
    ``embed_images=True`` embeds attributed pixels through the existing imagery
    renderer; that output stays local and must not be published or committed.
    Verification rows are written only when ``log_path`` is explicitly supplied.
    """
    kpis = dict(get_kpis(code, quarter))
    facts = [dict(item) for item in get_facts(code, quarter)]
    images = get_images(code, quarter=quarter)

    draft: dict | None = None
    model: str | None = None
    if use_model:
        draft, model = _draft_with_model(
            kpis,
            facts,
            client=client,
            budget=budget,
        )

    inspection_file = build_inspection_file(
        kpis,
        facts,
        images=images,
        llm=draft,
    )
    inspection_file["facts"] = facts

    verification: dict | None = None
    if draft:
        file_id = f"{code}_{quarter}"
        source = {"facts": facts, "kpis": kpis}
        rows: list[dict] = []
        paragraph = draft.get("paragraph")
        if isinstance(paragraph, str) and paragraph.strip():
            rows.extend(
                verify_text(
                    paragraph,
                    source,
                    file_id=file_id,
                    kind="paragraph",
                )
            )
        for index, question in enumerate(_sequence(draft.get("questions")), start=1):
            rows.extend(
                verify_text(
                    str(question),
                    source,
                    file_id=file_id,
                    kind=f"question_{index}",
                )
            )
        verification = summarize(rows)
        if log_path is not None:
            append_log(rows, log_path, checked_on=generated_at)

    image_payload = dict(images)
    image_payload["_metadata_only"] = not embed_images
    report_html = render_report_html(
        inspection_file,
        generated_at=generated_at,
        model=model,
        reviewer=reviewer,
        images=image_payload,
        verification=verification,
    )
    target_dir = Path(out_dir) if out_dir is not None else DEFAULT_OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"{code}_{quarter}.html"
    output_path.write_text(report_html, encoding="utf-8")
    return output_path


def main(argv: Sequence[str] | None = None) -> int:
    """Build the requested reports; read the clock only when time is omitted."""
    parser = argparse.ArgumentParser(
        description="Render guarded Arabic inspection reports as local HTML files.",
        epilog="PDF output: open the HTML and use the browser's Print to PDF command.",
    )
    parser.add_argument("--quarter", required=True, help="Quarter label, for example 2026Q3.")
    parser.add_argument("--codes", nargs="+", required=True, help="Compound codes to render.")
    parser.add_argument("--generated-at", help="Fixed ISO timestamp; the current time is used when omitted.")
    parser.add_argument("--use-model", action="store_true", help="Enable the optional bounded narrative draft.")
    parser.add_argument("--reviewer", help="Explicit reviewer label shown in the footer.")
    parser.add_argument("--out-dir", help="Output directory; defaults to app_data/files.")
    args = parser.parse_args(argv)

    generated_at = args.generated_at or datetime.now(UTC).isoformat(timespec="seconds")
    written: list[Path] = []
    for code in args.codes:
        try:
            output_path = build_report(
                code,
                args.quarter,
                generated_at=generated_at,
                use_model=args.use_model,
                reviewer=args.reviewer,
                out_dir=args.out_dir,
            )
        except LookupError as error:
            print(
                f"{code}: no KPI row for {args.quarter}; skipped ({error})",
                file=sys.stderr,
            )
            continue
        written.append(output_path)
        print(f"{output_path} ({output_path.stat().st_size} bytes)")

    if not written:
        print("No inspection reports were written.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
