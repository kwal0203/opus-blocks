import asyncio
import hashlib
import uuid
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from opus_blocks.contracts.agent_contracts import validate_librarian_output
from opus_blocks.core.config import settings
from opus_blocks.llm.provider import get_llm_provider
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


def _load_source_text(document: Document) -> tuple[str, str]:
    if not document.storage_uri:
        return "", ""
    try:
        content = Path(document.storage_uri).read_bytes()
    except OSError:
        return "", ""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin1", errors="ignore")
    content_hash = hashlib.sha256(content).hexdigest()
    return text, content_hash


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

        source_text, source_text_hash = _load_source_text(document)
        inputs_json = {
            "document_id": str(document.id),
            "source_type": document.source_type,
            "source_text_hash": source_text_hash,
            "source_text_len": len(source_text),
        }
        provider_inputs = {
            "document_id": str(document.id),
            "source_type": document.source_type,
            "source_text": source_text,
            "span_map": {"page_offsets": {}},
        }
        provider = get_llm_provider()
        try:
            llm_result = provider.extract_facts(inputs=provider_inputs)
        except Exception:
            job.status = "FAILED"
            document.status = "FAILED_EXTRACTION"
            session.add(job)
            session.add(document)
            await session.commit()
            await engine.dispose()
            return
        output_payload = llm_result.outputs

        if job.owner_id:
            await create_run(
                session,
                owner_id=job.owner_id,
                run_type="LIBRARIAN",
                paragraph_id=None,
                document_id=document.id,
                provider=llm_result.metadata.provider,
                model=llm_result.metadata.model,
                prompt_version=llm_result.metadata.prompt_version,
                inputs_json=inputs_json,
                outputs_json=output_payload,
                token_prompt=llm_result.metadata.token_prompt,
                token_completion=llm_result.metadata.token_completion,
                cost_usd=llm_result.metadata.cost_usd,
                latency_ms=llm_result.metadata.latency_ms,
            )

        existing_facts = await session.scalar(
            select(Fact.id).where(Fact.document_id == document.id).limit(1)
        )
        if not existing_facts and job.owner_id:
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

            for fact_payload in output_payload.get("facts", []):
                span_data = fact_payload.get("source_span") or {}
                span_id = None
                if span_data.get("page") is not None:
                    span = Span(
                        document_id=document.id,
                        page=span_data.get("page"),
                        start_char=span_data.get("start_char"),
                        end_char=span_data.get("end_char"),
                        quote=span_data.get("quote"),
                    )
                    session.add(span)
                    await session.flush()
                    span_id = span.id
                fact = Fact(
                    owner_id=job.owner_id,
                    document_id=document.id,
                    span_id=span_id,
                    source_type=fact_payload.get("source_type", "PDF"),
                    content=fact_payload["content"],
                    qualifiers=fact_payload.get("qualifiers", {}),
                    confidence=fact_payload["confidence"],
                    is_uncertain=False,
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
