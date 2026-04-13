import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_empty_cart_checkout_fails(
    test_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    r = await test_client.post(
        "/api/v1/checkout/preview",
        headers=auth_headers,
        json={"address_id": 1},
    )
    assert r.status_code in (400, 404, 500)
