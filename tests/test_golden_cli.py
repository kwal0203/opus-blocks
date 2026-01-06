import json
from pathlib import Path

from scripts.run_golden_set import _write_baseline


def test_write_baseline(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    metrics = {"sentence_support_rate": 0.5, "false_support_rate": 0.0}

    _write_baseline(baseline_path, metrics)

    data = json.loads(baseline_path.read_text())
    assert data["baseline_metrics"]["sentence_support_rate"] == 0.5
