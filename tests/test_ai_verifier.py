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
