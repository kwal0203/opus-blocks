import json
from pathlib import Path


class PromptLoader:
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path(__file__).resolve().parent

    def render(self, name: str, inputs: dict) -> str:
        template_path = self._root / f"{name}.md"
        template = template_path.read_text()
        payload = json.dumps(inputs, ensure_ascii=True)
        return template.replace("{input_json}", payload)
