from __future__ import annotations

import random
import string

from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import UnauthorizedError, ValidationAppError
from app.core.security import create_access_token, verify_telegram_init_data
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import AuthResponse, MessageResponse, UserResponse


class AuthService:
    def __init__(self, user_repo: UserRepository, redis: Redis | None = None) -> None:
        self.user_repo = user_repo
        self.redis = redis

    async def authenticate_telegram(self, init_data: str) -> AuthResponse:
        telegram_user = verify_telegram_init_data(init_data)
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
