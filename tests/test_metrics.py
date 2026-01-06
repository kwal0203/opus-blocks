import os
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from opus_blocks.core.config import settings
from opus_blocks.services.alerts import evaluate_alerts
from opus_blocks.services.metrics import create_snapshot


@pytest.mark.anyio
async def test_metrics_overview_endpoint(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/metrics/overview?hours=1")
    assert response.status_code == 200
    payload = response.json()
    assert "sentence_support_rate" in payload
    assert "paragraph_verified_rate" in payload
    assert "counts" in payload


@pytest.mark.anyio
async def test_metrics_snapshots_and_alerts(async_client: AsyncClient) -> None:
    original_url = settings.database_url
    settings.database_url = os.environ["OPUS_BLOCKS_TEST_DATABASE_URL"]
    try:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            window_end = datetime.now(tz=UTC)
            window_start = window_end - timedelta(hours=1)
            snapshot = await create_snapshot(
                session, window_start=window_start, window_end=window_end
            )
            metrics = dict(snapshot.metrics_json)
            metrics["sentence_support_rate"] = 0.0
            alerts = await evaluate_alerts(session, metrics=metrics)
            assert alerts
        await engine.dispose()
    finally:
        settings.database_url = original_url
