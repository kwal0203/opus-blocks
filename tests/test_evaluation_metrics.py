from opus_blocks.evaluation.metrics import compute_rate, compute_support_rate
from opus_blocks.evaluation.runner import (
    ParagraphEvaluation,
    SentenceEvaluation,
    compute_metrics,
)


def test_compute_support_rate_handles_zero() -> None:
    assert compute_support_rate(0, 0) == 0.0


def test_compute_rate_handles_zero() -> None:
    assert compute_rate(1, 0) == 0.0


def test_compute_metrics_aggregates_counts() -> None:
    sentence_evals = [
        SentenceEvaluation(expected_supported=True, actual_supported=True),
        SentenceEvaluation(expected_supported=True, actual_supported=False),
        SentenceEvaluation(expected_supported=False, actual_supported=True),
    ]
    paragraph_evals = [
        ParagraphEvaluation(expected_verified=True, actual_verified=True),
        ParagraphEvaluation(expected_verified=False, actual_verified=False),
        ParagraphEvaluation(expected_verified=True, actual_verified=False),
    ]
    metrics = compute_metrics(sentence_evals, paragraph_evals)

    assert metrics.sentence_support_rate == 2 / 3
    assert metrics.false_support_rate == 1 / 3
    assert metrics.verified_paragraph_rate == 1 / 3
    assert metrics.correct_refusal_rate == 1 / 3
    assert metrics.over_refusal_rate == 1 / 3
