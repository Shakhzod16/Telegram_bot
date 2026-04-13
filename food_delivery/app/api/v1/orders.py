from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import CreateOrderRequest, OrderListResponse, OrderOut
from app.services.checkout import CheckoutService
from app.services.order import OrderService

router = APIRouter()


@router.post("", response_model=OrderOut)
async def create_order(
    body: CreateOrderRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    user: User = Depends(get_current_user),
) -> OrderOut:
    o = await CheckoutService(db, redis).create_order(
        user.id,
        address_id=body.address_id,
        comment=body.comment,
        promo_code=body.promo_code,
        idempotency_key=body.idempotency_key,
    )
    return OrderOut.model_validate(o)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> OrderListResponse:
    return await OrderService(db, redis).list_orders(user.id, page, size)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    user: User = Depends(get_current_user),
) -> OrderOut:
    return await OrderService(db, redis).get_order(user.id, order_id)


@router.post("/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    user: User = Depends(get_current_user),
) -> OrderOut:
    return await OrderService(db, redis).cancel_order(user.id, order_id)


@router.post("/{order_id}/repeat")
async def repeat_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    user: User = Depends(get_current_user),
) -> dict:
    await OrderService(db, redis).repeat_order(user.id, order_id)
    return {"success": True}
