from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ManuscriptCreate(BaseModel):
    title: str
    description: str | None = None


class ManuscriptRead(BaseModel):
    id: UUID
    owner_id: UUID | None
    title: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
