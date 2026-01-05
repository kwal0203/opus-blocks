from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.models.document import Document
from opus_blocks.models.manuscript import Manuscript
from opus_blocks.models.manuscript_document import ManuscriptDocument


async def add_document_to_manuscript(
    session: AsyncSession, owner_id: UUID, manuscript_id: UUID, document_id: UUID
) -> None:
    manuscript_result = await session.execute(
        select(Manuscript).where(Manuscript.id == manuscript_id, Manuscript.owner_id == owner_id)
    )
    if not manuscript_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    document_result = await session.execute(
        select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
    )
    if not document_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    existing = await session.execute(
        select(ManuscriptDocument).where(
            ManuscriptDocument.manuscript_id == manuscript_id,
            ManuscriptDocument.document_id == document_id,
        )
    )
    if existing.scalar_one_or_none():
        return

    session.add(ManuscriptDocument(manuscript_id=manuscript_id, document_id=document_id))
    await session.commit()
