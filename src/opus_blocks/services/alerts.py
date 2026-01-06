from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.core.config import settings
from opus_blocks.models.alert_event import AlertEvent


async def create_alert(
    session: AsyncSession,
    *,
    name: str,
    status: str,
    value: float | None,
    threshold: float | None,
    context: dict,
) -> AlertEvent:
    alert = AlertEvent(
        name=name,
        status=status,
        value=value,
        threshold=threshold,
        context_json=context,
    )
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


async def evaluate_alerts(session: AsyncSession, *, metrics: dict) -> list[AlertEvent]:
    alerts: list[AlertEvent] = []
    sentence_support_rate = metrics.get("sentence_support_rate")
    paragraph_verified_rate = metrics.get("paragraph_verified_rate")
    job_failure_rate = metrics.get("job_failure_rate")

    if (
        sentence_support_rate is not None
        and sentence_support_rate < settings.alert_sentence_support_rate_min
    ):
        alerts.append(
            await create_alert(
                session,
                name="sentence_support_rate",
                status="BREACH",
                value=sentence_support_rate,
                threshold=settings.alert_sentence_support_rate_min,
                context=metrics,
            )
        )
    if (
        paragraph_verified_rate is not None
        and paragraph_verified_rate < settings.alert_paragraph_verified_rate_min
    ):
        alerts.append(
            await create_alert(
                session,
                name="paragraph_verified_rate",
                status="BREACH",
                value=paragraph_verified_rate,
                threshold=settings.alert_paragraph_verified_rate_min,
                context=metrics,
            )
        )
    if job_failure_rate is not None and job_failure_rate > settings.alert_job_failure_rate_max:
        alerts.append(
            await create_alert(
                session,
                name="job_failure_rate",
                status="BREACH",
                value=job_failure_rate,
                threshold=settings.alert_job_failure_rate_max,
                context=metrics,
            )
        )
    return alerts


async def list_alerts(session: AsyncSession, *, limit: int = 50) -> list[AlertEvent]:
    result = await session.execute(
        select(AlertEvent).order_by(AlertEvent.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())
