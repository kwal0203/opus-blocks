import math
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.core.config import settings
from opus_blocks.models.fact_embedding import FactEmbedding
from opus_blocks.services.embeddings import embed_text, upsert_fact_embedding
from opus_blocks.vector_store.base import VectorMatch, VectorStore


class StubVectorStore(VectorStore):
    async def upsert_fact(
        self,
        *,
        session: AsyncSession,
        fact_id: UUID,
        content: str,
        namespace: str,
        embedding: list[float] | None = None,
    ) -> None:
        embedding_value = embedding or embed_text(content)
        await upsert_fact_embedding(
            session,
            fact_id,
            vector_id=str(fact_id),
            embedding_model=settings.embeddings_model,
            namespace=namespace,
            embedding=embedding_value,
        )

    async def query(
        self,
        *,
        session: AsyncSession,
        query: str,
        namespace: str,
        allowed_fact_ids: list[UUID],
        limit: int = 10,
    ) -> list[VectorMatch]:
        if not allowed_fact_ids:
            return []
        result = await session.execute(
            select(FactEmbedding)
            .where(
                FactEmbedding.namespace == namespace,
                FactEmbedding.fact_id.in_(allowed_fact_ids),
            )
            .order_by(FactEmbedding.created_at.desc())
            .limit(limit)
        )
        query_embedding = embed_text(query)
        scored: list[VectorMatch] = []
        for item in result.scalars().all():
            score = _cosine_similarity(query_embedding, item.embedding)
            scored.append(VectorMatch(fact_id=item.fact_id, score=score))
        return sorted(scored, key=lambda x: x.score, reverse=True)

    async def delete_fact(
        self,
        *,
        session: AsyncSession,
        fact_id: UUID,
        namespace: str,
    ) -> None:
        result = await session.execute(
            select(FactEmbedding).where(
                FactEmbedding.fact_id == fact_id,
                FactEmbedding.namespace == namespace,
            )
        )
        embedding = result.scalar_one_or_none()
        if not embedding:
            return
        await session.delete(embedding)
        await session.commit()


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)
