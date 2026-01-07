# Frontend Phase 1 Checkpoint Plan

This checklist defines the remaining Phase 1 work required before moving to Phase 2.

---

## 1) API Client Coverage

- [x] Replace all remaining direct fetch usage with `apiJson` / `apiForm` helpers.
- [x] Add helper utilities for job polling (status fetch + terminal state check).
- [x] Standardize error handling to show `detail`/`message` where present.

## 2) Types + Data Contracts

- [x] Expand JSDoc typedefs in `frontend/src/api/types.js` to cover Manuscript, Document, Run, FactSuggestion.
- [x] Add inline JSDoc on any remaining untyped state or responses in `App.jsx`.
- [x] Add a brief `API_TYPES.md` (or inline comments) noting how frontend maps to backend schemas.

## 3) Config + Environment

- [x] Ensure `VITE_API_BASE_URL` is documented in `README.md` and optionally `.env.example` for frontend.
- [x] Add a small note explaining the Base URL input uses this value as a default.

## 4) App.jsx Consolidation

- [x] Extract the low-level API calls into `frontend/src/api/ops.js` so `App.jsx` only calls named functions.
- [x] Keep the existing UI behavior intact (no redesign yet).

## 5) Sanity Checks

- [x] Manual smoke test with docker compose: login, upload, extract, generate, verify, view.
- [x] Confirm queued jobs move when worker is running.
