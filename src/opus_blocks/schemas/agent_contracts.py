from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class SourceSpanOutput(BaseModel):
    document_id: UUID
    page: int | None = None
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, ge=0)
    quote: str | None = None

    @model_validator(mode="after")
    def validate_char_bounds(self) -> "SourceSpanOutput":
        if (self.start_char is None) != (self.end_char is None):
            raise ValueError("start_char and end_char must both be set or both be null")
        if self.start_char is not None and self.end_char is not None:
            if self.start_char > self.end_char:
                raise ValueError("start_char must be <= end_char")
        return self


class AtomicFactOutput(BaseModel):
    content: str = Field(..., min_length=1)
    source_type: Literal["PDF", "MANUAL"]
    source_span: SourceSpanOutput
    qualifiers: dict = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)


class UncertainFactOutput(BaseModel):
    content: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    source_span: SourceSpanOutput


class LibrarianOutput(BaseModel):
    facts: list[AtomicFactOutput]
    uncertain_facts: list[UncertainFactOutput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_facts(self) -> "LibrarianOutput":
        normalized = [fact.content.strip().lower() for fact in self.facts]
        if len(set(normalized)) != len(normalized):
            raise ValueError("facts must be unique by normalized content")
        return self


class WriterSentenceOutput(BaseModel):
    order: int = Field(..., ge=1)
    sentence_type: Literal["topic", "evidence", "conclusion", "transition"]
    text: str = Field(..., min_length=1)
    citations: list[UUID]

    @model_validator(mode="after")
    def validate_citations(self) -> "WriterSentenceOutput":
        if not self.citations:
            raise ValueError("citations must be non-empty for each sentence")
        return self


class MissingEvidenceOutput(BaseModel):
    needed_for: str = Field(..., min_length=1)
    why_missing: str = Field(..., min_length=1)
    suggested_fact_type: str = Field(..., min_length=1)


class WriterParagraphOutput(BaseModel):
    section: str
    intent: str
    sentences: list[WriterSentenceOutput] = Field(default_factory=list)
    missing_evidence: list[MissingEvidenceOutput] = Field(default_factory=list)


class WriterOutput(BaseModel):
    paragraph: WriterParagraphOutput


class VerifierSentenceResult(BaseModel):
    order: int = Field(..., ge=1)
    verdict: Literal["PASS", "FAIL"]
    failure_modes: list[str] = Field(default_factory=list)
    explanation: str = Field(..., min_length=1)
    required_fix: str = Field(..., min_length=1)
    suggested_rewrite: str | None = None

    @model_validator(mode="after")
    def validate_failure_modes(self) -> "VerifierSentenceResult":
        if self.verdict == "FAIL" and not self.failure_modes:
            raise ValueError("FAIL verdicts require failure_modes")
        return self


class VerifierOutput(BaseModel):
    overall_pass: bool
    sentence_results: list[VerifierSentenceResult]
    missing_evidence_summary: list[dict] = Field(default_factory=list)
