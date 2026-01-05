# OpusBlocks.com v1.0 — Implementation Plan (Backend-First)

## 0. Goals

- Multi-tenant from day one (owner_id isolation everywhere).
- Backend pipeline correctness before frontend polish.
- OpenAI first, with provider abstraction for expansion later.

---

## 1. Foundations (Schema + Invariants)

### 1.1 Data Model
- Implement Postgres schema from `docs/data-model.md`.
- Enforce enums and constraints for document/paragraph/job states.
- Indexes and tenant-scope (owner_id) where specified.

### 1.2 Core Invariants (Hard Gates)
- Verify-before-display enforced per `docs/grounded-generation-contract.md`.
- Writer only receives allowed_fact_ids per `docs/paragraph-manuscript-spec.md`.
- Sentence support requires at least one sentence_fact_link.

Acceptance
- Migrations apply cleanly.
- Constraint violations are caught in app logic + tests.

---

## 2. Auth + Multi-Tenancy

### 2.1 Auth
- Email/password auth.
- Every request resolves a user_id.

### 2.2 Tenant Isolation
- All queries scoped by owner_id.
- Vector store namespaces per user_id.
- Idempotency keys per user for job creation.

Acceptance
- Cross-tenant access is impossible via API tests.

---

## 3. Backend API (FastAPI)

### 3.1 Endpoints
Implement API surface from `docs/system-architecture.md`:
- Documents: upload, extract_facts, list facts
- Facts: manual entry
- Paragraphs: create spec, generate, edit, fetch result
- Jobs: status

### 3.2 Validation
- Paragraph Spec validation against `docs/paragraph-manuscript-spec.md`.
- Agent contract schema validation for all LLM outputs.

Acceptance
- All endpoints validate inputs and return contract-compliant outputs.

---

## 4. Async Pipeline (Celery)

### 4.1 Jobs
- extract_facts(document_id)
- generate_paragraph(paragraph_id)
- verify_paragraph(paragraph_id)

### 4.2 Failure Policy
- Retry rules per `docs/operational-plan.md`.
- Failures propagate to job + paragraph state.

Acceptance
- Full job lifecycle state transitions are persisted.

---

## 5. LLM Integration (OpenAI)

### 5.1 Provider Abstraction
- Provider interface with model, prompt_version, temperature.
- Inputs normalized and hashed.

### 5.2 Contracts
- Librarian/Writer/Verifier must emit JSON per `docs/agent-contract.md`.
- Backend rejects invalid outputs.

Acceptance
- Every run logged to `runs` table with trace_id, input_hash, cost.

---

## 6. Observability + Audit Trail

- Trace IDs propagated end-to-end.
- Store run metadata per `docs/data-model.md` and `docs/operational-plan.md`.

Acceptance
- A paragraph is reconstructible from DB artifacts.

---

## 7. Evaluation Harness

- Golden set runner per `docs/evaluation-plan.md`.
- Regression gating for prompt/model changes.

Acceptance
- Metrics computed; false support rate = 0 in golden set.

---

## 8. Local Dev + Tooling

- uv for Python deps.
- docker-compose for local services (Postgres, Redis).
- ruff + pre-commit hooks.
- mypy or pyright when useful.

---

## 9. Deferred (Post-Backend)

- Frontend UI flows in `docs/PRD.md`.
- Vector retrieval UX.
- Multi-provider LLMs.

---

## 10. Current Decisions

- Auth: email/password.
- Storage: local PDF storage for MVP.
- LLM: OpenAI provider first.
