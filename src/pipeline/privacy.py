"""Pre-model masking for supplied names, labelled personal names and phone formats.

This is a deterministic baseline, not a guarantee of general free-text anonymization.
"""

import re

PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{6,}\d)(?!\w)")
PERSON = re.compile(r"((?:اسم المواطن|مقدم الشكوى|الاسم|اسمي|name)\s*[:：]\s*)([^\n،,.;؛:：]{2,60})", re.IGNORECASE)


def mask_text(text, names=()):
    value = PHONE.sub("[PHONE]", str(text))
    value = PERSON.sub(lambda m: m[1] + "[NAME]", value)
    for name in sorted(set(names), key=len, reverse=True):
        if name.strip():
            value = re.sub(r"(?<!\w)" + re.escape(name.strip()) + r"(?!\w)", "[NAME]", value, flags=re.IGNORECASE)
    return value


def assert_safe_texts(texts, names=()):
    for value in texts:
        if mask_text(value, names) != str(value):
            raise ValueError("Text still contains a detectable phone or supplied/labelled personal name")
