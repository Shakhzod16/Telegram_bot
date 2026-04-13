from __future__ import annotations

import hashlib
import hmac
import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError


def verify_telegram_init_data(init_data: str) -> dict[str, Any]:
    """
    Validate Telegram WebApp initData and return parsed Telegram user payload.

    Telegram algorithm (official docs):
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

    secret_key = HMAC_SHA256(key=<bot_token>, msg="WebAppData")
    data_hash  = HMAC_SHA256(key=secret_key,  msg=data_check_string)
    """
    if not init_data:
        raise UnauthorizedError("Missing initData")

    # URL-decode the initData string
    pairs = urllib.parse.parse_qsl(init_data, keep_blank_values=True, strict_parsing=False)
    parsed: dict[str, str] = dict(pairs)

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise UnauthorizedError("Missing hash in initData")

    # Build data_check_string: sorted key=value pairs joined by \n
    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(parsed.items())
    )

    # ✅ FIX: key=bot_token, msg="WebAppData"  (was reversed before)
    secret_key = hmac.new(
        key=settings.telegram_bot_token.encode("utf-8"),
        msg=b"WebAppData",
        digestmod=hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise UnauthorizedError("Invalid Telegram initData signature")

    # Parse user field
    raw_user = parsed.get("user")
    if not raw_user:
        raise UnauthorizedError("Missing user in initData")

    try:
        user = json.loads(raw_user)
    except json.JSONDecodeError as exc:
        raise UnauthorizedError("Invalid user payload in initData") from exc

    if not isinstance(user, dict) or user.get("id") is None:
        raise UnauthorizedError("Invalid user payload in initData")

    return user


def create_access_token(
    data: dict[str, Any] | None = None,
    *,
    user_id: int | None = None,
    telegram_id: int | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    payload: dict[str, Any] = dict(data or {})

    if user_id is not None and "sub" not in payload:
        payload["sub"] = str(user_id)
    if telegram_id is not None and "telegram_id" not in payload:
        payload["telegram_id"] = str(telegram_id)

    payload["sub"] = str(payload["sub"]) if payload.get("sub") is not None else None
    payload["telegram_id"] = str(payload["telegram_id"]) if payload.get("telegram_id") is not None else None

    expire_after = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    payload["exp"] = datetime.now(timezone.utc) + expire_after

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    if not token:
        raise UnauthorizedError("Missing access token")
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired") from exc
    except JWTError as exc:
        raise UnauthorizedError("Invalid access token") from exc

    if not isinstance(payload, dict):
        raise UnauthorizedError("Invalid token payload")
    if payload.get("sub") is None:
        raise UnauthorizedError("Token subject is missing")
    return payload


def parse_user_from_init_data(init_data_payload: dict[str, Any] | str) -> dict[str, Any] | None:
    if isinstance(init_data_payload, str):
        try:
            return verify_telegram_init_data(init_data_payload)
        except UnauthorizedError:
            return None

    if "id" in init_data_payload and "user" not in init_data_payload:
        return init_data_payload

    raw_user = init_data_payload.get("user")
    if not raw_user:
        return None
    try:
        user = json.loads(raw_user) if isinstance(raw_user, str) else raw_user
    except json.JSONDecodeError:
        return None
    return user if isinstance(user, dict) else None