# OpusBlocks.com v1.0 — Operational Plan (LLMOps, Cost, Reliability)

## 1. Purpose

This document defines:

- operational assumptions and budgets
- runtime controls for cost, latency, and reliability
- observability requirements
- deployment and go-live checklist
- incident response and rollback procedures

It ensures the system is operable, not just correct.

---

## 2. Operating Assumptions (MVP)

### Usage Model

- Paragraph-by-paragraph generation
- Single-user or small multi-user (≤50 active users)
- Academic/research usage (bursty, not real-time critical)

### Load Expectations (Initial)

- Concurrent users: 5–20
- Paragraph generations per user per session: 5–15
- PDFs per manuscript: 1–5

These assumptions directly inform rate limits, worker counts, and cost budgets.

---

## 3. LLMOps Strategy

### 3.1 Model Usage by Agent

Agent       Model Profile               Temperature
Librarian   High-accuracy, JSON-stable  0.0–0.2
Writer      High-fidelity, conservative 0.2–0.3
Verifier    Deterministic, strict       0.0
Rewriter    Conservative rewrite        0.2

Policy

- Prefer the most conservative model that meets Verification thresholds.
- Never mix models within a single paragraph run without explicit logging.

---

### 3.2 Prompt Versioning

- Every agent call MUST include:
    - prompt_version
- Prompt versions are immutable once deployed.
- Changing a prompt requires:
    - version bump
    - golden set regression (Doc #7)

---

### 3.3 Input Normalization & Hashing

Before any LLM call:

- Normalize inputs (ordering, whitespace, stable JSON)
- Compute input_hash
- Store in runs table

This enables:

- caching
- deduplication
- forensic debugging

---

## 4. Cost Management

### 4.1 Cost Units (Primary KPI)

Primary cost unit:

- Cost per paragraph (USD)

Tracked per:

- agent
- model
- prompt version

---

### 4.2 Token Budgets (Hard Limits)

Stage                       Budget (tokens)
Librarian (per PDF chunk)   3k–6k
Writer (per paragraph)      2k–4k
Verifier (per paragraph)    1k–2k
Total per paragraph         ≤ 7k–10k

Budgets are enforced at runtime.

Exceeding budget → abort generation + log error.

---

### 4.3 Expected Cost Envelope (Illustrative)

Assuming modern frontier pricing:

- Cost per paragraph: $0.05 – $0.15
- 10 paragraphs/session → $0.50 – $1.50 per user session
- 50 users/month → <$75/month LLM spend (early MVP)

Rule

- If cost per paragraph spikes by >30% week-over-week → investigate.

---

## 5. Reliability & Fault Tolerance

### 5.1 Failure Classes

Class       Examples
Transient	LLM timeout, 429 rate limit
Recoverable	Invalid JSON output
Fatal       Contract violation, verifier bypass

---

### 5.2 Retry Policy

Failure             Retry
Timeout	Retry       1–2 times
429 / rate limit	Exponential backoff
Invalid JSON        Retry once
Contract violation  No retry

Retries MUST:

- reuse same inputs
- log retry count
- stop after max attempts

---

### 5.3 Circuit Breakers

Introduce circuit breakers for:

- LLM provider outage
- Excessive verification failures
- Cost anomaly detection

Breaker actions:

- Pause new jobs
- Allow read-only UI
- Surface status banner to user

---

## 6. Async Job Operations (Celery)

### 6.1 Worker Configuration (Initial)

- Workers: 2–4
- Concurrency per worker: 1–2
- Queue separation:
    - facts
    - generation
    - verification (optional)

---

### 6.2 Job Lifecycle

State       Meaning
QUEUED      Awaiting worker
RUNNING     Active
SUCCEEDED   Completed
FAILED      Non-recoverable error
CANCELLED   User/system cancelled

All transitions are logged.

---

## 7. Observability & Monitoring

### 7.1 Mandatory Metrics

### System

- Job success/failure rate
- Queue latency
- Worker utilization

### LLM

- Tokens per paragraph
- Cost per paragraph
- Latency P50 / P95
- Error rate by provider/model

### Quality

- Sentence support rate
- Paragraph verification rate
- Failure mode distribution

---

### 7.2 Tracing

Every paragraph run MUST have:

- trace_id
- spans:
    - Librarian
    - Writer
    - Verifier
- correlation across API → queue → worker

LangSmith / Phoenix dashboards should show:

- prompt version vs failure rate
- model vs cost/quality tradeoff

---

## 8. Alerts & SLOs

### 8.1 Alerts (Initial)

Trigger alert if:

- Verification PASS rate drops below 95%
- Any false support detected
- Cost per paragraph exceeds threshold
- Job failure rate >5% over 1 hour

---

### 8.2 Service-Level Objectives (MVP)

Metric                  Target
Paragraph success rate  ≥ 95%
False supports          0
P95 paragraph latency	≤ 30s
Availability            Best-effort (non-24/7)

---

## 9. Deployment & Release Process

### 9.1 Environments

- Local: developer testing
- Staging: golden set eval
- Production: user-facing

No direct deploy from local → prod.

---

### 9.2 Release Checklist (MANDATORY)

Before production deploy:

1. All migrations applied
2. Golden set regression PASS
3. Cost estimates reviewed
4. Prompt versions pinned
5. Secrets verified
6. Rollback plan ready

---

### 9.3 Rollback Strategy

Rollback triggers:

- verifier false positives
- cost explosion
- systemic failures

Rollback actions:

- revert prompt version
- revert model version
- disable generation temporarily

Rollback MUST NOT:

- corrupt stored data
- hide previously verified output

---

## 10. Incident Response

### 10.1 Incident Types

- Hallucination incident (critical)
- Data leakage (critical)
- Cost runaway
- Provider outage

---

### 10.2 Incident Procedure

1. Freeze generation
2. Preserve logs and runs
3. Identify scope via trace_id
4. Roll back offending change
5. Patch + add regression test
6. Post-mortem (internal)

---

## 11. Go-Live Criteria

OpusBlocks.com v1.0 is operationally ready when:

- All 9 documents are complete
- Verification gates are enforced
- Cost per paragraph is bounded
- Observability dashboards exist
- Kill switch is tested

---

## 12. Definition of Done (Operational Plan)

This document is complete when:

1. Costs are predictable and capped
2. Failures degrade safely
3. Quality regressions are detectable
4. Deployment and rollback are routine
5. System can be explained to an SRE or reviewer