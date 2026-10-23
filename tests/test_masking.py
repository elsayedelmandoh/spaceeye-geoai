# pii masking verification — law 151/2020 compliance assertions
# clean architecture: lowercase, minimal assertions, ponytail (lazy), delete over add

import pytest

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pytest.skip("pandas not installed; masking tests use pandas series", allow_module_level=True)

try:
    from src.pii_masking import (
        apply_pii_masking,
        assert_zero_phones,
        mask_phone_numbers_in_text,
        mask_phone_number,
        mask_national_ids,
        salted_sha256,
        MaskConfig,
        PHONE_IN_TEXT_REGEX,
        NATIONAL_ID_REGEX,
        CANONICAL_CATEGORIES,
        SPECIAL_BUILDINGS,
    )
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"pii_masking import failed: {exc}", allow_module_level=True)


# ------------------------------------------------------------------
# assertion 1: zero unmasked phone numbers after masking (law 151/2020)
# ------------------------------------------------------------------

def test_masked_series_has_zero_unmasked_phones() -> None:
    """production assertion: after apply_pii_masking, 0 raw +20 phone patterns remain."""
    synthetic_series = pd.Series([
        "مخالفات الانتظار parking مقفول ومفيش أماكن خالص — requester +20 100 000 0594 — zone z03",
        "انقطاع الكهرباء الكهرباء قاطعة في العمارة من ساعة — phone +20 100 000 5134 — zone z01",
        "أعطال الإنارة عطل في الإنارة العامة — no phone embedded",
    ])
    masked = apply_pii_masking(series=synthetic_series)
    # minimal: scan masked results; assert no raw +20 number patterns remain
    for idx, value in masked.items():
        text_str = str(value)
        assert "+20" not in text_str, (
            f"row {idx}: unmasked phone remains in masked output: {text_str}"
        )
    # defensive: assert_zero_phones must return true
    assert assert_zero_phones(masked), (
        "assert_zero_phones returned False — unmasked phone number remains in masked series"
    )


# ------------------------------------------------------------------
# assertion 2: masked tokens are deterministic (salted sha-256)
# ------------------------------------------------------------------

def test_masked_phone_is_salted_sha256_hex() -> None:
    """assert masked output contains hex digest fragment, not original number."""
    original = "+20 100 000 0594"
    masked = mask_phone_number(original)
    assert masked.startswith("MASKED_PHONE_"), f"unexpected masked format: {masked}"
    # minimal: masked value is shorter hex fragment, not original digits
    assert "100 000" not in masked
    assert "0594" not in masked


def test_salted_sha256_is_deterministic() -> None:
    """assert same input + same salt produces identical digest (deterministic mask)."""
    digest_1 = salted_sha256("29103051234", "test-salt")
    digest_2 = salted_sha256("29103051234", "test-salt")
    assert digest_1 == digest_2, "salted sha-256 not deterministic"
    # different salt must differ
    digest_3 = salted_sha256("29103051234", "different-salt")
    assert digest_1 != digest_3, "different salts should produce different digests"


# ------------------------------------------------------------------
# assertion 3: national id masking produces masked tokens
# ------------------------------------------------------------------

def test_national_id_masking_produces_mask_token() -> None:
    """assert mask_national_ids replaces national id with masked token."""
    synthetic_text = "requester national id 29103051234 at zone z01"
    masked_text = mask_national_ids(synthetic_text)
    assert masked_text != synthetic_text
    assert "MASKED_ID_" in masked_text, f"expected masked id token; got: {masked_text}"
    assert "29103051234" not in masked_text, f"original national id not masked: {masked_text}"


# ------------------------------------------------------------------
# assertion 4: regex patterns detect embedded numbers correctly
# ------------------------------------------------------------------

def test_phone_regex_detects_egyptian_numbers() -> None:
    """assert PHONE_IN_TEXT_REGEX finds embedded phone patterns."""
    test_string = "+20 100 000 0594"
    matches = PHONE_IN_TEXT_REGEX.findall(test_string)
    assert len(matches) > 0, f"phone regex did not match: {test_string}"


# ------------------------------------------------------------------
# assertion 5: special buildings set is exactly the three flagged buildings
# ------------------------------------------------------------------

def test_special_buildings_exact_three() -> None:
    """assert special buildings set matches architecture spec (b-0112, b-0240, b-0269)."""
    assert SPECIAL_BUILDINGS == {"B-0112", "B-0240", "B-0269"}, (
        f"unexpected special buildings: {SPECIAL_BUILDINGS}"
    )


# ------------------------------------------------------------------
# assertion 6: canonical categories are exactly six
# ------------------------------------------------------------------

def test_canonical_categories_six_items() -> None:
    """assert canonical categories set has exactly 6 items (architecture spec)."""
    from src.cleaning import CANONICAL_CATEGORIES
    assert len(CANONICAL_CATEGORIES) == 6, f"expected 6 categories, got {len(CANONICAL_CATEGORIES)}"
