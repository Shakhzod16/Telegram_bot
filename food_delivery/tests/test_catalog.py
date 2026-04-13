import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_categories(test_client: AsyncClient, auth_headers: dict[str, str]) -> None:
    r = await test_client.get("/api/v1/categories", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
