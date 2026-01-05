import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_register_and_login(async_client: AsyncClient) -> None:
    email = f"user-{uuid.uuid4()}@example.com"
    password = "Password123!"

    register_response = await async_client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == email

    login_response = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
