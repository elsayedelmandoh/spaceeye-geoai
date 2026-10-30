"""
src/inference/verify.py - Automated Inspection Fact Verifier (T-VE-05)

Responsibilities:
1. Fact-check every number, percentage, date, and code in generated AI text against source facts JSON.
2. Flag causal words ("بسبب", "because", etc.) that attempt ungrounded speculation.
3. Log all verification verdicts (correct, wrong_number, unsupported_claim, missing_context) to
   app_data/ai_verification_log.csv.
4. Adhere to Law 151/2020: never allow ungrounded commercial claims or speculative causality.
"""

import csv
import datetime
import math
import re
from pathlib import Path
from typing import Any

# Known causal trigger words requiring human inspector review
CAUSAL_WORDS_AR = [
    "بسبب", "أدى إلى", "أدت إلى", "نتيجة ل", "يرجع إلى", "ترجع إلى",
    "علّة", "سببه", "نتج عن", "بدافع", "بداعي"
]

CAUSAL_WORDS_EN = [
    "because", "due to", "caused by", "led to", "as a result of",
    "the reason is", "resulting in", "resulted in", "owing to"
]

ALL_CAUSAL_TERMS = CAUSAL_WORDS_AR + CAUSAL_WORDS_EN

# Verifier Verdicts
VERDICT_CORRECT = "correct"
VERDICT_WRONG_NUMBER = "wrong_number"
VERDICT_UNSUPPORTED = "unsupported_claim"
VERDICT_MISSING_CONTEXT = "missing_context"


