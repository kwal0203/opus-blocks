"""Vector store interfaces and default implementations."""

from opus_blocks.core.config import settings
from opus_blocks.vector_store.chroma import ChromaVectorStore
from opus_blocks.vector_store.stub import StubVectorStore


def get_vector_store() -> StubVectorStore | ChromaVectorStore:
    backend = settings.vector_backend.lower()
    if backend == "chroma":
        return ChromaVectorStore()
    return StubVectorStore()
