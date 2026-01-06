from fastapi import APIRouter, Query

from opus_blocks.api.deps import DbSession
from opus_blocks.schemas.alerts import AlertEventRead
from opus_blocks.schemas.metrics import MetricsOverview, MetricsSnapshotRead
from opus_blocks.services.alerts import list_alerts
from opus_blocks.services.metrics import compute_metrics, default_window, list_snapshots

router = APIRouter(prefix="/metrics")


@router.get("/overview", response_model=MetricsOverview)
async def metrics_overview(
    session: DbSession, hours: int = Query(default=24, ge=1, le=168)
) -> MetricsOverview:
    window_start, window_end = default_window(hours=hours)
    metrics = await compute_metrics(session, window_start=window_start, window_end=window_end)
    return MetricsOverview.model_validate(metrics)


@router.get("/snapshots", response_model=list[MetricsSnapshotRead])
async def metrics_snapshots(
    session: DbSession, limit: int = Query(default=30, ge=1, le=200)
) -> list[MetricsSnapshotRead]:
    snapshots = await list_snapshots(session, limit=limit)
    return [MetricsSnapshotRead.model_validate(item) for item in snapshots]


@router.get("/alerts", response_model=list[AlertEventRead])
async def metrics_alerts(
    session: DbSession, limit: int = Query(default=50, ge=1, le=200)
) -> list[AlertEventRead]:
    alerts = await list_alerts(session, limit=limit)
    return [AlertEventRead.model_validate(item) for item in alerts]
