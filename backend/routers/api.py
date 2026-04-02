# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.models import OrderStatus
from backend.routers.dependencies import (
    get_address_service,
    get_bootstrap_service,
    get_notification_service,
    get_order_service,
    get_payment_service,
)
from backend.schemas import (
    AddressActionRead,
    AddressRead,
    BootstrapResponse,
    ClickCompleteRead,
    ClickPrepareRead,
    OrderActionRead,
    OrderCreate,
    OrderRead,
    PaymentCallbackRead,
    PaymentCreate,
    PaymentRead,
    ReorderRead,
    SavedAddressCreate,
)
from backend.security import TelegramAuthContext, telegram_auth
from backend.services import AddressService, BootstrapService, NotificationService, OrderService, PaymentService
from backend.services.payment_service import PaymeServiceError
from utils.logger import get_logger

router = APIRouter(prefix="/api", tags=["api"])
log = get_logger("backend.routers.api")


@router.post("/bootstrap", response_model=BootstrapResponse, dependencies=[Depends(telegram_auth)])
async def bootstrap(
    auth: TelegramAuthContext = Depends(telegram_auth),
    db: AsyncSession = Depends(get_db),
    bootstrap_service: BootstrapService = Depends(get_bootstrap_service),
) -> BootstrapResponse:
    payload = await bootstrap_service.bootstrap_payload(auth.user)
    await db.commit()
    return BootstrapResponse.model_validate(payload)


@router.get("/addresses", response_model=list[AddressRead], dependencies=[Depends(telegram_auth)])
async def list_saved_addresses(
    auth: TelegramAuthContext = Depends(telegram_auth),
    db: AsyncSession = Depends(get_db),
    bootstrap_service: BootstrapService = Depends(get_bootstrap_service),
    address_service: AddressService = Depends(get_address_service),
) -> list[AddressRead]:
    user = await bootstrap_service.get_or_create_user(auth.user)
    rows = await address_service.list_addresses(user.id)
    await db.commit()
    return [AddressRead.model_validate(row) for row in rows]


@router.post("/addresses", response_model=AddressRead, dependencies=[Depends(telegram_auth)])
async def create_saved_address(
    payload: SavedAddressCreate,
    auth: TelegramAuthContext = Depends(telegram_auth),
    db: AsyncSession = Depends(get_db),
    bootstrap_service: BootstrapService = Depends(get_bootstrap_service),
    address_service: AddressService = Depends(get_address_service),
) -> AddressRead:
    user = await bootstrap_service.get_or_create_user(auth.user)
    created = await address_service.create_address(user_id=user.id, payload=payload)
    await db.commit()
    return AddressRead.model_validate(created)


@router.delete("/addresses/{address_id}", response_model=AddressActionRead, dependencies=[Depends(telegram_auth)])
async def delete_saved_address(
    address_id: int,
    auth: TelegramAuthContext = Depends(telegram_auth),
    db: AsyncSession = Depends(get_db),
    bootstrap_service: BootstrapService = Depends(get_bootstrap_service),
    address_service: AddressService = Depends(get_address_service),
) -> AddressActionRead:
    user = await bootstrap_service.get_or_create_user(auth.user)
    deleted_id = await address_service.delete_address(user_id=user.id, address_id=address_id)
    await db.commit()
    return AddressActionRead(ok=True, address_id=deleted_id)


@router.patch("/addresses/{address_id}/default", response_model=AddressRead, dependencies=[Depends(telegram_auth)])
async def set_default_saved_address(
    address_id: int,
    auth: TelegramAuthContext = Depends(telegram_auth),
    db: AsyncSession = Depends(get_db),
    bootstrap_service: BootstrapService = Depends(get_bootstrap_service),
    address_service: AddressService = Depends(get_address_service),
) -> AddressRead:
    user = await bootstrap_service.get_or_create_user(auth.user)
    entity = await address_service.set_default(user_id=user.id, address_id=address_id)
    await db.commit()
    return AddressRead.model_validate(entity)


@router.post("/order", response_model=OrderRead, dependencies=[Depends(telegram_auth)])
async def create_order(
    payload: OrderCreate,
    auth: TelegramAuthContext = Depends(telegram_auth),
    db: AsyncSession = Depends(get_db),
    bootstrap_service: BootstrapService = Depends(get_bootstrap_service),
    order_service: OrderService = Depends(get_order_service),
    notification_service: NotificationService = Depends(get_notification_service),
) -> OrderRead:
    user = await bootstrap_service.get_or_create_user(auth.user)
    if payload.user_id != user.telegram_user_id:
        raise HTTPException(status_code=403, detail="User mismatch")

    order = await order_service.create_order(
        user_id=user.id,
        telegram_user_id=user.telegram_user_id,
        language=user.language,
        items=payload.items,
        location=payload.location,
        payment_method=payload.payment_method,
    )
    await db.commit()

    refreshed = await order_service.order_repo.get(order.id, with_relations=True)
    if refreshed:
        await notification_service.notify_admin(refreshed)
        order = refreshed

    log.info("order_created order_id=%s user_id=%s total=%s", order.id, user.telegram_user_id, order.total_amount)
    return OrderRead(
        order_id=order.id,
        status=order.status,
        total_amount=order.total_amount,
        payment_method=order.payment_method,
    )


