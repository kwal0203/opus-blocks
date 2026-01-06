import os
import uuid
from pathlib import Path

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


@pytest.mark.anyio
async def test_document_upload_and_job_flow(async_client: AsyncClient, tmp_path: Path) -> None:
    original_root = settings.storage_root
    settings.storage_root = str(tmp_path)
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    file_content = b"%PDF-1.4 test content"
    files = {"file": ("example.pdf", file_content, "application/pdf")}
    upload_response = await async_client.post(
        "/api/v1/documents/upload", files=files, headers=headers
    )

    assert upload_response.status_code == 201
    doc = upload_response.json()
    assert doc["status"] == "UPLOADED"
    assert doc["filename"] == "example.pdf"
    assert Path(doc["storage_uri"]).exists()

    extract_response = await async_client.post(
        f"/api/v1/documents/{doc['id']}/extract_facts", headers=headers
    )
    assert extract_response.status_code == 200
    job = extract_response.json()
    assert job["job_type"] == "EXTRACT_FACTS"
    assert job["status"] == "QUEUED"

    job_response = await async_client.get(f"/api/v1/jobs/{job['id']}", headers=headers)
    assert job_response.status_code == 200
    assert job_response.json()["id"] == job["id"]

    original_db_url = settings.database_url
    settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
    try:
        await run_extract_facts_job(uuid.UUID(job["id"]), uuid.UUID(doc["id"]))
    finally:
        settings.database_url = original_db_url

    job_after = await async_client.get(f"/api/v1/jobs/{job['id']}", headers=headers)
    assert job_after.status_code == 200
    assert job_after.json()["status"] == "SUCCEEDED"

    doc_after = await async_client.get(f"/api/v1/documents/{doc['id']}", headers=headers)
    assert doc_after.status_code == 200
    assert doc_after.json()["status"] == "FACTS_READY"

    facts_response = await async_client.get(f"/api/v1/documents/{doc['id']}/facts", headers=headers)
    assert facts_response.status_code == 200
    facts = facts_response.json()
    assert len(facts) >= 3

    runs_response = await async_client.get(f"/api/v1/documents/{doc['id']}/runs", headers=headers)
    assert runs_response.status_code == 200
    runs = runs_response.json()
    assert len(runs) == 1
    assert runs[0]["run_type"] == "LIBRARIAN"

    settings.storage_root = original_root


class FakeProvider:
    def extract_facts(self, *, inputs: dict):  # type: ignore[no-untyped-def]
        document_id = inputs["document_id"]
        return type(
            "Result",
            (),
            {
                "outputs": {
                    "facts": [
                        {
                            "content": "Real extracted fact.",
                            "source_type": "PDF",
                            "source_span": {
                                "document_id": document_id,
                                "page": 1,
                                "start_char": 0,
                                "end_char": 5,
                                "quote": "facts",
                            },
                            "qualifiers": {"source": "unit"},
                            "confidence": 0.9,
                        }
                    ],
                    "uncertain_facts": [
                        {
                            "content": "Uncertain fact.",
                            "reason": "missing qualifier",
                            "source_span": {
                                "document_id": document_id,
                                "page": 2,
                                "start_char": 10,
                                "end_char": 20,
                                "quote": "uncertain",
                            },
                        }
                    ],
                },
                "metadata": type(
                    "Meta",
                    (),
                    {
                        "provider": "test",
                        "model": "test",
                        "prompt_version": "v1",
                        "token_prompt": None,
                        "token_completion": None,
                        "cost_usd": None,
                        "latency_ms": None,
                    },
                )(),
            },
        )()


@pytest.mark.anyio
async def test_extract_facts_persists_uncertain(
    async_client: AsyncClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_root = settings.storage_root
    settings.storage_root = str(tmp_path)
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    file_content = b"%PDF-1.4 test content"
    files = {"file": ("example.pdf", file_content, "application/pdf")}
    upload_response = await async_client.post(
        "/api/v1/documents/upload", files=files, headers=headers
    )

    assert upload_response.status_code == 201
    doc = upload_response.json()

    extract_response = await async_client.post(
        f"/api/v1/documents/{doc['id']}/extract_facts", headers=headers
    )
    assert extract_response.status_code == 200
    job = extract_response.json()

    monkeypatch.setattr("opus_blocks.tasks.documents.get_llm_provider", lambda: FakeProvider())

    original_db_url = settings.database_url
    settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
    try:
        await run_extract_facts_job(uuid.UUID(job["id"]), uuid.UUID(doc["id"]))
    finally:
        settings.database_url = original_db_url

    facts_response = await async_client.get(f"/api/v1/documents/{doc['id']}/facts", headers=headers)
    assert facts_response.status_code == 200
    facts = facts_response.json()
    assert len(facts) == 2
    uncertain = next(fact for fact in facts if fact["is_uncertain"])
    assert uncertain["qualifiers"]["reason"] == "missing qualifier"

    runs_response = await async_client.get(f"/api/v1/documents/{doc['id']}/runs", headers=headers)
    assert runs_response.status_code == 200
    runs = runs_response.json()
    assert runs[0]["outputs_json"]["facts"][0]["content"] == "Real extracted fact."

    settings.storage_root = original_root
