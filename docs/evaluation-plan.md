# OpusBlocks.com v1.0 — Verification & Evaluation Plan

## 1. Purpose

This document specifies:

- what “correct” means for grounded paragraph generation,
- how verification is performed and gated,
- how quality is measured offline and online,
- how regressions are detected and prevented.

This plan applies to all generated paragraphs and sentences and is mandatory for production readiness.

---

## 2. Scope

### In Scope

- Sentence-level grounding verification
- Paragraph-level acceptance criteria
- Offline evaluation (golden sets)
- Online monitoring and alerts
- Regression gating for prompts/models

### Out of Scope (v1)

- Cross-paragraph coherence metrics
- Human preference optimization
- Automated citation formatting checks

---

## 3. Verification vs Evaluation (Clear Distinction)

### Verification (Hard Gate)

- Deterministic decision: PASS or FAIL
- Applied before display
- Enforced for every sentence

### Evaluation (Measurement)

- Statistical metrics over datasets
- Used to track quality trends and regressions
- Does not override verification gates

---

## 4. Verification Rules (Normative)

A sentence MUST PASS verification to be displayed as supported.

### Mandatory Checks

1. Citation Presence
    - ≥1 fact cited per sentence
2. Citation Validity
    - All cited facts ∈ allowed_fact_ids
3. Semantic Entailment
    - Sentence meaning is entailed by cited facts
4. Qualifier Integrity
    - No added or altered qualifiers
5. Scope Fidelity
    - No generalization beyond evidence
6. Strength Fidelity
    - No strengthening (e.g., correlation → causation)
7. Numerical Accuracy
    - Numbers/units match facts exactly

### Verdicts

- PASS — sentence is fully supported
- FAIL — sentence violates ≥1 rule

If any sentence FAILs → paragraph is NOT VERIFIED.

---

## 5. Canonical Failure Modes

The Verifier must label each FAIL with ≥1 failure mode:

Failure Mode            Meaning
UNCITED_CLAIM           Claim without evidence
QUALIFIER_DRIFT         Added/changed population, timeframe, dosage, setting
STRENGTHENING           Claim stronger than evidence
SCOPE_DRIFT             Overgeneralization
NUMERICAL_DRIFT         Changed numbers or units
MISINTERPRETATION       Incorrect reading of evidence
CONTRADICTION           Conflicts with cited facts
INSUFFICIENT_SUPPORT    Related but not entailed

These labels are used for analytics and targeted improvement.

---

## 6. Paragraph-Level Acceptance Criteria

A paragraph is VERIFIED if and only if:

1. All sentences PASS verification
2. Required sentence structure (per Paragraph Spec) is satisfied
3. No forbidden claim types appear
4. Inline attribution is complete

Otherwise, paragraph status = NEEDS_REVISION.

---

## 7. Offline Evaluation (Golden Sets)

### 7.1 Purpose

Offline evaluation measures:

- grounding accuracy
- refusal correctness
- robustness across intents and sections

### 7.2 Golden Dataset Composition (MVP)

- 10–20 PDFs
- 100–300 Atomic Facts
- 20–40 Paragraph Specs, covering:
    - all IMRAD sections
    - ≥1 paragraph per intent

Each golden item includes:

- source PDF
- extracted facts (human-reviewed)
- paragraph spec
- expected:
    - supported sentences OR
    - expected refusal/missing evidence

### 7.3 Evaluation Procedure

For each golden paragraph:

1. Run full pipeline:
    - Writer → Verifier
2. Record:
    - sentence verdicts
    - failure modes
    - missing evidence reports
3. Compare against expected outcome

---

### 7.4 Offline Metrics

### Sentence-Level Metrics

- Support Rate
    - % sentences that PASS verification
- False Support Rate (Critical)
    - % sentences marked PASS that should FAIL
- Hallucination Rate
    - % sentences containing uncited claims

### Paragraph-Level Metrics

- Verified Paragraph Rate
- Correct Refusal Rate
- Over-Refusal Rate (refused but evidence exists)

### Failure Mode Distribution

- % QUALIFIER_DRIFT
- % STRENGTHENING
- % SCOPE_DRIFT
- etc.

---

## 8. Acceptance Thresholds (MVP)

These are release-blocking gates.

Metric                  Threshold
False Support Rate      0%
Sentence Support Rate   ≥ 95%
Correct Refusal Rate    ≥ 90%
Over-Refusal Rate       ≤ 10%
Critical Failures       0

If thresholds are not met → do not deploy.

---

## 9. Regression Testing & CI Gating

### 9.1 When to Run Regression

- Prompt changes
- Model changes
- Verifier logic updates
- Paragraph Spec changes

### 9.2 Regression Policy

- Re-run golden set
- Compare metrics against baseline
- Block merge/deploy if:
    - any new false supports appear
    - support rate drops >2%
    - refusal correctness drops >5%

---

## 10. Online Evaluation & Monitoring

### 10.1 Live Metrics (Per Day / Per Release)

- Sentence support rate
- Paragraph verification rate
- Regeneration rate
- Missing evidence rate
- Cost per paragraph
- Latency P50 / P95

### 10.2 Failure Alerts

Trigger alerts if:

- Any sentence marked PASS later found unsupported (manual review)
- Spike in QUALIFIER_DRIFT or STRENGTHENING
- Sudden rise in over-refusals

---

## 11. Human Review Loop (Lightweight)

For early production:

- Sample 1–5% of paragraphs weekly
- Human reviewer checks:
    - factual faithfulness
    - verifier correctness
- Use feedback to:
    - update golden sets
    - refine verifier prompts

Human review does not override verification gating.

---

## 12. Evaluation Artifact Storage

Persist:

- golden datasets (versioned)
- evaluation runs + metrics
- baseline comparison results

These artifacts enable:

- auditability
- demo credibility
- interview proof

---

## 13. Model & Prompt Comparison

When testing alternatives:

- Run golden set across:
    - multiple models (e.g., GPT-4o vs Claude 3.5)
    - multiple prompt versions
- Compare:
    - support rate
    - refusal behavior
    - cost per paragraph

Decision rule:

Prefer the most conservative model that meets thresholds.

---

## 14. Definition of Done (Verification & Evaluation)

This plan is complete when:

1. Verification gates are strictly enforced
2. Golden datasets exist and are versioned
3. Metrics are computable from stored data
4. Regression failures block deployment
5. Online monitoring dashboards exist