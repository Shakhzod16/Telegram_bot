from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_superadmin
from app.db.session import get_db
from app.models.admin_whitelist import AdminPhoneWhitelist
from app.models.user import User
from app.schemas.admin_whitelist import (
    AdminWhitelistCreate,
    AdminWhitelistResponse,
    AdminWhitelistUpdate,
)

router = APIRouter(prefix="/whitelist")


def _full_name(user: User | None) -> str | None:
    if user is None:
        return None
    parts = [part.strip() for part in ((user.first_name or ""), (user.last_name or "")) if part and part.strip()]
    if parts:
        return " ".join(parts)
    if user.username:
        return f"@{user.username}"
    return "Foydalanuvchi"


def _to_response(entry: AdminPhoneWhitelist, user: User | None) -> AdminWhitelistResponse:
    return AdminWhitelistResponse(
        id=entry.id,
        telegram_id=entry.telegram_id,
        added_by=entry.added_by,
        added_at=entry.added_at,
        is_active=entry.is_active,
        note=entry.note,
        user_full_name=_full_name(user),
        user_phone=user.phone if user else None,
    )


@router.post("", response_model=AdminWhitelistResponse)
async def create_whitelist_entry(
    body: AdminWhitelistCreate,
    db: AsyncSession = Depends(get_db),
    current_superadmin: User = Depends(require_superadmin),
) -> AdminWhitelistResponse:
    existing_result = await db.execute(
        select(AdminPhoneWhitelist).where(AdminPhoneWhitelist.telegram_id == body.telegram_id)
    )
    existing = existing_result.scalar_one_or_none()
    user_result = await db.execute(select(User).where(User.telegram_id == body.telegram_id))
    user = user_result.scalar_one_or_none()

    if existing is not None:
        if existing.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bu Telegram ID allaqachon aktiv whitelistda mavjud",
            )

        existing.is_active = True
        existing.added_by = current_superadmin.id
        existing.note = body.note

        if user is not None:
            user.is_admin = True

        await db.flush()
        await db.refresh(existing)
        return _to_response(existing, user)

    entry = AdminPhoneWhitelist(
        telegram_id=body.telegram_id,
        note=body.note,
        is_active=True,
        added_by=current_superadmin.id,
    )
    db.add(entry)

    if user is not None:
        user.is_admin = True

    await db.flush()
    await db.refresh(entry)
    return _to_response(entry, user)


@router.get("", response_model=list[AdminWhitelistResponse])
async def list_whitelist_entries(
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_superadmin: User = Depends(require_superadmin),
) -> list[AdminWhitelistResponse]:
    query = select(AdminPhoneWhitelist, User).outerjoin(
        User,
        User.telegram_id == AdminPhoneWhitelist.telegram_id,
    )
    if is_active is not None:
        query = query.where(AdminPhoneWhitelist.is_active.is_(is_active))

    if search and search.strip():
        token = f"%{search.strip()}%"
        query = query.where(
            or_(
                cast(AdminPhoneWhitelist.telegram_id, String).ilike(token),
                func.coalesce(AdminPhoneWhitelist.note, "").ilike(token),
                func.coalesce(User.first_name, "").ilike(token),
                func.coalesce(User.last_name, "").ilike(token),
                func.coalesce(User.username, "").ilike(token),
                func.coalesce(User.phone, "").ilike(token),
            )
        )

    result = await db.execute(query.order_by(AdminPhoneWhitelist.id.desc()))
    rows = result.all()
    return [_to_response(entry, user) for entry, user in rows]


@router.get("/{whitelist_id}", response_model=AdminWhitelistResponse)
async def get_whitelist_entry(
    whitelist_id: int,
    db: AsyncSession = Depends(get_db),
    _current_superadmin: User = Depends(require_superadmin),
) -> AdminWhitelistResponse:
    result = await db.execute(
        select(AdminPhoneWhitelist, User)
        .outerjoin(User, User.telegram_id == AdminPhoneWhitelist.telegram_id)
        .where(AdminPhoneWhitelist.id == whitelist_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whitelist yozuvi topilmadi",
        )
    entry, user = row
    return _to_response(entry, user)


@router.patch("/{whitelist_id}", response_model=AdminWhitelistResponse)
async def patch_whitelist_entry(
    whitelist_id: int,
    body: AdminWhitelistUpdate,
    db: AsyncSession = Depends(get_db),
    _current_superadmin: User = Depends(require_superadmin),
) -> AdminWhitelistResponse:
    result = await db.execute(
        select(AdminPhoneWhitelist).where(AdminPhoneWhitelist.id == whitelist_id)
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whitelist yozuvi topilmadi",
        )

    has_is_active = "is_active" in body.model_fields_set
    has_note = "note" in body.model_fields_set
    if not has_is_active and not has_note:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Kamida bitta maydon yuborilishi kerak: is_active yoki note",
        )

    user_result = await db.execute(select(User).where(User.telegram_id == entry.telegram_id))
    user = user_result.scalar_one_or_none()

    if has_is_active:
        if body.is_active is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="is_active qiymati true yoki false bo'lishi kerak",
            )
        entry.is_active = body.is_active
        if user is not None:
            if entry.is_active:
                user.is_admin = True
            elif not user.is_superadmin:
                user.is_admin = False

    if has_note:
        entry.note = body.note

    await db.flush()
    await db.refresh(entry)
    return _to_response(entry, user)


@router.delete("/{whitelist_id}", response_model=AdminWhitelistResponse)
async def delete_whitelist_entry(
    whitelist_id: int,
    db: AsyncSession = Depends(get_db),
    _current_superadmin: User = Depends(require_superadmin),
) -> AdminWhitelistResponse:
    result = await db.execute(
        select(AdminPhoneWhitelist).where(AdminPhoneWhitelist.id == whitelist_id)
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whitelist yozuvi topilmadi",
        )

    entry.is_active = False

    user_result = await db.execute(select(User).where(User.telegram_id == entry.telegram_id))
    user = user_result.scalar_one_or_none()
    if user is not None and not user.is_superadmin:
        user.is_admin = False

    await db.flush()
    await db.refresh(entry)
    return _to_response(entry, user)
