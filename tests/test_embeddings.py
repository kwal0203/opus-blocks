import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from opus_blocks.db.session import get_session
from opus_blocks.models.fact_embedding import FactEmbedding


@pytest.mark.anyio
async def test_fact_embeddings_created(async_client: AsyncClient) -> None:
    email = f"user-{uuid.uuid4()}@example.com"
    password = "Password123!"

    register_response = await async_client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert register_response.status_code == 201

    login_response = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    fact_response = await async_client.post(
        "/api/v1/facts/manual",
        json={"content": "Embedded fact"},
        headers=headers,
    )
    assert fact_response.status_code == 201
    fact = fact_response.json()

    manuscript_response = await async_client.post(
        "/api/v1/manuscripts",
        json={"title": "Embedding Manuscript"},
        headers=headers,
    )
    assert manuscript_response.status_code == 201
    manuscript = manuscript_response.json()

    paragraph_response = await async_client.post(
        "/api/v1/paragraphs",
        json={
            "manuscript_id": manuscript["id"],
            "spec": {
                "section": "Introduction",
                "intent": "Background Context",
                "required_structure": {
                    "topic_sentence": True,
                    "evidence_sentences": 1,
                    "conclusion_sentence": True,
                },
                "allowed_fact_ids": [fact["id"]],
                "style": {
                    "tense": "present",
                    "voice": "academic",
                    "target_length_words": [60, 90],
                },
                "constraints": {
                    "forbidden_claims": ["novelty"],
                    "allowed_scope": "facts only",
                },
            },
        },
        headers=headers,
    )
    assert paragraph_response.status_code == 201

    session_factory = async_client.app.dependency_overrides.get(get_session)
    assert session_factory is not None
    async for session in session_factory():
        result = await session.execute(
            select(FactEmbedding).where(FactEmbedding.fact_id == fact["id"])
        )
        embedding = result.scalar_one_or_none()
        assert embedding is not None
        break
