import json
from pathlib import Path

from opus_blocks.evaluation.metrics import EvaluationMetrics
from opus_blocks.evaluation.runner import evaluate_regression_gate, load_golden_dataset


def test_loads_baseline_metrics(tmp_path: Path) -> None:
    dataset_path = tmp_path / "golden.json"
    payload = {
        "version": "v1",
        "baseline_metrics": {
            "sentence_support_rate": 0.8,
            "false_support_rate": 0.0,
            "verified_paragraph_rate": 0.5,
            "correct_refusal_rate": 0.4,
            "over_refusal_rate": 0.1,
        },
        "paragraphs": [],
    }
    dataset_path.write_text(json.dumps(payload))

    loaded = load_golden_dataset(dataset_path)

    assert loaded.baseline_metrics is not None
    assert loaded.baseline_metrics.sentence_support_rate == 0.8


def test_regression_gate_passes_when_improved() -> None:
    baseline = EvaluationMetrics(
        sentence_support_rate=0.8,
        false_support_rate=0.01,
        verified_paragraph_rate=0.5,
        correct_refusal_rate=0.4,
        over_refusal_rate=0.1,
    )
    current = EvaluationMetrics(
        sentence_support_rate=0.9,
        false_support_rate=0.0,
        verified_paragraph_rate=0.6,
        correct_refusal_rate=0.4,
        over_refusal_rate=0.1,
    )

    result = evaluate_regression_gate(baseline, current, min_support_rate=0.85)

    assert result.passed is True


def test_regression_gate_fails_on_false_supports() -> None:
    baseline = EvaluationMetrics(
        sentence_support_rate=0.9,
        false_support_rate=0.0,
        verified_paragraph_rate=0.5,
        correct_refusal_rate=0.4,
        over_refusal_rate=0.1,
    )
    current = EvaluationMetrics(
        sentence_support_rate=0.9,
        false_support_rate=0.02,
        verified_paragraph_rate=0.5,
        correct_refusal_rate=0.4,
        over_refusal_rate=0.1,
    )

    result = evaluate_regression_gate(baseline, current)

    assert result.passed is False
