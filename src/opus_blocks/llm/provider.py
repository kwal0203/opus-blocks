import json
import time
from dataclasses import dataclass

from openai import OpenAI

from opus_blocks.core.config import settings
from opus_blocks.llm.prompts import loader
from opus_blocks.llm.token_budget import assert_token_budget


@dataclass(frozen=True)
class LLMMetadata:
    provider: str
    model: str
    prompt_version: str
    token_prompt: int | None = None
    token_completion: int | None = None
    cost_usd: float | None = None
    latency_ms: int | None = None


@dataclass(frozen=True)
class LLMResult:
    outputs: dict
    metadata: LLMMetadata


class StubLLMProvider:
    def __init__(self, provider: str, model: str, prompt_version: str) -> None:
        self._provider = provider
        self._model = model
        self._prompt_version = prompt_version

    def _metadata(self) -> LLMMetadata:
        return LLMMetadata(
            provider=self._provider, model=self._model, prompt_version=self._prompt_version
        )

    def extract_facts(self, *, inputs: dict) -> LLMResult:
        document_id = inputs.get("document_id")
        outputs = {
            "facts": [
                {
                    "content": "Placeholder extracted fact.",
                    "source_type": "PDF",
                    "source_span": {
                        "document_id": str(document_id),
                        "page": 1,
                        "start_char": 0,
                        "end_char": 24,
                        "quote": "Placeholder extracted span.",
                    },
                    "qualifiers": {},
                    "confidence": 0.5,
                },
                {
                    "content": "Secondary extracted fact.",
                    "source_type": "PDF",
                    "source_span": {
                        "document_id": str(document_id),
                        "page": 2,
                        "start_char": 50,
                        "end_char": 80,
                        "quote": "Additional placeholder span.",
                    },
                    "qualifiers": {},
                    "confidence": 0.7,
                },
                {
                    "content": "High-level extracted fact without span.",
                    "source_type": "PDF",
                    "source_span": {
                        "document_id": str(document_id),
                        "page": None,
                        "start_char": None,
                        "end_char": None,
                        "quote": None,
                    },
                    "qualifiers": {},
                    "confidence": 0.4,
                },
            ],
            "uncertain_facts": [],
        }
        return LLMResult(outputs=outputs, metadata=self._metadata())

    def generate_paragraph(self, *, inputs: dict) -> LLMResult:
        section = inputs.get("paragraph_spec", {}).get("section", "")
        intent = inputs.get("paragraph_spec", {}).get("intent", "")
        allowed_facts = inputs.get("allowed_facts", [])
        linked_fact_id = allowed_facts[0].get("fact_id") if allowed_facts else None
        paragraph_payload: dict = {
            "section": section,
            "intent": intent,
            "sentences": [],
            "missing_evidence": [],
        }
        if linked_fact_id:
            paragraph_payload["sentences"] = [
                {
                    "order": 1,
                    "sentence_type": "topic",
                    "text": "Placeholder generated sentence.",
                    "citations": [str(linked_fact_id)],
                }
            ]
        else:
            paragraph_payload["missing_evidence"] = [
                {
                    "needed_for": "placeholder sentence",
                    "why_missing": "no allowed facts provided",
                    "suggested_fact_type": "source fact",
                }
            ]
        outputs = {"paragraph": paragraph_payload}
        return LLMResult(outputs=outputs, metadata=self._metadata())

    def verify_paragraph(self, *, inputs: dict) -> LLMResult:
        sentence_inputs = inputs.get("sentences", [])
        results: list[dict] = []
        for sentence in sentence_inputs:
            verdict = "PASS" if sentence.get("has_links") else "FAIL"
            results.append(
                {
                    "order": sentence["order"],
                    "verdict": verdict,
                    "failure_modes": [] if verdict == "PASS" else ["UNCITED_CLAIM"],
                    "explanation": "Placeholder verification.",
                    "required_fix": "Add citations." if verdict == "FAIL" else "None",
                    "suggested_rewrite": None,
                }
            )
        outputs = {
            "overall_pass": all(result["verdict"] == "PASS" for result in results),
            "sentence_results": results,
            "missing_evidence_summary": [],
        }
        return LLMResult(outputs=outputs, metadata=self._metadata())


class OpenAIProvider:
    def __init__(self, api_key: str, model: str, prompt_version: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._prompt_version = prompt_version
        self._prompt_loader = loader.PromptLoader()

    def _metadata(self, start_time: float, usage: object | None) -> LLMMetadata:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        token_prompt = getattr(usage, "prompt_tokens", None) if usage else None
        token_completion = getattr(usage, "completion_tokens", None) if usage else None
        return LLMMetadata(
            provider="openai",
            model=self._model,
            prompt_version=self._prompt_version,
            token_prompt=token_prompt,
            token_completion=token_completion,
            latency_ms=latency_ms,
        )

    def _request(self, *, system_prompt: str, user_prompt: str, stage: str) -> LLMResult:
        assert_token_budget(stage, system_prompt, user_prompt)
        start_time = time.perf_counter()
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = response.choices[0].message.content if response.choices else ""
        try:
            outputs = json.loads(content or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("OpenAI response was not valid JSON") from exc
        metadata = self._metadata(start_time, response.usage)
        return LLMResult(outputs=outputs, metadata=metadata)

    def extract_facts(self, *, inputs: dict) -> LLMResult:
        system_prompt = self._prompt_loader.render("librarian", inputs)
        user_prompt = "Return JSON only."
        return self._request(
            system_prompt=system_prompt, user_prompt=user_prompt, stage="librarian"
        )

    def generate_paragraph(self, *, inputs: dict) -> LLMResult:
        system_prompt = self._prompt_loader.render("writer", inputs)
        user_prompt = "Return JSON only."
        return self._request(system_prompt=system_prompt, user_prompt=user_prompt, stage="writer")

    def verify_paragraph(self, *, inputs: dict) -> LLMResult:
        system_prompt = self._prompt_loader.render("verifier", inputs)
        user_prompt = "Return JSON only."
        return self._request(system_prompt=system_prompt, user_prompt=user_prompt, stage="verifier")


def get_llm_provider() -> StubLLMProvider | OpenAIProvider:
    provider_name = settings.llm_provider.lower()
    if provider_name == "openai" and settings.llm_use_openai:
        if not settings.openai_api_key:
            raise ValueError("openai_api_key must be set when llm_use_openai is true")
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            prompt_version=settings.llm_prompt_version,
        )
    if provider_name in {"openai", "stub", "test"}:
        return StubLLMProvider(
            provider=provider_name,
            model=settings.llm_model,
            prompt_version=settings.llm_prompt_version,
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
