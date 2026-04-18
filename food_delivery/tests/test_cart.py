import json
import urllib.parse

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cart_empty(test_client: AsyncClient, auth_headers: dict[str, str]) -> None:
    r = await test_client.get("/api/v1/cart", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_cart_with_telegram_init_data_header(
    test_client: AsyncClient,
    test_user,
) -> None:
    init_data = "user=" + urllib.parse.quote(
        json.dumps({"id": test_user.telegram_id, "first_name": "Test"}),
        safe="",
    )
    r = await test_client.get(
        "/api/v1/cart",
        headers={"X-Telegram-Init-Data": init_data},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_cart_with_referer_tg_data_fallback(
    test_client: AsyncClient,
    test_user,
) -> None:
    init_data = "user=" + urllib.parse.quote(
        json.dumps({"id": test_user.telegram_id, "first_name": "Test"}),
        safe="",
    )
    referer = "https://example.test/webapp/?tgWebAppData=" + urllib.parse.quote(
        init_data,
        safe="",
    )
    r = await test_client.get(
        "/api/v1/cart",
        headers={"Referer": referer},
    )
    assert r.status_code == 200
