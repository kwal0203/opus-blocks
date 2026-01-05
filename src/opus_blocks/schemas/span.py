from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SpanBase(BaseModel):
    page: int | None = None
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, ge=0)
    quote: str | None = None

    @model_validator(mode="after")
    def validate_char_bounds(self) -> "SpanBase":
        if (self.start_char is None) != (self.end_char is None):
            raise ValueError("start_char and end_char must both be set or both be null")
        if self.start_char is not None and self.end_char is not None:
            if self.start_char > self.end_char:
                raise ValueError("start_char must be <= end_char")
        return self


class SpanCreate(SpanBase):
    document_id: UUID


class SpanInput(SpanBase):
    pass


class FactSpanCreate(BaseModel):
    content: str = Field(..., min_length=1)
    qualifiers: dict = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    is_uncertain: bool = False
    created_by: str = "LIBRARIAN"
    source_type: str = "PDF"
    span: SpanInput | None = None

    @model_validator(mode="after")
    def validate_source_type(self) -> "FactSpanCreate":
        if self.source_type != "PDF":
            raise ValueError("source_type must be PDF for span facts")
        return self


class SpanRead(SpanBase):
    id: UUID
    document_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
