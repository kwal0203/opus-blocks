from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class VectorMatch:
    fact_id: UUID
    score: float


class VectorStore(Protocol):
    async def upsert_fact(
        self,
        *,
        session: AsyncSession,
        fact_id: UUID,
        content: str,
        namespace: str,
        embedding: list[float] | None = None,
    ) -> None: ...

    async def query(
        self,
        *,
        session: AsyncSession,
        query: str,
        namespace: str,
        allowed_fact_ids: list[UUID],
        limit: int = 10,
    ) -> list[VectorMatch]: ...

    async def delete_fact(
        self,
        *,
        session: AsyncSession,
        fact_id: UUID,
        namespace: str,
    ) -> None: ...
