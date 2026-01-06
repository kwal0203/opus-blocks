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
        json={"title": "Sentence Manuscript"},
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
    return fact_response.json()


@pytest.mark.anyio
async def test_sentence_and_fact_links(async_client: AsyncClient) -> None:
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    paragraph = await _create_paragraph(async_client, token)
    fact = await _create_fact(async_client, token)

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

    list_response = await async_client.get(
        f"/api/v1/sentences/paragraph/{paragraph['id']}", headers=headers
    )
    assert list_response.status_code == 200
    sentences = list_response.json()
    assert len(sentences) == 1
    assert sentences[0]["id"] == sentence["id"]

    link_response = await async_client.post(
        "/api/v1/sentences/links",
        json={"sentence_id": sentence["id"], "fact_id": fact["id"], "score": 0.95},
        headers=headers,
    )
    assert link_response.status_code == 201
    link = link_response.json()
    assert link["sentence_id"] == sentence["id"]
    assert link["fact_id"] == fact["id"]

    links_response = await async_client.get(
        f"/api/v1/sentences/{sentence['id']}/links", headers=headers
    )
    assert links_response.status_code == 200
    links = links_response.json()
    assert len(links) == 1
    assert links[0]["fact_id"] == fact["id"]

    verify_response = await async_client.post(
        f"/api/v1/sentences/{sentence['id']}/verify",
        json={
            "supported": True,
            "verifier_failure_modes": [],
            "verifier_explanation": None,
        },
        headers=headers,
    )
    assert verify_response.status_code == 200
    verified_sentence = verify_response.json()
    assert verified_sentence["supported"] is True

    runs_response = await async_client.get(
        f"/api/v1/paragraphs/{paragraph['id']}/runs", headers=headers
    )
    assert runs_response.status_code == 200
    runs = runs_response.json()
    assert any(run["run_type"] == "VERIFIER" for run in runs)


@pytest.mark.anyio
async def test_verify_requires_fact_links(async_client: AsyncClient) -> None:
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    paragraph = await _create_paragraph(async_client, token)

    sentence_response = await async_client.post(
        "/api/v1/sentences",
        json={
            "paragraph_id": paragraph["id"],
            "order": 1,
            "sentence_type": "topic",
            "text": "Unsupported sentence.",
            "is_user_edited": False,
        },
        headers=headers,
    )
    assert sentence_response.status_code == 201
    sentence = sentence_response.json()

    verify_response = await async_client.post(
        f"/api/v1/sentences/{sentence['id']}/verify",
        json={"supported": True, "verifier_failure_modes": [], "verifier_explanation": None},
        headers=headers,
    )
    assert verify_response.status_code == 400


@pytest.mark.anyio
async def test_edit_sentence_triggers_reverify(async_client: AsyncClient) -> None:
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    paragraph = await _create_paragraph(async_client, token)

    sentence_response = await async_client.post(
        "/api/v1/sentences",
        json={
            "paragraph_id": paragraph["id"],
            "order": 1,
            "sentence_type": "topic",
            "text": "Original sentence.",
            "is_user_edited": False,
        },
        headers=headers,
    )
    assert sentence_response.status_code == 201
    sentence = sentence_response.json()

    verify_response = await async_client.post(
        f"/api/v1/sentences/{sentence['id']}/verify",
        json={
            "supported": True,
            "verifier_failure_modes": [],
            "verifier_explanation": None,
        },
        headers=headers,
    )
    assert verify_response.status_code == 200

    edit_response = await async_client.patch(
        f"/api/v1/sentences/{sentence['id']}",
        json={"text": "Edited sentence."},
        headers=headers,
    )
    assert edit_response.status_code == 200
    edit_job = edit_response.json()
    assert edit_job["job_type"] == "VERIFY_PARAGRAPH"
    assert edit_job["status"] == "QUEUED"

    paragraph_response = await async_client.get(
        f"/api/v1/paragraphs/{paragraph['id']}", headers=headers
    )
    assert paragraph_response.status_code == 200
    assert paragraph_response.json()["status"] == "PENDING_VERIFY"

    list_response = await async_client.get(
        f"/api/v1/sentences/paragraph/{paragraph['id']}", headers=headers
    )
    assert list_response.status_code == 200
    sentences = list_response.json()
    assert sentences[0]["text"] == "Edited sentence."
    assert sentences[0]["is_user_edited"] is True
    assert sentences[0]["supported"] is False
    assert sentences[0]["verifier_failure_modes"] == []
    assert sentences[0]["verifier_explanation"] is None
