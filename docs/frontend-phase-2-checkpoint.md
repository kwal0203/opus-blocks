# Frontend Phase 2 Checkpoint Plan

This checklist defines Phase 2 (design system + layout) tasks to complete before moving to Phase 3.

---

## 1) Design System Foundation

- [x] Create tokenized typography, color, and spacing scales.
- [x] Define core semantic colors (background, surface, text, accent, success, warning, danger).
- [x] Add base typography rules and consistent focus/hover states.

## 2) UI Primitives

- [x] Build foundational components: Button, Input, Select, Textarea, Badge, Card, Skeleton, Toast.
- [x] Ensure variants for states (primary, muted, danger, success).
- [x] Apply consistent spacing and radius usage via tokens.

## 3) Layout Shell

- [x] Implement three-column shell: Library / Canvas / Inspector.
- [x] Add responsive behavior (stacked on smaller screens).
- [x] Add persistent header status area.

## 4) Style Integration

- [x] Replace ad-hoc styles in `App.jsx` with component-based styles.
- [x] Ensure no regressions to existing ops flow behavior.

## 5) Visual QA

- [x] Quick manual review in desktop + mobile widths.
- [x] Verify contrast and focus states meet accessibility minimums.

---

# Frontend Phase 3 Checkpoint Plan

This checklist defines Phase 3 (core product flows) tasks to complete before moving to Phase 4.

## 1) Auth Screens

- [ ] Build dedicated login and registration panels (full-screen, branded).
- [ ] Persist token to local storage and show user state in header.

## 2) Manuscript Canvas

- [ ] Create manuscript creation flow and route to canvas view.
- [ ] Render section blocks (Introduction/Methods/Results/Discussion) with paragraph slots.

## 3) Fact Library

- [x] Implement document upload + extract flows as a guided panel.
- [x] Render facts list with selection state for allowed facts.
- [x] Add search/filter for facts (by source_type, uncertainty).

## 4) Paragraph Flow

- [ ] Create paragraph spec builder UI (section, intent, structure, constraints).
- [ ] Generate + verify controls with job polling status.
- [ ] Render sentences with citations + failure modes.

## 5) Inspector Panel

- [ ] Active block inspector with paragraph/sentence metadata.
- [ ] Show run history and latest job status for the active paragraph.

## 6) UX Polish (Phase 3-level)

- [ ] Empty states for no manuscripts, no facts, no sentences.
- [ ] Inline error states for job failures and invalid actions.
