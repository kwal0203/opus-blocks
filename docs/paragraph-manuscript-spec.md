# OpusBlocks.com v1.0 — Paragraph & Manuscript Specification

## 1. Purpose

This document defines:

- the manuscript structure supported by OpusBlocks.com,
- the paragraph intent taxonomy,
- and the formal Paragraph Specification (Paragraph Spec) used to generate, verify, and audit paragraphs.

All paragraph generation must be driven by a Paragraph Spec defined here.

---

## 2. Manuscript Model (IMRAD)

OpusBlocks.com v1.0 supports the standard IMRAD structure:

Section         Purpose
Introduction    Establish context, problem, and knowledge gap
Methods         Describe study design and procedures
Results         Present empirical findings
Discussion      Interpret results and relate to literature

Each section is composed of independent paragraphs, generated one at a time.

---

## 3. Paragraph Intent Taxonomy (Core)

Each paragraph MUST declare exactly one Intent.
Intent determines structure, allowed claims, and required evidence types.

### 3.1 Introduction Intents

### I-1: Background Context

Goal: Describe established background facts.

Allowed:

- Well-supported descriptive facts
- Definitions (if present in sources)

Forbidden:

- Novel claims
- Study-specific results

Required evidence:

- General descriptive facts

---

### I-2: Prior Work Summary

Goal: Summarize existing studies or findings.

Allowed:

- Reporting results from cited studies
- Neutral comparison

Forbidden:

- Evaluation or criticism
- Claims of insufficiency unless explicit

Required evidence:

- Study outcome facts
- Population + method qualifiers

--- 
### I-3: Knowledge Gap

Goal: Explicitly state what is unknown, missing, or limited.

Allowed:

- Statements of absence or limitation only if supported
- Contradictions between studies

Forbidden:

- Implicit novelty claims without evidence
- Overgeneralized “no studies exist” claims

Required evidence:

- Explicit limitation statements
- Comparative or absence facts

---

### I-4: Study Objective

Goal: State the purpose of the current study.

Allowed:

- Rephrasing of study aims if present in sources
- Narrow objective statements

Forbidden:

- Claiming significance or impact

Required evidence:

- Explicit objective statements

--- 

### 3.2 Methods Intents

### M-1: Study Design

Goal: Describe experimental or observational design.

Required evidence:

- Design type
- Population
- Setting

Forbidden:

- Justification language (“appropriate”, “robust”)

---

### M-2: Participants / Data Sources

Goal: Describe sample or dataset.

Required evidence:

- Inclusion/exclusion
- Sample size
- Source

---

### M-3: Procedures / Protocol

Goal: Describe what was done.

Required evidence:

- Stepwise procedural facts
- Timing, dosage, instrumentation if present

---

### M-4: Analysis Methods

Goal: Describe statistical or analytical methods.

Required evidence:

- Named methods
- Parameters if stated

Forbidden:
- Claims of correctness or validity

---

### 3.3 Results Intents

### R-1: Primary Results

Goal: Report main findings.

Required evidence:

- Quantitative results
- Units, direction, magnitude

Forbidden:

- Interpretation
- Causal claims unless explicit

---

### R-2: Secondary Results

Goal: Report additional findings.

Same constraints as R-1.

---

### R-3: Null / Negative Results

Goal: Explicitly state non-findings.

Required evidence:

- Explicit “no significant difference” facts

Forbidden:

- Downplaying or reinterpretation

---

### 3.4 Discussion Intents

### D-1: Result Interpretation

Goal: Interpret findings within evidence limits.

Allowed:

- Restating findings in context
- Cautious interpretation if explicitly stated

Forbidden:

- Speculation
- New explanations

---

### D-2: Comparison to Prior Work

Goal: Compare results to cited studies.

Required evidence:

- Prior study results
- Explicit comparison facts

Forbidden:

- Claims of superiority or novelty without evidence

---

### D-3: Limitations

Goal: Describe study limitations.

Allowed:

- Only explicitly acknowledged limitations

Forbidden:

- Invented weaknesses

---

### D-4: Implications / Future Work

Goal: State implications or future directions.

Allowed:

- Explicitly stated implications
- Cautious framing

Forbidden:

- Predictions or strong recommendations

---

## 4. Paragraph Structural Requirements

Every paragraph consists of typed sentences.

Sentence Types

- topic — introduces paragraph purpose
- evidence — reports factual content
- conclusion — synthesizes or transitions
- transition — optional bridge to next paragraph

Each intent defines minimum required counts.

---

## 5. Paragraph Spec (Normative Schema)

This object is required for generation.

```
{
  "paragraph_id": "UUID",
  "section": "Introduction | Methods | Results | Discussion",
  "intent": "Knowledge Gap | Study Design | Primary Results | ...",
  "required_structure": {
    "topic_sentence": true,
    "evidence_sentences": 2,
    "conclusion_sentence": true
  },
  "allowed_fact_ids": ["FACT_001", "FACT_002"],
  "style": {
    "tense": "present | past",
    "voice": "academic",
    "target_length_words": [120, 150]
  },
  "constraints": {
    "forbidden_claims": [
      "novelty",
      "causation",
      "generalization beyond evidence"
    ],
    "allowed_scope": "as stated in facts only"
  }
}
```

## 6. Intent → Evidence Mapping Rules

Intent              Minimum Evidence Types
Background Context  Descriptive facts
Prior Work          Study result facts
Knowledge Gap       Limitation or absence facts
Study Design        Design + population
Procedures          Procedural steps
Results             Quantitative outcomes
Interpretation      Result restatement
Limitations         Explicit limitation statements

If required evidence types are missing → mandatory refusal.

---

## 7. Generation Constraints (Normative)

- One paragraph per generation request
- No cross-paragraph assumptions
- No reference to “this paper” unless explicitly stated in facts
- No evaluative language unless directly supported

---

## 8. Verification Hooks

Each Paragraph Spec MUST be logged with:

- Paragraph ID
- Intent
- Allowed facts
- Generated sentences
- Verifier outcomes

This enables:

- Intent-specific evaluation
- Drift analysis by intent
- Targeted improvements

---

## 9. Extensibility (Non-Blocking)

Future versions may add:

- Sub-intents
- Discipline-specific schemas
- Cross-paragraph coherence rules

All extensions MUST preserve:

- Sentence-level grounding
- Intent-based constraints

---

## 10. Definition of Compliance

A paragraph complies with this specification if:

1. It declares a valid section + intent
2. It satisfies required sentence structure
3. Every sentence is grounded per Contract
4. No forbidden claim types appear
5. Verification passes

---

## 11. Design Rationale (Informative)

This specification:

- forces intent clarity
- limits LLM freedom
- enables deterministic verification
- maps directly to prompts, schemas, and UI controls