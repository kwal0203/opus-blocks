import uuid

import pytest

from opus_blocks.contracts.agent_contracts import (
    validate_librarian_output,
    validate_verifier_output,
    validate_writer_output,
)


def _source_span(document_id: str) -> dict:
    return {
        "document_id": document_id,
        "page": 1,
        "start_char": 0,
        "end_char": 5,
        "quote": "quote",
    }


def test_librarian_output_valid() -> None:
    document_id = str(uuid.uuid4())
    payload = {
        "facts": [
            {
                "content": "Fact one.",
                "source_type": "PDF",
                "source_span": _source_span(document_id),
                "qualifiers": {},
                "confidence": 0.9,
            }
        ],
        "uncertain_facts": [],
    }
    validate_librarian_output(payload)


def test_librarian_output_rejects_duplicate() -> None:
    document_id = str(uuid.uuid4())
    payload = {
        "facts": [
            {
                "content": "Fact one.",
                "source_type": "PDF",
                "source_span": _source_span(document_id),
                "qualifiers": {},
                "confidence": 0.9,
            },
            {
                "content": " Fact one. ",
                "source_type": "PDF",
                "source_span": _source_span(document_id),
                "qualifiers": {},
                "confidence": 0.8,
            },
        ],
        "uncertain_facts": [],
    }
    with pytest.raises(ValueError):
        validate_librarian_output(payload)


def test_writer_output_validation() -> None:
    fact_id = uuid.uuid4()
    payload = {
        "paragraph": {
            "section": "Introduction",
            "intent": "Background Context",
            "sentences": [
                {
                    "order": 1,
                    "sentence_type": "topic",
                    "text": "Sentence.",
                    "citations": [fact_id],
                }
            ],
            "missing_evidence": [],
        }
    }
    validate_writer_output(payload, allowed_fact_ids={fact_id})


def test_writer_output_rejects_unknown_citation() -> None:
    payload = {
        "paragraph": {
            "section": "Introduction",
            "intent": "Background Context",
            "sentences": [
                {
                    "order": 1,
                    "sentence_type": "topic",
                    "text": "Sentence.",
                    "citations": [uuid.uuid4()],
                }
            ],
            "missing_evidence": [],
        }
    }
    with pytest.raises(ValueError):
        validate_writer_output(payload, allowed_fact_ids=set())


def test_verifier_output_validation() -> None:
    payload = {
        "overall_pass": True,
        "sentence_results": [
            {
                "order": 1,
                "verdict": "PASS",
                "failure_modes": [],
                "explanation": "ok",
                "required_fix": "none",
                "suggested_rewrite": None,
            }
        ],
        "missing_evidence_summary": [],
    }
    validate_verifier_output(payload, sentence_orders=[1])


def test_verifier_output_rejects_missing_sentence() -> None:
    payload = {
        "overall_pass": False,
        "sentence_results": [],
        "missing_evidence_summary": [],
    }
    with pytest.raises(ValueError):
        validate_verifier_output(payload, sentence_orders=[1])


def test_verifier_output_rejects_fail_without_failure_modes() -> None:
    payload = {
        "overall_pass": False,
        "sentence_results": [
            {
                "order": 1,
                "verdict": "FAIL",
                "failure_modes": [],
                "explanation": "missing support",
                "required_fix": "add evidence",
                "suggested_rewrite": None,
            }
        ],
        "missing_evidence_summary": [],
    }
    with pytest.raises(ValueError):
        validate_verifier_output(payload, sentence_orders=[1])
