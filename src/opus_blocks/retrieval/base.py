from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class RetrievedFact:
    fact_id: UUID
    score: float


class Retriever(Protocol):
    def retrieve(
        self,
        *,
        session: AsyncSession,
        owner_id: UUID,
        query: str,
        allowed_fact_ids: list[UUID],
        limit: int = 10,
    ) -> list[RetrievedFact]: ...
