from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class RetrievedFact:
    fact_id: UUID
    score: float


class Retriever(Protocol):
    def retrieve(
        self,
        *,
        owner_id: UUID,
        query: str,
        allowed_fact_ids: list[UUID],
        limit: int = 10,
    ) -> list[RetrievedFact]: ...
