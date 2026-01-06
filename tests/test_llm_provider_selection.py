from opus_blocks.core.config import settings
from opus_blocks.llm.provider import OpenAIProvider, StubLLMProvider, get_llm_provider


def test_get_llm_provider_defaults_to_stub(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "llm_use_openai", False)

    provider = get_llm_provider()

    assert isinstance(provider, StubLLMProvider)


def test_get_llm_provider_returns_openai_provider(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "llm_use_openai", True)
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    provider = get_llm_provider()

    assert isinstance(provider, OpenAIProvider)
