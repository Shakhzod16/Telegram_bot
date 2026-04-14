from __future__ import annotations

from typing import Optional, cast

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/telegram/init",
    auto_error=False,
)


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
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    x_telegram_id: int | None = Header(default=None),
) -> User:
    if x_telegram_id:
        user = await UserRepository(db).get_by_telegram_id(x_telegram_id)
        if user is not None and user.is_active:
            return user
        raise UnauthorizedError("User is inactive or not found")

    if not token:
        raise UnauthorizedError("Missing credentials")

    payload = decode_access_token(token)
    user_id_raw = payload.get("sub")
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError) as exc:
        raise UnauthorizedError("Invalid token subject") from exc

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User is inactive or not found")
    return user


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
