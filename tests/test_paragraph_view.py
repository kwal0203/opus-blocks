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


async def _create_paragraph(async_client: AsyncClient, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}

    manuscript_response = await async_client.post(
        "/api/v1/manuscripts",
        json={"title": "View Manuscript"},
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
    return fact_response.json(), document["id"]


@pytest.mark.anyio
async def test_paragraph_view_payload(async_client: AsyncClient) -> None:
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    paragraph = await _create_paragraph(async_client, token)
    fact, document_id = await _create_fact(async_client, token)

    attach_response = await async_client.post(
        f"/api/v1/manuscripts/{paragraph['manuscript_id']}/documents/{document_id}",
        headers=headers,
    )
    assert attach_response.status_code == 204

    sentence_response = await async_client.post(
        "/api/v1/sentences",
        json={
            "paragraph_id": paragraph["id"],
            "order": 1,
            "sentence_type": "topic",
            "text": "Background statement.",
            "is_user_edited": False,
        },
        headers=headers,
    )
    assert sentence_response.status_code == 201
    sentence = sentence_response.json()

    link_response = await async_client.post(
        "/api/v1/sentences/links",
        json={"sentence_id": sentence["id"], "fact_id": fact["id"], "score": 0.95},
        headers=headers,
    )
    assert link_response.status_code == 201

    view_response = await async_client.get(
        f"/api/v1/paragraphs/{paragraph['id']}/view", headers=headers
    )
    assert view_response.status_code == 200
    payload = view_response.json()
    assert payload["paragraph"]["id"] == paragraph["id"]
    assert payload["sentences"][0]["id"] == sentence["id"]
    assert payload["links"][0]["fact_id"] == fact["id"]
    assert payload["facts"][0]["id"] == fact["id"]
