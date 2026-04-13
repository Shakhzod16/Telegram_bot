from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_redis
from app.core.config import settings
from app.core.exceptions import RateLimitError
from app.models.admin_whitelist import AdminPhoneWhitelist
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import AuthResponse, PhoneRequestBody, PhoneVerifyBody, TelegramInitRequest
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

# ✅ FIX: limitni oshirdik — 5 → 30 (sahifa har ochilganda auth qiladi)
AUTH_INIT_RATE_LIMIT = 30
AUTH_INIT_RATE_WINDOW_SECONDS = 60


async def _enforce_init_rate_limit(request: Request, redis: Redis) -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"rl:auth:init:{client_ip}"
    request_count = await redis.incr(key)
    if request_count == 1:
        await redis.expire(key, AUTH_INIT_RATE_WINDOW_SECONDS)
    if request_count > AUTH_INIT_RATE_LIMIT:
        raise RateLimitError("Juda ko'p urinish. Bir daqiqadan so'ng qayta urinib ko'ring.")


@router.post("/telegram/init", response_model=AuthResponse)
async def telegram_init(
    body: TelegramInitRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthResponse:
    # DEBUG rejimida rate limit o'tkazib yuboriladi
    if not settings.debug:
        await _enforce_init_rate_limit(request, redis)

    auth_service = AuthService(user_repo=UserRepository(db))
    return await auth_service.authenticate_telegram(body.init_data)


@router.post("/phone/request")
async def phone_request(
    body: PhoneRequestBody,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    _user: User = Depends(get_current_user),
) -> dict:
    auth_service = AuthService(user_repo=UserRepository(db), redis=redis)
    return (await auth_service.request_phone_otp(body.phone)).model_dump()


@router.post("/phone/verify")
async def phone_verify(
    body: PhoneVerifyBody,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_user),
) -> dict:
    auth_service = AuthService(user_repo=UserRepository(db), redis=redis)
    await auth_service.verify_phone_otp(user.id, body.phone, body.code)

    # === SUPERADMIN TEKSHIRUVI ===
    # 1. Superadmin tekshiruvi (.env orqali)
    if user.telegram_id in settings.SUPERADMIN_TELEGRAM_IDS:
        user.is_superadmin = True
        user.is_admin = True

    # 2. Whitelist tekshiruvi (superadmin bo'lmasa)
    elif user.phone:
        whitelist_result = await db.execute(
            select(AdminPhoneWhitelist).where(
                AdminPhoneWhitelist.phone == user.phone,
                AdminPhoneWhitelist.is_active == True,
            )
        )
        whitelist_entry = whitelist_result.scalar_one_or_none()
        if whitelist_entry:
            user.is_admin = True
        else:
            # Whitelist dan chiqarilgan bo'lsa admin huquqini ol
            # (lekin superadmin bo'lsa tegma)
            if not user.is_superadmin:
                user.is_admin = False

    await db.commit()
    await db.refresh(user)
    # === SUPERADMIN TEKSHIRUVI TUGADI ===

    return {"success": True}
