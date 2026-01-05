# OpusBlocks.com v1.0 — Data Model & Storage Schema

## 1. Purpose

This document specifies the system-of-record data model for OpusBlocks.com v1.0, including:

- relational schema (PostgreSQL) for auditability and enforcement of grounding
- entity relationships and lifecycle/state
- minimum indexes and constraints for performance and correctness
- data retention + deletion semantics
- how the vector store relates to relational truth

This schema is designed to enforce:
- Grounded Generation Contract (Doc #2)
- Paragraph & Manuscript Spec (Doc #3)
- Verify-before-display (Doc #4)

---

## 2. Design Principles

1. Postgres is authoritative: all facts, sentences, and links live here.
2. Auditability first: every output is reproducible from stored artifacts.
3. Grounding is a first-class relation: sentence ↔ fact links are explicit.
4. Versioning is explicit: prompts/model params are recorded per run.
5. Vector store is derivative: embeddings can be regenerated; Postgres cannot.

---

## 3. Entity Overview

### Core entities

- User (optional for MVP; include if multi-tenant)
- Document (uploaded PDF or other source container)
- Span (provenance location inside a PDF)
- Fact (Atomic Fact from PDF or manual entry)
- Manuscript (logical workspace)
- Paragraph (one paragraph + Paragraph Spec + state)
- Sentence (generated or user-edited sentences)
- SentenceFactLink (grounding relation)
- Run (LLM invocation record: Librarian/Writer/Verifier)

### Supporting entities

- Job (async job tracking)
- PromptVersion (optional but recommended)
- EmbeddingRecord (optional pointer to vector store IDs)

---

## 4. PostgreSQL Schema (Normative)

Names are snake_case; primary keys are UUIDs.

Timestamps are timestamptz.

JSON columns are jsonb.

## 4.1 users (optional but recommended)

If you want simplest MVP single-user, you can omit and hardcode an owner. But production-grade should include it.

```
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 4.2 documents

Represents uploaded PDFs (and future sources).

```
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  owner_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
  source_type TEXT NOT NULL CHECK (source_type IN ('PDF')),
  filename TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  storage_uri TEXT NOT NULL,          -- S3 path or local path
  status TEXT NOT NULL CHECK (status IN (
    'UPLOADED','EXTRACTING_FACTS','FACTS_READY','FAILED_PARSE','FAILED_EXTRACTION'
  )),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX documents_owner_hash_uq
  ON documents(owner_id, content_hash);
```

Notes:

- content_hash prevents duplicate uploads.
- metadata may store page count, parser version, etc.

---

## 4.3 spans

Provenance anchors into PDF text.

```
CREATE TABLE spans (
  id UUID PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page INT NULL,
  start_char INT NULL,
  end_char INT NULL,
  quote TEXT NULL,                    -- short excerpt; keep small
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (
    (start_char IS NULL AND end_char IS NULL) OR (start_char <= end_char)
  )
);

CREATE INDEX spans_document_page_idx ON spans(document_id, page);
```

---

## 4.4 facts

Atomic Facts, either derived from PDF or manually entered.

```
CREATE TABLE facts (
  id UUID PRIMARY KEY,
  owner_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
  document_id UUID NULL REFERENCES documents(id) ON DELETE CASCADE,
  span_id UUID NULL REFERENCES spans(id) ON DELETE SET NULL,

  source_type TEXT NOT NULL CHECK (source_type IN ('PDF','MANUAL')),

  content TEXT NOT NULL,              -- normalized natural language atomic fact
  qualifiers JSONB NOT NULL DEFAULT '{}'::jsonb,

  confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  is_uncertain BOOLEAN NOT NULL DEFAULT FALSE,

  created_by TEXT NOT NULL CHECK (created_by IN ('LIBRARIAN','USER')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Invariants:
  CHECK (
    (source_type = 'PDF' AND document_id IS NOT NULL)
    OR
    (source_type = 'MANUAL')
  )
);

CREATE INDEX facts_owner_idx ON facts(owner_id);
CREATE INDEX facts_document_idx ON facts(document_id);
CREATE INDEX facts_source_type_idx ON facts(source_type);
```

Normative rules:
- For PDF facts: document_id must be present.
- For manual facts: document_id may be NULL (or allow linking to a manuscript; see below).

Optional enhancement:
- store a canonical triple structure later (subject/predicate/object) but not required for MVP.

---

## 4.5 manuscripts

Workspace container.

```
CREATE TABLE manuscripts (
  id UUID PRIMARY KEY,
  owner_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  description TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX manuscripts_owner_idx ON manuscripts(owner_id);
```

---

## 4.6 manuscript_documents (many-to-many)

Allows a manuscript to reference multiple PDFs.

```
CREATE TABLE manuscript_documents (
  manuscript_id UUID NOT NULL REFERENCES manuscripts(id) ON DELETE CASCADE,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  PRIMARY KEY (manuscript_id, document_id)
);
```

---

## 4.7 paragraphs

Each paragraph is a stateful unit with a stored Paragraph Spec.

```
CREATE TABLE paragraphs (
  id UUID PRIMARY KEY,
  manuscript_id UUID NOT NULL REFERENCES manuscripts(id) ON DELETE CASCADE,

  section TEXT NOT NULL CHECK (section IN ('Introduction','Methods','Results','Discussion')),
  intent TEXT NOT NULL,                           -- validated in app layer against taxonomy

  spec_json JSONB NOT NULL,                       -- Paragraph Spec (Doc #3)
  allowed_fact_ids UUID[] NOT NULL DEFAULT '{}'::uuid[],

  status TEXT NOT NULL CHECK (status IN (
    'CREATED','GENERATING','NEEDS_REVISION','VERIFIED','PENDING_VERIFY','FAILED_GENERATION'
  )),

  latest_run_id UUID NULL,                        -- pointer to latest writer run
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX paragraphs_manuscript_idx ON paragraphs(manuscript_id);
CREATE INDEX paragraphs_status_idx ON paragraphs(status);
```

Normative requirements:

- spec_json must contain required fields per Doc #3.
- allowed_fact_ids MUST be the only facts permitted in Writer context.

---

## 4.8 sentences

Stores generated and edited sentences.

```
CREATE TABLE sentences (
  id UUID PRIMARY KEY,
  paragraph_id UUID NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,

  "order" INT NOT NULL CHECK ("order" >= 1),
  sentence_type TEXT NOT NULL CHECK (sentence_type IN ('topic','evidence','conclusion','transition')),

  text TEXT NOT NULL,
  is_user_edited BOOLEAN NOT NULL DEFAULT FALSE,

  supported BOOLEAN NOT NULL DEFAULT FALSE,        -- set by verifier gate
  verifier_failure_modes TEXT[] NOT NULL DEFAULT '{}'::text[],
  verifier_explanation TEXT NULL,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE(paragraph_id, "order")
);

CREATE INDEX sentences_paragraph_idx ON sentences(paragraph_id);
CREATE INDEX sentences_supported_idx ON sentences(supported);
```

Normative:

- Sentences MUST NOT be considered displayable unless supported = true OR UI explicitly marks unsupported for review.

---

## 4.9 sentence_fact_links

The grounding relation; the core audit table.

```
CREATE TABLE sentence_fact_links (
  sentence_id UUID NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
  fact_id UUID NOT NULL REFERENCES facts(id) ON DELETE CASCADE,

  score DOUBLE PRECISION NULL CHECK (score IS NULL OR (score >= 0 AND score <= 1)),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (sentence_id, fact_id)
);

CREATE INDEX sfl_fact_idx ON sentence_fact_links(fact_id);
```

Normative invariant (enforced in app logic and tests):

-  For any sentence shown as supported, there MUST exist ≥1 row in this table.

---

## 4.10 runs

Stores each LLM call invocation record for audit and observability.

```
CREATE TABLE runs (
  id UUID PRIMARY KEY,
  owner_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
  paragraph_id UUID NULL REFERENCES paragraphs(id) ON DELETE SET NULL,
  document_id UUID NULL REFERENCES documents(id) ON DELETE SET NULL,

  run_type TEXT NOT NULL CHECK (run_type IN ('LIBRARIAN','WRITER','VERIFIER','REWRITER')),
  provider TEXT NOT NULL,                         -- e.g., 'openai', 'anthropic'
  model TEXT NOT NULL,                            -- e.g., 'gpt-4o', 'claude-3.5-sonnet'
  prompt_version TEXT NOT NULL,

  input_hash TEXT NOT NULL,                       -- hash of normalized inputs
  inputs_json JSONB NOT NULL,                     -- store references/IDs; avoid raw PDF text
  outputs_json JSONB NOT NULL,                    -- structured outputs (facts, sentences, verdicts)

  token_prompt INT NULL,
  token_completion INT NULL,
  cost_usd DOUBLE PRECISION NULL,

  latency_ms INT NULL,
  trace_id TEXT NULL,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX runs_paragraph_idx ON runs(paragraph_id);
CREATE INDEX runs_document_idx ON runs(document_id);
CREATE INDEX runs_type_idx ON runs(run_type);
CREATE INDEX runs_trace_idx ON runs(trace_id);
```

Guidance:

- Avoid storing full raw PDF text; store doc_id + span_ids + small quotes.
- inputs_json can contain allowed_fact_ids, paragraph_spec, etc.

---

## 4.11 jobs

Async job tracking for Celery.

```
CREATE TABLE jobs (
  id UUID PRIMARY KEY,
  owner_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
  job_type TEXT NOT NULL CHECK (job_type IN ('EXTRACT_FACTS','GENERATE_PARAGRAPH','VERIFY_PARAGRAPH','REGENERATE_SENTENCES')),
  target_id UUID NOT NULL,                         -- document_id or paragraph_id
  status TEXT NOT NULL CHECK (status IN ('QUEUED','RUNNING','SUCCEEDED','FAILED','CANCELLED')),
  progress JSONB NOT NULL DEFAULT '{}'::jsonb,
  error TEXT NULL,
  trace_id TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX jobs_target_idx ON jobs(target_id);
CREATE INDEX jobs_status_idx ON jobs(status);
```

---

## 5. Vector Store Schema (Derivative)

### What gets embedded (MVP)

- Embed facts, not raw chunks. Facts are the unit of grounding.

### Vector record fields (conceptual)

- vector_id (provider-specific)
- owner_id
- fact_id (foreign key to Postgres fact)
- embedding_model_version
- namespace (e.g., user:{owner_id})

Postgres remains source of truth; vector store only helps with candidate retrieval.

Optional table (if you want explicit tracking):

```
CREATE TABLE fact_embeddings (
  fact_id UUID PRIMARY KEY REFERENCES facts(id) ON DELETE CASCADE,
  vector_id TEXT NOT NULL,
  embedding_model TEXT NOT NULL,
  namespace TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

##  6. Constraints & Invariants (Normative)

### Invariant I-1: Sentence-level grounding required for display

A sentence is displayable as “verified” iff:
    - sentences.supported = true
    - count(sentence_fact_links where sentence_id = X) >= 1

### Invariant I-2: Writer constraint

Writer MUST only receive facts whose IDs are included in:
    - paragraphs.allowed_fact_ids

### Invariant I-3: Inline attribution completeness

For any verified paragraph:
    - every sentence has ≥1 citation fact link
    - all cited facts belong to allowed set

### Invariant I-4: Auditability

For any paragraph:
    - there exists a WRITER run and VERIFIER run (or combined run record) that can reproduce output

---

## 7. Indexing & Performance Minimums

Minimum indexes already listed above. Additional recommended indexes:

GIN index on facts.qualifiers if querying frequently:

```
CREATE INDEX facts_qualifiers_gin ON facts USING GIN (qualifiers);
```

Full-text index on facts.content if you want basic keyword filtering:

```
CREATE INDEX facts_content_tsv_idx ON facts USING GIN (to_tsvector('english', content));
```

---

## 8. Retention & Deletion Semantics

### Delete Document

When a document is deleted:
- documents row removed
- cascades delete:
    - spans
    - facts where document_id = that doc
    - embeddings for those facts (application must delete from vector store)
- paragraphs remain, but any allowed_fact_ids referencing deleted facts must be invalidated:
    - recommended behavior: mark affected paragraphs NEEDS_REVISION with error

### Delete Manuscript

Cascades delete:
    - paragraphs
    - sentences
    - sentence_fact_links
    - runs linked via paragraph_id

Facts are not automatically deleted unless explicitly requested (since facts may be shared across manuscripts if you allow).

### Delete User (if multi-tenant)

- cascade delete manuscripts
- cascade delete documents and facts
- delete vector namespaces

---

## 9. Migration & Versioning Notes

### Prompt/version tracking (required)

- runs.prompt_version MUST be set from a central registry (even a simple constant initially).

### Schema evolution

Future additions likely:
    - facts.subject/predicate/object triples
    - paragraphs.intent as enum table (not free text)
    - citations export formats
    - collaboration tables (teams, sharing)

---

## 10. Definition of Done (Data Model)

The data model is considered complete for v1.0 when:
    1. A generated paragraph can be fully reconstructed from DB:
        - spec_json, allowed facts, sentences, links, verifier outputs, run records
    2. Sentence-level grounding is queryable in SQL
    3. Deleting a document cleans up derived artifacts safely
    4. Logging/audit does not store raw PDFs beyond minimal quotes/spans