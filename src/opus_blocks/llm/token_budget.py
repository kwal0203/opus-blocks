import math

from opus_blocks.core.config import settings

_CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / _CHARS_PER_TOKEN))


def assert_token_budget(stage: str, system_prompt: str, user_prompt: str) -> None:
    if stage == "librarian":
        budget = settings.llm_token_budget_librarian
    elif stage == "writer":
        budget = settings.llm_token_budget_writer
    elif stage == "verifier":
        budget = settings.llm_token_budget_verifier
    else:
        raise ValueError(f"Unknown token budget stage: {stage}")

    if budget <= 0:
        return

    estimated = estimate_tokens(system_prompt) + estimate_tokens(user_prompt)
    if estimated > budget:
        raise ValueError(f"{stage} token budget exceeded: estimated {estimated}, budget {budget}")
