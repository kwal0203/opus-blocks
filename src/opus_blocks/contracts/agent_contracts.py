from uuid import UUID

from opus_blocks.schemas.agent_contracts import (
    LibrarianOutput,
    VerifierOutput,
    WriterOutput,
)


def validate_librarian_output(payload: dict) -> LibrarianOutput:
    return LibrarianOutput.model_validate(payload)


def validate_writer_output(payload: dict, allowed_fact_ids: set[UUID]) -> WriterOutput:
    output = WriterOutput.model_validate(payload)
    for sentence in output.paragraph.sentences:
        for citation in sentence.citations:
            if citation not in allowed_fact_ids:
                raise ValueError("citations must reference allowed_fact_ids")
    return output


def validate_verifier_output(payload: dict, sentence_orders: list[int]) -> VerifierOutput:
    output = VerifierOutput.model_validate(payload)
    orders = [result.order for result in output.sentence_results]
    if sorted(orders) != sorted(sentence_orders):
        raise ValueError("verifier output must include results for every sentence order")
    return output
