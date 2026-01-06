from uuid import UUID

from fastapi import APIRouter, status

from opus_blocks.api.deps import CurrentUser, DbSession
from opus_blocks.schemas.fact import FactRead, ManualFactCreate
from opus_blocks.services.facts import create_manual_fact, delete_fact

router = APIRouter(prefix="/facts")


@router.post("/manual", response_model=FactRead, status_code=status.HTTP_201_CREATED)
async def create_manual_fact_endpoint(
    fact_in: ManualFactCreate, session: DbSession, user: CurrentUser
) -> FactRead:
    fact = await create_manual_fact(session, owner_id=user.id, fact_in=fact_in)
    return FactRead.model_validate(fact)


@router.delete("/{fact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fact_endpoint(fact_id: UUID, session: DbSession, user: CurrentUser) -> None:
    await delete_fact(session, owner_id=user.id, fact_id=fact_id)
    return None
