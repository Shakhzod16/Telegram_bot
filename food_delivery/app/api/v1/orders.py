from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.bot_instance import bot
from app.db.session import get_db
from app.models.order import Order
from app.models.user import User
from app.schemas.order import CreateOrderRequest, OrderListResponse, OrderOut, OrderStatusUpdate
from app.services.checkout import CheckoutService
from app.services.order_notify import notify_admin_group
from app.services.order import OrderService

router = APIRouter()


@router.post("", response_model=OrderOut)
async def create_order(
    body: CreateOrderRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    user: User = Depends(get_current_user),
) -> OrderOut:
    new_order = await CheckoutService(db, redis).create_order(
        user.id,
        address_id=body.address_id,
        comment=body.comment,
        promo_code=body.promo_code,
        idempotency_key=body.idempotency_key,
    )

    try:
        await notify_admin_group(
            order_id=new_order.id,
            db=db,
            bot=bot,
        )
    except Exception as exc:
        import logging

        logging.error(f"Notify xato: {exc}")

    return OrderOut.model_validate(new_order)


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
    order = await OrderService(db, redis).get_order(user.id, order_id)
    return order.model_copy(update={"user_telegram_id": user.telegram_id})


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


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: int,
    body: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")

    order.status = body.status

    if body.status == "in_progress":
        order.courier_id = body.courier_id
        order.courier_name = body.courier_name
        order.accepted_at = datetime.utcnow()

    if body.status == "delivered":
        order.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(order)

    return {
        "message": "Status yangilandi",
        "order_id": order_id,
        "status": order.status,
    }
