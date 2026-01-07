# OpusBlocks v1.0 — Frontend Design Specification

This document serves as the formal "Source of Truth" for the OpusBlocks frontend implementation. It translates the backend data model and the "Grounded Generation Contract" into a modular, block-based user interface.

---

## 1. Design Philosophy: The Modular Block System

The UI is not a document editor; it is a Composition Canvas.

- Atomic Nature: Every piece of text is a "Block" tied to a specific database UUID.
- Visual Stability: Verified blocks are "solid" and immutable until explicitly edited.
- Traceability: Every block must visually anchor to its evidence source.

---

## 2. Component Taxonomy

### 2.1 Fact Blocks (AtomicFactCard)

- Data Source: facts table.
- Visuals: Small cards with a "pill" for source_type (PDF vs MANUAL).
- Interaction: Draggable into the "Allowed Evidence" slot of a paragraph.
- States: * Uncertain: Dashed yellow border if is_uncertain: true.
    - Cited: Highlighted when the parent sentence is hovered.

### 2.2 Sentence Blocks (SentenceBlock)

- Data Source: sentences table.
- Types: Topic, Evidence, Conclusion, Transition (indicated by subtle color accents).
- Verification Indicators (Invariant I-1):
    - Verified: Green left-border, blue citation badges [1] linked to sentence_fact_links.
    - Failed: Red "fractured" border with a hoverable error icon displaying failure_modes (e.g., QUALIFIER_DRIFT).

### 2.3 Paragraph Blocks (ParagraphContainer)

- Data Source: paragraphs table.
- Header: Displays the Section (IMRAD) and Intent (e.g., "Knowledge Gap").
- Status Overlay: While status is GENERATING, a skeleton loader covers the block.

---

## 3. State Management & API Strategy

### 3.1 Server State (TanStack Query)

The coding agent must implement the following "Resource Hooks":

- useManuscript(id): Fetches full manuscript hierarchy.
- useFacts(documentId): Fetches extracted facts with pagination.
- useJobStatus(jobId): Critical. Must poll every 2 seconds while a job is QUEUED or RUNNING.

### 3.2 Client State (Zustand/Context)

- activeBlockId: Tracks which paragraph/sentence is currently being edited or inspected.
- selectionStore: Manages the list of allowed_fact_ids before the user hits "Generate".

---

## 4. Primary User Flows

### Flow A: The Generation Sequence

1. Selection: User clicks "Add Block" and chooses an Intent (e.g., Background Context).
2. Constraint: User selects Fact Blocks to populate the allowed_fact_ids array.
3. Trigger: POST /paragraphs/{id}/generate.
4. Wait: UI displays a GENERATING skeleton block, polling the Job status.
5. Render: UI replaces skeleton with Sentence Blocks based on the verifier outcome.

### Flow B: The Verification Feedback Loop

1. Edit: User clicks a Sentence Block to modify text.
2. Pending State: Block immediately dims and displays a PENDING_VERIFY badge.
3. Re-Verify: Backend enqueues verify_paragraph job.
4. Feedback: If verification fails, the specific failure_modes and verifier_explanation are rendered in an inspector panel.

---

## 5. Layout Architecture

- Left Sidebar (The Library): Document uploader and searchable Fact repository.
- Center Canvas (The Manuscript): Vertical stack of Paragraph Blocks.
- Right Sidebar (The Inspector): Metadata for the activeBlockId, showing citation details, confidence scores, and Run history.

---

## 6. Definition of Done for Frontend Agent

[ ] Implements Invariant I-1: Supported sentences MUST have citation badges.

[ ] Implements Job Polling: No infinite spinners; UI updates as jobs succeed/fail.

[ ] Implements Strict Intent Mapping: Users cannot select "Results" intent in an "Introduction" section.

[ ] Implements Mobile Safety: Desktop-first layout, as scientific writing requires screen density.