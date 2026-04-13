from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import OrderStatusPatch
from app.schemas.order import OrderOut
from app.services.admin import AdminService

router = APIRouter()


@router.get("")
async def list_orders(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
    status: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
) -> dict:
    rows, total = await AdminService(db).list_admin_orders(status, page, size)
    return {
        "items": [OrderOut.model_validate(r) for r in rows],
        "total": total,
        "page": page,
        "size": size,
    }


@router.patch("/{order_id}/status")
async def patch_status(
    order_id: int,
    body: OrderStatusPatch,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict:
    await AdminService(db).patch_order_status(order_id, body.status)
    return {"success": True}
