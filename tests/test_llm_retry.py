import os
import uuid

import pytest
from httpx import AsyncClient

from opus_blocks.core.config import settings
from opus_blocks.tasks.documents import run_extract_facts_job
from opus_blocks.tasks.paragraphs import run_generate_job, run_verify_job


class FlakyProvider:
    def __init__(self) -> None:
        self.calls: dict[str, int] = {"extract": 0, "generate": 0, "verify": 0}

    def extract_facts(self, *, inputs: dict):  # type: ignore[no-untyped-def]
        self.calls["extract"] += 1
        if self.calls["extract"] == 1:
            raise ValueError("bad json")
        return _fake_librarian_result(inputs["document_id"])

    def generate_paragraph(self, *, inputs: dict):  # type: ignore[no-untyped-def]
        self.calls["generate"] += 1
        if self.calls["generate"] == 1:
            raise ValueError("bad json")
        return _fake_writer_result(inputs.get("allowed_facts", []))

    def verify_paragraph(self, *, inputs: dict):  # type: ignore[no-untyped-def]
        self.calls["verify"] += 1
        if self.calls["verify"] == 1:
            raise ValueError("bad json")
        return _fake_verifier_result(inputs["sentences"])


class Result:
    def __init__(self, outputs: dict) -> None:
        self.outputs = outputs
        self.metadata = type(
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
        )()


def _fake_librarian_result(document_id: str) -> Result:
    return Result(
        {
            "facts": [
                {
                    "content": "Fact A",
                    "source_type": "PDF",
                    "source_span": {
                        "document_id": document_id,
                        "page": 1,
                        "start_char": 0,
                        "end_char": 5,
                        "quote": "Fact A",
                    },
                    "qualifiers": {},
                    "confidence": 0.9,
                }
            ],
            "uncertain_facts": [],
        }
    )


def _fake_writer_result(allowed_facts: list[dict]) -> Result:
    citation_id = allowed_facts[0]["fact_id"] if allowed_facts else str(uuid.uuid4())
    return Result(
        {
            "paragraph": {
                "section": "Introduction",
                "intent": "Background Context",
                "sentences": [
                    {
                        "order": 1,
                        "sentence_type": "topic",
                        "text": "Generated sentence.",
                        "citations": [str(citation_id)],
                    }
                ],
                "missing_evidence": [],
            }
        }
    )


def _fake_verifier_result(sentences: list[dict]) -> Result:
    return Result(
        {
            "overall_pass": False,
            "sentence_results": [
                {
                    "order": sentence["order"],
                    "verdict": "FAIL",
                    "failure_modes": ["UNCITED_CLAIM"],
                    "explanation": "Needs citations.",
                    "required_fix": "Add citations.",
                    "suggested_rewrite": None,
                }
                for sentence in sentences
            ],
            "missing_evidence_summary": [],
        }
    )


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


async def _create_document(async_client: AsyncClient, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    upload_response = await async_client.post(
        "/api/v1/documents/upload",
        files={"file": ("example.pdf", b"%PDF-1.4 test", "application/pdf")},
        headers=headers,
    )
    assert upload_response.status_code == 201
    return upload_response.json()


async def _create_paragraph(
    async_client: AsyncClient, token: str, allowed_fact_ids: list[str]
) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    manuscript_response = await async_client.post(
        "/api/v1/manuscripts",
        json={"title": "Retry Manuscript"},
        headers=headers,
    )
    assert manuscript_response.status_code == 201
    manuscript = manuscript_response.json()

    spec_payload = {
        "section": "Introduction",
        "intent": "Background Context",
        "required_structure": {
            "topic_sentence": True,
            "evidence_sentences": 1,
            "conclusion_sentence": True,
        },
        "allowed_fact_ids": allowed_fact_ids,
        "style": {"tense": "present", "voice": "academic", "target_length_words": [60, 90]},
        "constraints": {"forbidden_claims": ["novelty"], "allowed_scope": "facts only"},
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
    fact_response = await async_client.post(
        "/api/v1/facts/manual",
        json={"content": "Manual fact"},
        headers=headers,
    )
    assert fact_response.status_code == 201
    return fact_response.json()


@pytest.mark.anyio
async def test_retry_on_extract_failure(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    document = await _create_document(async_client, token)

    extract_response = await async_client.post(
        f"/api/v1/documents/{document['id']}/extract_facts", headers=headers
    )
    assert extract_response.status_code == 200
    extract_job = extract_response.json()

    provider = FlakyProvider()
    monkeypatch.setattr("opus_blocks.tasks.documents.get_llm_provider", lambda: provider)

    original_url = settings.database_url
    settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
    try:
        await run_extract_facts_job(uuid.UUID(extract_job["id"]), uuid.UUID(document["id"]))
    finally:
        settings.database_url = original_url

    assert provider.calls["extract"] == 2


@pytest.mark.anyio
async def test_retry_on_generate_and_verify(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    fact = await _create_fact(async_client, token)
    paragraph = await _create_paragraph(async_client, token, [fact["id"]])

    generate_response = await async_client.post(
        f"/api/v1/paragraphs/{paragraph['id']}/generate", headers=headers
    )
    assert generate_response.status_code == 200
    generate_job = generate_response.json()

    verify_response = await async_client.post(
        f"/api/v1/paragraphs/{paragraph['id']}/verify", headers=headers
    )
    assert verify_response.status_code == 200
    verify_job = verify_response.json()

    provider = FlakyProvider()
    monkeypatch.setattr("opus_blocks.tasks.paragraphs.get_llm_provider", lambda: provider)

    original_url = settings.database_url
    settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
    try:
        await run_generate_job(uuid.UUID(generate_job["id"]), uuid.UUID(paragraph["id"]))
        await run_verify_job(uuid.UUID(verify_job["id"]), uuid.UUID(paragraph["id"]))
    finally:
        settings.database_url = original_url

    assert provider.calls["generate"] == 2
    assert provider.calls["verify"] == 2
