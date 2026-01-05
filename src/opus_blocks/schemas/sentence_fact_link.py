from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SentenceFactLinkCreate(BaseModel):
    sentence_id: UUID
    fact_id: UUID
    score: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_score(self) -> "SentenceFactLinkCreate":
        if self.score is not None and not (0.0 <= self.score <= 1.0):
            raise ValueError("score must be between 0 and 1")
        return self


class SentenceFactLinkRead(BaseModel):
    sentence_id: UUID
    fact_id: UUID
    score: float | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
