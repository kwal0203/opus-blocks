from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from opus_blocks.api.deps import CurrentUser, DbSession
from opus_blocks.core.config import settings
from opus_blocks.core.rate_limit import rate_limit
from opus_blocks.retrieval import get_retriever
from opus_blocks.schemas.fact import FactRead
from opus_blocks.schemas.job import JobRead
from opus_blocks.schemas.paragraph import ParagraphCreate, ParagraphRead
from opus_blocks.schemas.paragraph_view import ParagraphView
from opus_blocks.schemas.retrieval import FactSuggestion
from opus_blocks.schemas.run import RunRead
from opus_blocks.schemas.sentence import SentenceRead
from opus_blocks.schemas.sentence_fact_link import SentenceFactLinkRead
from opus_blocks.services.facts import list_manuscript_facts
from opus_blocks.services.jobs import create_job, enqueue_job
from opus_blocks.services.paragraphs import (
    create_paragraph,
    get_paragraph,
    update_paragraph_verification,
)
from opus_blocks.services.runs import create_run, list_paragraph_runs
from opus_blocks.services.sentences import list_paragraph_sentences, list_sentence_fact_links

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
@rate_limit(settings.rate_limit_job)
async def generate_paragraph(paragraph_id: UUID, session: DbSession, user: CurrentUser) -> JobRead:
    paragraph = await get_paragraph(session, owner_id=user.id, paragraph_id=paragraph_id)
    if not paragraph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")

    paragraph.status = "GENERATING"
    session.add(paragraph)
    await session.commit()

    job = await create_job(session, user.id, "GENERATE_PARAGRAPH", paragraph.id)
    run = await create_run(
        session,
        owner_id=user.id,
        run_type="WRITER",
        paragraph_id=paragraph.id,
        document_id=None,
        provider=settings.llm_provider,
        model=settings.llm_model,
        prompt_version=settings.llm_prompt_version,
        inputs_json={"paragraph_id": str(paragraph.id), "spec": paragraph.spec_json},
        outputs_json={},
        trace_id=job.trace_id,
    )
    paragraph.latest_run_id = run.id
    session.add(paragraph)
    await session.commit()

    enqueue_job("generate_paragraph", job.id, paragraph.id)
    return JobRead.model_validate(job)


@router.post("/{paragraph_id}/verify", response_model=JobRead)
@rate_limit(settings.rate_limit_job)
async def verify_paragraph(paragraph_id: UUID, session: DbSession, user: CurrentUser) -> JobRead:
    paragraph = await get_paragraph(session, owner_id=user.id, paragraph_id=paragraph_id)
    if not paragraph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")

    paragraph.status = "PENDING_VERIFY"
    session.add(paragraph)
    await session.commit()

    job = await create_job(session, user.id, "VERIFY_PARAGRAPH", paragraph.id)
    await create_run(
        session,
        owner_id=user.id,
        run_type="VERIFIER",
        paragraph_id=paragraph.id,
        document_id=None,
        provider=settings.llm_provider,
        model=settings.llm_model,
        prompt_version=settings.llm_prompt_version,
        inputs_json={"paragraph_id": str(paragraph.id)},
        outputs_json={},
        trace_id=job.trace_id,
    )

    enqueue_job("verify_paragraph", job.id, paragraph.id)
    return JobRead.model_validate(job)


@router.get("/{paragraph_id}/runs", response_model=list[RunRead])
async def list_runs(paragraph_id: UUID, session: DbSession, user: CurrentUser) -> list[RunRead]:
    runs = await list_paragraph_runs(session, owner_id=user.id, paragraph_id=paragraph_id)
    return [RunRead.model_validate(run) for run in runs]


@router.post("/{paragraph_id}/verify-rollup", response_model=ParagraphRead)
async def verify_paragraph_rollup(
    paragraph_id: UUID, session: DbSession, user: CurrentUser
) -> ParagraphRead:
    paragraph = await update_paragraph_verification(
        session, owner_id=user.id, paragraph_id=paragraph_id
    )
    return ParagraphRead.model_validate(paragraph)


@router.get("/{paragraph_id}/view", response_model=ParagraphView)
async def get_paragraph_view(
    paragraph_id: UUID, session: DbSession, user: CurrentUser
) -> ParagraphView:
    paragraph = await get_paragraph(session, owner_id=user.id, paragraph_id=paragraph_id)
    if not paragraph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")

    sentences = await list_paragraph_sentences(session, owner_id=user.id, paragraph_id=paragraph_id)
    links: list[SentenceFactLinkRead] = []
    for sentence in sentences:
        sentence_links = await list_sentence_fact_links(
            session, owner_id=user.id, sentence_id=sentence.id
        )
        links.extend(SentenceFactLinkRead.model_validate(link) for link in sentence_links)

    facts = await list_manuscript_facts(
        session, owner_id=user.id, manuscript_id=paragraph.manuscript_id
    )

    return ParagraphView(
        paragraph=ParagraphRead.model_validate(paragraph),
        sentences=[SentenceRead.model_validate(sentence) for sentence in sentences],
        links=links,
        facts=[FactRead.model_validate(fact) for fact in facts],
    )


@router.get("/{paragraph_id}/suggest-facts", response_model=list[FactSuggestion])
async def suggest_facts(
    paragraph_id: UUID, session: DbSession, user: CurrentUser
) -> list[FactSuggestion]:
    paragraph = await get_paragraph(session, owner_id=user.id, paragraph_id=paragraph_id)
    if not paragraph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paragraph not found")

    allowed_fact_ids = paragraph.allowed_fact_ids
    if not allowed_fact_ids:
        facts = await list_manuscript_facts(
            session, owner_id=user.id, manuscript_id=paragraph.manuscript_id
        )
        allowed_fact_ids = [fact.id for fact in facts]

    retrieval_query = f"{paragraph.section} - {paragraph.intent}"
    retriever = get_retriever()
    retrieved = await retriever.retrieve(
        session=session,
        owner_id=user.id,
        query=retrieval_query,
        allowed_fact_ids=allowed_fact_ids,
        limit=5,
    )
    return [FactSuggestion(fact_id=item.fact_id, score=item.score) for item in retrieved]
