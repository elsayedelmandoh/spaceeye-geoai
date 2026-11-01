"""Contract tests for deterministic verification of generated inspection text."""

from __future__ import annotations

import csv

import pytest

from src.inference.verifier import append_log, summarize, verify_text


def _matching_source() -> dict[str, object]:
    return {
        "code": "C01",
        "kpis": {"level": 2, "score": 12.5, "count": 4},
        "facts": [
            {
                "published_date": "2024-06-01",
                "quarter": "2024Q2",
                "detail": "Fabricated source detail.",
            }
        ],
    }


def test_all_matching_tokens_are_correct() -> None:
    text = (
        "Compound C01 is at level 2 with score 12.5 and count 4 "
        "on 2024-06-01 in 2024Q2."
    )

    rows = verify_text(text, _matching_source(), file_id="C01")

    assert len(rows) == 6
    assert {row["verdict"] for row in rows} == {"correct"}
    summary = summarize(rows)
    assert summary["correct"] == 6
    assert summary["needs_review"] is False


def test_wrong_number_is_flagged() -> None:
    rows = verify_text(
        "The score is 13.5.",
        {"score": 12.5},
        file_id="C01",
    )

    wrong_rows = [row for row in rows if row["verdict"] == "wrong number"]
    assert len(wrong_rows) == 1
    assert wrong_rows[0]["token"] == "13.5"
    assert wrong_rows[0]["token_type"] == "number"
    assert "source number 12.5" in wrong_rows[0]["note"]
    summary = summarize(rows)
    assert summary["wrong number"] == 1
    assert summary["needs_review"] is True


def test_source_list_is_walked_recursively() -> None:
    rows = verify_text(
        "C01 score 12.5.",
        [{"code": "C01"}, {"score": 12.5}],
        file_id="C01",
    )

    assert {row["verdict"] for row in rows} == {"correct"}


def test_arabic_indic_digits_are_normalised_before_matching() -> None:
    rows = verify_text(
        "النتيجة ١٢٫٥.",
        {"score": 12.5},
        file_id="C01",
    )

    assert rows == [
        {
            "file_id": "C01",
            "kind": "paragraph",
            "token": "12.5",
            "token_type": "number",
            "verdict": "correct",
            "note": "matched source value",
        }
    ]


def test_date_and_quarter_tokens_are_matched_as_dates() -> None:
    rows = verify_text(
        "As of 2024-06-01 in 2024Q2.",
        {"published_date": "2024-06-01", "quarter": "2024Q2"},
        file_id="C01",
    )

    assert [(row["token"], row["token_type"], row["verdict"]) for row in rows] == [
        ("2024-06-01", "date", "correct"),
        ("2024Q2", "date", "correct"),
    ]


def test_code_missing_from_source_is_an_unsupported_claim() -> None:
    rows = verify_text(
        "C01 and D03.",
        {"code": "C01"},
        file_id="C01",
    )

    unsupported = [row for row in rows if row["verdict"] == "unsupported claim"]
    assert len(unsupported) == 1
    assert unsupported[0]["token"] == "D03"
    assert unsupported[0]["token_type"] == "code"
    assert summarize(rows)["unsupported claim"] == 1


@pytest.mark.parametrize(
    ("text", "causal_token"),
    [
        ("The delay happened because review continued.", "because"),
        ("تأخر المشروع بسبب قيد المراجعة.", "بسبب"),
    ],
)
def test_causal_wording_requires_manual_review(text: str, causal_token: str) -> None:
    rows = verify_text(text, {}, file_id="C01")

    causal_rows = [row for row in rows if row["token"] == causal_token]
    assert len(causal_rows) == 1
    assert causal_rows[0]["verdict"] == "unsupported claim"
    assert causal_rows[0]["note"] == "causal wording: manual review"


def test_missing_level_is_reported_as_missing_context() -> None:
    rows = verify_text(
        "The compound remains under observation.",
        {"kpis": {"level": 2}, "facts": [{"detail": "Fabricated fact."}]},
        file_id="C01",
    )

    missing_rows = [row for row in rows if row["verdict"] == "missing context"]
    assert len(missing_rows) == 1
    assert missing_rows[0]["token"] == "level"
    assert "text states no level" in missing_rows[0]["note"]
    assert summarize(rows)["missing context"] == 1


