"""Custom front end for screens 1 and 2: one in-page Streamlit component (st.components.v2).

The page sends a plain dict built from stored files; the component only draws it.
"""

from __future__ import annotations

import base64
import io
from collections.abc import Callable
from pathlib import Path

import streamlit as st
from PIL import Image

ASSETS = Path(__file__).with_name("front")

# Every curated Wayback frame comes from the official print renderer at this size. The top band
# repeats the code and date the page already shows; the footer carries each frame's own credits,
# shown under the picture as it was printed.
FRAME_SIZE = (1024, 916)
FRAME_PARTS = {"body": (0, 48, 1024, 816), "foot": (0, 816, 1024, 916)}

_component = st.components.v2.component(
    "spaceeye_front",
    css=(ASSETS / "screens.css").read_text(encoding="utf-8"),
    js=(ASSETS / "screens.js").read_text(encoding="utf-8"),
)


@st.cache_data(show_spinner=False, max_entries=128)
def _frame_uri(path_str: str, mtime_ns: int, part: str, width: int) -> str | None:
    image = Image.open(path_str).convert("RGB")
    if image.size == FRAME_SIZE:
        image = image.crop(FRAME_PARTS[part])
    elif part == "foot":
        return None  # another layout: the whole picture is the body, credits included
    if image.width > width:
        image = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=80, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def frame_uri(path: Path, part: str = "body", width: int = 960) -> str | None:
    """One part of a Wayback frame as an inline JPEG: the picture ("body") or its credits ("foot")."""
    return _frame_uri(str(path), path.stat().st_mtime_ns, part, width)


def mount(data: dict, key: str, on_open: Callable[[], None] | None = None):
    """Draw one screen; `open` is set when the visitor asks to open a compound file."""
    return _component(data=data, key=key, on_open_change=on_open or (lambda: None))
