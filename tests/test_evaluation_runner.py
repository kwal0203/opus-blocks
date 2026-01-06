import json
from pathlib import Path

from opus_blocks.evaluation.runner import load_golden_dataset, run_golden_set


def test_load_golden_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "golden.json"
    dataset = {
        "version": "v0",
        "paragraphs": [
            {
                "paragraph_id": "p1",
                "expected_verified": True,
                "sentences": [
                    {"order": 1, "expected_supported": True},
                    {"order": 2, "expected_supported": False},
                ],
            }
        ],
    }
    dataset_path.write_text(json.dumps(dataset))

    loaded = load_golden_dataset(dataset_path)

    assert loaded.version == "v0"
    assert len(loaded.paragraphs) == 1
    assert loaded.paragraphs[0].paragraph_id == "p1"
    assert loaded.paragraphs[0].sentences[1].expected_supported is False


def test_run_golden_set_uses_expected_as_actual(tmp_path: Path) -> None:
    dataset_path = tmp_path / "golden.json"
    dataset = {
        "version": "v0",
        "paragraphs": [
            {
                "paragraph_id": "p1",
                "expected_verified": True,
                "sentences": [
                    {"order": 1, "expected_supported": True},
                    {"order": 2, "expected_supported": False},
                ],
            }
        ],
    }
    dataset_path.write_text(json.dumps(dataset))

    loaded = load_golden_dataset(dataset_path)
    result = run_golden_set(loaded)

    assert result.metrics.sentence_support_rate == 0.5
    assert result.metrics.false_support_rate == 0.0
    assert result.metrics.verified_paragraph_rate == 1.0
