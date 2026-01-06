import uuid

from opus_blocks.retrieval.stub import StubRetriever


def test_stub_retriever_returns_empty() -> None:
    retriever = StubRetriever()
    results = retriever.retrieve(
        owner_id=uuid.uuid4(),
        query="Introduction - Background Context",
        allowed_fact_ids=[uuid.uuid4()],
        limit=5,
    )
    assert results == []
