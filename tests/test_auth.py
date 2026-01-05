import os
import uuid

import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alembic import command
from opus_blocks.app import app
from opus_blocks.db.session import get_session


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    database_url = os.environ.get("OPUS_BLOCKS_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("OPUS_BLOCKS_TEST_DATABASE_URL is not set")

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")

    yield config

    command.downgrade(config, "base")


@pytest.fixture()
async def client(alembic_config: Config) -> AsyncClient:
    database_url = alembic_config.get_main_option("sqlalchemy.url")
    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session() -> AsyncSession:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.anyio
async def test_register_and_login(client: AsyncClient) -> None:
    email = f"user-{uuid.uuid4()}@example.com"
    password = "Password123!"

    register_response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == email

    login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
