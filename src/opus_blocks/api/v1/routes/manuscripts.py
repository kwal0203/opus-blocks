from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from opus_blocks.api.deps import CurrentUser, DbSession
from opus_blocks.schemas.manuscript import ManuscriptCreate, ManuscriptRead
from opus_blocks.services.manuscripts import create_manuscript, get_manuscript

router = APIRouter(prefix="/manuscripts")


@router.post("", response_model=ManuscriptRead, status_code=status.HTTP_201_CREATED)
async def create_manuscript_endpoint(
    manuscript_in: ManuscriptCreate, session: DbSession, user: CurrentUser
) -> ManuscriptRead:
    manuscript = await create_manuscript(
        session, owner_id=user.id, title=manuscript_in.title, description=manuscript_in.description
    )
    return ManuscriptRead.model_validate(manuscript)


@router.get("/{manuscript_id}", response_model=ManuscriptRead)
async def get_manuscript_endpoint(
    manuscript_id: UUID, session: DbSession, user: CurrentUser
) -> ManuscriptRead:
    manuscript = await get_manuscript(session, owner_id=user.id, manuscript_id=manuscript_id)
    if not manuscript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")
    return ManuscriptRead.model_validate(manuscript)
