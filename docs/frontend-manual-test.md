# Frontend Manual Test Checklist (Phase 7)

This checklist validates the core frontend flow after Phase 7 QA + polish updates.

## Environment

- `docker compose up --build -d`
- Ensure worker is running: `docker compose ps` shows `worker` as "Up"

## Auth

- Register a new user
- Login and confirm you land on the canvas
- Sign out returns you to auth screen

## Generate Facts

- Upload a PDF (button triggers file picker)
- Extract facts and wait for auto-refresh
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
- Tab to a sentence card and press Space to select it
- Run history shows at least one run entry
- Allowed Facts and Citations panels show expected entries

## UX + Accessibility

- Keyboard tab to action buttons and select with Enter/Space
- Verify focus ring is visible on buttons/inputs
- Resize viewport under 860px and verify mobile warning appears
