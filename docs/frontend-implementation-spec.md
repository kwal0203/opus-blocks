# OpusBlocks Frontend Implementation Spec (v1)

This document extends `docs/frontend.md` into a build-ready, implementation-level specification. It defines API contracts, UI behavior, state management, and acceptance criteria.

---

## 1) Scope and Principles

- Product goal: a block-based, evidence-grounded manuscript editor.
- Non-goals: full WYSIWYG editor, collaborative editing, offline mode.
- Primary persona: internal researchers/reviewers validating outputs.

---

## 2) Information Architecture

### 2.1 Routes

- `/login` (auth)
- `/register` (auth)
- `/manuscripts/:id` (canvas + inspector)
- `/documents/:id` (facts explorer)
- Note: there is no `GET /manuscripts` list endpoint yet; UI should create and route directly.

### 2.2 Layout

- Left Sidebar: Document uploader + Fact library + filters.
- Center Canvas: Paragraph blocks by manuscript section.
- Right Sidebar: Inspector for active block, job status, run history.

---

## 3) Design System (Tokens)

- Typeface: define a purposeful pairing (e.g., serif for content, sans for UI chrome).
- Colors (CSS variables):
  - `--bg`, `--surface`, `--text`, `--muted`, `--accent`, `--success`, `--warning`, `--danger`.
- Spacing scale: 4/8/12/16/24/32.
- Status styles:
  - Verified: green border, blue citation badges.
  - Failed: red fractured border, error icon + tooltip.
  - Generating: skeleton overlay + spinner.
- Accessibility: minimum contrast 4.5:1, focus ring visible.

---

## 4) Data Model Mapping

### 4.1 Fact

- Source: `facts` table.
- Render:
  - `content`, `source_type`, `confidence`, `is_uncertain`.
  - `span_id` for source anchor; if null, show "No span" badge.
- States:
  - `is_uncertain` => dashed yellow border.
  - Highlight when used by hovered sentence.

### 4.2 Sentence

- Source: `sentences` table + `sentence_fact_links`.
- Fields: `text`, `order`, `sentence_type`, `supported`, `verifier_failure_modes`, `verifier_explanation`.
- Render:
  - Citation badges map to `sentence_fact_links`.
  - `supported == true` => Verified style.
  - `supported == false` => Failed style with failure list.

### 4.3 Paragraph

- Source: `paragraphs` table + `paragraph_runs`.
- Fields: `section`, `intent`, `status`, `spec_json`, `latest_run_id`.
- Render:
  - Header with Section + Intent.
  - If status in `GENERATING` or `PENDING_VERIFY`, show overlay.

---

## 5) API Contract (Backend v1)

Base URL: `/api/v1`.
Auth: Bearer token in `Authorization` header.

### 5.1 Auth

- `POST /auth/register` -> `{ id, email }`
- `POST /auth/login` -> `{ access_token, token_type }`

### 5.2 Manuscripts

- `POST /manuscripts` -> create
- `GET /manuscripts/{id}` -> manuscript detail
- `POST /manuscripts/{id}/documents/{doc_id}` -> link document (204)
- `GET /manuscripts/{id}/facts` -> list facts
- `GET /manuscripts/{id}/facts/with-spans` -> list facts + span

### 5.3 Documents + Facts

- `POST /documents/upload` (multipart) -> document
- `GET /documents/{id}` -> document
- `POST /documents/{id}/extract_facts` -> job
- `GET /documents/{id}/facts` -> list (no pagination yet)
- `GET /documents/{id}/facts/with-spans` -> list facts + span
- `POST /documents/{id}/facts` -> create fact + span
- `GET /documents/{id}/runs` -> list document runs
- `POST /facts/manual` -> create manual fact
- `DELETE /facts/{id}` -> delete fact

### 5.4 Paragraphs

- `POST /paragraphs` -> create with `{ manuscript_id, spec }`
  - `spec` matches `ParagraphSpecInput`: `section`, `intent`, `required_structure`, `allowed_fact_ids`, `style`, `constraints`.
- `POST /paragraphs/{id}/generate` -> job
- `POST /paragraphs/{id}/verify` -> job
- `POST /paragraphs/{id}/verify-rollup` -> refresh paragraph status from sentences
- `GET /paragraphs/{id}/view` -> paragraph + sentences + facts + links
- `GET /paragraphs/{id}/runs` -> list paragraph runs
- `GET /paragraphs/{id}/suggest-facts` -> list fact suggestions

### 5.5 Sentences

- `PATCH /sentences/{id}` -> edit sentence, returns job (verify enqueued)
- `POST /sentences/{id}/verify` -> direct sentence verification update
- `POST /sentences` -> create sentence
- `GET /sentences/paragraph/{paragraph_id}` -> list sentences
- `POST /sentences/links` -> create sentence-fact link
- `GET /sentences/{id}/links` -> list sentence-fact links

### 5.6 Runs

- `GET /runs` -> filterable by `run_type`, `paragraph_id`, `document_id`

### 5.7 Jobs

- `GET /jobs/{id}` -> `{ status, progress, error, trace_id }`

---

## 6) State Management

### 6.1 Server State (TanStack Query)

Hooks:

- `useManuscript(id)`
- `useFacts(documentId)`
- `useParagraphView(id)`
- `useJobStatus(jobId)` with polling every 2s when status is QUEUED/RUNNING

### 6.2 Client State (Zustand or Context)

- `activeBlockId`: string | null
- `selectionStore`: `allowed_fact_ids[]`
- `authStore`: `token`, `user`, `expires_at`

---

## 7) Critical UX Flows

### 7.1 Generation Sequence

1. User creates paragraph with `section` + `intent` (spec includes `allowed_fact_ids`).
2. User selects allowed facts before creation; there is no update endpoint yet.
3. POST generate, capture job ID.
4. Poll job status until terminal state.
5. Render sentences with citations, mark verified or failed.

### 7.2 Verification Loop

1. User edits a sentence.
2. UI dims block, shows `PENDING_VERIFY`.
3. Backend verify job enqueued.
4. On completion, update `supported` and `verifier_failure_modes`.

---

## 8) Empty, Loading, and Error States

- No manuscripts: CTA to create.
- No facts: explain extraction and show "Extract" button.
- Jobs failed: inline error with retry.
- No citations: show "Uncited" badge and failure mode.
- Loading: skeleton for paragraph + spinner for job.

---

## 9) Validation Rules

- Strict Intent Mapping: disallow invalid intent/section combos; disable options in UI.
- Block immutability: verified sentences are read-only until user explicitly edits.
- Citation invariants: sentence with `supported == true` must render citations.

---

## 10) Testing Expectations

- Unit: rendering of Fact, Sentence, Paragraph blocks.
- Integration: job polling + state transitions.
- E2E: login -> upload -> extract -> generate -> verify -> edit -> reverify.

---

## 11) Definition of Done

- Invariant I-1 enforced: verified sentences show citations.
- Job polling reliable with terminal state resolution.
- Intent mapping enforced in UI.
- Responsive layout works on desktop; mobile displays warning/limited mode.
