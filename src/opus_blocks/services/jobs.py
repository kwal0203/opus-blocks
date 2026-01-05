from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.models.job import Job


async def create_job(
    session: AsyncSession,
    owner_id: UUID,
    job_type: str,
    target_id: UUID,
    status: str = "QUEUED",
) -> Job:
    job = Job(
        owner_id=owner_id,
        job_type=job_type,
        target_id=target_id,
        status=status,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_job(session: AsyncSession, owner_id: UUID, job_id: UUID) -> Job | None:
    result = await session.execute(select(Job).where(Job.id == job_id, Job.owner_id == owner_id))
    return result.scalar_one_or_none()
