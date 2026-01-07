# Frontend Manual Test Checklist (Phase 4)

This checklist validates the core frontend flow after Phase 4 changes.

## Environment

- `docker compose up --build -d`
- Ensure worker is running: `docker compose ps` shows `worker` as "Up"

## Auth

- Register a new user
- Login and confirm you land on the canvas
- Sign out returns you to auth screen

## Document + Facts

- Upload a PDF
- Extract facts
- Verify fact list loads and shows max 5 entries at a time
- Use search to highlight matches
- Select 1-2 facts and verify selection indicator

## Manuscript + Paragraph

- Create manuscript and link document
- Create paragraph, generate, verify
- Confirm job status auto-updates and toasts show success

## Paragraph View + Inspector

- Load paragraph view and see sentences/citations
- Click a sentence and confirm inspector updates
- Run history shows at least one run entry

## UX + Accessibility

- Keyboard tab to a fact card and select with Enter/Space
- Verify focus ring is visible on buttons/inputs
- Resize viewport under 860px and verify mobile warning appears

