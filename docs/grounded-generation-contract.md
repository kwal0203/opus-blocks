# OpusBlocks.com v1.0 — Grounded Generation Contract

## 1. Purpose

This document defines the hard guarantees OpusBlocks.com provides regarding factual grounding, attribution, and refusal behavior during paragraph generation.

All system components (agents, backend services, UI) must conform to this contract.
Any output that violates this contract must not be displayed to the user.

---

## 2. Scope

This contract applies to:

- Paragraph-by-paragraph generation
- All generated sentences
- All evidence sources (PDF-derived and user-entered facts)

Out of scope:

- Full-manuscript coherence
- External knowledge retrieval
- Citation formatting styles (APA, IEEE, etc.)

---

## 3. Core Definitions

### 3.1 Atomic Fact

An Atomic Fact is the smallest indivisible factual claim that:

- is explicitly supported by a user-provided source, and
- loses or changes meaning if any component is removed.

### Atomic Fact Requirements

1. An Atomic Fact MUST:
    - Be derived from explicit source content (PDF text or user input)
2. Contain all relevant qualifiers, including when present:
    - population
    - setting
    - timeframe
    - method
    - measurement units
3. Avoid aggregation or inference beyond the source
4. Be stored with provenance metadata

### Atomic Fact Schema (Normative)

```
AtomicFact {
  id: UUID
  content: string
  source_type: PDF | MANUAL
  source_span: {
    document_id: string
    page: int | null
    start_char: int | null
    end_char: int | null
    quote: string | null
  }
  qualifiers: JSON
  confidence: float
}
```

---

### 3.2 Supported Sentence

A Supported Sentence is a generated sentence for which:

- every factual claim in the sentence is entailed by ≥1 Atomic Fact
- no factual detail exceeds, strengthens, or generalizes beyond those facts

A sentence is either Supported or Unsupported.

There is no partial support.

---

### 3.3 Inline Attribution

Inline Attribution is the explicit linking of a sentence to its supporting Atomic Fact IDs at render time.

Example:

Treatment X reduced symptom severity in older adults. [FACT_012][FACT_018]

Inline attribution is mandatory for every sentence.

---

## 4. System Guarantees (Non-Negotiable)

### G-1: No Ungrounded Sentences

The system SHALL NOT display any sentence that does not pass verification against its cited Atomic Facts.

---

### G-2: Sentence-Level Grounding

Grounding SHALL be enforced at the sentence level, not paragraph or document level.

Each sentence must:

- reference ≥1 Atomic Fact
- be independently verifiable

---

### G-3: No External Knowledge

The system SHALL NOT:

- use background knowledge
- rely on common sense
- introduce domain knowledge not present in Atomic Facts

All reasoning must be reducible to provided facts.

---

### G-4: Qualifier Preservation

The system SHALL NOT:

- add new qualifiers
- alter scope
- strengthen claims
- generalize populations

If a qualifier is missing from available facts, the sentence must omit it or refuse.

---

### G-5: Mandatory Refusal on Insufficient Evidence

If required evidence is missing, ambiguous, or conflicting, the system SHALL:

- refuse to generate the unsupported sentence
- explicitly state what evidence is required

Silent approximation is forbidden.

---

## 5. Allowed and Forbidden Operations

### 5.1 Allowed

- Rephrasing factual content without changing meaning
- Combining multiple Atomic Facts only if the resulting sentence is strictly entailed
- Restating facts in academic prose

---

### 5.2 Forbidden

- Hallucination or inference
- Strengthening claims (e.g., correlation → causation)
- Scope expansion (sample → population)
- Qualifier drift (timeframe, dosage, setting)
- Numerical modification
- Using uncited facts

---

## 6. Verification Requirements

### 6.1 Verification Is Mandatory

Every generated sentence MUST pass verification before display.

Verification SHALL check:

- Citation presence
- Semantic entailment
- Qualifier integrity
- Scope and strength fidelity
- Numerical accuracy

---

### 6.2 Verification Outcome States

Each sentence must be labeled as exactly one of:

- PASS — fully supported
- FAIL — unsupported or partially supported

If any sentence FAILs, the paragraph SHALL be marked as not verified.

---

## 7. Failure Handling Policy

### 7.1 On Verification Failure

The system SHALL:

- suppress the failed sentence from final output, OR
- visually mark it as unsupported and block finalization

The user MUST be informed:

- why the sentence failed
- what evidence is required to fix it

---

### 7.2 User Edits

If a user edits a sentence:

- verification MUST re-run
- unsupported edits MUST be blocked or flagged

---

## 8. Manual Facts as First-Class Evidence

User-entered facts:

- are treated identically to PDF-derived facts
- are subject to the same grounding rules
- must still support all generated claims

Manual facts do NOT bypass verification.

---

## 9. Conflict Policy

If two Atomic Facts conflict:

- the system SHALL NOT resolve the conflict automatically
- the system MAY:
    - present both with explicit attribution, OR
    - refuse and ask the user to choose an authoritative fact

---

## 10. Auditability & Traceability

For every generated paragraph, the system MUST be able to reconstruct:

- the Paragraph Spec
- the allowed Atomic Facts
- each sentence
- its cited facts
- the verifier decision and rationale

This data SHALL be persisted for debugging and evaluation.

---

## 11. Compliance Criteria (Definition of Contract Adherence)

The system is compliant with this contract if and only if:

1. No displayed sentence lacks inline attribution
2. No displayed sentence fails verification
3. Refusals occur deterministically on missing evidence
4. All claims are traceable to Atomic Facts
5. Verification outcomes are logged and inspectable

---

## 12. Design Intent (Non-Normative)

This contract is intentionally strict.

OpusBlocks.com prioritizes:

- scientific integrity over fluency
- refusal over hallucination
- traceability over creativity

Any future relaxation of these rules MUST be explicit and versioned.