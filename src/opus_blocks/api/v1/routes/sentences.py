from uuid import UUID

from fastapi import APIRouter, status

from opus_blocks.api.deps import CurrentUser, DbSession
from opus_blocks.core.config import settings
from opus_blocks.schemas.job import JobRead
from opus_blocks.schemas.sentence import SentenceCreate, SentenceRead, SentenceUpdate
from opus_blocks.schemas.sentence_fact_link import SentenceFactLinkCreate, SentenceFactLinkRead
from opus_blocks.schemas.verification import SentenceVerificationUpdate
from opus_blocks.services.jobs import create_job, enqueue_job
from opus_blocks.services.runs import create_run
from opus_blocks.services.sentences import (
    create_sentence,
    create_sentence_fact_link,
    list_paragraph_sentences,
    list_sentence_fact_links,
    update_sentence_text,
    update_sentence_verification,
)

router = APIRouter(prefix="/sentences")


@router.post("", response_model=SentenceRead, status_code=status.HTTP_201_CREATED)
async def create_sentence_endpoint(
    sentence_in: SentenceCreate, session: DbSession, user: CurrentUser
) -> SentenceRead:
    sentence = await create_sentence(session, owner_id=user.id, sentence_in=sentence_in)
    return SentenceRead.model_validate(sentence)


@router.get("/paragraph/{paragraph_id}", response_model=list[SentenceRead])
async def list_sentences_endpoint(
    paragraph_id: UUID, session: DbSession, user: CurrentUser
) -> list[SentenceRead]:
    sentences = await list_paragraph_sentences(session, owner_id=user.id, paragraph_id=paragraph_id)
    return [SentenceRead.model_validate(sentence) for sentence in sentences]


@router.post("/links", response_model=SentenceFactLinkRead, status_code=status.HTTP_201_CREATED)
async def create_sentence_fact_link_endpoint(
    link_in: SentenceFactLinkCreate, session: DbSession, user: CurrentUser
) -> SentenceFactLinkRead:
    link = await create_sentence_fact_link(session, owner_id=user.id, link_in=link_in)
    return SentenceFactLinkRead.model_validate(link)


@router.get("/{sentence_id}/links", response_model=list[SentenceFactLinkRead])
async def list_sentence_fact_links_endpoint(
    sentence_id: UUID, session: DbSession, user: CurrentUser
) -> list[SentenceFactLinkRead]:
    links = await list_sentence_fact_links(session, owner_id=user.id, sentence_id=sentence_id)
    return [SentenceFactLinkRead.model_validate(link) for link in links]


@router.post("/{sentence_id}/verify", response_model=SentenceRead)
async def verify_sentence_endpoint(
    sentence_id: UUID,
    update: SentenceVerificationUpdate,
    session: DbSession,
    user: CurrentUser,
) -> SentenceRead:
    sentence = await update_sentence_verification(
        session, owner_id=user.id, sentence_id=sentence_id, update=update
    )
    return SentenceRead.model_validate(sentence)


@router.patch("/{sentence_id}", response_model=JobRead)
async def update_sentence_endpoint(
    sentence_id: UUID,
    update: SentenceUpdate,
    session: DbSession,
    user: CurrentUser,
) -> JobRead:
    sentence = await update_sentence_text(
        session, owner_id=user.id, sentence_id=sentence_id, text=update.text
    )
    job = await create_job(session, user.id, "VERIFY_PARAGRAPH", sentence.paragraph_id)
    await create_run(
        session,
        owner_id=user.id,
        run_type="VERIFIER",
        paragraph_id=sentence.paragraph_id,
        document_id=None,
        provider=settings.llm_provider,
        model=settings.llm_model,
        prompt_version=settings.llm_prompt_version,
        inputs_json={
            "paragraph_id": str(sentence.paragraph_id),
            "trigger": "manual_edit",
            "sentence_id": str(sentence.id),
        },
        outputs_json={},
        trace_id=job.trace_id,
    )
    enqueue_job("verify_paragraph", job.id, sentence.paragraph_id)
    return JobRead.model_validate(job)
