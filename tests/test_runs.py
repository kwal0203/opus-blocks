import os
import uuid

import pytest
from httpx import AsyncClient

from opus_blocks.core.config import settings
from opus_blocks.tasks.documents import run_extract_facts_job


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


async def _create_paragraph(async_client: AsyncClient, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}

    manuscript_response = await async_client.post(
        "/api/v1/manuscripts",
        json={"title": "Runs Manuscript"},
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
        "allowed_fact_ids": [],
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


async def _create_document(async_client: AsyncClient, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    upload_response = await async_client.post(
        "/api/v1/documents/upload",
        files={"file": ("example.pdf", b"%PDF-1.4 test", "application/pdf")},
        headers=headers,
    )
    assert upload_response.status_code == 201
    return upload_response.json()


@pytest.mark.anyio
async def test_run_filters(async_client: AsyncClient) -> None:
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    paragraph = await _create_paragraph(async_client, token)
    document = await _create_document(async_client, token)

    generate_response = await async_client.post(
        f"/api/v1/paragraphs/{paragraph['id']}/generate", headers=headers
    )
    assert generate_response.status_code == 200

    extract_response = await async_client.post(
        f"/api/v1/documents/{document['id']}/extract_facts", headers=headers
    )
    assert extract_response.status_code == 200
    extract_job = extract_response.json()

    original_url = settings.database_url
    settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
    try:
        await run_extract_facts_job(uuid.UUID(extract_job["id"]), uuid.UUID(document["id"]))
    finally:
        settings.database_url = original_url

    all_runs_response = await async_client.get("/api/v1/runs", headers=headers)
    assert all_runs_response.status_code == 200
    all_runs = all_runs_response.json()
    assert len(all_runs) >= 2

    writer_runs_response = await async_client.get("/api/v1/runs?run_type=WRITER", headers=headers)
    assert writer_runs_response.status_code == 200
    writer_runs = writer_runs_response.json()
    assert len(writer_runs) >= 1
    assert all(run["run_type"] == "WRITER" for run in writer_runs)

    paragraph_runs_response = await async_client.get(
        f"/api/v1/runs?paragraph_id={paragraph['id']}", headers=headers
    )
    assert paragraph_runs_response.status_code == 200
    paragraph_runs = paragraph_runs_response.json()
    assert all(run["paragraph_id"] == paragraph["id"] for run in paragraph_runs)

    document_runs_response = await async_client.get(
        f"/api/v1/runs?document_id={document['id']}", headers=headers
    )
    assert document_runs_response.status_code == 200
    document_runs = document_runs_response.json()
    assert all(run["document_id"] == document["id"] for run in document_runs)
