from pydantic import BaseModel, Field


class SentenceVerificationUpdate(BaseModel):
    supported: bool
    verifier_failure_modes: list[str] = Field(default_factory=list)
    verifier_explanation: str | None = None
