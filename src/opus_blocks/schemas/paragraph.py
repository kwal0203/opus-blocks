from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

_SECTION_INTENTS: dict[str, set[str]] = {
    "Introduction": {
        "Background Context",
        "Prior Work Summary",
        "Knowledge Gap",
        "Study Objective",
    },
    "Methods": {
        "Study Design",
        "Participants / Data Sources",
        "Procedures / Protocol",
        "Analysis Methods",
    },
    "Results": {
        "Primary Results",
        "Secondary Results",
        "Null / Negative Results",
    },
    "Discussion": {
        "Result Interpretation",
        "Comparison to Prior Work",
        "Limitations",
        "Implications / Future Work",
    },
}


class ParagraphStructure(BaseModel):
    topic_sentence: bool
    evidence_sentences: int = Field(..., ge=1)
    conclusion_sentence: bool


class ParagraphStyle(BaseModel):
    tense: str
    voice: str
    target_length_words: tuple[int, int]

    @model_validator(mode="after")
    def validate_length_range(self) -> "ParagraphStyle":
        minimum, maximum = self.target_length_words
        if minimum < 1 or maximum < 1 or minimum > maximum:
            raise ValueError("target_length_words must be a positive ascending range")
        return self


class ParagraphConstraints(BaseModel):
    forbidden_claims: list[str]
    allowed_scope: str


class ParagraphSpecInput(BaseModel):
    section: str
    intent: str
    required_structure: ParagraphStructure
    allowed_fact_ids: list[UUID] = Field(default_factory=list)
    style: ParagraphStyle
    constraints: ParagraphConstraints

    @model_validator(mode="after")
    def validate_intent(self) -> "ParagraphSpecInput":
        intents = _SECTION_INTENTS.get(self.section)
        if not intents:
            raise ValueError("section must be one of Introduction, Methods, Results, Discussion")
        if self.intent not in intents:
            raise ValueError("intent is not valid for the provided section")
        return self


class ParagraphSpec(ParagraphSpecInput):
    paragraph_id: UUID


class ParagraphCreate(BaseModel):
    manuscript_id: UUID
    spec: ParagraphSpecInput


class ParagraphRead(BaseModel):
    id: UUID
    manuscript_id: UUID
    section: str
    intent: str
    spec_json: dict
    allowed_fact_ids: list[UUID]
    status: str
    latest_run_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
