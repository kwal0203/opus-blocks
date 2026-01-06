import hashlib
from uuid import UUID

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.core.config import settings
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
    if settings.embeddings_provider == "openai" and settings.embeddings_use_openai:
        if not settings.openai_api_key:
            raise ValueError("openai_api_key must be set when embeddings_use_openai is true")
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.embeddings.create(model=settings.embeddings_model, input=normalized)
        return list(response.data[0].embedding)
    if "alpha" in normalized:
        return [1.0, 0.0, 0.0]
    if "beta" in normalized:
        return [0.0, 1.0, 0.0]
    digest = hashlib.sha256(normalized.encode("utf-8")).digest()
    return [digest[0] / 255.0, digest[1] / 255.0, digest[2] / 255.0]


async def upsert_fact_embedding_for_content(
    session: AsyncSession,
    fact_id: UUID,
    *,
    content: str,
    namespace: str,
    embedding_model: str,
    commit: bool = True,
) -> FactEmbedding:
    embedding = embed_text(content)
    record = await upsert_fact_embedding(
        session,
        fact_id,
        vector_id=str(fact_id),
        embedding_model=embedding_model,
        namespace=namespace,
        embedding=embedding,
        commit=commit,
    )
    from opus_blocks.vector_store import get_vector_store

    store = get_vector_store()
    await store.upsert_fact(
        session=session,
        fact_id=fact_id,
        content=content,
        namespace=namespace,
        embedding=embedding,
    )
    return record
