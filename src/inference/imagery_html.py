"""Embed installed attributed map figures only at HTML rendering time, never in model context."""

import base64
from html import escape
from urllib.parse import urlsplit

from src.pipeline.common import APP
from src.pipeline.portable_io import relative_file


def render_imagery_html(images):
    cards = []
    for row in images.get("images", []) if images.get("status") == "available" else []:
        try:
            path = (APP / relative_file(str(row.get("path", "")))).resolve()
        except ValueError:
            continue
        if not path.is_relative_to(APP.resolve()) or path.suffix.lower() not in {".jpg", ".jpeg", ".png"} or not path.is_file():
            continue
        data = path.read_bytes()
        mime = "image/png" if data.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg" if data.startswith(b"\xff\xd8") else None
        if mime is None:
            continue
        date = row.get("capture_date")
        if not date:
            dates = row.get("capture_dates") or []
            date = " / ".join(dates) + " (mixed capture dates)" if dates else "Capture date unavailable"
        attribution = escape(str(row.get("attribution") or "Source attribution unavailable"))
        source = str(row.get("source_url") or "")
        source_link = f'<a href="{escape(source, quote=True)}">Source item</a>' if urlsplit(source).scheme == "https" else ""
        age = row.get("capture_age_months_at_asof")
        age_caption = (f' (latest capture {escape(str(age))} completed months before as-of '
                       f'{escape(str(row.get("asof_date") or "configured quarter"))})') if age is not None else ""
        cards.append('<figure style="margin:0;break-inside:avoid">'
                     f'<img class="sat-img" alt="{escape(str(row.get("image_type") or "Observed image"))}" '
                     f'src="data:{mime};base64,{base64.b64encode(data).decode()}">'
                     f'<figcaption class="img-caption" dir="ltr">Capture: {escape(str(date))}{age_caption}; '
                     f'release: {escape(str(row.get("release_date") or "Unknown"))}<br>{attribution} {source_link}</figcaption></figure>')
    if not cards:
        return ('<div class="imagery-box placeholder"><div class="imagery-title">Observed imagery</div>'
                '<p>Imagery files are not installed, or no dated release is available by this cutoff. '
                'Install the T-AH-15 imagery snapshot; no image is fabricated.</p></div>')
    return ('<div class="imagery-box"><div class="imagery-title">Observed imagery timeline</div>'
            '<p dir="ltr">Static attributed map context; working boundary, not a legal survey or finishing measurement.</p>'
            '<div class="imagery-grid">' + ''.join(cards) + '</div></div>')
