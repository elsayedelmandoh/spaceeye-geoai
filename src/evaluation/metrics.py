"""propose: compute nlp and generative alignment metrics (loss, perplexity, rouge, bleu).
input: artifacts/evaluation/predictions/ (model outputs), ground truth targets.
output: dict of computed scores."""


def compute_alignment_metrics(predictions: list, references: list) -> dict:
    """computes generation quality metrics like rouge, bleu, or exact match."""
    return {"accuracy": 0.0, "rougeL": 0.0, "bleu": 0.0}


def compute_loss_metrics(eval_loss: float) -> dict:
    """computes perplexity from evaluation loss."""
    import math

    try:
        return {"perplexity": math.exp(eval_loss)}
    except OverflowError:
        return {"perplexity": float("inf")}
