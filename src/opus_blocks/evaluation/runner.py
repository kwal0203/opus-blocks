from dataclasses import dataclass

from opus_blocks.evaluation.metrics import EvaluationMetrics, compute_rate, compute_support_rate


@dataclass(frozen=True)
class SentenceEvaluation:
    expected_supported: bool
    actual_supported: bool


@dataclass(frozen=True)
class ParagraphEvaluation:
    expected_verified: bool
    actual_verified: bool


@dataclass(frozen=True)
class EvaluationResult:
    sentence_evaluations: list[SentenceEvaluation]
    paragraph_evaluations: list[ParagraphEvaluation]
    metrics: EvaluationMetrics


def compute_metrics(
    sentence_evaluations: list[SentenceEvaluation],
    paragraph_evaluations: list[ParagraphEvaluation],
) -> EvaluationMetrics:
    total_sentences = len(sentence_evaluations)
    supported_sentences = sum(1 for s in sentence_evaluations if s.actual_supported)
    false_supports = sum(
        1 for s in sentence_evaluations if s.actual_supported and not s.expected_supported
    )

    total_paragraphs = len(paragraph_evaluations)
    verified_paragraphs = sum(1 for p in paragraph_evaluations if p.actual_verified)
    correct_refusals = sum(
        1 for p in paragraph_evaluations if not p.actual_verified and not p.expected_verified
    )
    over_refusals = sum(
        1 for p in paragraph_evaluations if not p.actual_verified and p.expected_verified
    )

    return EvaluationMetrics(
        sentence_support_rate=compute_support_rate(total_sentences, supported_sentences),
        false_support_rate=compute_rate(false_supports, total_sentences),
        verified_paragraph_rate=compute_rate(verified_paragraphs, total_paragraphs),
        correct_refusal_rate=compute_rate(correct_refusals, total_paragraphs),
        over_refusal_rate=compute_rate(over_refusals, total_paragraphs),
    )
