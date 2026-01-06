import os
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from opus_blocks.core.config import settings
from opus_blocks.models.fact_embedding import FactEmbedding
from opus_blocks.retrieval.vector import VectorStoreRetriever
from opus_blocks.tools.embeddings_backfill import run_backfill


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

    original_url = settings.database_url
    settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
    try:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            result = await session.execute(
                select(FactEmbedding).where(FactEmbedding.fact_id == fact["id"])
            )
            embedding = result.scalar_one_or_none()
            assert embedding is not None
        await engine.dispose()
    finally:
        settings.database_url = original_url


@pytest.mark.anyio
async def test_retriever_orders_by_similarity(async_client: AsyncClient) -> None:
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

    alpha_response = await async_client.post(
        "/api/v1/facts/manual",
        json={"content": "alpha fact"},
        headers=headers,
    )
    assert alpha_response.status_code == 201
    alpha_fact = alpha_response.json()

    beta_response = await async_client.post(
        "/api/v1/facts/manual",
        json={"content": "beta fact"},
        headers=headers,
    )
    assert beta_response.status_code == 201
    beta_fact = beta_response.json()

    original_url = settings.database_url
    settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
    try:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            retriever = VectorStoreRetriever()
            results = await retriever.retrieve(
                session=session,
                owner_id=uuid.UUID(alpha_fact["owner_id"]),
                query="alpha",
                allowed_fact_ids=[
                    uuid.UUID(alpha_fact["id"]),
                    uuid.UUID(beta_fact["id"]),
                ],
                limit=2,
            )
            assert results[0].fact_id == uuid.UUID(alpha_fact["id"])
        await engine.dispose()
    finally:
        settings.database_url = original_url


@pytest.mark.anyio
async def test_backfill_embeddings_recreates_missing(async_client: AsyncClient) -> None:
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
        json={"content": "alpha fact"},
        headers=headers,
    )
    assert fact_response.status_code == 201
    fact = fact_response.json()

    original_url = settings.database_url
    settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
    try:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            result = await session.execute(
                select(FactEmbedding).where(FactEmbedding.fact_id == fact["id"])
            )
            embedding = result.scalar_one_or_none()
            assert embedding is not None
            await session.delete(embedding)
            await session.commit()

        await run_backfill(owner_id=fact["owner_id"], limit=None)

        async with session_factory() as session:
            result = await session.execute(
                select(FactEmbedding).where(FactEmbedding.fact_id == fact["id"])
            )
            embedding = result.scalar_one_or_none()
            assert embedding is not None
        await engine.dispose()
    finally:
        settings.database_url = original_url
