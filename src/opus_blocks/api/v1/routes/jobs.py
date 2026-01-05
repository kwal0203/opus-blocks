from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from opus_blocks.api.deps import CurrentUser, DbSession
from opus_blocks.schemas.job import JobRead
from opus_blocks.services.jobs import get_job

router = APIRouter(prefix="/jobs")


@router.get("/{job_id}", response_model=JobRead)
async def get_job_status(
    job_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
) -> JobRead:
    job = await get_job(session, current_user.id, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return JobRead.model_validate(job)
