from __future__ import annotations

import json
import random
import string
import urllib.parse
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import UnauthorizedError, ValidationAppError
from app.core.logging import get_logger
from app.core.security import create_access_token, verify_telegram_init_data
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import AuthResponse, MessageResponse, UserResponse

logger = get_logger(__name__)


class AuthService:
    def __init__(self, user_repo: UserRepository, redis: Redis | None = None) -> None:
        self.user_repo = user_repo
        self.redis = redis

    def _parse_unverified_telegram_user(self, init_data: str) -> dict[str, Any]:
        if not init_data:
            raise UnauthorizedError("Missing initData")

        parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
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

    async def authenticate_telegram(self, init_data: str) -> AuthResponse:
        if not settings.DEV_MODE:
            telegram_user = verify_telegram_init_data(init_data)
        else:
            logger.warning("telegram_init_data_validation_skipped_dev_mode")
            telegram_user = self._parse_unverified_telegram_user(init_data)
        telegram_id = int(telegram_user["id"])

        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            user = await self.user_repo.create_from_telegram(telegram_user)
        else:
            await self.user_repo.update_last_seen(user.id)

        await self.user_repo.session.commit()
        await self.user_repo.session.refresh(user)

        token = create_access_token({"sub": str(user.id), "telegram_id": str(user.telegram_id)})
        return AuthResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    # Backward-compatible method used by existing code paths.
    async def telegram_init(self, init_data: str) -> tuple[str, User]:
        auth = await self.authenticate_telegram(init_data)
        user = await self.user_repo.get_by_id(auth.user.id)
        if user is None:
            raise UnauthorizedError("User not found after authentication")
        return auth.access_token, user

    def _require_redis(self) -> Redis:
        if self.redis is None:
            raise ValidationAppError("Redis is not configured")
        return self.redis

    async def request_phone_otp(self, phone: str) -> MessageResponse:
        redis = self._require_redis()
        code = "".join(random.choices(string.digits, k=6))
        await redis.setex(f"otp:{phone}", settings.otp_ttl_seconds, code)
        return MessageResponse(
            message="OTP sent",
            debug_code=code if settings.debug else None,
        )

    async def verify_phone_otp(self, user_id: int, phone: str, code: str) -> None:
        redis = self._require_redis()
        raw = await redis.get(f"otp:{phone}")
        if raw is None:
            raise ValidationAppError("Invalid or expired code")

        stored = raw.decode() if isinstance(raw, bytes) else str(raw)
        if stored.strip() != code.strip():
            raise ValidationAppError("Invalid or expired code")

        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found")

        user.phone = phone
        await self.user_repo.session.commit()
        await redis.delete(f"otp:{phone}")
