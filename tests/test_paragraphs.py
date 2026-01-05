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
async def test_create_manuscript_and_paragraph(async_client: AsyncClient) -> None:
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    manuscript_response = await async_client.post(
        "/api/v1/manuscripts",
        json={"title": "Sample Manuscript", "description": "Draft notes"},
        headers=headers,
    )
    assert manuscript_response.status_code == 201
    manuscript = manuscript_response.json()

    get_manuscript_response = await async_client.get(
        f"/api/v1/manuscripts/{manuscript['id']}", headers=headers
    )
    assert get_manuscript_response.status_code == 200
    assert get_manuscript_response.json()["id"] == manuscript["id"]

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
    assert paragraph["status"] == "CREATED"
    assert paragraph["spec_json"]["paragraph_id"] == paragraph["id"]

    get_response = await async_client.get(f"/api/v1/paragraphs/{paragraph['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == paragraph["id"]


@pytest.mark.anyio
async def test_invalid_paragraph_intent(async_client: AsyncClient) -> None:
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    manuscript_response = await async_client.post(
        "/api/v1/manuscripts",
        json={"title": "Invalid Intent Test"},
        headers=headers,
    )
    assert manuscript_response.status_code == 201
    manuscript = manuscript_response.json()

    spec_payload = {
        "section": "Methods",
        "intent": "Background Context",
        "required_structure": {
            "topic_sentence": True,
            "evidence_sentences": 1,
            "conclusion_sentence": False,
        },
        "allowed_fact_ids": [],
        "style": {
            "tense": "past",
            "voice": "academic",
            "target_length_words": [80, 120],
        },
        "constraints": {
            "forbidden_claims": ["novelty"],
            "allowed_scope": "as stated in facts only",
        },
    }

    response = await async_client.post(
        "/api/v1/paragraphs",
        json={"manuscript_id": manuscript["id"], "spec": spec_payload},
        headers=headers,
    )
    assert response.status_code == 422
