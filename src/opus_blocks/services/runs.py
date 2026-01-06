import hashlib
import json
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.models.manuscript import Manuscript
from opus_blocks.models.paragraph import Paragraph
from opus_blocks.models.run import Run


def _hash_inputs(payload: dict) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def create_run(
    session: AsyncSession,
    owner_id: UUID,
    run_type: str,
    paragraph_id: UUID | None,
    document_id: UUID | None,
    provider: str,
    model: str,
    prompt_version: str,
    inputs_json: dict,
    outputs_json: dict,
    token_prompt: int | None = None,
    token_completion: int | None = None,
    cost_usd: float | None = None,
    latency_ms: int | None = None,
    trace_id: str | None = None,
) -> Run:
    run = Run(
        owner_id=owner_id,
        paragraph_id=paragraph_id,
        document_id=document_id,
        run_type=run_type,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        input_hash=_hash_inputs(inputs_json),
        inputs_json=inputs_json,
        outputs_json=outputs_json,
        token_prompt=token_prompt,
        token_completion=token_completion,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
        trace_id=trace_id or str(uuid.uuid4()),
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def list_paragraph_runs(
    session: AsyncSession, owner_id: UUID, paragraph_id: UUID
) -> list[Run]:
    result = await session.execute(
        select(Run)
        .join(Paragraph, Run.paragraph_id == Paragraph.id)
        .join(Manuscript, Paragraph.manuscript_id == Manuscript.id)
        .where(Run.paragraph_id == paragraph_id, Manuscript.owner_id == owner_id)
        .order_by(Run.created_at.asc())
    )
    return list(result.scalars().all())


async def list_document_runs(session: AsyncSession, owner_id: UUID, document_id: UUID) -> list[Run]:
    result = await session.execute(
        select(Run)
        .where(Run.document_id == document_id, Run.owner_id == owner_id)
        .order_by(Run.created_at.asc())
    )
    return list(result.scalars().all())


async def list_runs_filtered(
    session: AsyncSession,
    owner_id: UUID,
    run_type: str | None = None,
    paragraph_id: UUID | None = None,
    document_id: UUID | None = None,
) -> list[Run]:
    query = select(Run).where(Run.owner_id == owner_id)
    if run_type:
        query = query.where(Run.run_type == run_type)
    if paragraph_id:
        query = query.where(Run.paragraph_id == paragraph_id)
    if document_id:
        query = query.where(Run.document_id == document_id)
    result = await session.execute(query.order_by(Run.created_at.asc()))
    return list(result.scalars().all())
