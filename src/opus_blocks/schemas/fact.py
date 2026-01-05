from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from opus_blocks.schemas.span import SpanRead


class ManualFactCreate(BaseModel):
    content: str = Field(..., min_length=1)
    document_id: UUID | None = None
    qualifiers: dict = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    is_uncertain: bool = False


class FactRead(BaseModel):
    id: UUID
    owner_id: UUID | None
    document_id: UUID | None
    span_id: UUID | None
    source_type: str
    content: str
    qualifiers: dict
    confidence: float
    is_uncertain: bool
    created_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FactWithSpanRead(FactRead):
    span: SpanRead | None = None
