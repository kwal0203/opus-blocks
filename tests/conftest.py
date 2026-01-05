import os

import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alembic import command
from opus_blocks.app import app
from opus_blocks.db.session import get_session


@pytest.fixture()
async def async_client() -> AsyncClient:
    database_url = os.environ.get("OPUS_BLOCKS_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("OPUS_BLOCKS_TEST_DATABASE_URL is not set")

    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_session() -> AsyncSession:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    database_url = os.environ.get("OPUS_BLOCKS_TEST_DATABASE_URL")
    if not database_url:
        pytest.fail("OPUS_BLOCKS_TEST_DATABASE_URL is not set")

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    config.set_section_option(config.config_ini_section, "sqlalchemy.url", database_url)

    # Run migrations up
    command.upgrade(config, "head")

    yield

    # Optional: Run migrations down
    # command.downgrade(config, "base")
