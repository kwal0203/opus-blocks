from __future__ import annotations

from datetime import UTC, datetime, timedelta
from statistics import quantiles

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.models.job import Job
from opus_blocks.models.metrics_snapshot import MetricsSnapshot
from opus_blocks.models.paragraph import Paragraph
from opus_blocks.models.run import Run
from opus_blocks.models.sentence import Sentence


def _percentile(values: list[int], percentile: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    qs = quantiles(values, n=100, method="inclusive")
    return float(qs[int(percentile) - 1])


async def compute_metrics(
    session: AsyncSession, *, window_start: datetime, window_end: datetime
) -> dict:
    sentence_total_raw = await session.scalar(
        select(func.count()).where(Sentence.created_at.between(window_start, window_end))
    )
    sentence_supported_raw = await session.scalar(
        select(func.count()).where(
            Sentence.created_at.between(window_start, window_end),
            Sentence.supported.is_(True),
        )
    )
    paragraph_total_raw = await session.scalar(
        select(func.count()).where(Paragraph.created_at.between(window_start, window_end))
    )
    paragraph_verified_raw = await session.scalar(
        select(func.count()).where(
            Paragraph.created_at.between(window_start, window_end),
            Paragraph.status == "VERIFIED",
        )
    )
    job_total_raw = await session.scalar(
        select(func.count()).where(Job.created_at.between(window_start, window_end))
    )
    job_failed_raw = await session.scalar(
        select(func.count()).where(
            Job.created_at.between(window_start, window_end),
            Job.status == "FAILED",
        )
    )
    sentence_total = int(sentence_total_raw or 0)
    sentence_supported = int(sentence_supported_raw or 0)
    paragraph_total = int(paragraph_total_raw or 0)
    paragraph_verified = int(paragraph_verified_raw or 0)
    job_total = int(job_total_raw or 0)
    job_failed = int(job_failed_raw or 0)

    runs_result = await session.execute(
        select(Run)
        .where(Run.created_at.between(window_start, window_end))
        .order_by(Run.created_at.asc())
    )
    runs = list(runs_result.scalars().all())

    latency_values = [run.latency_ms for run in runs if run.latency_ms is not None]
    cost_values = [run.cost_usd for run in runs if run.cost_usd is not None]
    paragraph_ids = {
        run.paragraph_id
        for run in runs
        if run.paragraph_id is not None and run.run_type in {"WRITER", "VERIFIER"}
    }

    missing_evidence_count = 0
    writer_runs = [run for run in runs if run.run_type == "WRITER"]
    for run in writer_runs:
        paragraph_payload = (
            run.outputs_json.get("paragraph") if isinstance(run.outputs_json, dict) else None
        )
        missing_evidence: list[dict] = []
        if isinstance(paragraph_payload, dict):
            missing_evidence = paragraph_payload.get("missing_evidence") or []
        if missing_evidence:
            missing_evidence_count += 1

    sentence_support_rate = (
        float(sentence_supported) / float(sentence_total) if sentence_total else None
    )
    paragraph_verified_rate = (
        float(paragraph_verified) / float(paragraph_total) if paragraph_total else None
    )
    job_failure_rate = float(job_failed) / float(job_total) if job_total else None
    missing_evidence_rate = (
        float(missing_evidence_count) / float(len(writer_runs)) if writer_runs else None
    )
    cost_per_paragraph = (
        float(sum(cost_values)) / float(len(paragraph_ids))
        if paragraph_ids and cost_values
        else None
    )

    return {
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "sentence_support_rate": sentence_support_rate,
        "paragraph_verified_rate": paragraph_verified_rate,
        "job_failure_rate": job_failure_rate,
        "missing_evidence_rate": missing_evidence_rate,
        "cost_per_paragraph": cost_per_paragraph,
        "latency_p50_ms": _percentile(latency_values, 50),
        "latency_p95_ms": _percentile(latency_values, 95),
        "counts": {
            "sentences": sentence_total,
            "paragraphs": paragraph_total,
            "jobs": job_total,
        },
    }


async def create_snapshot(
    session: AsyncSession,
    *,
    window_start: datetime,
    window_end: datetime,
    scope: str = "global",
) -> MetricsSnapshot:
    metrics = await compute_metrics(session, window_start=window_start, window_end=window_end)
    snapshot = MetricsSnapshot(
        window_start=window_start,
        window_end=window_end,
        metrics_json=metrics,
        scope=scope,
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot


async def list_snapshots(session: AsyncSession, *, limit: int = 30) -> list[MetricsSnapshot]:
    result = await session.execute(
        select(MetricsSnapshot).order_by(MetricsSnapshot.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


def default_window(hours: int = 24) -> tuple[datetime, datetime]:
    end = datetime.now(tz=UTC)
    start = end - timedelta(hours=hours)
    return start, end
