from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.models.fact_embedding import FactEmbedding


async def upsert_fact_embedding(
    session: AsyncSession,
    fact_id: UUID,
    *,
    vector_id: str,
    embedding_model: str,
    namespace: str,
    commit: bool = True,
) -> FactEmbedding:
    result = await session.execute(select(FactEmbedding).where(FactEmbedding.fact_id == fact_id))
    embedding = result.scalar_one_or_none()
    if embedding:
        embedding.vector_id = vector_id
        embedding.embedding_model = embedding_model
        embedding.namespace = namespace
    else:
        embedding = FactEmbedding(
            fact_id=fact_id,
            vector_id=vector_id,
            embedding_model=embedding_model,
            namespace=namespace,
        )
        session.add(embedding)
    if commit:
        await session.commit()
    else:
        await session.flush()
    await session.refresh(embedding)
    return embedding
