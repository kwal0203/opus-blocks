from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MetricsCounts(BaseModel):
    sentences: int | None
    paragraphs: int | None
    jobs: int | None


class MetricsOverview(BaseModel):
    window_start: datetime
    window_end: datetime
    sentence_support_rate: float | None
    paragraph_verified_rate: float | None
    job_failure_rate: float | None
    missing_evidence_rate: float | None
    cost_per_paragraph: float | None
    latency_p50_ms: float | None
    latency_p95_ms: float | None
    counts: MetricsCounts


class MetricsSnapshotRead(BaseModel):
    id: str
    window_start: datetime
    window_end: datetime
    metrics_json: dict
    scope: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
