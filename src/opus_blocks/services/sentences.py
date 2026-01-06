from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.core.config import settings
from opus_blocks.models.fact import Fact
from opus_blocks.models.manuscript import Manuscript
from opus_blocks.models.paragraph import Paragraph
from opus_blocks.models.sentence import Sentence
from opus_blocks.models.sentence_fact_link import SentenceFactLink
from opus_blocks.schemas.sentence import SentenceCreate
from opus_blocks.schemas.sentence_fact_link import SentenceFactLinkCreate
from opus_blocks.schemas.verification import SentenceVerificationUpdate
from opus_blocks.services.runs import create_run


async def create_sentence(
    session: AsyncSession, owner_id: UUID, sentence_in: SentenceCreate
) -> Sentence:
    paragraph_result = await session.execute(
        select(Paragraph)
        .join(Manuscript, Paragraph.manuscript_id == Manuscript.id)
        .where(Paragraph.id == sentence_in.paragraph_id, Manuscript.owner_id == owner_id)
    )
    paragraph = paragraph_result.scalar_one_or_none()
    if not paragraph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")

    sentence = Sentence(
        paragraph_id=sentence_in.paragraph_id,
        order=sentence_in.order,
        sentence_type=sentence_in.sentence_type,
        text=sentence_in.text,
        is_user_edited=sentence_in.is_user_edited,
    )
    session.add(sentence)
    await session.commit()
    await session.refresh(sentence)
    return sentence


async def list_paragraph_sentences(
    session: AsyncSession, owner_id: UUID, paragraph_id: UUID
) -> list[Sentence]:
    paragraph_result = await session.execute(
        select(Paragraph)
        .join(Manuscript, Paragraph.manuscript_id == Manuscript.id)
        .where(Paragraph.id == paragraph_id, Manuscript.owner_id == owner_id)
    )
    if not paragraph_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")

    sentences_result = await session.execute(
        select(Sentence).where(Sentence.paragraph_id == paragraph_id).order_by(Sentence.order.asc())
    )
    return list(sentences_result.scalars().all())


async def create_sentence_fact_link(
    session: AsyncSession, owner_id: UUID, link_in: SentenceFactLinkCreate
) -> SentenceFactLink:
    sentence_result = await session.execute(
        select(Sentence)
        .join(Paragraph, Sentence.paragraph_id == Paragraph.id)
        .join(Manuscript, Paragraph.manuscript_id == Manuscript.id)
        .where(Sentence.id == link_in.sentence_id, Manuscript.owner_id == owner_id)
    )
    sentence = sentence_result.scalar_one_or_none()
    if not sentence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sentence not found")

    fact_result = await session.execute(
        select(Fact).where(Fact.id == link_in.fact_id, Fact.owner_id == owner_id)
    )
    if not fact_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fact not found")

    link = SentenceFactLink(
        sentence_id=link_in.sentence_id,
        fact_id=link_in.fact_id,
        score=link_in.score,
    )
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


async def list_sentence_fact_links(
    session: AsyncSession, owner_id: UUID, sentence_id: UUID
) -> list[SentenceFactLink]:
    sentence_result = await session.execute(
        select(Sentence)
        .join(Paragraph, Sentence.paragraph_id == Paragraph.id)
        .join(Manuscript, Paragraph.manuscript_id == Manuscript.id)
        .where(Sentence.id == sentence_id, Manuscript.owner_id == owner_id)
    )
    if not sentence_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sentence not found")

    links_result = await session.execute(
        select(SentenceFactLink).where(SentenceFactLink.sentence_id == sentence_id)
    )
    return list(links_result.scalars().all())


async def update_sentence_text(
    session: AsyncSession,
    owner_id: UUID,
    sentence_id: UUID,
    text: str,
) -> Sentence:
    sentence_result = await session.execute(
        select(Sentence)
        .join(Paragraph, Sentence.paragraph_id == Paragraph.id)
        .join(Manuscript, Paragraph.manuscript_id == Manuscript.id)
        .where(Sentence.id == sentence_id, Manuscript.owner_id == owner_id)
    )
    sentence = sentence_result.scalar_one_or_none()
    if not sentence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sentence not found")

    paragraph = await session.scalar(select(Paragraph).where(Paragraph.id == sentence.paragraph_id))
    if not paragraph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")

    sentence.text = text
    sentence.is_user_edited = True
    sentence.supported = False
    sentence.verifier_failure_modes = []
    sentence.verifier_explanation = None
    paragraph.status = "PENDING_VERIFY"

    session.add(sentence)
    session.add(paragraph)
    await session.commit()
    await session.refresh(sentence)
    return sentence


async def update_sentence_verification(
    session: AsyncSession,
    owner_id: UUID,
    sentence_id: UUID,
    update: SentenceVerificationUpdate,
) -> Sentence:
    sentence_result = await session.execute(
        select(Sentence)
        .join(Paragraph, Sentence.paragraph_id == Paragraph.id)
        .join(Manuscript, Paragraph.manuscript_id == Manuscript.id)
        .where(Sentence.id == sentence_id, Manuscript.owner_id == owner_id)
    )
    sentence = sentence_result.scalar_one_or_none()
    if not sentence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sentence not found")

    if update.supported:
        links_result = await session.execute(
            select(SentenceFactLink).where(SentenceFactLink.sentence_id == sentence_id)
        )
        if not links_result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supported sentences require at least one fact link",
            )

    sentence.supported = update.supported
    sentence.verifier_failure_modes = update.verifier_failure_modes
    sentence.verifier_explanation = update.verifier_explanation
    session.add(sentence)

    await session.commit()
    await session.refresh(sentence)

    await create_run(
        session,
        owner_id=owner_id,
        run_type="VERIFIER",
        paragraph_id=sentence.paragraph_id,
        document_id=None,
        provider=settings.llm_provider,
        model=settings.llm_model,
        prompt_version=settings.llm_prompt_version,
        inputs_json={"sentence_id": str(sentence.id)},
        outputs_json={
            "supported": update.supported,
            "failure_modes": update.verifier_failure_modes,
            "explanation": update.verifier_explanation,
        },
    )
    return sentence
