import asyncio
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from opus_blocks.core.config import settings
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

            sentence = Sentence(
                paragraph_id=paragraph.id,
                order=1,
                sentence_type="topic",
                text="Placeholder generated sentence.",
                is_user_edited=False,
                supported=False,
            )
            session.add(sentence)
            await session.flush()

            if linked_fact:
                session.add(
                    SentenceFactLink(
                        sentence_id=sentence.id,
                        fact_id=linked_fact.id,
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

        paragraph.status = "VERIFIED"
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
