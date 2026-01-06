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
async def test_suggest_facts_returns_ranked_matches(async_client: AsyncClient) -> None:
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    alpha_response = await async_client.post(
        "/api/v1/facts/manual",
        json={"content": "alpha evidence"},
        headers=headers,
    )
    assert alpha_response.status_code == 201
    alpha_fact = alpha_response.json()

    beta_response = await async_client.post(
        "/api/v1/facts/manual",
        json={"content": "beta evidence"},
        headers=headers,
    )
    assert beta_response.status_code == 201
    beta_fact = beta_response.json()

    manuscript_response = await async_client.post(
        "/api/v1/manuscripts",
        json={"title": "Suggest Manuscript"},
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
                "allowed_fact_ids": [alpha_fact["id"], beta_fact["id"]],
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
    paragraph = paragraph_response.json()

    suggest_response = await async_client.get(
        f"/api/v1/paragraphs/{paragraph['id']}/suggest-facts", headers=headers
    )
    assert suggest_response.status_code == 200
    suggestions = suggest_response.json()
    assert len(suggestions) == 2
    assert suggestions[0]["fact_id"] == alpha_fact["id"]
