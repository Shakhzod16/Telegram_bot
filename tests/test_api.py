import hashlib
import hmac
import json
import os
from pathlib import Path
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient


TEST_DB_PATH = Path(__file__).resolve().parent / "test_food_delivery.db"
os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("WEB_APP_URL", "https://example.com")
os.environ.setdefault("DATABASE_PATH", str(TEST_DB_PATH))
os.environ.setdefault("CLICK_SECRET_KEY", "click_secret")
os.environ.setdefault("PAYME_KEY", "payme_key")

from backend.main import app, db  # noqa: E402


client = TestClient(app)


def build_init_data(user: dict, bot_token: str) -> str:
    payload = {
        "auth_date": "1893456000",
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "user": json.dumps(user, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    payload["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(payload)


@pytest.fixture(autouse=True)
def reset_db():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    db.path = TEST_DB_PATH
    db.init()
    db.upsert_user(
        123,
        name="Test User",
        phone="+998901234567",
        city="Tashkent",
        language="uz",
    )
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


def auth_headers(user_id: int = 123) -> dict[str, str]:
    return {
        "X-Init-Data": build_init_data(
            {"id": user_id, "first_name": "Test", "username": "tester"},
            os.environ["BOT_TOKEN"],
        )
    }


def test_bootstrap_returns_products():
    response = client.post("/api/bootstrap", json={}, headers=auth_headers())
    assert response.status_code == 200
    assert "products" in response.json()


def test_create_order():
    response = client.post(
        "/api/orders",
        json={
            "user_id": 123,
            "items": [{"product_id": 1, "quantity": 2}],
            "total": 64000,
            "location": {"label": "Toshkent, Chilonzor"},
        },
        headers=auth_headers(),
    )
    assert response.status_code == 200
    assert "order_id" in response.json()


def test_invalid_payment_webhook():
    response = client.post(
        "/api/payments/click/webhook",
        data={
            "sign_string": "wrong_hash",
            "action": "2",
        },
    )
    assert response.json()["error"] == -1
