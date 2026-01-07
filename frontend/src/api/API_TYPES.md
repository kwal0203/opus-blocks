# Frontend API Types Mapping

This folder mirrors backend response schemas to keep the frontend in sync.

Sources of truth (backend):
- `src/opus_blocks/schemas/user.py` -> User, Token
- `src/opus_blocks/schemas/document.py` -> Document
- `src/opus_blocks/schemas/manuscript.py` -> Manuscript
- `src/opus_blocks/schemas/fact.py` -> Fact
- `src/opus_blocks/schemas/paragraph.py` -> Paragraph
- `src/opus_blocks/schemas/sentence.py` -> Sentence
- `src/opus_blocks/schemas/sentence_fact_link.py` -> SentenceFactLink
- `src/opus_blocks/schemas/job.py` -> Job
- `src/opus_blocks/schemas/run.py` -> Run
- `src/opus_blocks/schemas/retrieval.py` -> FactSuggestion
- `src/opus_blocks/schemas/paragraph_view.py` -> ParagraphView

The typedefs in `frontend/src/api/types.js` should be updated whenever backend
schemas change.
