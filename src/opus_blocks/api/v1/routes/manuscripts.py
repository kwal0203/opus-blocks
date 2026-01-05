from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from opus_blocks.api.deps import CurrentUser, DbSession
from opus_blocks.schemas.fact import FactRead, FactWithSpanRead
from opus_blocks.schemas.manuscript import ManuscriptCreate, ManuscriptRead
from opus_blocks.schemas.span import SpanRead
from opus_blocks.services.facts import list_manuscript_facts, list_manuscript_facts_with_spans
from opus_blocks.services.manuscripts import create_manuscript, get_manuscript
from opus_blocks.services.manuscripts_documents import add_document_to_manuscript

router = APIRouter(prefix="/manuscripts")


@router.post("", response_model=ManuscriptRead, status_code=status.HTTP_201_CREATED)
async def create_manuscript_endpoint(
    manuscript_in: ManuscriptCreate, session: DbSession, user: CurrentUser
) -> ManuscriptRead:
    manuscript = await create_manuscript(
        session, owner_id=user.id, title=manuscript_in.title, description=manuscript_in.description
    )
    return ManuscriptRead.model_validate(manuscript)


@router.get("/{manuscript_id}", response_model=ManuscriptRead)
async def get_manuscript_endpoint(
    manuscript_id: UUID, session: DbSession, user: CurrentUser
) -> ManuscriptRead:
    manuscript = await get_manuscript(session, owner_id=user.id, manuscript_id=manuscript_id)
    if not manuscript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")
    return ManuscriptRead.model_validate(manuscript)


@router.post(
    "/{manuscript_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def attach_document(
    manuscript_id: UUID,
    document_id: UUID,
    session: DbSession,
    user: CurrentUser,
) -> None:
    await add_document_to_manuscript(
        session, owner_id=user.id, manuscript_id=manuscript_id, document_id=document_id
    )


@router.get("/{manuscript_id}/facts", response_model=list[FactRead])
async def list_manuscript_facts_endpoint(
    manuscript_id: UUID,
    session: DbSession,
    user: CurrentUser,
) -> list[FactRead]:
    facts = await list_manuscript_facts(session, owner_id=user.id, manuscript_id=manuscript_id)
    return [FactRead.model_validate(fact) for fact in facts]


@router.get("/{manuscript_id}/facts/with-spans", response_model=list[FactWithSpanRead])
async def list_manuscript_facts_with_spans_endpoint(
    manuscript_id: UUID,
    session: DbSession,
    user: CurrentUser,
) -> list[FactWithSpanRead]:
    facts = await list_manuscript_facts_with_spans(
        session, owner_id=user.id, manuscript_id=manuscript_id
    )
    response: list[FactWithSpanRead] = []
    for fact, span in facts:
        payload = FactWithSpanRead.model_validate(fact)
        if span:
            payload.span = SpanRead.model_validate(span)
        response.append(payload)
    return response
