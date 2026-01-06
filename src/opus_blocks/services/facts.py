import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.models.document import Document
from opus_blocks.models.fact import Fact
from opus_blocks.models.manuscript import Manuscript
from opus_blocks.models.manuscript_document import ManuscriptDocument
from opus_blocks.models.span import Span
from opus_blocks.schemas.fact import ManualFactCreate
from opus_blocks.schemas.span import FactSpanCreate
from opus_blocks.services.embeddings import upsert_fact_embedding


async def create_manual_fact(
    session: AsyncSession, owner_id: UUID, fact_in: ManualFactCreate
) -> Fact:
    if fact_in.document_id:
        result = await session.execute(
            select(Document).where(
                Document.id == fact_in.document_id, Document.owner_id == owner_id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    fact = Fact(
        owner_id=owner_id,
        document_id=fact_in.document_id,
        span_id=None,
        source_type="MANUAL",
        content=fact_in.content,
        qualifiers=fact_in.qualifiers,
        confidence=fact_in.confidence,
        is_uncertain=fact_in.is_uncertain,
        created_by="USER",
    )
    session.add(fact)
    await session.commit()
    await session.refresh(fact)
    if owner_id:
        await upsert_fact_embedding(
            session,
            fact.id,
            vector_id=str(uuid.uuid4()),
            embedding_model="stub-embedding-v1",
            namespace=f"user:{owner_id}",
        )
    return fact


async def list_document_facts(
    session: AsyncSession, owner_id: UUID, document_id: UUID
) -> list[Fact]:
    result = await session.execute(
        select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    facts_result = await session.execute(
        select(Fact).where(Fact.document_id == document_id, Fact.owner_id == owner_id)
    )
    return list(facts_result.scalars().all())


async def list_document_facts_with_spans(
    session: AsyncSession, owner_id: UUID, document_id: UUID
) -> list[tuple[Fact, Span | None]]:
    result = await session.execute(
        select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    facts_result = await session.execute(
        select(Fact, Span)
        .outerjoin(Span, Fact.span_id == Span.id)
        .where(Fact.document_id == document_id, Fact.owner_id == owner_id)
    )
    return list(facts_result.tuples().all())


async def list_manuscript_facts(
    session: AsyncSession, owner_id: UUID, manuscript_id: UUID
) -> list[Fact]:
    manuscript_result = await session.execute(
        select(Manuscript).where(Manuscript.id == manuscript_id, Manuscript.owner_id == owner_id)
    )
    if not manuscript_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    facts_result = await session.execute(
        select(Fact)
        .join(ManuscriptDocument, Fact.document_id == ManuscriptDocument.document_id)
        .where(
            ManuscriptDocument.manuscript_id == manuscript_id,
            Fact.owner_id == owner_id,
        )
    )
    return list(facts_result.scalars().all())


async def list_manuscript_facts_with_spans(
    session: AsyncSession, owner_id: UUID, manuscript_id: UUID
) -> list[tuple[Fact, Span | None]]:
    manuscript_result = await session.execute(
        select(Manuscript).where(Manuscript.id == manuscript_id, Manuscript.owner_id == owner_id)
    )
    if not manuscript_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    facts_result = await session.execute(
        select(Fact, Span)
        .join(ManuscriptDocument, Fact.document_id == ManuscriptDocument.document_id)
        .outerjoin(Span, Fact.span_id == Span.id)
        .where(
            ManuscriptDocument.manuscript_id == manuscript_id,
            Fact.owner_id == owner_id,
        )
    )
    return list(facts_result.tuples().all())


async def create_fact_with_span(
    session: AsyncSession,
    owner_id: UUID,
    document_id: UUID,
    fact_in: FactSpanCreate,
) -> Fact:
    document_result = await session.execute(
        select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
    )
    if not document_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    span_id = None
    span = None
    if fact_in.span:
        span = Span(
            document_id=document_id,
            page=fact_in.span.page,
            start_char=fact_in.span.start_char,
            end_char=fact_in.span.end_char,
            quote=fact_in.span.quote,
        )
        session.add(span)
        await session.flush()
        span_id = span.id

    fact = Fact(
        owner_id=owner_id,
        document_id=document_id,
        span_id=span_id,
        source_type=fact_in.source_type,
        content=fact_in.content,
        qualifiers=fact_in.qualifiers,
        confidence=fact_in.confidence,
        is_uncertain=fact_in.is_uncertain,
        created_by=fact_in.created_by,
    )
    session.add(fact)
    await session.commit()
    await session.refresh(fact)
    if span:
        await session.refresh(span)
    await upsert_fact_embedding(
        session,
        fact.id,
        vector_id=str(uuid.uuid4()),
        embedding_model="stub-embedding-v1",
        namespace=f"user:{owner_id}",
    )
    return fact