@router.post("/orders", response_model=OrderRead, dependencies=[Depends(telegram_auth)])
async def create_order_compat(
    payload: OrderCreate,
    auth: TelegramAuthContext = Depends(telegram_auth),
    db: AsyncSession = Depends(get_db),
    bootstrap_service: BootstrapService = Depends(get_bootstrap_service),
    order_service: OrderService = Depends(get_order_service),
    notification_service: NotificationService = Depends(get_notification_service),
) -> OrderRead:
    return await create_order(
        payload=payload,
        auth=auth,
        db=db,
        bootstrap_service=bootstrap_service,
        order_service=order_service,
        notification_service=notification_service,
    )


@router.post("/orders/{order_id}/reorder", response_model=ReorderRead, dependencies=[Depends(telegram_auth)])
async def reorder_order(
    order_id: int,
    auth: TelegramAuthContext = Depends(telegram_auth),
    db: AsyncSession = Depends(get_db),
    bootstrap_service: BootstrapService = Depends(get_bootstrap_service),
    order_service: OrderService = Depends(get_order_service),
) -> ReorderRead:
    user = await bootstrap_service.get_or_create_user(auth.user)
    payload = await order_service.reorder_from_order(
        order_id=order_id,
        user_id=user.id,
        language=user.language,
    )
    await db.commit()
    return ReorderRead.model_validate(payload)


@router.post("/payments/create", response_model=PaymentRead, dependencies=[Depends(telegram_auth)])
async def create_payment(
    payload: PaymentCreate,
    auth: TelegramAuthContext = Depends(telegram_auth),
    db: AsyncSession = Depends(get_db),
    bootstrap_service: BootstrapService = Depends(get_bootstrap_service),
    payment_service: PaymentService = Depends(get_payment_service),
) -> PaymentRead:
    user = await bootstrap_service.get_or_create_user(auth.user)
    result = await payment_service.create_payment(
        user_id=user.id,
        order_id=payload.order_id,
        provider=payload.provider,
    )
    await db.commit()
    return PaymentRead.model_validate(result)


@router.post("/payments/callback", response_model=PaymentCallbackRead)
async def payments_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
    payment_service: PaymentService = Depends(get_payment_service),
) -> PaymentCallbackRead:
    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8", errors="ignore")
    content_type = request.headers.get("content-type", "").lower()
    result = await payment_service.process_callback(request=request, body_text=body_text, content_type=content_type)
    await db.commit()
    return PaymentCallbackRead.model_validate(result)


@router.post("/payment/click/prepare", response_model=ClickPrepareRead)
async def click_prepare(
    request: Request,
    db: AsyncSession = Depends(get_db),
    payment_service: PaymentService = Depends(get_payment_service),
) -> ClickPrepareRead:
    body = (await request.body()).decode("utf-8", errors="ignore")
    result = await payment_service.process_click_prepare(body)
    await db.commit()
    return ClickPrepareRead.model_validate(result)


@router.post("/payment/click/complete", response_model=ClickCompleteRead)
async def click_complete(
    request: Request,
    db: AsyncSession = Depends(get_db),
    payment_service: PaymentService = Depends(get_payment_service),
) -> ClickCompleteRead:
    body = (await request.body()).decode("utf-8", errors="ignore")
    result = await payment_service.process_click_complete(body)
    await db.commit()
    return ClickCompleteRead.model_validate(result)


@router.post("/payment/payme")
async def payme_rpc(
    request: Request,
    db: AsyncSession = Depends(get_db),
    payment_service: PaymentService = Depends(get_payment_service),
) -> dict:
    auth = request.headers.get("Authorization", "")
    if not payment_service.verify_payme_auth(auth):
        return {"error": {"code": -32504, "message": "Incorrect login"}, "id": None}

    body = await request.json()
    method = str(body.get("method") or "")
    params = body.get("params", {})
    payload_id = body.get("id")
    try:
        result = await payment_service.process_payme_rpc(method, params)
        await db.commit()
        return {"result": result, "id": payload_id}
    except PaymeServiceError as exc:
        await db.commit()
        response = {"error": {"code": exc.code, "message": exc.message}, "id": payload_id}
        if exc.data is not None:
            response["error"]["data"] = exc.data
        return response


@router.patch("/orders/{order_id}/deliver", response_model=OrderActionRead, dependencies=[Depends(telegram_auth)])
async def mark_delivered(
    order_id: int,
    _: TelegramAuthContext = Depends(telegram_auth),
    db: AsyncSession = Depends(get_db),
    order_service: OrderService = Depends(get_order_service),
) -> OrderActionRead:
    order = await order_service.update_status(
        order_id=order_id,
        new_status=OrderStatus.DELIVERED.value,
        changed_by="api:deliver",
        notes="Marked delivered from API",
    )
    await db.commit()
    return OrderActionRead(ok=True, order_id=order.id, status=order.status)
