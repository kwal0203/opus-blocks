import uuid

import pytest

from opus_blocks.retrieval.stub import StubRetriever


class FakeResult:
    def scalars(self):  # type: ignore[no-untyped-def]
        return self

    def all(self):  # type: ignore[no-untyped-def]
        return []


class FakeSession:
    async def execute(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return FakeResult()


@pytest.mark.anyio
async def test_stub_retriever_returns_empty() -> None:
    retriever = StubRetriever()
    results = await retriever.retrieve(
        session=FakeSession(),
        owner_id=uuid.uuid4(),
        query="Introduction - Background Context",
        allowed_fact_ids=[uuid.uuid4()],
        limit=5,
    )
    assert results == []
