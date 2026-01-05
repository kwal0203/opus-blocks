from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobRead(BaseModel):
    id: UUID
    owner_id: UUID | None = None
    job_type: str
    target_id: UUID
    status: str
    progress: dict
    error: str | None = None
    trace_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
