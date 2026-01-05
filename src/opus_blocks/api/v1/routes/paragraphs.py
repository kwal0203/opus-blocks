from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from opus_blocks.api.deps import CurrentUser, DbSession
from opus_blocks.schemas.job import JobRead
from opus_blocks.schemas.paragraph import ParagraphCreate, ParagraphRead
from opus_blocks.services.jobs import create_job
from opus_blocks.services.paragraphs import create_paragraph, get_paragraph

router = APIRouter(prefix="/paragraphs")


@router.post("", response_model=ParagraphRead, status_code=status.HTTP_201_CREATED)
async def create_paragraph_endpoint(
    paragraph_in: ParagraphCreate, session: DbSession, user: CurrentUser
) -> ParagraphRead:
    paragraph = await create_paragraph(
        session,
        owner_id=user.id,
        manuscript_id=paragraph_in.manuscript_id,
        spec=paragraph_in.spec,
    )
    return ParagraphRead.model_validate(paragraph)


@router.get("/{paragraph_id}", response_model=ParagraphRead)
async def get_paragraph_endpoint(
    paragraph_id: UUID, session: DbSession, user: CurrentUser
) -> ParagraphRead:
    paragraph = await get_paragraph(session, owner_id=user.id, paragraph_id=paragraph_id)
    if not paragraph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")
    return ParagraphRead.model_validate(paragraph)


@router.post("/{paragraph_id}/generate", response_model=JobRead)
async def generate_paragraph(paragraph_id: UUID, session: DbSession, user: CurrentUser) -> JobRead:
    paragraph = await get_paragraph(session, owner_id=user.id, paragraph_id=paragraph_id)
    if not paragraph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")

    paragraph.status = "GENERATING"
    session.add(paragraph)
    await session.commit()

    job = await create_job(session, user.id, "GENERATE_PARAGRAPH", paragraph.id)
    return JobRead.model_validate(job)


@router.post("/{paragraph_id}/verify", response_model=JobRead)
async def verify_paragraph(paragraph_id: UUID, session: DbSession, user: CurrentUser) -> JobRead:
    paragraph = await get_paragraph(session, owner_id=user.id, paragraph_id=paragraph_id)
    if not paragraph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")

    paragraph.status = "PENDING_VERIFY"
    session.add(paragraph)
    await session.commit()

    job = await create_job(session, user.id, "VERIFY_PARAGRAPH", paragraph.id)
    return JobRead.model_validate(job)
