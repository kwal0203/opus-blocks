import types

from opus_blocks.llm.provider import OpenAIProvider


class FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [types.SimpleNamespace(message=types.SimpleNamespace(content=content))]
        self.usage = types.SimpleNamespace(prompt_tokens=12, completion_tokens=34)


class FakeCompletions:
    def create(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return FakeResponse('{"facts": [], "uncertain_facts": []}')


class FakeChat:
    def __init__(self) -> None:
        self.completions = FakeCompletions()


class FakeClient:
    def __init__(self) -> None:
        self.chat = FakeChat()


def test_openai_provider_parses_json(monkeypatch) -> None:
    provider = OpenAIProvider(api_key="test", model="gpt-test", prompt_version="v1")
    monkeypatch.setattr(provider, "_client", FakeClient())

    result = provider.extract_facts(inputs={"document_id": "doc", "source_text": ""})

    assert result.outputs["facts"] == []
    assert result.metadata.token_prompt == 12
    assert result.metadata.token_completion == 34
