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
from opus_blocks.retrieval import get_retriever
from opus_blocks.services.runs import get_latest_run_by_type, update_run_outputs
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
            allowed_facts: list[Fact] = []
            retrieved_facts: list[dict] = []
            retrieval_query = f"{paragraph.section} - {paragraph.intent}"
            if paragraph.allowed_fact_ids and job.owner_id:
                facts_result = await session.execute(
                    select(Fact).where(
                        Fact.id.in_(paragraph.allowed_fact_ids),
                        Fact.owner_id == job.owner_id,
                    )
                )
                allowed_facts = list(facts_result.scalars().all())
                retriever = get_retriever()
                retrieved = await retriever.retrieve(
                    session=session,
                    owner_id=job.owner_id,
                    query=retrieval_query,
                    allowed_fact_ids=paragraph.allowed_fact_ids,
                    limit=5,
                )
                retrieved_facts = [
                    {"fact_id": str(item.fact_id), "score": item.score} for item in retrieved
                ]

            writer_inputs = {
                "paragraph_id": str(paragraph.id),
                "paragraph_spec": paragraph.spec_json,
                "allowed_facts": [
                    {
                        "fact_id": str(fact.id),
                        "content": fact.content,
                        "qualifiers": fact.qualifiers,
                    }
                    for fact in allowed_facts
                ],
                "retrieval_query": retrieval_query,
                "retrieved_facts": retrieved_facts,
            }
            provider = get_llm_provider()
            try:
                writer_result = provider.generate_paragraph(inputs=writer_inputs)
            except Exception:
                try:
                    writer_result = provider.generate_paragraph(inputs=writer_inputs)
                except Exception as exc:
                    paragraph.status = "FAILED_GENERATION"
                    job.status = "FAILED"
                    job.error = f"LLM generate failed: {exc}"
                    session.add(paragraph)
                    session.add(job)
                    await session.commit()
                    await engine.dispose()
                    return
            writer_payload = writer_result.outputs

            try:
                validate_writer_output(
                    writer_payload, allowed_fact_ids=set(paragraph.allowed_fact_ids)
                )
            except ValueError:
                try:
                    writer_result = provider.generate_paragraph(inputs=writer_inputs)
                    writer_payload = writer_result.outputs
                    validate_writer_output(
                        writer_payload, allowed_fact_ids=set(paragraph.allowed_fact_ids)
                    )
                except ValueError as exc:
                    paragraph.status = "FAILED_GENERATION"
                    job.status = "FAILED"
                    job.error = f"Writer contract validation failed: {exc}"
                    job.progress = {
                        "invalid_outputs": writer_payload,
                    }
                    session.add(paragraph)
                    session.add(job)
                    await session.commit()
                    await engine.dispose()
                    return

            latest_run = await get_latest_run_by_type(session, paragraph.id, "WRITER")
            if latest_run:
                await update_run_outputs(
                    session,
                    run_id=latest_run.id,
                    outputs_json=writer_payload,
                    token_prompt=writer_result.metadata.token_prompt,
                    token_completion=writer_result.metadata.token_completion,
                    cost_usd=writer_result.metadata.cost_usd,
                    latency_ms=writer_result.metadata.latency_ms,
                )

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
        fact_map: dict[UUID, Fact] = {}
        if sentences and job.owner_id:
            facts_result = await session.execute(
                select(Fact).where(
                    Fact.owner_id == job.owner_id,
                )
            )
            fact_map = {fact.id: fact for fact in facts_result.scalars().all()}
        for sentence in sentences:
            link_rows = await session.execute(
                select(SentenceFactLink).where(SentenceFactLink.sentence_id == sentence.id)
            )
            links = list(link_rows.scalars().all())
            citation_ids = [link.fact_id for link in links]
            citations_payload = [
                {
                    "fact_id": str(fact_id),
                    "content": fact.content if (fact := fact_map.get(fact_id)) else None,
                    "qualifiers": fact.qualifiers if fact else {},
                }
                for fact_id in citation_ids
            ]
            sentence_inputs.append(
                {
                    "order": sentence.order,
                    "text": sentence.text,
                    "has_links": bool(citation_ids),
                    "citations": [str(fact_id) for fact_id in citation_ids],
                    "citation_facts": citations_payload,
                }
            )

        verifier_inputs = {
            "paragraph_id": str(paragraph.id),
            "sentences": sentence_inputs,
        }
        provider = get_llm_provider()
        try:
            verifier_result = provider.verify_paragraph(inputs=verifier_inputs)
        except Exception:
            try:
                verifier_result = provider.verify_paragraph(inputs=verifier_inputs)
            except Exception as exc:
                job.status = "FAILED"
                paragraph.status = "NEEDS_REVISION"
                job.error = f"LLM verify failed: {exc}"
                session.add(paragraph)
                session.add(job)
                await session.commit()
                await engine.dispose()
                return
        verifier_payload = verifier_result.outputs
        try:
            validate_verifier_output(verifier_payload, sentence_orders=[s.order for s in sentences])
        except ValueError:
            try:
                verifier_result = provider.verify_paragraph(inputs=verifier_inputs)
                verifier_payload = verifier_result.outputs
                validate_verifier_output(
                    verifier_payload, sentence_orders=[s.order for s in sentences]
                )
            except ValueError as exc:
                job.status = "FAILED"
                paragraph.status = "NEEDS_REVISION"
                job.error = f"Verifier contract validation failed: {exc}"
                job.progress = {
                    "invalid_outputs": verifier_payload,
                }
                session.add(paragraph)
                session.add(job)
                await session.commit()
                await engine.dispose()
                return

        latest_run = await get_latest_run_by_type(session, paragraph.id, "VERIFIER")
        if latest_run:
            await update_run_outputs(
                session,
                run_id=latest_run.id,
                outputs_json=verifier_payload,
                token_prompt=verifier_result.metadata.token_prompt,
                token_completion=verifier_result.metadata.token_completion,
                cost_usd=verifier_result.metadata.cost_usd,
                latency_ms=verifier_result.metadata.latency_ms,
            )

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
