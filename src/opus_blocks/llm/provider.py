from dataclasses import dataclass
from uuid import UUID

from opus_blocks.core.config import settings


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

    def extract_facts(self, *, document_id: UUID) -> LLMResult:
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

    def generate_paragraph(
        self,
        *,
        paragraph_id: UUID,
        section: str,
        intent: str,
        allowed_fact_ids: list[UUID],
        linked_fact_id: UUID | None,
    ) -> LLMResult:
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

    def verify_paragraph(
        self,
        *,
        paragraph_id: UUID,
        sentence_inputs: list[dict],
    ) -> LLMResult:
        results: list[dict] = []
        for sentence in sentence_inputs:
            verdict = "PASS" if sentence["has_links"] else "FAIL"
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


def get_llm_provider() -> StubLLMProvider:
    provider_name = settings.llm_provider.lower()
    if provider_name not in {"openai", "stub", "test"}:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    return StubLLMProvider(
        provider=provider_name,
        model=settings.llm_model,
        prompt_version=settings.llm_prompt_version,
    )
