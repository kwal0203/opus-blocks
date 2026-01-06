import math
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.models.fact_embedding import FactEmbedding
from opus_blocks.retrieval.base import RetrievedFact, Retriever
from opus_blocks.services.embeddings import embed_text


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
        query_embedding = embed_text(query)
        scored: list[RetrievedFact] = []
        for item in result.scalars().all():
            score = _cosine_similarity(query_embedding, item.embedding)
            scored.append(RetrievedFact(fact_id=item.fact_id, score=score))
        return sorted(scored, key=lambda x: x.score, reverse=True)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)
