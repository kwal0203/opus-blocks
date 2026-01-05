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
