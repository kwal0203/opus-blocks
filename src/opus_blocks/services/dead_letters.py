from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.models.dead_letter import DeadLetter


async def create_dead_letter(
    session: AsyncSession,
    *,
    job_id: UUID | None,
    task_name: str,
    payload_json: dict,
    error: str | None,
    retry_count: int,
) -> DeadLetter:
    dead_letter = DeadLetter(
        job_id=job_id,
        task_name=task_name,
        payload_json=payload_json,
        error=error,
        retry_count=retry_count,
    )
    session.add(dead_letter)
    await session.commit()
    await session.refresh(dead_letter)
    return dead_letter
