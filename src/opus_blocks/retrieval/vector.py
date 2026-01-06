from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.retrieval.base import RetrievedFact, Retriever
from opus_blocks.vector_store import get_vector_store


class VectorStoreRetriever(Retriever):
    async def retrieve(
        self,
        *,
        session: AsyncSession,
        owner_id: UUID,
        query: str,
        allowed_fact_ids: list[UUID],
        limit: int = 10,
    ) -> list[RetrievedFact]:
        namespace = f"user:{owner_id}"
        store = get_vector_store()
        matches = await store.query(
            session=session,
            query=query,
            namespace=namespace,
            allowed_fact_ids=allowed_fact_ids,
            limit=limit,
        )
        return [RetrievedFact(fact_id=match.fact_id, score=match.score) for match in matches]
