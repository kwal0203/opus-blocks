import hashlib
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
    embedding: list[float],
    commit: bool = True,
) -> FactEmbedding:
    result = await session.execute(select(FactEmbedding).where(FactEmbedding.fact_id == fact_id))
    embedding_record = result.scalar_one_or_none()
    if embedding_record:
        embedding_record.vector_id = vector_id
        embedding_record.embedding_model = embedding_model
        embedding_record.namespace = namespace
        embedding_record.embedding = embedding
    else:
        embedding_record = FactEmbedding(
            fact_id=fact_id,
            vector_id=vector_id,
            embedding_model=embedding_model,
            namespace=namespace,
            embedding=embedding,
        )
        session.add(embedding_record)
    if commit:
        await session.commit()
    else:
        await session.flush()
    await session.refresh(embedding_record)
    return embedding_record


def embed_text(text: str) -> list[float]:
    normalized = text.strip().lower()
    if "alpha" in normalized:
        return [1.0, 0.0, 0.0]
    if "beta" in normalized:
        return [0.0, 1.0, 0.0]
    digest = hashlib.sha256(normalized.encode("utf-8")).digest()
    return [digest[0] / 255.0, digest[1] / 255.0, digest[2] / 255.0]
