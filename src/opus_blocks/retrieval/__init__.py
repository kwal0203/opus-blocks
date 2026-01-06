"""Retrieval interfaces and default implementations."""

from opus_blocks.retrieval.vector import VectorStoreRetriever


def get_retriever() -> VectorStoreRetriever:
    return VectorStoreRetriever()
