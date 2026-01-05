# OpusBlocks.com v1.0 — Product Requirements Document (PRD)

## 1. Overview

### Product Name

OpusBlocks.com

### Version

v1.0 (MVP)

### One-Line Description

OpusBlocks.com is a grounded scientific writing assistant that helps researchers draft individual manuscript paragraphs where every sentence is explicitly supported by user-provided evidence.

---

## 2. Problem Statement

Scientific writing tools powered by large language models often:

- hallucinate facts
- blur qualifiers (population, timeframe, scope)
- generate uncited or weakly supported claims
- obscure where information comes from

These failures are unacceptable in scientific and academic writing, where traceability, attribution, and precision are mandatory.

Researchers need a system that:

- assists with writing without inventing knowledge
- enforces evidence grounding
- makes attribution explicit and auditable

---

## 3. Product Goals

### Primary Goals

1. Enable paragraph-by-paragraph scientific drafting
2. Guarantee explicit grounding of every generated sentence
3. Support PDF-derived evidence and user-entered facts as first-class inputs
4. Provide inline attribution at the sentence level

Make unsupported claims impossible to silently generate

Non-Goals (Explicitly Out of Scope)

- Full manuscript auto-generation
- Autonomous research or hypothesis generation
- External web browsing or citation scraping
- Generating novel scientific claims
- Medical, legal, or policy advice

## 4. Target Users

### Primary User

- Academic researchers (PhD students, postdocs, faculty)
- Industry researchers writing technical reports or papers

### Secondary User

- AI/ML engineers evaluating grounded generation systems
- Hiring managers/interviewers assessing Responsible AI systems

---

## 5. User Workflow (MVP)

### Primary Flow

1. User uploads one or more PDF documents
2. User optionally adds manual supporting facts
3. System extracts Atomic Facts from PDFs
4. User selects:
    - Manuscript section (IMRAD)
    - Paragraph intent (e.g., Knowledge Gap, Study Protocol)
5. System builds a Paragraph Spec
6. System generates one paragraph
7. System verifies sentence ↔ fact support
8. UI displays paragraph with inline citations
9. User edits, regenerates, or locks paragraph

### UX Guarantees

- No sentence is displayed without verified support.
- If evidence is insufficient, the system asks or refuses.
- All attributions are visible and inspectable.

---

## 6. Core Functional Requirements

### FR-1: Evidence Ingestion

- Accept PDF uploads.
- Accept manual user-entered facts.
- PDFs are parsed and passed to the Librarian agent.
- Manual facts are stored directly and treated identically to extracted facts.

---

### FR-2: Atomic Fact Extraction

- Extract facts that are:
    - atomic
    - explicitly supported by source text
    - qualified where possible
- Each fact stores:
    - source type (PDF or MANUAL)
    - source span (if PDF)
    - confidence score

---

### FR-3: Paragraph Specification

- Each paragraph generation request must include:
    - manuscript section (IMRAD)
    - paragraph intent
    - required structural components
    - allowed evidence set
- Paragraphs are generated one at a time

---

### FR-4: Constrained Paragraph Generation

- The system must:
    - pass only allowed facts to the Writer agent
    - forbid external knowledge
    - require per-sentence citations
- Output must be structured (sentences + citations)

---

### FR-5: Verification & Gating

- Every generated sentence must be verified
- Verification checks:
    - citation presence
    - semantic entailment
    - qualifier integrity
    - scope and strength
- If verification fails:
    - sentence is rejected
    - failure reason is surfaced

---

### FR-6: Inline Attribution

- Each sentence displays inline references (e.g., [1][3]).
- Hover/click reveals:
    - fact text
    - source document and page (or “User-provided”)

---

### FR-7: Regeneration & Editing

- Users may:
    - regenerate failed sentences
    - add new supporting facts
    - manually edit sentences (re-verification required)

---

## 7. Non-Functional Requirements

### NFR-1: Reliability

- Paragraph generation must be idempotent
- Async jobs must support retries and failure states

### NFR-2: Latency

- Paragraph generation target:
    - P50 < 10s
    - P95 < 30s (async acceptable)

### NFR-3: Cost

- Token budgets enforced per paragraph
- Cost per paragraph must be logged and observable

### NFR-4: Observability

- Full trace per paragraph generation:
    - prompt version
    - fact IDs
    - verifier outcome
    - model used
    - token usage

### NFR-5: Security & Privacy

- API keys stored via secrets manager
- No raw document text logged without redaction
- User data isolated per account

## 8. Success Metrics

### Functional Metrics

- ≥ 95% sentences generated with valid citations
- 0 silent hallucinations in verified output
- ≥ 90% verifier agreement on golden test set

### UX Metrics

- Average regenerations per paragraph
- % paragraphs completed without manual correction

---

### System Metrics

- Cost per paragraph
- Average facts per sentence
- Verification failure rate by category

## 9. Edge Cases & Failure Handling

Scenario                    Expected Behavior
PDF contains vague claims   Extract uncertain facts or none
Insufficient facts          Refuse generation and explain
Conflicting facts           Surface conflict, do not resolve automatically
User edits sentence         Re-verify before display
LLM timeout                 Retry or fail gracefully

---

## 10. Open Questions (Deferred, Not Blocking MVP)

- Multi-document cross-comparison policies
- Multi-paragraph coherence enforcement
- Citation style export formats
- Collaboration / shared manuscripts

---

## 11. MVP Definition of Done

OpusBlocks.com v1.0 is considered complete when:
- A user can generate a single verified paragraph
- Every sentence has inline attribution
- Unsupported claims are blocked
- The grounding contract is mechanically enforced
- Paragraph generation is traceable end-to-end

--- 

## 12. Positioning Statement (Internal)

OpusBlocks.com is not a creative writing tool.

It is a constrained reasoning system that enforces scientific accountability at the sentence level.