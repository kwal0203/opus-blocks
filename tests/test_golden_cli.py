import json
from pathlib import Path

from opus_blocks.evaluation.metrics import EvaluationMetrics
from opus_blocks.evaluation.runner import (
    EvaluationResult,
    GoldenDataset,
    ParagraphEvaluation,
    RegressionGateResult,
    SentenceEvaluation,
    write_baseline,
    write_evaluation_artifact,
)


def test_write_baseline(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    metrics = EvaluationMetrics(
        sentence_support_rate=0.5,
        false_support_rate=0.0,
        verified_paragraph_rate=0.2,
        correct_refusal_rate=0.1,
        over_refusal_rate=0.0,
    )

    write_baseline(baseline_path, metrics)

    data = json.loads(baseline_path.read_text())
    assert data["baseline_metrics"]["sentence_support_rate"] == 0.5


def test_write_evaluation_artifact(tmp_path: Path) -> None:
    artifact_path = tmp_path / "artifact.json"
    dataset = GoldenDataset(version="v0", paragraphs=[])
    result = EvaluationResult(
        sentence_evaluations=[SentenceEvaluation(expected_supported=True, actual_supported=True)],
        paragraph_evaluations=[ParagraphEvaluation(expected_verified=True, actual_verified=True)],
        metrics=EvaluationMetrics(
            sentence_support_rate=1.0,
            false_support_rate=0.0,
            verified_paragraph_rate=1.0,
            correct_refusal_rate=1.0,
            over_refusal_rate=0.0,
        ),
    )
    gate = RegressionGateResult(passed=True, diffs={})

    write_evaluation_artifact(artifact_path, dataset, result, gate)

    data = json.loads(artifact_path.read_text())
    assert data["version"] == "v0"
    assert data["gate_passed"] is True
