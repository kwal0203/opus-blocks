from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.models.manuscript import Manuscript


async def create_manuscript(
    session: AsyncSession, owner_id: UUID, title: str, description: str | None
) -> Manuscript:
    manuscript = Manuscript(owner_id=owner_id, title=title, description=description)
    session.add(manuscript)
    await session.commit()
    await session.refresh(manuscript)
    return manuscript


async def get_manuscript(
    session: AsyncSession, owner_id: UUID, manuscript_id: UUID
) -> Manuscript | None:
    result = await session.execute(
        select(Manuscript).where(Manuscript.id == manuscript_id, Manuscript.owner_id == owner_id)
    )
    return result.scalar_one_or_none()
