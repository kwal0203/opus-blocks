import uuid

import pytest
from httpx import AsyncClient


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


@pytest.mark.anyio
async def test_generate_and_verify_jobs(async_client: AsyncClient) -> None:
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    manuscript_response = await async_client.post(
        "/api/v1/manuscripts",
        json={"title": "Job Manuscript"},
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
    paragraph = paragraph_response.json()

    generate_response = await async_client.post(
        f"/api/v1/paragraphs/{paragraph['id']}/generate", headers=headers
    )
    assert generate_response.status_code == 200
    generate_job = generate_response.json()
    assert generate_job["job_type"] == "GENERATE_PARAGRAPH"
    assert generate_job["status"] == "QUEUED"

    paragraph_after_generate = await async_client.get(
        f"/api/v1/paragraphs/{paragraph['id']}", headers=headers
    )
    assert paragraph_after_generate.status_code == 200
    assert paragraph_after_generate.json()["status"] == "GENERATING"

    verify_response = await async_client.post(
        f"/api/v1/paragraphs/{paragraph['id']}/verify", headers=headers
    )
    assert verify_response.status_code == 200
    verify_job = verify_response.json()
    assert verify_job["job_type"] == "VERIFY_PARAGRAPH"
    assert verify_job["status"] == "QUEUED"

    paragraph_after_verify = await async_client.get(
        f"/api/v1/paragraphs/{paragraph['id']}", headers=headers
    )
    assert paragraph_after_verify.status_code == 200
    assert paragraph_after_verify.json()["status"] == "PENDING_VERIFY"
