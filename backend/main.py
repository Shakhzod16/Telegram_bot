# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qsl

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from telegram import Bot

from config import settings
from database.models import MANAGEABLE_ORDER_STATUSES, Database
from utils.texts import frontend_texts, status_text, t

try:
    import structlog
except ImportError:  # pragma: no cover - fallback when optional dependency is absent
    structlog = None

if structlog:
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ]
    )
    log = structlog.get_logger()
else:  # pragma: no cover - fallback when optional dependency is absent
    class _FallbackLogger:
        def __init__(self) -> None:
            self._logger = logging.getLogger("backend")

        def info(self, event: str, **kwargs: object) -> None:
            self._logger.info("%s | %s", event, kwargs)

        def warning(self, event: str, **kwargs: object) -> None:
            self._logger.warning("%s | %s", event, kwargs)

        def error(self, event: str, **kwargs: object) -> None:
            self._logger.error("%s | %s", event, kwargs)

    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    log = _FallbackLogger()

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

db = Database(settings.database_path)


@dataclass(slots=True)
class TelegramAuthContext:
    init_data: str
    parsed: dict
    user: dict


class LocationPayload(BaseModel):
    label: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class CartItemPayload(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=99)


class BootstrapPayload(BaseModel):
    pass


class OrderPayload(BaseModel):
    user_id: int
    items: list[CartItemPayload]
    total: int
    location: LocationPayload | None = None


class PaymentPayload(BaseModel):
    order_id: int
    provider: str


class OrderStatusPayload(BaseModel):
    status: str


app = FastAPI(title="Telegram Food Delivery API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


def validate_telegram_init_data(init_data: str, bot_token: str) -> bool:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    hash_value = parsed.pop("hash", None)
    if not hash_value:
        return False

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed_hash, hash_value)


def parse_telegram_init_data(init_data: str) -> dict:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    if "user" in parsed:
        try:
            parsed["user"] = json.loads(parsed["user"])
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=401, detail="Invalid Telegram user payload.") from exc
    return parsed


async def telegram_auth(
    x_init_data: str = Header(..., alias="X-Init-Data"),
) -> TelegramAuthContext:
    if not validate_telegram_init_data(x_init_data, settings.bot_token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    parsed = parse_telegram_init_data(x_init_data)
    auth_date_raw = parsed.get("auth_date")
    if auth_date_raw and str(auth_date_raw).isdigit():
        auth_age = int(time.time()) - int(auth_date_raw)
        if auth_age > settings.webapp_init_data_ttl_seconds:
            raise HTTPException(status_code=401, detail="Telegram session expired.")

    user = parsed.get("user")
    if not isinstance(user, dict) or "id" not in user:
        raise HTTPException(status_code=401, detail="Telegram user is missing.")

    return TelegramAuthContext(init_data=x_init_data, parsed=parsed, user=user)


async def admin_telegram_auth(
    auth: TelegramAuthContext = Depends(telegram_auth),
) -> TelegramAuthContext:
    if not settings.admin_chat_id or int(auth.user["id"]) != settings.admin_chat_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return auth


async def notify_user_status_change(order_id: int, status: str) -> None:
    try:
        summary = db.get_order_summary(order_id)
        language = summary["user"]["language"]
        message = t(
            "status_changed",
            language,
            order_id=str(order_id),
            status=status_text(status, language),
        )
        async with Bot(settings.bot_token) as bot:
            await bot.send_message(chat_id=summary["user"]["id"], text=message)
    except Exception as exc:  # pragma: no cover - external network side effect
        log.error("notify_user_status_change_failed", order_id=order_id, status=status, error=str(exc))


def payment_url_for(provider: str, order: dict) -> str:
    template = (
        settings.click_payment_url_template
        if provider == "click"
        else settings.payme_payment_url_template
    )
    return template.format(
        provider=provider,
        order_id=order["order_id"],
        amount=order["total_amount"],
    )


async def handle_click_webhook(request: Request) -> JSONResponse:
    body = await request.body()
    data = dict(parse_qsl(body.decode(), keep_blank_values=True))
    sign_string = (
        f"{data.get('click_trans_id', '')}"
        f"{data.get('service_id', '')}"
        f"{settings.click_secret_key}"
        f"{data.get('merchant_trans_id', '')}"
        f"{data.get('amount', '')}"
        f"{data.get('action', '')}"
        f"{data.get('sign_time', '')}"
    )
    expected_sign = hashlib.md5(sign_string.encode()).hexdigest()

    if data.get("sign_string") != expected_sign:
        log.warning("click_invalid_signature", payload=data)
        return JSONResponse({"error": -1, "error_note": "Invalid sign"})

    payment_id = int(data["merchant_prepare_id"]) if data.get("merchant_prepare_id") else None
    order_id = int(data["merchant_trans_id"]) if data.get("merchant_trans_id") else None
    action = str(data.get("action", ""))

    if action == "2" and order_id:
        db.update_order_status(order_id, "PAID")
        if payment_id is not None:
            db.update_payment_status(
                provider="click",
                payment_id=payment_id,
                external_id=str(data.get("click_trans_id") or ""),
                status="PAID",
                raw_payload=data,
            )
        await notify_user_status_change(order_id, "PAID")
        log.info("click_payment_confirmed", order_id=order_id, payment_id=payment_id)

    return JSONResponse({"error": 0, "error_note": "Success"})


async def handle_payme_webhook(request: Request) -> JSONResponse:
    auth_header = request.headers.get("Authorization", "")
    expected = base64.b64encode(f"Paycom:{settings.payme_key}".encode()).decode()
    if auth_header != f"Basic {expected}":
        log.warning("payme_invalid_auth")
        return JSONResponse({"error": {"code": -32504, "message": "Forbidden"}}, status_code=401)

    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    account = params.get("account", {})

    if method == "PerformTransaction":
        order_id = int(account["order_id"])
        db.update_order_status(order_id, "PAID")
        await notify_user_status_change(order_id, "PAID")
        log.info("payme_payment_confirmed", order_id=order_id)
        return JSONResponse({"result": {"perform_time": int(time.time() * 1000)}})

    return JSONResponse({"result": {"allow": True}})


@app.on_event("startup")
async def startup() -> None:
    db.init()


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(
        FRONTEND_DIR / "index.html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/styles.css")
async def styles() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "styles.css")


