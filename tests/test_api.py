import base64
import hashlib
import hmac
import json
import os
import sqlite3
from pathlib import Path
from urllib.parse import urlencode

from fastapi.testclient import TestClient


TEST_DB_PATH = Path(__file__).resolve().parent / "test_food_delivery.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["BOT_TOKEN"] = "123456:TEST_TOKEN"
os.environ["WEB_APP_URL"] = "https://example.com"
os.environ["FRONTEND_ORIGIN"] = "https://example.netlify.app"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["ADMIN_API_KEY"] = "admin-secret"
os.environ["CLICK_SECRET_KEY"] = "test-click-secret"
os.environ["PAYME_KEY"] = "payme-test-key"

from backend.main import app  # noqa: E402


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


def auth_headers(user_id: int = 123, language_code: str = "uz") -> dict[str, str]:
    return {
        "X-Init-Data": build_init_data(
            {"id": user_id, "first_name": "Test", "username": "tester", "language_code": language_code},
            os.environ["BOT_TOKEN"],
        )
    }


def admin_headers() -> dict[str, str]:
    return {"X-Admin-Key": "admin-secret"}


def payme_auth_header() -> dict[str, str]:
    token = base64.b64encode(f"Paycom:{os.environ['PAYME_KEY']}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def build_click_payload(order_id: int, amount: int, action: str = "2", sign: bool = True) -> str:
    data = {
        "click_trans_id": "9001",
        "service_id": "777",
        "merchant_trans_id": str(order_id),
        "amount": str(amount),
        "action": action,
        "sign_time": "2026-03-28 12:00:00",
    }
    sign_source = (
        f"{data['click_trans_id']}"
        f"{data['service_id']}"
        f"{os.environ['CLICK_SECRET_KEY']}"
        f"{data['merchant_trans_id']}"
        f"{data['amount']}"
        f"{data['action']}"
        f"{data['sign_time']}"
    )
    data["sign_string"] = hashlib.md5(sign_source.encode()).hexdigest() if sign else "broken-sign"
    return urlencode(data)


def _create_order(client: TestClient, user_id: int = 123, payment_method: str = "click") -> int:
    client.post("/api/bootstrap", json={}, headers=auth_headers(user_id))
    response = client.post(
        "/api/order",
        json={
            "user_id": user_id,
            "items": [{"product_id": 1, "quantity": 1}],
            "location": {"label": "Tashkent"},
            "payment_method": payment_method,
        },
        headers=auth_headers(user_id),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["payment_method"] == payment_method
    return body["order_id"]


def _history_count(order_id: int) -> int:
    with sqlite3.connect(TEST_DB_PATH) as conn:
        row = conn.execute("SELECT COUNT(*) FROM order_status_history WHERE order_id = ?", (order_id,)).fetchone()
    return int(row[0] if row else 0)


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_bootstrap_requires_auth():
    with TestClient(app) as client:
        response = client.post("/api/bootstrap", json={})
        assert response.status_code in {401, 422}


def test_bootstrap_returns_products():
    with TestClient(app) as client:
        response = client.post("/api/bootstrap", json={}, headers=auth_headers())
        assert response.status_code == 200
        body = response.json()
        assert "products" in body
        assert isinstance(body["products"], list)
        assert "user" in body


def test_bootstrap_frontend_texts_are_loaded_for_three_languages():
    with TestClient(app) as client:
        for idx, language in enumerate(("uz", "ru", "en"), start=1):
            response = client.post("/api/bootstrap", json={}, headers=auth_headers(user_id=1000 + idx, language_code=language))
            assert response.status_code == 200
            body = response.json()
            assert body["user"]["language"] == language
            assert body["texts"]["frontend_title"]
            assert body["texts"]["frontend_order"]


def test_click_prepare_complete_and_idempotency():
    with TestClient(app) as client:
        order_id = _create_order(client, payment_method="click")
        body = build_click_payload(order_id=order_id, amount=32000)

        prepare = client.post(
            "/api/payment/click/prepare",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert prepare.status_code == 200
        assert prepare.json()["error"] == 0

        first = client.post(
            "/api/payment/click/complete",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert first.status_code == 200
        assert first.json()["status"] == "confirmed"

        second = client.post(
            "/api/payment/click/complete",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert second.status_code == 200
        assert second.json()["status"] == "confirmed"


def test_click_invalid_signature_rejected():
    with TestClient(app) as client:
        order_id = _create_order(client, payment_method="click")
        bad_body = build_click_payload(order_id=order_id, amount=32000, sign=False)
        response = client.post(
            "/api/payment/click/complete",
            data=bad_body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 400


def test_order_status_flow_transition_and_history():
    with TestClient(app) as client:
        order_id = _create_order(client, payment_method="click")

        paid = client.post(
            "/api/payment/click/complete",
            data=build_click_payload(order_id=order_id, amount=32000),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert paid.status_code == 200
        assert paid.json()["status"] == "confirmed"

        preparing = client.patch(
            f"/admin/orders/{order_id}/status",
            params={"status": "preparing"},
            headers=admin_headers(),
        )
        assert preparing.status_code == 200
        assert preparing.json()["status"] == "preparing"

        delivering = client.patch(
            f"/admin/orders/{order_id}/status",
            params={"status": "delivering"},
            headers=admin_headers(),
        )
        assert delivering.status_code == 200
        assert delivering.json()["status"] == "delivering"

        delivered = client.patch(f"/api/orders/{order_id}/deliver", headers=auth_headers())
        assert delivered.status_code == 200
        assert delivered.json()["status"] == "delivered"

        invalid_back = client.patch(
            f"/admin/orders/{order_id}/status",
            params={"status": "pending"},
            headers=admin_headers(),
        )
        assert invalid_back.status_code == 400

        assert _history_count(order_id) >= 4


def test_payme_rpc_flow_and_auth():
    with TestClient(app) as client:
        order_id = _create_order(client, payment_method="payme")
        amount_tiyin = 32000 * 100

        wrong_auth = client.post(
            "/api/payment/payme",
            json={"id": 1, "method": "CheckPerformTransaction", "params": {"amount": amount_tiyin, "account": {"order_id": order_id}}},
            headers={"Authorization": "Basic broken"},
        )
        assert wrong_auth.status_code == 200
        assert wrong_auth.json()["error"]["code"] == -32504

        check = client.post(
            "/api/payment/payme",
            json={"id": 1, "method": "CheckPerformTransaction", "params": {"amount": amount_tiyin, "account": {"order_id": order_id}}},
            headers=payme_auth_header(),
        )
        assert check.status_code == 200
        assert check.json()["result"]["allow"] is True

        create = client.post(
            "/api/payment/payme",
            json={
                "id": 2,
                "method": "CreateTransaction",
                "params": {"id": "payme-tx-1", "amount": amount_tiyin, "account": {"order_id": order_id}},
            },
            headers=payme_auth_header(),
        )
        assert create.status_code == 200
        assert create.json()["result"]["state"] == 1

        perform = client.post(
            "/api/payment/payme",
            json={"id": 3, "method": "PerformTransaction", "params": {"id": "payme-tx-1"}},
            headers=payme_auth_header(),
        )
        assert perform.status_code == 200
        assert perform.json()["result"]["state"] == 2
        assert perform.json()["result"]["status"] == "confirmed"


def test_payme_cancel_marks_order_cancelled():
    with TestClient(app) as client:
        order_id = _create_order(client, payment_method="payme")
        amount_tiyin = 32000 * 100

        create = client.post(
            "/api/payment/payme",
            json={
                "id": 11,
                "method": "CreateTransaction",
                "params": {"id": "payme-tx-cancel", "amount": amount_tiyin, "account": {"order_id": order_id}},
            },
            headers=payme_auth_header(),
        )
        assert create.status_code == 200

        cancel = client.post(
            "/api/payment/payme",
            json={"id": 12, "method": "CancelTransaction", "params": {"id": "payme-tx-cancel", "reason": 5}},
            headers=payme_auth_header(),
        )
        assert cancel.status_code == 200
        assert cancel.json()["result"]["state"] == -1

        # Cancel transition pushes order to cancelled from pending/confirmed.
        order_list = client.get("/admin/orders", headers=admin_headers()).json()
        row = next((item for item in order_list if item["id"] == order_id), None)
        assert row is not None
        assert row["status"] == "cancelled"


def test_cash_payment_flow_and_admin_cash_received():
    with TestClient(app) as client:
        order_id = _create_order(client, payment_method="cash")

        payment = client.post(
            "/api/payments/create",
            json={"order_id": order_id, "provider": "cash"},
            headers=auth_headers(),
        )
        assert payment.status_code == 200
        assert payment.json()["provider"] == "cash"
        assert payment.json()["status"] == "awaiting_cash"
        assert payment.json()["payment_url"] == ""

        admin_mark = client.patch(f"/admin/orders/{order_id}/cash-received", headers=admin_headers())
        assert admin_mark.status_code == 200
        assert admin_mark.json()["status"] == "confirmed"

        rows = client.get("/admin/orders", headers=admin_headers()).json()
        order = next((row for row in rows if row["id"] == order_id), None)
        assert order is not None
        assert order["payment_method"] == "cash"
        assert order["payment_status"] == "cash_received"


def test_admin_orders_protected():
    with TestClient(app) as client:
        denied = client.get("/admin/orders")
        assert denied.status_code == 403
        ok = client.get("/admin/orders", headers=admin_headers())
        assert ok.status_code == 200


def test_saved_addresses_crud_default_and_limit():
    with TestClient(app) as client:
        headers = auth_headers(777)
        boot = client.post("/api/bootstrap", json={}, headers=headers)
        assert boot.status_code == 200
        assert boot.json()["saved_addresses"] == []

        first = client.post(
            "/api/addresses",
            json={"label": "Home", "address_text": "Tashkent, Chilonzor"},
            headers=headers,
        )
        assert first.status_code == 200
        first_id = first.json()["id"]
        assert first.json()["is_default"] is True

        second = client.post(
            "/api/addresses",
            json={"label": "Work", "address_text": "Tashkent City"},
            headers=headers,
        )
        assert second.status_code == 200
        second_id = second.json()["id"]
        assert second.json()["is_default"] is False

        listed = client.get("/api/addresses", headers=headers)
        assert listed.status_code == 200
        rows = listed.json()
        assert len(rows) == 2
        assert sum(1 for row in rows if row["is_default"]) == 1
        assert any(row["id"] == first_id and row["is_default"] for row in rows)

        make_default = client.patch(f"/api/addresses/{second_id}/default", headers=headers)
        assert make_default.status_code == 200
        assert make_default.json()["id"] == second_id
        assert make_default.json()["is_default"] is True

        listed_after_default = client.get("/api/addresses", headers=headers).json()
        assert sum(1 for row in listed_after_default if row["is_default"]) == 1
        assert any(row["id"] == second_id and row["is_default"] for row in listed_after_default)

        deleted = client.delete(f"/api/addresses/{second_id}", headers=headers)
        assert deleted.status_code == 200
        assert deleted.json()["ok"] is True

        listed_after_delete = client.get("/api/addresses", headers=headers).json()
        assert len(listed_after_delete) == 1
        assert listed_after_delete[0]["id"] == first_id
        assert listed_after_delete[0]["is_default"] is True

        for idx in range(4):
            created = client.post(
                "/api/addresses",
                json={"label": f"Addr {idx}", "address_text": f"Location {idx}"},
                headers=headers,
            )
            assert created.status_code == 200
        too_many = client.post(
            "/api/addresses",
            json={"label": "Overflow", "address_text": "Too much"},
            headers=headers,
        )
        assert too_many.status_code == 400


def test_reorder_endpoint_returns_cart_items_and_skips_inactive_products():
    with TestClient(app) as client:
        user_id = 888
        headers = auth_headers(user_id)
        client.post("/api/bootstrap", json={}, headers=headers)

        create = client.post(
            "/api/order",
            json={
                "user_id": user_id,
                "items": [
                    {"product_id": 1, "quantity": 2},
                    {"product_id": 2, "quantity": 1},
                ],
                "location": {"label": "Tashkent"},
                "payment_method": "cash",
            },
            headers=headers,
        )
        assert create.status_code == 200
        order_id = create.json()["order_id"]

        with sqlite3.connect(TEST_DB_PATH) as conn:
            conn.execute("UPDATE products SET is_active = 0 WHERE id = 1")
            conn.commit()

        reorder = client.post(f"/api/orders/{order_id}/reorder", headers=headers)
        assert reorder.status_code == 200
        payload = reorder.json()
        assert payload["order_id"] == order_id
        assert payload["skipped_count"] == 1
        assert any(item["product_id"] == 2 and item["quantity"] == 1 for item in payload["items"])
