import os
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient

from opus_blocks.core.config import settings
from opus_blocks.tasks.paragraphs import run_generate_job, run_verify_job


async def _register_and_login(async_client: AsyncClient) -> str:
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
    return login_response.json()["access_token"]


async def _create_paragraph(
    async_client: AsyncClient, token: str, allowed_fact_ids: list[str] | None = None
) -> dict:
    headers = {"Authorization": f"Bearer {token}"}

    manuscript_response = await async_client.post(
        "/api/v1/manuscripts",
        json={"title": "Worker Manuscript"},
        headers=headers,
    )
    assert manuscript_response.status_code == 201
    manuscript = manuscript_response.json()

    spec_payload = {
        "section": "Introduction",
        "intent": "Background Context",
        "required_structure": {
            "topic_sentence": True,
            "evidence_sentences": 2,
            "conclusion_sentence": True,
        },
        "allowed_fact_ids": allowed_fact_ids or [],
        "style": {
            "tense": "present",
            "voice": "academic",
            "target_length_words": [120, 150],
        },
        "constraints": {
            "forbidden_claims": ["novelty"],
            "allowed_scope": "as stated in facts only",
        },
    }
    paragraph_response = await async_client.post(
        "/api/v1/paragraphs",
        json={"manuscript_id": manuscript["id"], "spec": spec_payload},
        headers=headers,
    )
    assert paragraph_response.status_code == 201
    return paragraph_response.json()


async def _create_fact(async_client: AsyncClient, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    document_response = await async_client.post(
        "/api/v1/documents/upload",
        files={"file": ("example.pdf", b"%PDF-1.4 test", "application/pdf")},
        headers=headers,
    )
    assert document_response.status_code == 201
    document = document_response.json()

    fact_response = await async_client.post(
        f"/api/v1/documents/{document['id']}/facts",
        json={
            "content": "PDF fact content.",
            "qualifiers": {},
            "confidence": 1.0,
            "is_uncertain": False,
            "span": {
                "page": 1,
                "start_char": 0,
                "end_char": 5,
                "quote": "facts",
            },
        },
        headers=headers,
    )
    assert fact_response.status_code == 201
    return fact_response.json()


@pytest.mark.anyio
async def test_worker_updates_generate_and_verify(
    async_client: AsyncClient, tmp_path: Path
) -> None:
    original_root = settings.storage_root
    settings.storage_root = str(tmp_path)
    try:
        token = await _register_and_login(async_client)
        headers = {"Authorization": f"Bearer {token}"}
        paragraph = await _create_paragraph(async_client, token)

        generate_response = await async_client.post(
            f"/api/v1/paragraphs/{paragraph['id']}/generate", headers=headers
        )
        assert generate_response.status_code == 200
        generate_job = generate_response.json()

        original_url = settings.database_url
        settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
        try:
            await run_generate_job(uuid.UUID(generate_job["id"]), uuid.UUID(paragraph["id"]))
        finally:
            settings.database_url = original_url

        job_response = await async_client.get(f"/api/v1/jobs/{generate_job['id']}", headers=headers)
        assert job_response.status_code == 200
        assert job_response.json()["status"] == "SUCCEEDED"

        paragraph_response = await async_client.get(
            f"/api/v1/paragraphs/{paragraph['id']}", headers=headers
        )
        assert paragraph_response.status_code == 200
        assert paragraph_response.json()["status"] == "PENDING_VERIFY"

        sentences_response = await async_client.get(
            f"/api/v1/sentences/paragraph/{paragraph['id']}", headers=headers
        )
        assert sentences_response.status_code == 200
        sentences = sentences_response.json()
        assert len(sentences) == 1
        assert sentences[0]["text"] == "Placeholder generated sentence."

        verify_response = await async_client.post(
            f"/api/v1/paragraphs/{paragraph['id']}/verify", headers=headers
        )
        assert verify_response.status_code == 200
        verify_job = verify_response.json()

        settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
        try:
            await run_verify_job(uuid.UUID(verify_job["id"]), uuid.UUID(paragraph["id"]))
        finally:
            settings.database_url = original_url

        verify_job_response = await async_client.get(
            f"/api/v1/jobs/{verify_job['id']}", headers=headers
        )
        assert verify_job_response.status_code == 200
        assert verify_job_response.json()["status"] == "SUCCEEDED"

        paragraph_after_verify = await async_client.get(
            f"/api/v1/paragraphs/{paragraph['id']}", headers=headers
        )
        assert paragraph_after_verify.status_code == 200
        assert paragraph_after_verify.json()["status"] == "VERIFIED"
    finally:
        settings.storage_root = original_root


@pytest.mark.anyio
async def test_verify_rollup_requires_supported_sentences(
    async_client: AsyncClient, tmp_path: Path
) -> None:
    original_root = settings.storage_root
    settings.storage_root = str(tmp_path)
    try:
        token = await _register_and_login(async_client)
        headers = {"Authorization": f"Bearer {token}"}
        paragraph = await _create_paragraph(async_client, token)

        sentence_response = await async_client.post(
            "/api/v1/sentences",
            json={
                "paragraph_id": paragraph["id"],
                "order": 1,
                "sentence_type": "topic",
                "text": "Needs verification.",
                "is_user_edited": False,
            },
            headers=headers,
        )
        assert sentence_response.status_code == 201
        sentence = sentence_response.json()

        verify_response = await async_client.post(
            f"/api/v1/sentences/{sentence['id']}/verify",
            json={
                "supported": False,
                "verifier_failure_modes": ["missing_evidence"],
                "verifier_explanation": None,
            },
            headers=headers,
        )
        assert verify_response.status_code == 200

        rollup_response = await async_client.post(
            f"/api/v1/paragraphs/{paragraph['id']}/verify-rollup", headers=headers
        )
        assert rollup_response.status_code == 200
        assert rollup_response.json()["status"] == "NEEDS_REVISION"
    finally:
        settings.storage_root = original_root


@pytest.mark.anyio
async def test_generate_creates_sentence_links(async_client: AsyncClient, tmp_path: Path) -> None:
    original_root = settings.storage_root
    settings.storage_root = str(tmp_path)
    try:
        token = await _register_and_login(async_client)
        headers = {"Authorization": f"Bearer {token}"}
        fact = await _create_fact(async_client, token)
        paragraph = await _create_paragraph(async_client, token, [fact["id"]])

        generate_response = await async_client.post(
            f"/api/v1/paragraphs/{paragraph['id']}/generate", headers=headers
        )
        assert generate_response.status_code == 200
        generate_job = generate_response.json()

        original_url = settings.database_url
        settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
        try:
            await run_generate_job(uuid.UUID(generate_job["id"]), uuid.UUID(paragraph["id"]))
        finally:
            settings.database_url = original_url

        sentences_response = await async_client.get(
            f"/api/v1/sentences/paragraph/{paragraph['id']}", headers=headers
        )
        assert sentences_response.status_code == 200
        sentence = sentences_response.json()[0]

        links_response = await async_client.get(
            f"/api/v1/sentences/{sentence['id']}/links", headers=headers
        )
        assert links_response.status_code == 200
        links = links_response.json()
        assert len(links) == 1
        assert links[0]["fact_id"] == fact["id"]
    finally:
        settings.storage_root = original_root
