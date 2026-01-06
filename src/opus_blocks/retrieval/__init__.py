"""Retrieval interfaces and default implementations."""

from opus_blocks.retrieval.stub import StubRetriever


def get_retriever() -> StubRetriever:
    return StubRetriever()
