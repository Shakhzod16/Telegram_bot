from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_superadmin
from app.db.session import get_db
from app.models.admin_whitelist import AdminPhoneWhitelist
from app.models.category import Category
from app.models.order import Order
from app.models.product import Product
from app.models.user import User

router = APIRouter(prefix="/stats")


class SuperadminStatsResponse(BaseModel):
    total_users: int
    total_admins: int
    total_superadmins: int
    total_products: int
    total_categories: int
    total_orders: int
    total_revenue: float
    active_whitelist_count: int
    inactive_whitelist_count: int
    today_orders: int
    today_revenue: float


def _as_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


@router.get("", response_model=SuperadminStatsResponse)
async def get_superadmin_stats(
    db: AsyncSession = Depends(get_db),
    _current_superadmin: User = Depends(require_superadmin),
) -> SuperadminStatsResponse:
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_admins = (
        await db.execute(
            select(func.count(User.id)).where(
                User.is_admin.is_(True),
                User.is_superadmin.is_(False),
            )
        )
    ).scalar_one()
    total_superadmins = (
        await db.execute(select(func.count(User.id)).where(User.is_superadmin.is_(True)))
    ).scalar_one()

    total_products = (await db.execute(select(func.count(Product.id)))).scalar_one()
    total_categories = (await db.execute(select(func.count(Category.id)))).scalar_one()
    total_orders = (await db.execute(select(func.count(Order.id)))).scalar_one()
    total_revenue_value = (await db.execute(select(func.coalesce(func.sum(Order.total_amount), 0)))).scalar_one()

    active_whitelist_count = (
        await db.execute(
            select(func.count(AdminPhoneWhitelist.id)).where(AdminPhoneWhitelist.is_active.is_(True))
        )
    ).scalar_one()
    inactive_whitelist_count = (
        await db.execute(
            select(func.count(AdminPhoneWhitelist.id)).where(AdminPhoneWhitelist.is_active.is_(False))
        )
    ).scalar_one()

    today = date.today()
    today_orders = (
        await db.execute(select(func.count(Order.id)).where(func.date(Order.created_at) == today))
    ).scalar_one()
    today_revenue_value = (
        await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(func.date(Order.created_at) == today)
        )
    ).scalar_one()

    return SuperadminStatsResponse(
        total_users=int(total_users or 0),
        total_admins=int(total_admins or 0),
        total_superadmins=int(total_superadmins or 0),
        total_products=int(total_products or 0),
        total_categories=int(total_categories or 0),
        total_orders=int(total_orders or 0),
        total_revenue=_as_float(total_revenue_value),
        active_whitelist_count=int(active_whitelist_count or 0),
        inactive_whitelist_count=int(inactive_whitelist_count or 0),
        today_orders=int(today_orders or 0),
        today_revenue=_as_float(today_revenue_value),
    )
