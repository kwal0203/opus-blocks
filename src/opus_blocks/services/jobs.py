import logging
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.core.config import settings
from opus_blocks.models.job import Job
from opus_blocks.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def create_job(
    session: AsyncSession,
    owner_id: UUID,
    job_type: str,
    target_id: UUID,
    status: str = "QUEUED",
    trace_id: str | None = None,
) -> Job:
    job = Job(
        owner_id=owner_id,
        job_type=job_type,
        target_id=target_id,
        status=status,
        trace_id=trace_id or str(uuid.uuid4()),
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_job(session: AsyncSession, owner_id: UUID, job_id: UUID) -> Job | None:
    result = await session.execute(select(Job).where(Job.id == job_id, Job.owner_id == owner_id))
    return result.scalar_one_or_none()


def enqueue_job(task_name: str, *args: UUID) -> None:
    if not settings.jobs_enqueue_enabled:
        logger.debug("Job dispatch disabled; skipping %s", task_name)
        return
    celery_app.send_task(task_name, args=[str(arg) for arg in args])
