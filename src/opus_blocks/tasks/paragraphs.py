import asyncio
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from opus_blocks.contracts.agent_contracts import (
    validate_verifier_output,
    validate_writer_output,
)
from opus_blocks.core.config import settings
from opus_blocks.llm.provider import get_llm_provider
from opus_blocks.models.fact import Fact
from opus_blocks.models.job import Job
from opus_blocks.models.paragraph import Paragraph
from opus_blocks.models.sentence import Sentence
from opus_blocks.models.sentence_fact_link import SentenceFactLink
from opus_blocks.tasks.celery_app import celery_app


def _build_session_factory() -> tuple[async_sessionmaker, AsyncEngine]:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return session_factory, engine


async def run_generate_job(job_id: UUID, paragraph_id: UUID) -> None:
    session_factory, engine = _build_session_factory()
    async with session_factory() as session:
        job = await session.scalar(select(Job).where(Job.id == job_id))
        paragraph = await session.scalar(select(Paragraph).where(Paragraph.id == paragraph_id))
        if not job or not paragraph:
            await engine.dispose()
            return

        job.status = "RUNNING"
        session.add(job)
        await session.commit()

        existing_sentence = await session.scalar(
            select(Sentence).where(Sentence.paragraph_id == paragraph.id).limit(1)
        )
        if not existing_sentence:
            linked_fact = None
            if paragraph.allowed_fact_ids and job.owner_id:
                linked_fact = await session.scalar(
                    select(Fact)
                    .where(
                        Fact.id.in_(paragraph.allowed_fact_ids),
                        Fact.owner_id == job.owner_id,
                    )
                    .limit(1)
                )

            provider = get_llm_provider()
            writer_result = provider.generate_paragraph(
                paragraph_id=paragraph.id,
                section=paragraph.section,
                intent=paragraph.intent,
                allowed_fact_ids=paragraph.allowed_fact_ids,
                linked_fact_id=linked_fact.id if linked_fact else None,
            )
            writer_payload = writer_result.outputs

            try:
                validate_writer_output(
                    writer_payload, allowed_fact_ids=set(paragraph.allowed_fact_ids)
                )
            except ValueError:
                paragraph.status = "FAILED_GENERATION"
                job.status = "FAILED"
                session.add(paragraph)
                session.add(job)
                await session.commit()
                await engine.dispose()
                return

            for sentence_payload in writer_payload["paragraph"].get("sentences", []):
                sentence = Sentence(
                    paragraph_id=paragraph.id,
                    order=sentence_payload["order"],
                    sentence_type=sentence_payload["sentence_type"],
                    text=sentence_payload["text"],
                    is_user_edited=False,
                    supported=False,
                )
                session.add(sentence)
                await session.flush()

                for citation in sentence_payload.get("citations", []):
                    session.add(
                        SentenceFactLink(
                            sentence_id=sentence.id,
                            fact_id=UUID(str(citation)),
                            score=0.5,
                        )
                    )

        paragraph.status = "PENDING_VERIFY"
        job.status = "SUCCEEDED"
        session.add(paragraph)
        session.add(job)
        await session.commit()

    await engine.dispose()


async def run_verify_job(job_id: UUID, paragraph_id: UUID) -> None:
    session_factory, engine = _build_session_factory()
    async with session_factory() as session:
        job = await session.scalar(select(Job).where(Job.id == job_id))
        paragraph = await session.scalar(select(Paragraph).where(Paragraph.id == paragraph_id))
        if not job or not paragraph:
            await engine.dispose()
            return

        job.status = "RUNNING"
        session.add(job)
        await session.commit()

        sentences_result = await session.execute(
            select(Sentence).where(Sentence.paragraph_id == paragraph.id)
        )
        sentences = list(sentences_result.scalars().all())
        sentence_inputs: list[dict] = []
        for sentence in sentences:
            has_links = await session.scalar(
                select(SentenceFactLink).where(SentenceFactLink.sentence_id == sentence.id).limit(1)
            )
            sentence_inputs.append({"order": sentence.order, "has_links": bool(has_links)})

        provider = get_llm_provider()
        verifier_result = provider.verify_paragraph(
            paragraph_id=paragraph.id, sentence_inputs=sentence_inputs
        )
        verifier_payload = verifier_result.outputs
        try:
            validate_verifier_output(verifier_payload, sentence_orders=[s.order for s in sentences])
        except ValueError:
            job.status = "FAILED"
            paragraph.status = "NEEDS_REVISION"
            session.add(paragraph)
            session.add(job)
            await session.commit()
            await engine.dispose()
            return

        for sentence in sentences:
            result = next(
                item
                for item in verifier_payload["sentence_results"]
                if item["order"] == sentence.order
            )
            sentence.supported = result["verdict"] == "PASS"
            sentence.verifier_failure_modes = result.get("failure_modes", [])
            sentence.verifier_explanation = result.get("explanation")
            session.add(sentence)

        paragraph.status = "VERIFIED" if verifier_payload["overall_pass"] else "NEEDS_REVISION"
        job.status = "SUCCEEDED"
        session.add(paragraph)
        session.add(job)
        await session.commit()

    await engine.dispose()


@celery_app.task(name="generate_paragraph")
def generate_paragraph(job_id: str, paragraph_id: str) -> None:
    asyncio.run(run_generate_job(uuid.UUID(job_id), uuid.UUID(paragraph_id)))


@celery_app.task(name="verify_paragraph")
def verify_paragraph(job_id: str, paragraph_id: str) -> None:
    asyncio.run(run_verify_job(uuid.UUID(job_id), uuid.UUID(paragraph_id)))
