from pydantic import BaseModel

from opus_blocks.schemas.fact import FactRead
from opus_blocks.schemas.paragraph import ParagraphRead
from opus_blocks.schemas.sentence import SentenceRead
from opus_blocks.schemas.sentence_fact_link import SentenceFactLinkRead


class ParagraphView(BaseModel):
    paragraph: ParagraphRead
    sentences: list[SentenceRead]
    links: list[SentenceFactLinkRead]
    facts: list[FactRead]
