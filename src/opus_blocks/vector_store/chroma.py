from uuid import UUID

import chromadb
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.core.config import settings
from opus_blocks.services.embeddings import embed_text
from opus_blocks.vector_store.base import VectorMatch, VectorStore


class ChromaVectorStore(VectorStore):
    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(path=settings.vector_persist_path)
        self._collection = self._client.get_or_create_collection(name=settings.vector_collection)

    async def upsert_fact(
        self,
        *,
        session: AsyncSession,
        fact_id: UUID,
        content: str,
        namespace: str,
        embedding: list[float] | None = None,
    ) -> None:
        embedding_value = embedding or embed_text(content)
        self._collection.upsert(
            ids=[str(fact_id)],
            embeddings=[embedding_value],
            metadatas=[{"fact_id": str(fact_id), "namespace": namespace}],
            documents=[content],
        )

    async def query(
        self,
        *,
        session: AsyncSession,
        query: str,
        namespace: str,
        allowed_fact_ids: list[UUID],
        limit: int = 10,
    ) -> list[VectorMatch]:
        if not allowed_fact_ids:
            return []
        query_embedding = embed_text(query)
        response = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where={
                "namespace": namespace,
                "fact_id": {"$in": [str(fact_id) for fact_id in allowed_fact_ids]},
            },
            include=["metadatas", "distances"],
        )
        matches: list[VectorMatch] = []
        for metadata, distance in zip(
            response.get("metadatas", [[]])[0],
            response.get("distances", [[]])[0],
            strict=False,
        ):
            if not metadata:
                continue
            matches.append(
                VectorMatch(
                    fact_id=UUID(metadata["fact_id"]),
                    score=_distance_to_score(distance),
                )
            )
        return matches

    async def delete_fact(
        self,
        *,
        session: AsyncSession,
        fact_id: UUID,
        namespace: str,
    ) -> None:
        self._collection.delete(
            ids=[str(fact_id)],
            where={"namespace": namespace},
        )


def _distance_to_score(distance: float) -> float:
    if distance is None:
        return 0.0
    return 1.0 / (1.0 + distance)
