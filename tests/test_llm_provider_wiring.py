import hashlib
import json
import os
import uuid

import pytest
from httpx import AsyncClient

from opus_blocks.core.config import settings
from opus_blocks.llm.provider import LLMMetadata, LLMResult
from opus_blocks.tasks.documents import run_extract_facts_job
from opus_blocks.tasks.paragraphs import run_generate_job, run_verify_job


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


async def _create_document(async_client: AsyncClient, token: str) -> tuple[dict, bytes]:
    headers = {"Authorization": f"Bearer {token}"}
    file_bytes = b"%PDF-1.4 test"
    upload_response = await async_client.post(
        "/api/v1/documents/upload",
        files={"file": ("example.pdf", file_bytes, "application/pdf")},
        headers=headers,
    )
    assert upload_response.status_code == 201
    return upload_response.json(), file_bytes


def _hash_inputs(payload: dict) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class FakeExtractProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.metadata = LLMMetadata(
            provider="test-provider", model="test-model", prompt_version="test-v1"
        )

    def extract_facts(self, *, inputs: dict) -> LLMResult:
        document_id = inputs["document_id"]
        self.calls.append(f"extract:{document_id}")
        outputs = {
            "facts": [
                {
                    "content": "Fact A",
                    "source_type": "PDF",
                    "source_span": {
                        "document_id": str(document_id),
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
        return LLMResult(outputs=outputs, metadata=self.metadata)


class FakeParagraphProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.metadata = LLMMetadata(
            provider="test-provider", model="test-model", prompt_version="test-v1"
        )

    def generate_paragraph(self, *, inputs: dict) -> LLMResult:
        paragraph_id = inputs["paragraph_id"]
        paragraph_spec = inputs["paragraph_spec"]
        allowed_facts = inputs["allowed_facts"]
        linked_fact_id = allowed_facts[0]["fact_id"] if allowed_facts else None
        self.calls.append(f"generate:{paragraph_id}")
        outputs = {
            "paragraph": {
                "section": paragraph_spec["section"],
                "intent": paragraph_spec["intent"],
                "sentences": [
                    {
                        "order": 1,
                        "sentence_type": "topic",
                        "text": "Test sentence.",
                        "citations": [str(linked_fact_id)],
                    }
                ],
                "missing_evidence": [],
            }
        }
        return LLMResult(outputs=outputs, metadata=self.metadata)

    def verify_paragraph(self, *, inputs: dict) -> LLMResult:
        paragraph_id = inputs["paragraph_id"]
        sentence_inputs = inputs["sentences"]
        self.calls.append(f"verify:{paragraph_id}")
        outputs = {
            "overall_pass": True,
            "sentence_results": [
                {
                    "order": sentence["order"],
                    "verdict": "PASS",
                    "failure_modes": [],
                    "explanation": "All good.",
                    "required_fix": "None",
                    "suggested_rewrite": None,
                }
                for sentence in sentence_inputs
            ],
            "missing_evidence_summary": [],
        }
        return LLMResult(outputs=outputs, metadata=self.metadata)


@pytest.mark.anyio
async def test_llm_provider_runs_metadata_and_hash(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    document, file_bytes = await _create_document(async_client, token)

    extract_response = await async_client.post(
        f"/api/v1/documents/{document['id']}/extract_facts", headers=headers
    )
    assert extract_response.status_code == 200
    extract_job = extract_response.json()

    fake_provider = FakeExtractProvider()
    monkeypatch.setattr("opus_blocks.tasks.documents.get_llm_provider", lambda: fake_provider)

    original_url = settings.database_url
    settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
    try:
        await run_extract_facts_job(uuid.UUID(extract_job["id"]), uuid.UUID(document["id"]))
    finally:
        settings.database_url = original_url

    runs_response = await async_client.get(
        f"/api/v1/documents/{document['id']}/runs", headers=headers
    )
    assert runs_response.status_code == 200
    runs = runs_response.json()
    librarian_run = next(run for run in runs if run["run_type"] == "LIBRARIAN")

    assert fake_provider.calls
    assert librarian_run["provider"] == fake_provider.metadata.provider
    assert librarian_run["model"] == fake_provider.metadata.model
    assert librarian_run["prompt_version"] == fake_provider.metadata.prompt_version
    source_text = file_bytes.decode("utf-8")
    source_text_hash = hashlib.sha256(file_bytes).hexdigest()
    expected_hash = _hash_inputs(
        {
            "document_id": document["id"],
            "source_type": "PDF",
            "source_text_hash": source_text_hash,
            "source_text_len": len(source_text),
        }
    )
    assert librarian_run["input_hash"] == expected_hash


@pytest.mark.anyio
async def test_llm_provider_called_for_generate_and_verify(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = await _register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    manuscript_response = await async_client.post(
        "/api/v1/manuscripts", json={"title": "Provider Manuscript"}, headers=headers
    )
    assert manuscript_response.status_code == 201
    manuscript = manuscript_response.json()

    fact_response = await async_client.post(
        "/api/v1/facts/manual",
        json={"content": "Manual fact"},
        headers=headers,
    )
    assert fact_response.status_code == 201
    fact = fact_response.json()

    spec_payload = {
        "section": "Introduction",
        "intent": "Background Context",
        "required_structure": {
            "topic_sentence": True,
            "evidence_sentences": 1,
            "conclusion_sentence": True,
        },
        "allowed_fact_ids": [fact["id"]],
        "style": {"tense": "present", "voice": "academic", "target_length_words": [60, 90]},
        "constraints": {"forbidden_claims": ["novelty"], "allowed_scope": "facts only"},
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

    verify_response = await async_client.post(
        f"/api/v1/paragraphs/{paragraph['id']}/verify", headers=headers
    )
    assert verify_response.status_code == 200
    verify_job = verify_response.json()

    fake_provider = FakeParagraphProvider()
    monkeypatch.setattr("opus_blocks.tasks.paragraphs.get_llm_provider", lambda: fake_provider)

    original_url = settings.database_url
    settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
    try:
        await run_generate_job(uuid.UUID(generate_job["id"]), uuid.UUID(paragraph["id"]))
        await run_verify_job(uuid.UUID(verify_job["id"]), uuid.UUID(paragraph["id"]))
    finally:
        settings.database_url = original_url

    assert any(call.startswith("generate:") for call in fake_provider.calls)
    assert any(call.startswith("verify:") for call in fake_provider.calls)
