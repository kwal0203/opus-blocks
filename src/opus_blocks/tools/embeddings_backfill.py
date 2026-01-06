import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from opus_blocks.core.config import settings
from opus_blocks.models.fact import Fact
from opus_blocks.services.embeddings import upsert_fact_embedding_for_content


async def run_backfill(owner_id: str | None = None, limit: int | None = None) -> int:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    processed = 0
    async with session_factory() as session:
        query = select(Fact)
        if owner_id:
            query = query.where(Fact.owner_id == uuid.UUID(owner_id))
        if limit:
            query = query.limit(limit)
        result = await session.execute(query)
        facts = list(result.scalars().all())
        for fact in facts:
            if not fact.owner_id:
                continue
            await upsert_fact_embedding_for_content(
                session,
                fact.id,
                content=fact.content,
                embedding_model=settings.embeddings_model,
                namespace=f"user:{fact.owner_id}",
                commit=False,
            )
            processed += 1
        await session.commit()
    await engine.dispose()
    return processed
