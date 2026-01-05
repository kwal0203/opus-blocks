from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RunRead(BaseModel):
    id: UUID
    owner_id: UUID | None
    paragraph_id: UUID | None
    document_id: UUID | None
    run_type: str
    provider: str
    model: str
    prompt_version: str
    input_hash: str
    inputs_json: dict
    outputs_json: dict
    token_prompt: int | None
    token_completion: int | None
    cost_usd: float | None
    latency_ms: int | None
    trace_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
