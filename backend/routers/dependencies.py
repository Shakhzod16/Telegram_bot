# -*- coding: utf-8 -*-
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.repositories import (
    AddressRepository,
    CartRepository,
    OrderRepository,
    OrderStatusHistoryRepository,
    PaymentRepository,
    ProductRepository,
    UserRepository,
)
from backend.services import (
    AddressService,
    BootstrapService,
    CartService,
    NotificationService,
    OrderService,
    PaymentService,
)
from config.settings import settings


def get_notification_service() -> NotificationService:
    return NotificationService(bot_token=settings.bot_token, admin_chat_id=settings.admin_chat_id)


def get_bootstrap_service(db: AsyncSession = Depends(get_db)) -> BootstrapService:
    return BootstrapService(
        user_repo=UserRepository(db),
        product_repo=ProductRepository(db),
        address_repo=AddressRepository(db),
        cache_ttl_seconds=settings.cache_ttl_seconds,
    )


def get_address_service(db: AsyncSession = Depends(get_db)) -> AddressService:
    return AddressService(address_repo=AddressRepository(db))


def get_cart_service(db: AsyncSession = Depends(get_db)) -> CartService:
    return CartService(cart_repo=CartRepository(db))


def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(
        order_repo=OrderRepository(db),
        product_repo=ProductRepository(db),
        history_repo=OrderStatusHistoryRepository(db),
        notification_service=get_notification_service(),
    )


def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    notification_service = get_notification_service()
    order_service = OrderService(
        order_repo=OrderRepository(db),
        product_repo=ProductRepository(db),
        history_repo=OrderStatusHistoryRepository(db),
        notification_service=notification_service,
    )
    return PaymentService(
        payment_repo=PaymentRepository(db),
        order_repo=OrderRepository(db),
        order_service=order_service,
        notification_service=notification_service,
    )
