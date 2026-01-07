# OpusBlocks Frontend Plan (Vite + React)

This plan implements the frontend based on `docs/frontend-implementation-spec.md` using Vite + React.

---

## Phase 1: Project Setup + API Contract

- Scaffold a Vite + React app in `frontend/` (if not already) and align package scripts.
- Add a typed API client (fetch wrapper) with auth header injection.
- Define shared TypeScript types that mirror backend schemas.
- Add environment config: `VITE_API_BASE_URL` with default `/api/v1`.

Deliverables:
- `frontend/src/api/client.ts`
- `frontend/src/api/types.ts`
- `frontend/src/config.ts`

---

## Phase 2: Design System + Layout

- Establish typography pairing and color tokens.
- Build base UI primitives: Button, Input, Select, Badge, Card, Skeleton, Toast.
- Implement layout shell: Left Library, Center Canvas, Right Inspector.

Deliverables:
- `frontend/src/styles/tokens.css`
- `frontend/src/components/ui/*`
- `frontend/src/layout/*`

---

## Phase 3: Auth + Manuscript Bootstrap

- Build login/register forms.
- Store tokens (localStorage + in-memory).
- Create manuscript flow (POST `/manuscripts`), route to manuscript canvas.

Deliverables:
- `frontend/src/pages/Login.tsx`
- `frontend/src/pages/Register.tsx`
- `frontend/src/pages/Manuscript.tsx`

---

## Phase 4: Documents + Facts

- Implement document upload and extract flow.
- Facts library with filtering and selection for allowed facts.
- Render FactBlock cards with uncertainty states.

Deliverables:
- `frontend/src/features/facts/*`
- Fact selection store + UI.

---

## Phase 5: Paragraph + Sentences

- Paragraph creation with strict intent mapping.
- Generate + Verify jobs with polling and status overlays.
- Render Sentence blocks with citations + failure modes.
- Sentence edit + reverify flow.

Deliverables:
- `frontend/src/features/paragraphs/*`
- `frontend/src/features/sentences/*`

---

## Phase 6: Jobs + Inspector

- Job polling hook for all job types.
- Right sidebar inspector with metadata, citations, and run history.

Deliverables:
- `frontend/src/features/jobs/*`
- `frontend/src/features/inspector/*`

---

## Phase 7: QA + Polish

- Empty, loading, and error states across flows.
- Accessibility checks (focus, contrast, keyboard nav).
- Manual test script for end-to-end demo.

Deliverables:
- `docs/frontend-manual-test.md`

