from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationMetrics:
    sentence_support_rate: float
    false_support_rate: float
    verified_paragraph_rate: float
    correct_refusal_rate: float
    over_refusal_rate: float


def compute_support_rate(total_sentences: int, supported_sentences: int) -> float:
    if total_sentences == 0:
        return 0.0
    return supported_sentences / total_sentences


def compute_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
