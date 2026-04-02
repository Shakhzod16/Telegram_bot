# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.models import OrderStatus
from backend.routers.dependencies import get_order_service, get_payment_service
from backend.schemas import OrderActionRead, OrderAdminRead, OrderItemAdminRead, OrderUserSummary
from backend.security import admin_key_auth
from backend.services import OrderService, PaymentService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.patch("/orders/{order_id}/status", response_model=OrderActionRead, dependencies=[Depends(admin_key_auth)])
async def admin_update_order_status(
    order_id: int,
    status: str,
    db: AsyncSession = Depends(get_db),
    order_service: OrderService = Depends(get_order_service),
) -> OrderActionRead:
    target = status.lower().strip()
    allowed = {item.value for item in OrderStatus}
    if target not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported status. Allowed: {sorted(allowed)}")

    order = await order_service.update_status(
        order_id=order_id,
        new_status=target,
        changed_by="admin:api",
        notes="Updated from admin endpoint",
    )
    await db.commit()
    return OrderActionRead(ok=True, order_id=order.id, status=order.status)


@router.patch(
    "/orders/{order_id}/cash-received",
    response_model=OrderActionRead,
    dependencies=[Depends(admin_key_auth)],
)
async def admin_mark_cash_received(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    payment_service: PaymentService = Depends(get_payment_service),
) -> OrderActionRead:
    result = await payment_service.mark_cash_received(order_id=order_id, changed_by="admin:cash")
    await db.commit()
    return OrderActionRead(ok=True, order_id=result["order_id"], status=result["status"])


@router.get("/orders", response_model=list[OrderAdminRead], dependencies=[Depends(admin_key_auth)])
async def admin_orders(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    order_service: OrderService = Depends(get_order_service),
) -> list[OrderAdminRead]:
    rows = await order_service.get_admin_orders(limit=limit)
    response: list[OrderAdminRead] = []
    for row in rows:
        response.append(
            OrderAdminRead(
                id=row.id,
                status=row.status,
                total_amount=row.total_amount,
                payment_method=row.payment_method,
                payment_status=(row.payments[-1].status if row.payments else None),
                created_at=row.created_at,
                paid_at=row.paid_at,
                delivered_at=row.delivered_at,
                user=OrderUserSummary(
                    telegram_user_id=row.user.telegram_user_id if row.user else None,
                    name=row.user.first_name if row.user else "",
                    phone=row.user.phone if row.user else "",
                ),
                items=[
                    OrderItemAdminRead(
                        name=item.product_name,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.total_price,
                    )
                    for item in row.items
                ],
            )
        )
    await db.commit()
    return response
