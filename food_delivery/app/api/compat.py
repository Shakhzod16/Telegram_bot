from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.admin_whitelist import AdminPhoneWhitelist
from app.db.session import get_db
from app.models.address import Address
from app.models.user import User

router = APIRouter(prefix="/api", tags=["compat"])


class RegisterUserBody(BaseModel):
    telegram_id: int
    phone: str | None = Field(default=None, max_length=20)
    name: str | None = Field(default=None, max_length=100)
    lang: str = Field(default="uz", max_length=5)


class SaveAddressBody(BaseModel):
    telegram_id: int
    address: str = Field(min_length=1, max_length=500)
    lat: float | None = None
    lon: float | None = None


async def _sync_user_roles(db: AsyncSession, user: User) -> bool:
    """
    Keep compat endpoints aligned with role rules used across the app.
    We only promote roles from trusted sources and avoid implicit demotion.
    """
    changed = False
    telegram_id = int(user.telegram_id)

    if telegram_id in settings.SUPERADMIN_TELEGRAM_IDS:
        if not user.is_superadmin:
            user.is_superadmin = True
            changed = True
        if not user.is_admin:
            user.is_admin = True
            changed = True
        return changed

    if telegram_id in settings.admin_telegram_id_set and not user.is_admin:
        user.is_admin = True
        changed = True

    whitelist_result = await db.execute(
        select(AdminPhoneWhitelist.id).where(
            AdminPhoneWhitelist.telegram_id == telegram_id,
            AdminPhoneWhitelist.is_active.is_(True),
        )
    )
    if whitelist_result.scalar_one_or_none() is not None and not user.is_admin:
        user.is_admin = True
        changed = True

    return changed


@router.get("/users/{telegram_id}")
async def get_user_by_telegram_id(
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if await _sync_user_roles(db, user):
        await db.commit()
        await db.refresh(user)

    full_name = " ".join(
        part.strip()
        for part in ((user.first_name or ""), (user.last_name or ""))
        if part and part.strip()
    ).strip()
    if not full_name:
        full_name = user.first_name or ""

    return {
        "telegram_id": user.telegram_id,
        "phone": user.phone,
        "name": full_name,
        "lang": user.language or "uz",
        "is_admin": bool(user.is_admin),
        "is_superadmin": bool(user.is_superadmin),
    }


@router.post("/users/register")
async def register_user(
    body: RegisterUserBody,
    db: AsyncSession = Depends(get_db),
) -> dict:
    safe_lang = (body.lang or "uz").strip().lower()[:5] or "uz"

    result = await db.execute(select(User).where(User.telegram_id == body.telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            telegram_id=body.telegram_id,
            first_name=(body.name or "").strip(),
            phone=(body.phone or "").strip() or None,
            language=safe_lang,
            is_active=True,
            is_admin=False,
            is_superadmin=False,
        )
        db.add(user)
        await db.flush()
    else:
        if body.name is not None:
            user.first_name = (body.name or "").strip()
        if body.phone is not None:
            user.phone = (body.phone or "").strip() or None
        user.language = safe_lang
        await db.flush()

    await _sync_user_roles(db, user)
    await db.commit()
    await db.refresh(user)

    return {
        "success": True,
        "telegram_id": user.telegram_id,
        "lang": user.language,
        "is_admin": bool(user.is_admin),
        "is_superadmin": bool(user.is_superadmin),
    }


@router.post("/addresses/save")
async def save_address(
    body: SaveAddressBody,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user_result = await db.execute(select(User).where(User.telegram_id == body.telegram_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    address_text = (body.address or "").strip()
    if address_text.lower() == "geo" and body.lat is not None and body.lon is not None:
        address_text = f"{body.lat:.6f}, {body.lon:.6f}"

    existing_result = await db.execute(select(Address).where(Address.user_id == user.id))
    existing = list(existing_result.scalars().all())
    for item in existing:
        item.is_default = False

    new_address = Address(
        user_id=user.id,
        title="Asosiy manzil",
        address_line=address_text,
        lat=body.lat,
        lng=body.lon,
        is_default=True,
    )
    db.add(new_address)
    await db.flush()

    return {"success": True, "address_id": new_address.id}
