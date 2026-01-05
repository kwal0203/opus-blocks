from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.models.document import Document
from opus_blocks.models.fact import Fact
from opus_blocks.models.manuscript import Manuscript
from opus_blocks.models.manuscript_document import ManuscriptDocument
from opus_blocks.schemas.fact import ManualFactCreate


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
