from opus_blocks.core.config import settings
from opus_blocks.vector_store import get_vector_store
from opus_blocks.vector_store.stub import StubVectorStore


def test_vector_store_defaults_to_stub(monkeypatch) -> None:
    monkeypatch.setattr(settings, "vector_backend", "stub")
    store = get_vector_store()
    assert isinstance(store, StubVectorStore)


def test_vector_store_uses_chroma(monkeypatch) -> None:
    class DummyChroma:
        pass

    monkeypatch.setattr(settings, "vector_backend", "chroma")
    monkeypatch.setattr("opus_blocks.vector_store.ChromaVectorStore", DummyChroma)
    store = get_vector_store()
    assert isinstance(store, DummyChroma)