def test_append_log_creates_one_header_and_appends_each_batch(tmp_path) -> None:
    log_path = tmp_path / "ai_verification_log.csv"
    rows = verify_text("Score 12.5.", {"score": 12.5}, file_id="C01")

    append_log(rows, log_path, checked_on="2025-01-02")
    append_log(rows, log_path, checked_on="2025-01-02")

    raw_log = log_path.read_text(encoding="utf-8")
    assert raw_log.count(
        "file_id,kind,token,token_type,verdict,note,checked_on"
    ) == 1
    with log_path.open(encoding="utf-8", newline="") as log_file:
        logged_rows = list(csv.DictReader(log_file))
    assert len(logged_rows) == 2
    assert {row["checked_on"] for row in logged_rows} == {"2025-01-02"}


def test_append_log_never_writes_the_free_text(tmp_path) -> None:
    log_path = tmp_path / "ai_verification_log.csv"
    free_text = "private draft phrase must not be logged"
    rows = verify_text(
        f"{free_text} with score 12.5.",
        {"score": 12.5},
        file_id="C01",
    )

    append_log(rows, log_path, checked_on="2025-01-02")

    assert free_text not in log_path.read_text(encoding="utf-8")


def test_verification_is_deterministic() -> None:
    text = "C01 level 2 has score 12.5 on 2024-06-01 because review continued."
    source = _matching_source()

    first = verify_text(text, source, file_id="C01", kind="paragraph")
    second = verify_text(text, source, file_id="C01", kind="paragraph")

    assert first == second
    assert summarize(first) == summarize(second)


def _kpi_source() -> dict[str, object]:
    return {
        "code": "C01",
        "kpis": {
            "level": 4,
            "A": 0.87,
            "K2": 0.0,
            "K2_stoppage_quarters": 0.0,
            "K3": 5,
            "K3_delay_months": 5,
            "K5_months": None,
            "K5_fine_eligible_months": None,
            "series": [{"level": 2, "K2": 2.0, "A": 0.35}],
        },
    }


def _wrong_tokens(text: str) -> list[str]:
    rows = verify_text(text, _kpi_source(), file_id="C01")
    return [row["token"] for row in rows if row["verdict"] == "wrong number"]


def test_swapped_level_is_a_wrong_number_even_when_the_digit_is_in_the_source() -> None:
    assert _wrong_tokens("C01 is at level 2.") == ["2"]
    assert _wrong_tokens("C01 is at level 4.") == []


def test_swapped_arabic_level_word_is_a_wrong_number() -> None:
    assert _wrong_tokens("صُنّف المركب C01 في المستوى الثاني.") == ["الثاني"]
    assert _wrong_tokens("صُنّف المركب C01 في المستوى الرابع.") == []


def test_quarters_and_activity_are_tied_to_their_fields() -> None:
    assert _wrong_tokens("C01 stalled for 5 quarters, activity 0.5.") == ["5", "0.5"]
    assert _wrong_tokens("C01 has K2 = 0 and activity score 0.87.") == []


def test_months_and_k_labels_must_equal_the_field_value() -> None:
    assert _wrong_tokens("K3 is 7 months late.") == ["7"]
    assert _wrong_tokens("K3 is 5 months late.") == []
    assert _wrong_tokens("K5 shows 11 months.") == ["11"]


@pytest.mark.parametrize(
    "text",
    [
        "المركب C01 متعثر حالياً.",
        "بلغت نسبة الإنجاز 40 بالمئة.",
        "المشروع مكتمل ميدانياً.",
        "Compound C01 is distressed.",
    ],
)
def test_forbidden_wording_is_flagged_in_arabic_and_english(text: str) -> None:
    rows = verify_text(text, _kpi_source(), file_id="C01")

    flagged = [row for row in rows if row["note"] == "forbidden wording"]
    assert len(flagged) == 1
    assert flagged[0]["verdict"] == "unsupported claim"


def test_hedged_may_be_complete_wording_is_not_forbidden() -> None:
    rows = verify_text("قد يكون مكتملًا وفق إعلان التسليم.", _kpi_source(), file_id="C01")

    assert "forbidden wording" not in {row["note"] for row in rows}


@pytest.mark.parametrize("word", ["لأن", "جراء", "أدى إلى", "نتيجة"])
def test_arabic_causal_words_require_manual_review(word: str) -> None:
    rows = verify_text(f"توقف العمل {word} نقص التمويل.", _kpi_source(), file_id="C01")

    causal_rows = [row for row in rows if row["token"] == word]
    assert len(causal_rows) == 1
    assert causal_rows[0]["note"] == "causal wording: manual review"


def test_a_named_compound_is_flagged_but_a_code_is_not() -> None:
    named = verify_text("المركب النخيل متأخر.", _kpi_source(), file_id="C01")
    coded = verify_text("المركب C01 متأخر.", _kpi_source(), file_id="C01")

    assert "compound named without a code" in {row["note"] for row in named}
    assert "compound named without a code" not in {row["note"] for row in coded}
