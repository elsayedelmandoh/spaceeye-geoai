"""Local evaluation for the five-class complaints classifier.

The benchmark is synthetic capability data. All complaint text is processed in
this local process; this module makes no provider or network calls.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, recall_score
from sklearn.pipeline import Pipeline

from src.inference.complaints_classifier import normalize_ar, predict_position_aware
from src.pipeline.privacy import mask_text

CATEGORIES = ("delay", "stoppage", "payment", "quality", "other")
DISCLAIMER = (
    "Texts were written by the team (generated); scores do not prove accuracy "
    "on real complaints."
)

# This list was fixed before scoring and was not tuned on the test or check texts.
KEYWORDS = {
    "delay": ("تأخير", "استلام", "تسليم"),
    "stoppage": ("توقف", "واقف", "مقاول"),
    "payment": ("قسط", "دفع", "سداد"),
    "quality": ("تشطيب", "شروخ", "تسريب"),
    "other": (),
}


class _MaskText(BaseEstimator, TransformerMixin):
    """Apply the repository's deterministic pre-model text masking."""

    def fit(self, X: Sequence[str], y: Sequence[str] | None = None) -> _MaskText:
        return self

    def transform(self, X: Sequence[str]) -> list[str]:
        return [mask_text(value) for value in X]


def _required_columns(frame: pd.DataFrame, required: set[str], source: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{source} is missing required columns: {', '.join(missing)}")


def _nonempty_strings(series: pd.Series) -> set[str]:
    return {
        str(value)
        for value in series
        if pd.notna(value) and str(value).strip()
    }


def _normalized_texts(series: pd.Series) -> set[str]:
    return {
        normalize_ar(str(value))
        for value in series
        if pd.notna(value) and str(value).strip()
    }


def _frame_ids(frame: pd.DataFrame) -> set[str]:
    if "complaint_id" not in frame.columns:
        return set()
    return _nonempty_strings(frame["complaint_id"])


def _leak_report(
    train_df: pd.DataFrame, test_df: pd.DataFrame, check_df: pd.DataFrame
) -> dict[str, int]:
    train_ids = _frame_ids(train_df)
    test_ids = _frame_ids(test_df)
    check_ids = _frame_ids(check_df)
    train_texts = _normalized_texts(train_df["text_ar"])
    test_texts = _normalized_texts(test_df["text_ar"])
    check_texts = _normalized_texts(check_df["text_ar"])
    return {
        "check_ids_in_train": len(check_ids.intersection(train_ids)),
        "check_normalized_texts_in_train": len(check_texts.intersection(train_texts)),
        "check_ids_in_test": len(check_ids.intersection(test_ids)),
        "check_normalized_texts_in_test": len(check_texts.intersection(test_texts)),
    }


def load_splits(
    benchmark_csv: str | Path, check_csv: str | Path
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load benchmark train/validation, benchmark test, and check frames.

    The returned frames carry a ``leak_report`` attribute containing the number
    of unique check IDs and normalized texts that also occur in train. A
    non-zero train overlap invalidates the check-set score and must be stated.
    """
    benchmark = pd.read_csv(benchmark_csv)
    check = pd.read_csv(check_csv)
    _required_columns(
        benchmark,
        {"complaint_id", "text_ar", "label_category", "split"},
        "benchmark CSV",
    )
    _required_columns(
        check,
        {"complaint_id", "text_ar", "label_category"},
        "check CSV",
    )

    train_df = benchmark[benchmark["split"].isin(("train", "validation"))].copy()
    test_df = benchmark[benchmark["split"].eq("test")].copy()
    check_df = check.copy()
    if train_df.empty or test_df.empty or check_df.empty:
        raise ValueError("train/validation, test, and check splits must all be non-empty")

    report = _leak_report(train_df, test_df, check_df)
    for frame in (train_df, test_df, check_df):
        frame.attrs["leak_report"] = dict(report)
    return train_df, test_df, check_df


def keyword_baseline(text: str) -> str:
    """Classify with a simple fixed keyword list.

    The list was fixed before scoring and was not tuned on the test or check
    texts.
    """
    normalized = normalize_ar(text)
    for category in CATEGORIES:
        if any(keyword in normalized for keyword in KEYWORDS[category]):
            return category
    return "other"


def train_tfidf(train_df: pd.DataFrame) -> Pipeline:
    """Fit masked TF-IDF plus logistic regression on train/validation rows only."""
    _required_columns(train_df, {"text_ar", "label_category"}, "training frame")
    fit_df = train_df
    if "split" in fit_df.columns:
        fit_df = fit_df[fit_df["split"].isin(("train", "validation"))]
    if fit_df.empty:
        raise ValueError("no train or validation rows are available for fitting")

    model = Pipeline(
        [
            ("mask_text", _MaskText()),
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=1,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(C=2.0, max_iter=500, random_state=42),
            ),
        ]
    )
    model.fit(fit_df["text_ar"], fit_df["label_category"])
    return model


def _score_row(
    model: str,
    eval_set: str,
    y_true: pd.Series,
    y_pred: Sequence[str],
    notes: str,
) -> dict[str, object]:
    truth = y_true.astype(str).reset_index(drop=True)
    predictions = pd.Series(list(y_pred), dtype="string").reset_index(drop=True)
    recalls = recall_score(
        truth,
        predictions,
        labels=list(CATEGORIES),
        average=None,
        zero_division=0,
    )
    count_parts: list[str] = []
    correct_total = 0
    for category, recall in zip(CATEGORIES, recalls, strict=True):
        total = int(truth.eq(category).sum())
        correct = int((truth.eq(category) & predictions.eq(category)).sum())
        correct_total += correct
        count_parts.append(f"{category} {correct}/{total}")
    return {
        "model": model,
        "eval_set": eval_set,
        "accuracy": accuracy_score(truth, predictions),
        "macro_f1": f1_score(
            truth,
            predictions,
            labels=list(CATEGORIES),
            average="macro",
            zero_division=0,
        ),
        **{
            f"recall_{category}": float(recall)
            for category, recall in zip(CATEGORIES, recalls, strict=True)
        },
        "n_of_m": "; ".join(count_parts),
        "n_correct": correct_total,
        "n_total": len(truth),
        "notes": notes,
    }


def _evaluation_notes(leak_report: dict[str, int]) -> dict[str, str]:
    overlap_note = (
        f"Check/train overlap: {leak_report['check_ids_in_train']} IDs; "
        f"{leak_report['check_normalized_texts_in_train']} normalized texts."
    )
    if (
        leak_report["check_ids_in_train"]
        or leak_report["check_normalized_texts_in_train"]
    ):
        overlap_note += " Check-set score invalid due to training leakage."
    test_overlap_note = (
        f"Check-set overlap with benchmark test: {leak_report['check_ids_in_test']} IDs; "
        f"{leak_report['check_normalized_texts_in_test']} normalized texts; "
        "the check set is not independent when this is non-zero."
    )
    return {
        "keyword_baseline": (
            "Fixed keyword list; fixed before scoring and not tuned on test or check "
            f"texts. {overlap_note} {test_overlap_note} {DISCLAIMER}"
        ),
        "tfidf_logistic": (
            "Masked TF-IDF (1-2 grams) plus LogisticRegression fitted on train and "
            f"validation rows only. {overlap_note} {test_overlap_note} {DISCLAIMER}"
        ),
        "hand_tuned_reference": (
            "hand_tuned_reference, tuned on corpus phrases, optimistic. "
            f"{overlap_note} {test_overlap_note} {DISCLAIMER}"
        ),
    }


def _model_predictions(
    tfidf_model: Pipeline, texts: list[str]
) -> dict[str, list[str]]:
    return {
        "keyword_baseline": [keyword_baseline(text) for text in texts],
        "tfidf_logistic": list(tfidf_model.predict(texts)),
        "hand_tuned_reference": [predict_position_aware(text) for text in texts],
    }


def evaluate(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    check_df: pd.DataFrame,
) -> pd.DataFrame:
    """Evaluate the fixed baseline, TF-IDF model, and optimistic reference rule."""
    _required_columns(train_df, {"text_ar", "label_category"}, "training frame")
    _required_columns(test_df, {"text_ar", "label_category"}, "test frame")
    _required_columns(check_df, {"text_ar", "label_category"}, "check frame")

    tfidf_model = train_tfidf(train_df)
    model_notes = _evaluation_notes(_leak_report(train_df, test_df, check_df))
    rows: list[dict[str, object]] = []
    for eval_set, frame in (("benchmark_test", test_df), ("check_30", check_df)):
        texts = frame["text_ar"].tolist()
        predictions = _model_predictions(tfidf_model, texts)
        for model_name, model_predictions in predictions.items():
            rows.append(
                _score_row(
                    model_name,
                    eval_set,
                    frame["label_category"],
                    model_predictions,
                    model_notes[model_name],
                )
            )
    return pd.DataFrame(rows)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate the local five-class complaints classifiers."
    )
    parser.add_argument(
        "--benchmark-csv",
        type=Path,
        required=True,
        help="Path to complaints_benchmark.csv.",
    )
    parser.add_argument(
        "--check-csv",
        type=Path,
        default=Path("app_data/complaints_30.csv"),
        help="Path to the 30-item check CSV (default: app_data/complaints_30.csv).",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("docs/deliverables/complaints_eval.csv"),
        help="Path for the evaluation CSV.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the local evaluation, write its CSV, and print the score table."""
    args = _parser().parse_args(argv)
    train_df, test_df, check_df = load_splits(args.benchmark_csv, args.check_csv)
    results = evaluate(train_df, test_df, check_df)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.output_csv, index=False, encoding="utf-8")

    print(results.to_string(index=False))
    report = _leak_report(train_df, test_df, check_df)
    print(
        "Leak report: "
        f"check IDs in train={report['check_ids_in_train']}; "
        "check normalized texts in train="
        f"{report['check_normalized_texts_in_train']}; "
        f"check IDs in benchmark test={report['check_ids_in_test']}; "
        "check normalized texts in benchmark test="
        f"{report['check_normalized_texts_in_test']}."
    )
    print(DISCLAIMER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
