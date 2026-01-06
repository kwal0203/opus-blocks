import os
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient

from opus_blocks.core.config import settings
from opus_blocks.llm.provider import LLMMetadata, LLMResult, OpenAIProvider
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


async def _create_fact(async_client: AsyncClient, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    fact_response = await async_client.post(
        "/api/v1/facts/manual",
        json={"content": "Manual fact"},
        headers=headers,
    )
    assert fact_response.status_code == 201
    return fact_response.json()


async def _create_paragraph(
    async_client: AsyncClient, token: str, allowed_fact_ids: list[str]
) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    manuscript_response = await async_client.post(
        "/api/v1/manuscripts",
        json={"title": "OpenAI Flow"},
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


@pytest.mark.anyio
async def test_openai_writer_and_verifier_flow(
    async_client: AsyncClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_root = settings.storage_root
    original_provider = settings.llm_provider
    original_flag = settings.llm_use_openai
    original_key = settings.openai_api_key
    settings.storage_root = str(tmp_path)
    settings.llm_provider = "openai"
    settings.llm_use_openai = True
    settings.openai_api_key = "test-key"

    def fake_generate(self, *, inputs: dict) -> LLMResult:  # type: ignore[no-untyped-def]
        sentence = {
            "order": 1,
            "sentence_type": "topic",
            "text": "OpenAI generated sentence.",
            "citations": [inputs["allowed_facts"][0]["fact_id"]],
        }
        outputs = {
            "paragraph": {
                "section": inputs["paragraph_spec"]["section"],
                "intent": inputs["paragraph_spec"]["intent"],
                "sentences": [sentence],
                "missing_evidence": [],
            }
        }
        metadata = LLMMetadata(provider="openai", model="test", prompt_version="v1")
        return LLMResult(outputs=outputs, metadata=metadata)

    def fake_verify(self, *, inputs: dict) -> LLMResult:  # type: ignore[no-untyped-def]
        results = [
            {
                "order": sentence["order"],
                "verdict": "PASS",
                "failure_modes": [],
                "explanation": "Supported.",
                "required_fix": "None",
                "suggested_rewrite": None,
            }
            for sentence in inputs["sentences"]
        ]
        outputs = {
            "overall_pass": True,
            "sentence_results": results,
            "missing_evidence_summary": [],
        }
        metadata = LLMMetadata(provider="openai", model="test", prompt_version="v1")
        return LLMResult(outputs=outputs, metadata=metadata)

    monkeypatch.setattr(OpenAIProvider, "generate_paragraph", fake_generate)
    monkeypatch.setattr(OpenAIProvider, "verify_paragraph", fake_verify)

    try:
        token = await _register_and_login(async_client)
        headers = {"Authorization": f"Bearer {token}"}
        fact = await _create_fact(async_client, token)
        paragraph = await _create_paragraph(async_client, token, [fact["id"]])

        generate_response = await async_client.post(
            f"/api/v1/paragraphs/{paragraph['id']}/generate", headers=headers
        )
        assert generate_response.status_code == 200
        generate_job = generate_response.json()

        original_url = settings.database_url
        settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
        try:
            await run_generate_job(uuid.UUID(generate_job["id"]), uuid.UUID(paragraph["id"]))
        finally:
            settings.database_url = original_url

        verify_response = await async_client.post(
            f"/api/v1/paragraphs/{paragraph['id']}/verify", headers=headers
        )
        assert verify_response.status_code == 200
        verify_job = verify_response.json()

        settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
        try:
            await run_verify_job(uuid.UUID(verify_job["id"]), uuid.UUID(paragraph["id"]))
        finally:
            settings.database_url = original_url

        sentences_response = await async_client.get(
            f"/api/v1/sentences/paragraph/{paragraph['id']}", headers=headers
        )
        assert sentences_response.status_code == 200
        sentence = sentences_response.json()[0]
        assert sentence["text"] == "OpenAI generated sentence."
        assert sentence["supported"] is True

        paragraph_response = await async_client.get(
            f"/api/v1/paragraphs/{paragraph['id']}", headers=headers
        )
        assert paragraph_response.status_code == 200
        assert paragraph_response.json()["status"] == "VERIFIED"
    finally:
        settings.storage_root = original_root
        settings.llm_provider = original_provider
        settings.llm_use_openai = original_flag
        settings.openai_api_key = original_key