def extract_context_facts(context: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    """
    Extracts all primitive numbers, dates, and identifier codes from the source context dictionary.
    Returns: (known_numbers, known_dates, known_codes)
    """
    known_numbers = set()
    known_dates = set()
    known_codes = set()

    def walk(obj):
        if obj is None:
            return
        if isinstance(obj, float) and math.isnan(obj):
            return
        if isinstance(obj, (int, float)):
            # Store integer representation and float representation
            val_str = str(obj)
            known_numbers.add(val_str)
            if isinstance(obj, float):
                # E.g., 0.34 -> also 34% or 34
                pct_val = round(obj * 100, 1)
                known_numbers.add(str(pct_val).rstrip('0').rstrip('.'))
                known_numbers.add(f"{round(obj * 100)}")
                known_numbers.add(f"{obj:.2f}")
                known_numbers.add(f"{obj:.3f}")
            else:
                known_numbers.add(str(int(obj)))
        elif isinstance(obj, str):
            clean_str = obj.strip()
            # Check if it is a date YYYY-MM-DD or YYYYQ[1-4]
            if re.match(r"^\d{4}-\d{2}-\d{2}$", clean_str) or re.match(r"^\d{4}Q[1-4]$", clean_str):
                known_dates.add(clean_str)
                known_numbers.add(clean_str[:4]) # Add year
            # Check if it is a compound/developer/region code
            if re.match(r"^[CD]\d{2}$", clean_str) or re.match(r"^R\d+$", clean_str) or re.match(r"^K\d+$", clean_str):
                known_codes.add(clean_str)
            # Check if the string contains a plain number
            num_match = re.search(r"^\d+(?:\.\d+)?$", clean_str)
            if num_match:
                known_numbers.add(clean_str)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(k, str) and (re.match(r"^[CD]\d{2}$", k) or re.match(r"^K\d+$", k)):
                    known_codes.add(k)
                walk(v)
        elif isinstance(obj, (list, tuple, set)):
            for item in obj:
                walk(item)

    walk(context)

    # Standard benign numbers allowed in structured outputs (e.g. 3 questions, 1 paragraph, 2 images, 2184, 119)
    benign_numbers = {"1", "2", "3", "4", "5", "2184", "2022", "119", "2008", "151", "2020", "27"}
    known_numbers.update(benign_numbers)

    return known_numbers, known_dates, known_codes


def find_causal_words(text: str) -> list[str]:
    """Finds ungrounded causal words in Arabic or English text."""
    found = []
    text_lower = text.lower()
    for term in ALL_CAUSAL_TERMS:
        # Use word boundaries or space checks
        pattern = r"(?:\b|\s|^)" + re.escape(term) + r"(?:\b|\s|$|[،.,!؟])"
        if re.search(pattern, text_lower):
            found.append(term)
    return list(dict.fromkeys(found))


def extract_numbers_from_text(text: str) -> list[str]:
    """Extracts all numbers and percentage values from text."""
    # Matches numbers like 0.34, 34%, 120, 2026
    raw_nums = re.findall(r"\b\d+(?:\.\d+)?%?\b", text)
    cleaned = []
    for n in raw_nums:
        # remove % if present
        val = n.rstrip('%')
        cleaned.append(val)
    return cleaned


def extract_codes_from_text(text: str) -> list[str]:
    """Extracts entity codes like C07, D12, R7, K2-K6."""
    codes = re.findall(r"\b[CD]\d{2}\b|\bR\d+\b|\bK[1-6]\b", text, re.IGNORECASE)
    return [c.upper() for c in codes]


def extract_dates_from_text(text: str) -> list[str]:
    """Extracts dates YYYY-MM-DD or YYYYQ[1-4] or standalone years from text."""
    dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{4}Q[1-4]\b", text)
    return dates


def verify_inspection_text(
    text: str,
    source_context: dict[str, Any],
    compound_id: str = "",
    quarter: str = ""
) -> dict[str, Any]:
    """
    Verifies the inspection text against source context facts.
    
    Returns structured dict:
    {
        "verdict": "correct" | "wrong_number" | "unsupported_claim" | "missing_context",
        "is_valid": bool,
        "flags": list of detected discrepancies/issues,
        "causal_words": list of causal words found,
        "wrong_numbers": list of ungrounded numbers,
        "wrong_codes": list of unknown codes,
        "details": human readable summary
    }
    """
    if not text or not text.strip():
        return {
            "verdict": VERDICT_MISSING_CONTEXT,
            "is_valid": False,
            "flags": ["Empty or missing text"],
            "causal_words": [],
            "wrong_numbers": [],
            "wrong_codes": [],
            "details": "Inspection text is completely empty."
        }

    if not source_context:
        return {
            "verdict": VERDICT_MISSING_CONTEXT,
            "is_valid": False,
            "flags": ["Source context dictionary is empty"],
            "causal_words": [],
            "wrong_numbers": [],
            "wrong_codes": [],
            "details": "Source facts context is empty or None."
        }

    known_numbers, _known_dates, known_codes = extract_context_facts(source_context)
    
    # 1. Check Causal Words
    causal_found = find_causal_words(text)
    
    # 2. Check Numbers
    text_numbers = extract_numbers_from_text(text)
    wrong_numbers = []
    for num in text_numbers:
        # Check if number matches as integer, float, or rounded
        matched = False
        if num in known_numbers:
            matched = True
        else:
            try:
                flt = float(num)
                # Check near matches (e.g. 34.0 == 34)
                if str(int(flt)) in known_numbers or f"{flt:.1f}" in known_numbers or f"{flt:.2f}" in known_numbers:
                    matched = True
            except ValueError:
                pass
        if not matched:
            wrong_numbers.append(num)
            
    # 3. Check Codes
    text_codes = extract_codes_from_text(text)
    wrong_codes = []
    for code in text_codes:
        if code not in known_codes and code not in {"R7", "K1", "K2", "K3", "K4", "K5", "K6"}:
            wrong_codes.append(code)

    # Compile Flags
    flags = []
    verdict = VERDICT_CORRECT

    if wrong_numbers:
        verdict = VERDICT_WRONG_NUMBER
        flags.append(f"Unverified numbers found: {wrong_numbers}")

    if wrong_codes:
        if verdict == VERDICT_CORRECT:
            verdict = VERDICT_UNSUPPORTED
        flags.append(f"Unverified entity codes found: {wrong_codes}")

    if causal_found:
        flags.append(f"Speculative causal terms requiring inspector review: {causal_found}")
        # Note: causal words do not automatically fail the facts if numbers match,
        # but they must be logged and flagged. If there are no other errors, it can be flagged as unsupported_claim or flagged for review.
        if verdict == VERDICT_CORRECT:
            verdict = VERDICT_UNSUPPORTED

    is_valid = (verdict == VERDICT_CORRECT)
    details = f"Verified: {len(text_numbers)} numbers, {len(text_codes)} codes. Verdict: {verdict}."
    if flags:
        details += " Flags: " + " | ".join(flags)

    return {
        "verdict": verdict,
        "is_valid": is_valid,
        "flags": flags,
        "causal_words": causal_found,
        "wrong_numbers": wrong_numbers,
        "wrong_codes": wrong_codes,
        "details": details
    }


def log_verification_result(
    result: dict[str, Any],
    compound_id: str,
    quarter: str,
    text_preview: str,
    log_path: Path | None = None
) -> str:
    """
    Logs verification verdict to app_data/ai_verification_log.csv.
    Ensures safe header creation and atomic append.
    """
    if log_path is None:
        module_dir = Path(__file__).resolve().parent
        log_path = module_dir.parent.parent / "app_data" / "ai_verification_log.csv"

    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = log_path.exists() and log_path.stat().st_size > 0

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    preview_clean = text_preview.replace("\n", " ").replace("\r", " ").strip()[:120]
    flagged_str = "; ".join(result.get("flags", []))

    fieldnames = [
        "timestamp",
        "compound_id",
        "quarter",
        "verdict",
        "is_valid",
        "flagged_items",
        "details",
        "text_preview"
    ]

    with open(log_path, mode="a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": timestamp,
            "compound_id": compound_id or "UNKNOWN",
            "quarter": quarter or "UNKNOWN",
            "verdict": result["verdict"],
            "is_valid": "PASS" if result["is_valid"] else "FAIL",
            "flagged_items": flagged_str,
            "details": result["details"],
            "text_preview": preview_clean
        })

    return str(log_path)
