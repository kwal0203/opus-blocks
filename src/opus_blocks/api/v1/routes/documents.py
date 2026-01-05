from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, status

from opus_blocks.api.deps import CurrentUser, DbSession
from opus_blocks.schemas.document import DocumentRead
from opus_blocks.schemas.fact import FactRead, FactWithSpanRead
from opus_blocks.schemas.job import JobRead
from opus_blocks.schemas.span import FactSpanCreate, SpanRead
from opus_blocks.services.documents import create_document, get_document
from opus_blocks.services.facts import (
    create_fact_with_span,
    list_document_facts,
    list_document_facts_with_spans,
)
from opus_blocks.services.jobs import create_job

router = APIRouter(prefix="/documents")


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    session: DbSession,
    current_user: CurrentUser,
) -> DocumentRead:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty upload")

    filename = file.filename or "upload.bin"
    document = await create_document(session, current_user.id, filename, content)
    return DocumentRead.model_validate(document)


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document_endpoint(
    document_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
) -> DocumentRead:
    document = await get_document(session, current_user.id, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentRead.model_validate(document)


@router.post("/{document_id}/extract_facts", response_model=JobRead)
async def extract_facts(
    document_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
) -> JobRead:
    document = await get_document(session, current_user.id, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    document.status = "EXTRACTING_FACTS"
    session.add(document)
    await session.commit()

    job = await create_job(session, current_user.id, "EXTRACT_FACTS", document.id)
    return JobRead.model_validate(job)


@router.get("/{document_id}/facts", response_model=list[FactRead])
async def list_facts(
    document_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
) -> list[FactRead]:
    facts = await list_document_facts(session, owner_id=current_user.id, document_id=document_id)
    return [FactRead.model_validate(fact) for fact in facts]


@router.get("/{document_id}/facts/with-spans", response_model=list[FactWithSpanRead])
async def list_facts_with_spans(
    document_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
) -> list[FactWithSpanRead]:
    facts = await list_document_facts_with_spans(
        session, owner_id=current_user.id, document_id=document_id
    )
    response: list[FactWithSpanRead] = []
    for fact, span in facts:
        payload = FactWithSpanRead.model_validate(fact)
        if span:
            payload.span = SpanRead.model_validate(span)
        response.append(payload)
    return response


@router.post("/{document_id}/facts", response_model=FactRead, status_code=status.HTTP_201_CREATED)
async def create_fact_for_document(
    document_id: UUID,
    fact_in: FactSpanCreate,
    session: DbSession,
    current_user: CurrentUser,
) -> FactRead:
    fact = await create_fact_with_span(
        session, owner_id=current_user.id, document_id=document_id, fact_in=fact_in
    )
    return FactRead.model_validate(fact)
