from uuid import UUID

from pydantic import BaseModel


class FactSuggestion(BaseModel):
    fact_id: UUID
    score: float
