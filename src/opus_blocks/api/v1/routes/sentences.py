from uuid import UUID

from fastapi import APIRouter, status

from opus_blocks.api.deps import CurrentUser, DbSession
from opus_blocks.schemas.sentence import SentenceCreate, SentenceRead
from opus_blocks.schemas.sentence_fact_link import SentenceFactLinkCreate, SentenceFactLinkRead
from opus_blocks.services.sentences import (
    create_sentence,
    create_sentence_fact_link,
    list_paragraph_sentences,
    list_sentence_fact_links,
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
