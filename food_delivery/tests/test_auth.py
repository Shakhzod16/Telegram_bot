import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(test_client: AsyncClient) -> None:
    r = await test_client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


@pytest.mark.asyncio
async def test_init_invalid(test_client: AsyncClient) -> None:
    r = await test_client.post("/api/v1/auth/telegram/init", json={"init_data": "invalid"})
    assert r.status_code in (400, 401, 422, 500)


@pytest.mark.asyncio
async def test_jwt_protected_without_token(test_client: AsyncClient) -> None:
    r = await test_client.get("/api/v1/profile")
    assert r.status_code in (401, 403, 500)


@pytest.mark.asyncio
async def test_profile_with_token(test_client: AsyncClient, auth_headers: dict[str, str]) -> None:
    r = await test_client.get("/api/v1/profile", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "telegram_id" in data or ("id" in data and "first_name" in data)
