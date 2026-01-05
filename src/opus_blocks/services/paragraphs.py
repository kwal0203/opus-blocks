import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.models.fact import Fact
from opus_blocks.models.manuscript import Manuscript
from opus_blocks.models.paragraph import Paragraph
from opus_blocks.schemas.paragraph import ParagraphSpecInput


async def _ensure_facts_owned(
    session: AsyncSession, owner_id: UUID, allowed_fact_ids: list[UUID]
) -> None:
    if not allowed_fact_ids:
        return
    result = await session.execute(
        select(Fact.id).where(Fact.owner_id == owner_id, Fact.id.in_(allowed_fact_ids))
    )
    found = set(result.scalars().all())
    missing = set(allowed_fact_ids) - found
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more allowed_fact_ids are invalid",
        )


async def create_paragraph(
    session: AsyncSession,
    owner_id: UUID,
    manuscript_id: UUID,
    spec: ParagraphSpecInput,
) -> Paragraph:
    manuscript_result = await session.execute(
        select(Manuscript).where(Manuscript.id == manuscript_id, Manuscript.owner_id == owner_id)
    )
    manuscript = manuscript_result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    await _ensure_facts_owned(session, owner_id, spec.allowed_fact_ids)

    paragraph_id = uuid.uuid4()
    spec_payload = spec.model_dump(mode="json")
    spec_payload["paragraph_id"] = str(paragraph_id)

    paragraph = Paragraph(
        id=paragraph_id,
        manuscript_id=manuscript.id,
        section=spec.section,
        intent=spec.intent,
        spec_json=spec_payload,
        allowed_fact_ids=spec.allowed_fact_ids,
        status="CREATED",
    )
    session.add(paragraph)
    await session.commit()
    await session.refresh(paragraph)
    return paragraph


async def get_paragraph(
    session: AsyncSession, owner_id: UUID, paragraph_id: UUID
) -> Paragraph | None:
    result = await session.execute(
        select(Paragraph)
        .join(Manuscript, Paragraph.manuscript_id == Manuscript.id)
        .where(Paragraph.id == paragraph_id, Manuscript.owner_id == owner_id)
    )
    return result.scalar_one_or_none()
