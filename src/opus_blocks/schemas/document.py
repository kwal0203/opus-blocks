from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentRead(BaseModel):
    id: UUID
    owner_id: UUID | None = None
    source_type: str
    filename: str
    content_hash: str
    storage_uri: str
    status: str
    metadata: dict = Field(alias="metadata_")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
