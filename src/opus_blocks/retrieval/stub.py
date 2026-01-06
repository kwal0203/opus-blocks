from uuid import UUID

from opus_blocks.retrieval.base import RetrievedFact, Retriever


class StubRetriever(Retriever):
    def retrieve(
        self,
        *,
        owner_id: UUID,
        query: str,
        allowed_fact_ids: list[UUID],
        limit: int = 10,
    ) -> list[RetrievedFact]:
        return []
