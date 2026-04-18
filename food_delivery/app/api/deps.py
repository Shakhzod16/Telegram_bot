from __future__ import annotations

import json
import urllib.parse
from typing import Any
from typing import Optional, cast

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.logging import get_logger
from app.core.security import decode_access_token, verify_telegram_init_data
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/telegram/init",
    auto_error=False,
)


def _parse_unverified_telegram_user(init_data: str) -> dict[str, Any]:
    parsed = dict(
        urllib.parse.parse_qsl(
            init_data,
            keep_blank_values=True,
            strict_parsing=False,
        )
    )
    raw_user = parsed.get("user")
    if not raw_user:
        raise UnauthorizedError("Missing user in initData")

    try:
        telegram_user = json.loads(raw_user)
    except json.JSONDecodeError as exc:
        raise UnauthorizedError("Invalid user payload in initData") from exc

    if not isinstance(telegram_user, dict) or telegram_user.get("id") is None:
        raise UnauthorizedError("Invalid user payload in initData")
    return telegram_user


def _extract_telegram_id_from_init_data(init_data: str) -> int:
    if not init_data:
        raise UnauthorizedError("Missing initData")

    if settings.DEV_MODE:
        telegram_user = _parse_unverified_telegram_user(init_data)
    else:
        telegram_user = verify_telegram_init_data(init_data)

    try:
        return int(telegram_user["id"])
    except (TypeError, ValueError, KeyError) as exc:
        raise UnauthorizedError("Invalid Telegram user id in initData") from exc


def _extract_init_data_from_referer(referer: str | None) -> str | None:
    if not referer:
        return None
    try:
        parsed = urllib.parse.urlparse(referer)
        params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    except Exception:
        return None

    for key in ("tgWebAppData", "tg_web_app_data", "init_data"):
        values = params.get(key)
        if values and values[0]:
            return values[0]
    return None


async def _get_active_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> User:
    user = await UserRepository(db).get_by_telegram_id(telegram_id)
    if user is not None and user.is_active:
        return user
    raise UnauthorizedError("User is inactive or not found")


async def get_redis(request: Request) -> Redis:
    redis = getattr(request.app.state, "redis", None)
    if redis is not None:
        return redis

    try:
        from fakeredis.aioredis import FakeRedis

        fallback = cast(Redis, FakeRedis(decode_responses=False))
        request.app.state.redis = fallback
        logger.warning("redis_runtime_fallback_enabled")
        return fallback
    except Exception as exc:
        raise UnauthorizedError("Redis is not configured") from exc


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    x_telegram_id: int | None = Header(default=None),
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    x_telegram_init_data_alt: str | None = Header(default=None, alias="X-Telegram-InitData"),
    x_init_data: str | None = Header(default=None, alias="X-Init-Data"),
) -> User:
    init_data_header = x_telegram_init_data or x_telegram_init_data_alt or x_init_data

    if x_telegram_id:
        return await _get_active_user_by_telegram_id(db, x_telegram_id)

    if token:
        try:
            payload = decode_access_token(token)
            user_id_raw = payload.get("sub")
            try:
                user_id = int(user_id_raw)
            except (TypeError, ValueError) as exc:
                raise UnauthorizedError("Invalid token subject") from exc

            user = await UserRepository(db).get_by_id(user_id)
            if user is not None and user.is_active:
                return user
            raise UnauthorizedError("User is inactive or not found")
        except UnauthorizedError:
            if not init_data_header:
                raise
            logger.warning("jwt_invalid_or_expired_fallback_to_init_data")

    if init_data_header:
        telegram_id = _extract_telegram_id_from_init_data(init_data_header)
        return await _get_active_user_by_telegram_id(db, telegram_id)

    referer_init_data = _extract_init_data_from_referer(request.headers.get("referer"))
    if referer_init_data:
        logger.warning("auth_using_referer_init_data_fallback")
        telegram_id = _extract_telegram_id_from_init_data(referer_init_data)
        return await _get_active_user_by_telegram_id(db, telegram_id)

    logger.warning(
        "missing_credentials_with_headers",
        extra={
            "path": str(request.url.path),
            "origin": request.headers.get("origin"),
            "referer": request.headers.get("referer"),
            "has_authorization": bool(request.headers.get("authorization")),
            "has_x_telegram_init_data": bool(x_telegram_init_data),
            "has_x_telegram_init_data_alt": bool(x_telegram_init_data_alt),
            "has_x_init_data": bool(x_init_data),
        },
    )
    raise UnauthorizedError("Missing credentials")


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise ForbiddenError("Admin only")
    return current_user


# Backward-compatible alias used by existing endpoints.
require_admin = get_current_admin


async def require_superadmin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu amal faqat superadmin uchun ruxsat etilgan",
        )
    return current_user


def check_resource_ownership(resource_owner_id: Optional[int], current_user: User) -> bool:
    """
    Superadmin hamma resursga kiradi.
    Admin faqat o'z resursiga kiradi.
    Boshqacha bo'lsa 403 ko'taradi.
    """
    if current_user.is_superadmin:
        return True
    if resource_owner_id is None or resource_owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu resurs sizga tegishli emas",
        )
    return True


def get_owner_filter(current_user: User) -> Optional[int]:
    """
    Superadmin uchun None qaytaradi (barcha resurslar).
    Admin uchun current_user.id qaytaradi (faqat o'ziniki).
    """
    if current_user.is_superadmin:
        return None
    return current_user.id
