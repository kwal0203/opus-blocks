import argparse
import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from opus_blocks.core.config import settings
from opus_blocks.services.alerts import evaluate_alerts
from opus_blocks.services.metrics import create_snapshot, default_window


async def _run(hours: int) -> None:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    window_start, window_end = default_window(hours=hours)
    async with session_factory() as session:
        snapshot = await create_snapshot(
            session,
            window_start=window_start,
            window_end=window_end,
        )
        await evaluate_alerts(session, metrics=snapshot.metrics_json)
        print(
            f"Snapshot {snapshot.id} stored for "
            f"{window_start.isoformat()} - {window_end.isoformat()}"
        )
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute metrics snapshot + alerts.")
    parser.add_argument("--hours", type=int, default=24, help="Window size in hours.")
    args = parser.parse_args()
    asyncio.run(_run(args.hours))


if __name__ == "__main__":
    main()
