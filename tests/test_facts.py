import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient

from opus_blocks.core.config import settings


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


async def _upload_document(async_client: AsyncClient, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    file_content = b"%PDF-1.4 test content"
    files = {"file": ("example.pdf", file_content, "application/pdf")}
    upload_response = await async_client.post(
        "/api/v1/documents/upload", files=files, headers=headers
    )
    assert upload_response.status_code == 201
    return upload_response.json()


@pytest.mark.anyio
async def test_manual_fact_and_listings(async_client: AsyncClient, tmp_path: Path) -> None:
    original_root = settings.storage_root
    settings.storage_root = str(tmp_path)
    try:
        token = await _register_and_login(async_client)
        headers = {"Authorization": f"Bearer {token}"}

        document = await _upload_document(async_client, token)

        manual_fact_payload = {
            "content": "Manual fact content.",
            "document_id": document["id"],
            "qualifiers": {"source": "note"},
            "confidence": 0.9,
            "is_uncertain": False,
        }
        fact_response = await async_client.post(
            "/api/v1/facts/manual", json=manual_fact_payload, headers=headers
        )
        assert fact_response.status_code == 201
        fact = fact_response.json()
        assert fact["source_type"] == "MANUAL"
        assert fact["created_by"] == "USER"

        list_response = await async_client.get(
            f"/api/v1/documents/{document['id']}/facts", headers=headers
        )
        assert list_response.status_code == 200
        facts = list_response.json()
        assert len(facts) == 1
        assert facts[0]["id"] == fact["id"]

        pdf_fact_payload = {
            "content": "PDF fact content.",
            "qualifiers": {"section": "intro"},
            "confidence": 0.75,
            "is_uncertain": False,
            "span": {
                "page": 1,
                "start_char": 0,
                "end_char": 12,
                "quote": "PDF excerpt",
            },
        }
        pdf_fact_response = await async_client.post(
            f"/api/v1/documents/{document['id']}/facts", json=pdf_fact_payload, headers=headers
        )
        assert pdf_fact_response.status_code == 201
        pdf_fact = pdf_fact_response.json()
        assert pdf_fact["source_type"] == "PDF"

        spans_response = await async_client.get(
            f"/api/v1/documents/{document['id']}/facts/with-spans", headers=headers
        )
        assert spans_response.status_code == 200
        spans_payload = spans_response.json()
        assert len(spans_payload) == 2
        span_fact = next(item for item in spans_payload if item["id"] == pdf_fact["id"])
        assert span_fact["span"]["quote"] == "PDF excerpt"

        manuscript_response = await async_client.post(
            "/api/v1/manuscripts",
            json={"title": "Fact Manuscript"},
            headers=headers,
        )
        assert manuscript_response.status_code == 201
        manuscript = manuscript_response.json()

        attach_response = await async_client.post(
            f"/api/v1/manuscripts/{manuscript['id']}/documents/{document['id']}",
            headers=headers,
        )
        assert attach_response.status_code == 204

        manuscript_facts_response = await async_client.get(
            f"/api/v1/manuscripts/{manuscript['id']}/facts", headers=headers
        )
        assert manuscript_facts_response.status_code == 200
        manuscript_facts = manuscript_facts_response.json()
        assert len(manuscript_facts) == 2
        assert {item["id"] for item in manuscript_facts} == {fact["id"], pdf_fact["id"]}

        manuscript_spans_response = await async_client.get(
            f"/api/v1/manuscripts/{manuscript['id']}/facts/with-spans", headers=headers
        )
        assert manuscript_spans_response.status_code == 200
        manuscript_spans = manuscript_spans_response.json()
        assert len(manuscript_spans) == 2
        manuscript_span_fact = next(
            item for item in manuscript_spans if item["id"] == pdf_fact["id"]
        )
        assert manuscript_span_fact["span"]["page"] == 1
    finally:
        settings.storage_root = original_root


@pytest.mark.anyio
async def test_delete_fact_removes_from_document(async_client: AsyncClient, tmp_path: Path) -> None:
    original_root = settings.storage_root
    settings.storage_root = str(tmp_path)
    try:
        token = await _register_and_login(async_client)
        headers = {"Authorization": f"Bearer {token}"}
        document = await _upload_document(async_client, token)

        manual_fact_payload = {
            "content": "Manual fact content.",
            "document_id": document["id"],
            "qualifiers": {"source": "note"},
            "confidence": 0.9,
            "is_uncertain": False,
        }
        fact_response = await async_client.post(
            "/api/v1/facts/manual", json=manual_fact_payload, headers=headers
        )
        assert fact_response.status_code == 201
        fact = fact_response.json()

        delete_response = await async_client.delete(f"/api/v1/facts/{fact['id']}", headers=headers)
        assert delete_response.status_code == 204

        list_response = await async_client.get(
            f"/api/v1/documents/{document['id']}/facts", headers=headers
        )
        assert list_response.status_code == 200
        facts = list_response.json()
        assert not facts
    finally:
        settings.storage_root = original_root
