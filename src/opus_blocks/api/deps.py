from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.db.session import get_session

DbSession = Annotated[AsyncSession, Depends(get_session)]
