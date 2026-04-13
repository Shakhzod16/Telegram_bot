import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cart_empty(test_client: AsyncClient, auth_headers: dict[str, str]) -> None:
    r = await test_client.get("/api/v1/cart", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
