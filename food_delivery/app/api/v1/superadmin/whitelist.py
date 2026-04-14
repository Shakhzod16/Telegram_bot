from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
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


@router.post("", response_model=AdminWhitelistResponse, status_code=status.HTTP_201_CREATED)
async def create_whitelist_entry(
    body: AdminWhitelistCreate,
    db: AsyncSession = Depends(get_db),
    current_superadmin: User = Depends(require_superadmin),
) -> AdminWhitelistResponse:
    existing_result = await db.execute(
        select(AdminPhoneWhitelist).where(AdminPhoneWhitelist.phone == body.phone)
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu telefon whitelistda allaqachon mavjud",
        )

    entry = AdminPhoneWhitelist(
        phone=body.phone,
        note=body.note,
        is_active=True,
        added_by=current_superadmin.id,
    )
    db.add(entry)

    user_result = await db.execute(select(User).where(User.phone == body.phone))
    user = user_result.scalar_one_or_none()
    if user is not None:
        user.is_admin = True

    await db.flush()
    await db.refresh(entry)
    return entry


@router.get("", response_model=list[AdminWhitelistResponse])
async def list_whitelist_entries(
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_superadmin: User = Depends(require_superadmin),
) -> list[AdminWhitelistResponse]:
    query = select(AdminPhoneWhitelist)
    if is_active is not None:
        query = query.where(AdminPhoneWhitelist.is_active == is_active)

    if search:
        token = f"%{search.strip()}%"
        query = query.where(
            or_(
                AdminPhoneWhitelist.phone.ilike(token),
                func.coalesce(AdminPhoneWhitelist.note, "").ilike(token),
            )
        )

    result = await db.execute(query.order_by(AdminPhoneWhitelist.id.desc()))
    return list(result.scalars().all())


@router.get("/{whitelist_id}", response_model=AdminWhitelistResponse)
async def get_whitelist_entry(
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
    return entry


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

    if has_is_active:
        if body.is_active is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="is_active qiymati true yoki false bo'lishi kerak",
            )
        entry.is_active = body.is_active
        user_result = await db.execute(select(User).where(User.phone == entry.phone))
        user = user_result.scalar_one_or_none()
        if user is not None:
            if entry.is_active:
                user.is_admin = True
            elif not user.is_superadmin:
                user.is_admin = False

    if has_note:
        entry.note = body.note

    await db.flush()
    await db.refresh(entry)
    return entry


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

    user_result = await db.execute(select(User).where(User.phone == entry.phone))
    user = user_result.scalar_one_or_none()
    if user is not None and not user.is_superadmin:
        user.is_admin = False

    await db.flush()
    await db.refresh(entry)
    return entry
