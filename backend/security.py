# -*- coding: utf-8 -*-
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from fastapi import Depends, Header, HTTPException

from config.settings import settings


@dataclass(slots=True)
class TelegramAuthContext:
    init_data: str
    parsed: dict
    user: dict


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
    user_raw = parsed.get("user")
    if user_raw:
        try:
            parsed["user"] = json.loads(user_raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=401, detail="Invalid Telegram user payload.") from exc
    return parsed


async def telegram_auth(x_init_data: str = Header(..., alias="X-Init-Data")) -> TelegramAuthContext:
    if not validate_telegram_init_data(x_init_data, settings.bot_token):
        raise HTTPException(status_code=401, detail="Invalid Telegram signature")

    parsed = parse_telegram_init_data(x_init_data)
    auth_date_raw = parsed.get("auth_date")
    if auth_date_raw and str(auth_date_raw).isdigit():
        auth_age = int(time.time()) - int(auth_date_raw)
        if auth_age > settings.webapp_init_data_ttl_seconds:
            raise HTTPException(status_code=401, detail="Telegram session expired")

    user = parsed.get("user")
    if not isinstance(user, dict) or "id" not in user:
        raise HTTPException(status_code=401, detail="Telegram user is missing")
    return TelegramAuthContext(init_data=x_init_data, parsed=parsed, user=user)


async def admin_key_auth(x_admin_key: str = Header("", alias="X-Admin-Key")) -> None:
    if not settings.admin_api_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Forbidden")


def validate_click_signature(data: dict) -> bool:
    sign_string = (
        f"{data.get('click_trans_id', '')}"
        f"{data.get('service_id', '')}"
        f"{settings.click_secret_key}"
        f"{data.get('merchant_trans_id', '')}"
        f"{data.get('amount', '')}"
        f"{data.get('action', '')}"
        f"{data.get('sign_time', '')}"
    )
    expected = hashlib.md5(sign_string.encode()).hexdigest()
    return hmac.compare_digest(str(data.get("sign_string", "")), expected)


def validate_payme_authorization(value: str) -> bool:
    expected = base64_token(f"Paycom:{settings.payme_key}")
    return hmac.compare_digest(value, f"Basic {expected}")


def base64_token(value: str) -> str:
    import base64

    return base64.b64encode(value.encode()).decode()


def validate_internal_callback_signature(signature: str, body: str, secret: str) -> bool:
    if not secret:
        return False
    expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)
