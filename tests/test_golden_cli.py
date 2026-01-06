import json
from pathlib import Path

from opus_blocks.evaluation.metrics import EvaluationMetrics
from opus_blocks.evaluation.runner import write_baseline


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
