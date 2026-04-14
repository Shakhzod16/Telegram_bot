import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_superadmin_stats_without_auth():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v1/superadmin/stats")
    assert resp.status_code == 401 or resp.status_code == 403


@pytest.mark.asyncio
async def test_superadmin_whitelist_without_auth():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v1/superadmin/whitelist")
    assert resp.status_code == 401 or resp.status_code == 403


@pytest.mark.asyncio
async def test_superadmin_admins_without_auth():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v1/superadmin/admins")
    assert resp.status_code == 401 or resp.status_code == 403


@pytest.mark.asyncio
async def test_whitelist_invalid_telegram_id():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/superadmin/whitelist",
            json={"telegram_id": "abc"}
        )
    assert resp.status_code in [401, 403, 422]