@app.get("/app.js")
async def app_js() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "app.js")


@app.post("/api/bootstrap")
async def bootstrap(
    _: BootstrapPayload,
    auth: TelegramAuthContext = Depends(telegram_auth),
) -> dict:
    user = db.get_user(int(auth.user["id"]))
    if not user:
        raise HTTPException(status_code=404, detail="User is not onboarded.")

    return {
        "user": user,
        "products": db.list_products(user["language"]),
        "texts": frontend_texts(user["language"]),
        "payment_providers": ["click", "payme"],
        "payme_docs_url": settings.payme_merchant_api_url,
    }


@app.post("/api/orders")
async def create_order(
    payload: OrderPayload,
    auth: TelegramAuthContext = Depends(telegram_auth),
) -> dict:
    auth_user_id = int(auth.user["id"])
    if payload.user_id != auth_user_id:
        raise HTTPException(status_code=403, detail="User mismatch.")

    user = db.get_user(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    try:
        order = db.create_order(
            user_id=payload.user_id,
            language=user["language"],
            items=[item.model_dump() for item in payload.items],
            location_label=payload.location.label if payload.location else None,
            latitude=payload.location.latitude if payload.location else None,
            longitude=payload.location.longitude if payload.location else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log.info(
        "order_created",
        order_id=order["id"],
        user_id=payload.user_id,
        total=order["total_amount"],
        items=len(order["items"]),
    )

    return {
        "order_id": order["id"],
        "status": order["status"],
        "total_amount": order["total_amount"],
        "items": order["items"],
    }


@app.patch("/api/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    payload: OrderStatusPayload,
    _: TelegramAuthContext = Depends(admin_telegram_auth),
) -> dict:
    normalized_status = payload.status.upper()
    if normalized_status not in MANAGEABLE_ORDER_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    try:
        order = db.update_order_status(order_id, normalized_status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await notify_user_status_change(order_id, normalized_status)
    log.info("order_status_updated", order_id=order_id, status=normalized_status)
    return {"ok": True, "order_id": order["id"], "status": order["status"]}


@app.post("/api/payments/create")
async def create_payment(
    payload: PaymentPayload,
    auth: TelegramAuthContext = Depends(telegram_auth),
) -> dict:
    try:
        summary = db.get_order_summary(payload.order_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if int(summary["user"]["id"]) != int(auth.user["id"]):
        raise HTTPException(status_code=403, detail="Order does not belong to this user.")

    provider = payload.provider.lower()
    if provider not in {"click", "payme"}:
        raise HTTPException(status_code=400, detail="Unsupported payment provider.")

    payment = db.create_payment(
        order_id=payload.order_id,
        provider=provider,
        amount=summary["total_amount"],
        payment_url=payment_url_for(provider, summary),
    )
    log.info("payment_created", payment_id=payment["id"], order_id=payload.order_id, provider=provider)
    return {
        "payment_id": payment["id"],
        "provider": payment["provider"],
        "payment_url": payment["payment_url"],
        "status": payment["status"],
    }


@app.post("/api/payments/click/webhook")
async def click_webhook(request: Request) -> JSONResponse:
    return await handle_click_webhook(request)


@app.post("/api/payments/payme/webhook")
async def payme_webhook(request: Request) -> JSONResponse:
    return await handle_payme_webhook(request)


@app.post("/api/payments/{provider}/webhook")
async def payment_webhook(provider: str, request: Request) -> JSONResponse:
    provider = provider.lower()
    if provider == "click":
        return await handle_click_webhook(request)
    if provider == "payme":
        return await handle_payme_webhook(request)
    raise HTTPException(status_code=400, detail="Unsupported provider.")
