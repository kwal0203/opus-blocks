from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.models.fact_embedding import FactEmbedding
from opus_blocks.retrieval.base import RetrievedFact, Retriever


class StubRetriever(Retriever):
    async def retrieve(
        self,
        *,
        session: AsyncSession,
        owner_id: UUID,
        query: str,
        allowed_fact_ids: list[UUID],
        limit: int = 10,
    ) -> list[RetrievedFact]:
        if not allowed_fact_ids:
            return []
        result = await session.execute(
            select(FactEmbedding)
            .where(FactEmbedding.fact_id.in_(allowed_fact_ids))
            .order_by(FactEmbedding.created_at.desc())
            .limit(limit)
        )
        return [RetrievedFact(fact_id=item.fact_id, score=1.0) for item in result.scalars().all()]
