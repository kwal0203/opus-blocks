from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SentenceCreate(BaseModel):
    paragraph_id: UUID
    order: int = Field(..., ge=1)
    sentence_type: str
    text: str = Field(..., min_length=1)
    is_user_edited: bool = False

    @model_validator(mode="after")
    def validate_sentence_type(self) -> "SentenceCreate":
        allowed = {"topic", "evidence", "conclusion", "transition"}
        if self.sentence_type not in allowed:
            raise ValueError("sentence_type must be topic, evidence, conclusion, or transition")
        return self


class SentenceRead(BaseModel):
    id: UUID
    paragraph_id: UUID
    order: int
    sentence_type: str
    text: str
    is_user_edited: bool
    supported: bool
    verifier_failure_modes: list[str]
    verifier_explanation: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
