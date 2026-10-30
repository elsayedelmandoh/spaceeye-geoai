from pathlib import Path

import pandas as pd
import pytest

from src.inference.complaints_eval import (
    DISCLAIMER,
    evaluate,
    keyword_baseline,
    load_splits,
    main,
    train_tfidf,
)

CATEGORIES = ("delay", "stoppage", "payment", "quality", "other")
TEXTS = {
    "delay": ("تأخير في التسليم", "موعد الاستلام متأخر"),
    "stoppage": ("توقف العمل", "المقاول واقف"),
    "payment": ("دفع القسط", "سداد الدفعة"),
    "quality": ("تشطيب فيه شروخ", "تسريب في سقف"),
    "other": ("طلب نسخة العقد", "استفسار عن الحجز"),
}


def _benchmark_frame() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    row_number = 0
    for split, repeats in (("train", 2), ("validation", 1), ("test", 1)):
        for category in CATEGORIES:
            for text in TEXTS[category][:repeats]:
                row_number += 1
                rows.append(
                    {
                        "complaint_id": f"S-{row_number}",
                        "text_ar": text,
                        "label_category": category,
                        "split": split,
                    }
                )
    return pd.DataFrame(rows)


def _check_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "complaint_id": f"CHECK-{index}",
                "text_ar": TEXTS[category][0],
                "label_category": category,
            }
            for index, category in enumerate(CATEGORIES)
        ]
    )


def test_keyword_baseline_returns_all_five_categories() -> None:
    assert keyword_baseline("تأخير في التسليم") == "delay"
    assert keyword_baseline("توقف العمل") == "stoppage"
    assert keyword_baseline("دفع القسط") == "payment"
    assert keyword_baseline("تشطيب فيه شروخ") == "quality"
    assert keyword_baseline("طلب نسخة العقد") == "other"


def test_train_tfidf_uses_only_supplied_rows_and_masks_phone_text() -> None:
    train = pd.DataFrame(
        {
            "text_ar": [
                "phone 01012345678 trainonlytoken",
                "beta trainonlytoken",
                "gamma trainonlytoken",
                "delta trainonlytoken",
                "epsilon trainonlytoken",
            ],
            "label_category": list(CATEGORIES),
            "split": ["train"] * len(CATEGORIES),
        }
    )
    held_out = pd.DataFrame(
        {
            "text_ar": ["heldouttoken"],
            "label_category": ["delay"],
            "split": ["test"],
        }
    )
    model = train_tfidf(pd.concat([train, held_out], ignore_index=True))
    vocabulary = set(model.named_steps["tfidf"].get_feature_names_out())

    assert "trainonlytoken" in vocabulary
    assert "heldouttoken" not in vocabulary
    assert "01012345678" not in vocabulary
    assert "phone" in vocabulary


def test_load_splits_reports_check_to_train_overlap(tmp_path: Path) -> None:
    benchmark = pd.DataFrame(
        [
            {
                "complaint_id": "T-1",
                "text_ar": "نص تدريب",
                "label_category": "delay",
                "split": "train",
            },
            {
                "complaint_id": "V-1",
                "text_ar": "نص تحقق",
                "label_category": "payment",
                "split": "validation",
            },
            {
                "complaint_id": "S-1",
                "text_ar": "نص اختبار",
                "label_category": "quality",
                "split": "test",
            },
        ]
    )
    check = pd.DataFrame(
        [
            {
                "complaint_id": "T-1",
                "text_ar": "نص مختلف",
                "label_category": "delay",
            },
            {
                "complaint_id": "C-2",
                "text_ar": "نص تدريب",
                "label_category": "delay",
            },
            {
                "complaint_id": "C-3",
                "text_ar": "نص نظيف",
                "label_category": "other",
            },
        ]
    )
    benchmark_path = tmp_path / "benchmark.csv"
    check_path = tmp_path / "check.csv"
    benchmark.to_csv(benchmark_path, index=False)
    check.to_csv(check_path, index=False)

    train, test, check_frame = load_splits(benchmark_path, check_path)
    report = check_frame.attrs["leak_report"]

    assert len(train) == 2
    assert len(test) == 1
    assert len(check_frame) == 3
    assert report["check_ids_in_train"] == 1
    assert report["check_normalized_texts_in_train"] == 1
    assert report["check_ids_in_test"] == 0


def test_evaluate_returns_metrics_and_n_of_m_counts() -> None:
    train = pd.DataFrame(
        {
            "text_ar": [TEXTS[category][0] for category in CATEGORIES],
            "label_category": list(CATEGORIES),
        }
    )
    test = train.copy()
    check = train.copy()

    results = evaluate(train, test, check)
    expected_columns = {
        "model",
        "eval_set",
        "accuracy",
        "macro_f1",
        "recall_delay",
        "recall_stoppage",
        "recall_payment",
        "recall_quality",
        "recall_other",
        "n_of_m",
        "n_correct",
        "n_total",
        "notes",
    }

    assert expected_columns.issubset(results.columns)
    assert set(results["model"]) == {
        "keyword_baseline",
        "tfidf_logistic",
        "hand_tuned_reference",
    }
    assert set(results["eval_set"]) == {"benchmark_test", "check_30"}
    keyword_test = results[
        (results["model"] == "keyword_baseline")
        & (results["eval_set"] == "benchmark_test")
    ].iloc[0]
    assert keyword_test["n_correct"] == 5
    assert keyword_test["n_total"] == 5
    assert keyword_test["n_of_m"] == (
        "delay 1/1; stoppage 1/1; payment 1/1; quality 1/1; other 1/1"
    )


def test_shipped_check_set_is_balanced_and_complete() -> None:
    path = Path(__file__).resolve().parents[1] / "app_data" / "complaints_30.csv"
    check = pd.read_csv(path)

    assert len(check) == 30
    assert check["label_category"].value_counts().to_dict() == {
        "delay": 6,
        "stoppage": 6,
        "payment": 6,
        "quality": 6,
        "other": 6,
    }
    assert set(check["label_category"]) == set(CATEGORIES)


def test_main_writes_csv_and_prints_disclaimer(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    benchmark_path = tmp_path / "benchmark.csv"
    check_path = tmp_path / "check.csv"
    output_path = tmp_path / "complaints_eval.csv"
    _benchmark_frame().to_csv(benchmark_path, index=False)
    _check_frame().to_csv(check_path, index=False)

    main(
        [
            "--benchmark-csv",
            str(benchmark_path),
            "--check-csv",
            str(check_path),
            "--output-csv",
            str(output_path),
        ]
    )

    output = capsys.readouterr().out
    results = pd.read_csv(output_path)
    assert DISCLAIMER in output
    assert results["notes"].str.contains(DISCLAIMER, regex=False).all()
