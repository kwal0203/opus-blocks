from fastapi import APIRouter, status

from opus_blocks.api.deps import CurrentUser, DbSession
from opus_blocks.schemas.fact import FactRead, ManualFactCreate
from opus_blocks.services.facts import create_manual_fact

router = APIRouter(prefix="/facts")


@router.post("/manual", response_model=FactRead, status_code=status.HTTP_201_CREATED)
async def create_manual_fact_endpoint(
    fact_in: ManualFactCreate, session: DbSession, user: CurrentUser
) -> FactRead:
    fact = await create_manual_fact(session, owner_id=user.id, fact_in=fact_in)
    return FactRead.model_validate(fact)
