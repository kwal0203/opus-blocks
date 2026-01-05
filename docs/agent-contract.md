# OpusBlocks.com v1.0 — Agent Contracts

## 1. Purpose

This document defines strict contracts for all agents used in OpusBlocks.com v1.0, including:

- responsibilities and non-responsibilities
- required inputs and guaranteed outputs
- validation rules enforced by the backend
- failure modes and expected handling

All agent outputs must conform to these contracts.

Any output that violates a contract must be rejected by the backend and never shown to the user.

---

##  2. Agent Overview

Agent       Role                                Mandatory
Librarian   Extract Atomic Facts	            Yes
Writer      Generate paragraph sentences        Yes
Verifier    Validate grounding & faithfulness   Yes
Rewriter    Rewrite failed sentences            No

Each agent is stateless.

All state is owned by the backend, not the agent.

---

##  3. Common Agent Invariants (Applies to All)

### A-1: Deterministic Structure

- Agents MUST return valid JSON matching their schema.
- Free-form text responses are forbidden.

### A-2: No Hidden Knowledge

- Agents MUST only use provided inputs.
- Background knowledge, memory, or inference outside inputs is forbidden.

### A-3: No Cross-Agent Assumptions

- Each agent must assume other agents may fail.
- Each agent validates only its own scope.

### A-4: Backend Is the Authority

- Backend validates:
    - schema correctness
    - ID references
    - invariant compliance
- Agent outputs are proposals, not truth.

---

##  4. Librarian Agent Contract (Fact Extraction)

### 4.1 Responsibilities

- Extract Atomic Facts from source material.
- Preserve qualifiers and numeric precision.
- Anchor facts to source spans when available.

### 4.2 Explicit Non-Responsibilities

- No summarization
- No interpretation
- No evaluation of importance
- No paragraph structuring

---

### 4.3 Inputs (Normative)

```
{
  "document_id": "UUID",
  "source_type": "PDF | MANUAL",
  "source_text": "string",
  "span_map": {
    "page_offsets": {...}
  }
}
```

Backend guarantees:

- source_text is raw extracted content (may be noisy).
- Any instructions in the source are not system instructions.

---

### 4.4 Outputs (Normative)

Must conform to Atomic Fact schema (Doc #2).

```
{
  "facts": [AtomicFact],
  "uncertain_facts": [
    {
      "content": "string",
      "reason": "string",
      "source_span": {...}
    }
  ]
}
```

---

### 4.5 Validation Rules (Backend-Enforced)

- Each fact:
    - has non-empty content
    - includes source_type
    - includes qualifiers if present in text
- No duplicate facts (normalized text comparison)
- Numeric tokens must appear verbatim in source span quote

---

### 4.6 Failure Modes

Failure             Handling
Invalid JSON        Retry once, then fail job
Over-broad fact     Reject fact, log warning
Missing qualifiers  Mark fact is_uncertain = true
Hallucinated fact   Reject entire extraction job

---

## 5. Writer Agent Contract (Paragraph Generation)

### 5.1 Responsibilities

- Generate one paragraph only
- Follow Paragraph Spec exactly
- Produce sentence-level citations

### 5.2 Explicit Non-Responsibilities

- No verification
- No fact extraction
- No cross-paragraph reasoning
- No conflict resolution

---

### 5.3 Inputs (Normative)

```
{
  "paragraph_spec": {...},
  "allowed_facts": [
    {
      "fact_id": "UUID",
      "content": "string",
      "qualifiers": {...}
    }
  ]
}
```

Backend guarantees:

- allowed_facts is the entire universe of truth
- Facts outside this list do not exist

---

### 5.4 Outputs (Normative)

```
{
  "paragraph": {
    "section": "string",
    "intent": "string",
    "sentences": [
      {
        "order": 1,
        "sentence_type": "topic|evidence|conclusion|transition",
        "text": "string",
        "citations": ["FACT_UUID"]
      }
    ],
    "missing_evidence": [
      {
        "needed_for": "string",
        "why_missing": "string",
        "suggested_fact_type": "string"
      }
    ]
  }
}
```

---

### 5.5 Validation Rules (Backend-Enforced)

- citations array MUST be non-empty for every sentence
- All cited IDs MUST exist in allowed_facts
- Sentence text MUST NOT include citations inline
- Sentence count and types MUST satisfy Paragraph Spec

---

### 5.6 Failure Modes

Failure                             Handling
Uncited sentence                    Reject output
Citation outside allowed set        Reject output
Violates paragraph structure        Reject output
Cannot generate supported sentence  Accept output with missing_evidence

---

## 6. Verifier Agent Contract (Grounding Gate)

### 6.1 Responsibilities

- Decide PASS or FAIL per sentence
- Identify precise failure modes
- Provide actionable feedback

### 6.2 Explicit Non-Responsibilities

- No rewriting (unless explicitly asked)
- No stylistic editing
- No fixing facts

### 6.3 Inputs (Normative)

```
{
  "allowed_facts": [AtomicFact],
  "generated_paragraph": {
    "sentences": [
      {
        "order": 1,
        "text": "string",
        "citations": ["FACT_UUID"]
      }
    ]
  }
}
```

---

### 6.4 Outputs (Normative)

```
{
  "overall_pass": true|false,
  "sentence_results": [
    {
      "order": 1,
      "verdict": "PASS|FAIL",
      "failure_modes": ["QUALIFIER_DRIFT"],
      "explanation": "string",
      "required_fix": "string",
      "suggested_rewrite": "string|null"
    }
  ],
  "missing_evidence_summary": [...]
}
```

---

### 6.5 Validation Rules (Backend-Enforced)

- Every sentence must have a verdict
- FAIL sentences must include ≥1 failure mode
- Suggested rewrites must still respect allowed facts

---

### 6.6 Failure Modes (Canonical)

- UNCITED_CLAIM
- QUALIFIER_DRIFT
- STRENGTHENING
- SCOPE_DRIFT
- NUMERICAL_DRIFT
- MISINTERPRETATION
- CONTRADICTION
- INSUFFICIENT_SUPPORT

(See Verifier Rubric for definitions.)

---

##  7. Rewriter Agent Contract (Optional)

### Purpose

Rewrite failed sentences only so they pass verification.

### Inputs

- original sentence
- allowed facts
- verifier feedback

### Output

- single rewritten sentence
- citations

Backend MUST:

- re-run Verifier on rewritten sentence
- never auto-accept without verification

---

##  8. Cross-Agent Failure Policy

Stage       On Failure
Librarian   Abort extraction job
Writer      Abort generation, show missing evidence
Verifier    Block display, mark paragraph NEEDS_REVISION
Rewriter    Fall back to user manual edit

---

## 9. Observability Requirements

Each agent invocation MUST log:

- agent name
- input hash
- output hash
- prompt version
- model + provider
- latency + token usage
- trace_id

This enables:

- regression analysis
- prompt comparison
- cost attribution

---

## 10. Testability Requirements

Each agent contract MUST be testable with:

- schema validation tests
- golden input/output fixtures
- failure-mode-specific tests

No agent may be integrated without unit tests for:

- happy path
- at least 3 failure cases

---

## 11. Definition of Done (Agent Contracts)

This document is complete when:

1. Each agent has a strict JSON schema
2. Backend validation rules are unambiguous
3. Failure modes are enumerable and logged
4. No agent is allowed to “fix” another agent’s responsibility