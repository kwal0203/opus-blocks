import json
from pathlib import Path

from opus_blocks.evaluation.runner import load_golden_dataset


def test_golden_dataset_v0_shape() -> None:
    dataset_path = Path("datasets/golden/golden-dataset-v0.json")
    raw = json.loads(dataset_path.read_text())
    assert raw["version"] == "v0"
    dataset = load_golden_dataset(dataset_path)
    assert dataset.version == "v0"
    assert len(dataset.paragraphs) == 2
