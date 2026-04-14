from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_superadmin
from app.db.session import get_db
from app.models.admin_whitelist import AdminPhoneWhitelist
from app.models.category import Category
from app.models.product import Product
from app.models.user import User

router = APIRouter(prefix="/admins")


class AdminListItem(BaseModel):
    id: int
    telegram_id: int
    phone: str
    full_name: str
    is_admin: bool
    is_superadmin: bool
    products_count: int
    categories_count: int
    created_at: datetime


class AdminStatsResponse(BaseModel):
    user_id: int
    products_count: int
    categories_count: int
    active_products: int
    inactive_products: int


class AdminDetailResponse(AdminListItem):
    stats: AdminStatsResponse


class RemoveAdminResponse(BaseModel):
    message: str


def _full_name(user: User) -> str:
    parts = [part.strip() for part in ((user.first_name or ""), (user.last_name or "")) if part and part.strip()]
    if parts:
        return " ".join(parts)
    if user.username:
        return f"@{user.username}"
    return "Foydalanuvchi"


async def _get_admin_stats(db: AsyncSession, user_id: int) -> AdminStatsResponse:
    products_result = await db.execute(
        select(
            func.count(Product.id),
            func.coalesce(func.sum(case((Product.is_active.is_(True), 1), else_=0)), 0),
            func.coalesce(func.sum(case((Product.is_active.is_(False), 1), else_=0)), 0),
        ).where(Product.owner_id == user_id)
    )
    products_count, active_products, inactive_products = products_result.one()

    categories_result = await db.execute(
        select(func.count(Category.id)).where(Category.owner_id == user_id)
    )
    categories_count = categories_result.scalar_one()

    return AdminStatsResponse(
        user_id=user_id,
        products_count=int(products_count or 0),
        categories_count=int(categories_count or 0),
        active_products=int(active_products or 0),
        inactive_products=int(inactive_products or 0),
    )


@router.get("", response_model=list[AdminListItem])
async def list_admins(
    db: AsyncSession = Depends(get_db),
    _superadmin: User = Depends(require_superadmin),
) -> list[AdminListItem]:
    admins_result = await db.execute(
        select(User)
        .where(
            User.is_admin.is_(True),
            User.is_superadmin.is_(False),
        )
        .order_by(User.id.desc())
    )
    admins = list(admins_result.scalars().all())
    if not admins:
        return []

    admin_ids = [admin.id for admin in admins]

    product_counts_result = await db.execute(
        select(Product.owner_id, func.count(Product.id))
        .where(Product.owner_id.in_(admin_ids))
        .group_by(Product.owner_id)
    )
    product_counts = {int(owner_id): int(count) for owner_id, count in product_counts_result.all() if owner_id is not None}

    category_counts_result = await db.execute(
        select(Category.owner_id, func.count(Category.id))
        .where(Category.owner_id.in_(admin_ids))
        .group_by(Category.owner_id)
    )
    category_counts = {
        int(owner_id): int(count) for owner_id, count in category_counts_result.all() if owner_id is not None
    }

    return [
        AdminListItem(
            id=admin.id,
            telegram_id=admin.telegram_id,
            phone=admin.phone or "—",
            full_name=_full_name(admin),
            is_admin=admin.is_admin,
            is_superadmin=admin.is_superadmin,
            products_count=product_counts.get(admin.id, 0),
            categories_count=category_counts.get(admin.id, 0),
            created_at=admin.created_at,
        )
        for admin in admins
    ]


@router.get("/{user_id}/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _superadmin: User = Depends(require_superadmin),
) -> AdminStatsResponse:
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_admin or user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin topilmadi",
        )

    return await _get_admin_stats(db, user_id=user_id)


@router.get("/{user_id}", response_model=AdminDetailResponse)
async def get_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _superadmin: User = Depends(require_superadmin),
) -> AdminDetailResponse:
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_admin or user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin topilmadi",
        )

    stats = await _get_admin_stats(db, user_id=user.id)
    return AdminDetailResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        phone=user.phone or "—",
        full_name=_full_name(user),
        is_admin=user.is_admin,
        is_superadmin=user.is_superadmin,
        products_count=stats.products_count,
        categories_count=stats.categories_count,
        created_at=user.created_at,
        stats=stats,
    )


@router.delete("/{user_id}", response_model=RemoveAdminResponse)
async def remove_admin_rights(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _superadmin: User = Depends(require_superadmin),
) -> RemoveAdminResponse:
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi",
        )
    if user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Superadmin huquqini olib bo'lmaydi",
        )

    user.is_admin = False

    whitelist_result = await db.execute(
        select(AdminPhoneWhitelist).where(AdminPhoneWhitelist.telegram_id == user.telegram_id)
    )
    whitelist_entry = whitelist_result.scalar_one_or_none()
    if whitelist_entry is not None:
        whitelist_entry.is_active = False

    await db.flush()
    return RemoveAdminResponse(message="Admin huquqi muvaffaqiyatli olindi")
