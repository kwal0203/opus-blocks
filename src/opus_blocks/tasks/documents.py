import asyncio
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from opus_blocks.contracts.agent_contracts import validate_librarian_output
from opus_blocks.core.config import settings
from opus_blocks.models.document import Document
from opus_blocks.models.fact import Fact
from opus_blocks.models.job import Job
from opus_blocks.models.span import Span
from opus_blocks.services.runs import create_run
from opus_blocks.tasks.celery_app import celery_app


def _build_session_factory() -> tuple[async_sessionmaker, AsyncEngine]:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return session_factory, engine


async def run_extract_facts_job(job_id: UUID, document_id: UUID) -> None:
    session_factory, engine = _build_session_factory()
    async with session_factory() as session:
        job = await session.scalar(select(Job).where(Job.id == job_id))
        document = await session.scalar(select(Document).where(Document.id == document_id))
        if not job or not document:
            await engine.dispose()
            return

        job.status = "RUNNING"
        session.add(job)
        await session.commit()

        if job.owner_id:
            await create_run(
                session,
                owner_id=job.owner_id,
                run_type="LIBRARIAN",
                paragraph_id=None,
                document_id=document.id,
                provider=settings.llm_provider,
                model=settings.llm_model,
                prompt_version=settings.llm_prompt_version,
                inputs_json={"document_id": str(document.id)},
                outputs_json={"status": "stub"},
            )

        existing_facts = await session.scalar(
            select(Fact.id).where(Fact.document_id == document.id).limit(1)
        )
        if not existing_facts and job.owner_id:
            placeholders = [
                (
                    1,
                    0,
                    24,
                    "Placeholder extracted span.",
                    "Placeholder extracted fact.",
                    0.5,
                    True,
                ),
                (
                    2,
                    50,
                    80,
                    "Additional placeholder span.",
                    "Secondary extracted fact.",
                    0.7,
                    False,
                ),
                (
                    None,
                    None,
                    None,
                    None,
                    "High-level extracted fact without span.",
                    0.4,
                    True,
                ),
            ]
            output_payload = {
                "facts": [
                    {
                        "content": content,
                        "source_type": "PDF",
                        "source_span": {
                            "document_id": str(document.id),
                            "page": page,
                            "start_char": start_char,
                            "end_char": end_char,
                            "quote": quote,
                        },
                        "qualifiers": {},
                        "confidence": confidence,
                    }
                    for (
                        page,
                        start_char,
                        end_char,
                        quote,
                        content,
                        confidence,
                        _,
                    ) in placeholders
                ],
                "uncertain_facts": [],
            }
            try:
                validate_librarian_output(output_payload)
            except ValueError:
                job.status = "FAILED"
                document.status = "FAILED_EXTRACTION"
                session.add(job)
                session.add(document)
                await session.commit()
                await engine.dispose()
                return
            for (
                page,
                start_char,
                end_char,
                quote,
                content,
                confidence,
                is_uncertain,
            ) in placeholders:
                span_id = None
                if page is not None:
                    span = Span(
                        document_id=document.id,
                        page=page,
                        start_char=start_char,
                        end_char=end_char,
                        quote=quote,
                    )
                    session.add(span)
                    await session.flush()
                    span_id = span.id
                fact = Fact(
                    owner_id=job.owner_id,
                    document_id=document.id,
                    span_id=span_id,
                    source_type="PDF",
                    content=content,
                    qualifiers={},
                    confidence=confidence,
                    is_uncertain=is_uncertain,
                    created_by="LIBRARIAN",
                )
                session.add(fact)

        document.status = "FACTS_READY"
        job.status = "SUCCEEDED"
        session.add(document)
        session.add(job)
        await session.commit()

    await engine.dispose()


@celery_app.task(name="extract_facts")
def extract_facts(job_id: str, document_id: str) -> None:
    asyncio.run(run_extract_facts_job(uuid.UUID(job_id), uuid.UUID(document_id)))
