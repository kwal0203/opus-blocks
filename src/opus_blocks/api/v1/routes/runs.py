from uuid import UUID

from fastapi import APIRouter

from opus_blocks.api.deps import CurrentUser, DbSession
from opus_blocks.schemas.run import RunRead
from opus_blocks.services.runs import list_runs_filtered

router = APIRouter(prefix="/runs")


@router.get("", response_model=list[RunRead])
async def list_runs(
    session: DbSession,
    user: CurrentUser,
    run_type: str | None = None,
    paragraph_id: UUID | None = None,
    document_id: UUID | None = None,
) -> list[RunRead]:
    runs = await list_runs_filtered(
        session,
        owner_id=user.id,
        run_type=run_type,
        paragraph_id=paragraph_id,
        document_id=document_id,
    )
    return [RunRead.model_validate(run) for run in runs]
