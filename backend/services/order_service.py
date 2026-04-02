# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException

from backend.models import Order, OrderStatus, PaymentMethod
from backend.repositories.order_repo import OrderRepository
from backend.repositories.order_status_history_repo import OrderStatusHistoryRepository
from backend.repositories.product_repo import ProductRepository
from backend.schemas.address import AddressCreate
from backend.schemas.cart import CartItemAdd
from backend.services.cart_service import CartService
from backend.services.notification_service import NotificationService
from utils.logger import get_logger

VALID_ORDER_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.PENDING.value: {
        OrderStatus.CONFIRMED.value,
        OrderStatus.CANCELLED.value,
    },
    OrderStatus.CONFIRMED.value: {
        OrderStatus.PREPARING.value,
        OrderStatus.CANCELLED.value,
    },
    OrderStatus.PREPARING.value: {
        OrderStatus.DELIVERING.value,
    },
    OrderStatus.DELIVERING.value: {
        OrderStatus.DELIVERED.value,
    },
    OrderStatus.DELIVERED.value: set(),
    OrderStatus.CANCELLED.value: set(),
}


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        product_repo: ProductRepository,
        history_repo: OrderStatusHistoryRepository,
        notification_service: NotificationService,
    ) -> None:
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.history_repo = history_repo
        self.notification = notification_service
        self.log = get_logger("backend.services.order")

    async def create_order(
        self,
        *,
        user_id: int,
        telegram_user_id: int,
        language: str,
        items: list[CartItemAdd],
        location: AddressCreate | None,
        payment_method: str = PaymentMethod.CLICK.value,
    ) -> Order:
        product_ids = [item.product_id for item in items]
        rows = await self.product_repo.get_many_active(product_ids)
        rows_by_id = {row.id: row for row in rows}
        if len(rows_by_id) != len(set(product_ids)):
            raise HTTPException(status_code=400, detail="Invalid products")

        order = await self.order_repo.create(
            {
                "user_id": user_id,
                "status": OrderStatus.PENDING.value,
                "total_amount": 0,
                "payment_method": self._normalize_payment_method(payment_method),
                "location_label": (
                    (location.address_text or location.label or "").strip()
                    if location
                    else ""
                ),
                "latitude": location.latitude if location else None,
                "longitude": location.longitude if location else None,
            }
        )

        total = 0
        lang = language if language in {"uz", "ru", "en"} else "en"
        for line in items:
            product = rows_by_id[line.product_id]
            line_total = product.price * line.quantity
            total += line_total
            await self.order_repo.create_item(
                {
                    "order_id": order.id,
                    "product_id": product.id,
                    "quantity": line.quantity,
                    "unit_price": product.price,
                    "total_price": line_total,
                    "product_name": getattr(product, f"name_{lang}"),
                }
            )

        order.total_amount = total
        await self.history_repo.create(
            {
                "order_id": order.id,
                "old_status": "",
                "new_status": order.status,
                "changed_by": f"user:{telegram_user_id}",
                "notes": f"Order created via {payment_method}",
            }
        )
        await self.order_repo.session.flush()
        loaded = await self.order_repo.get(order.id, with_relations=True)
        return loaded or order

    @staticmethod
    def _transition_allowed(current: str, target: str) -> bool:
        return target in VALID_ORDER_TRANSITIONS.get(current, set())

    @staticmethod
    def _normalize_status(value: str) -> str:
        normalized = (value or "").strip().lower()
        legacy_map = {
            "paid": OrderStatus.CONFIRMED.value,
            "in_progress": OrderStatus.PREPARING.value,
            "created": OrderStatus.PENDING.value,
        }
        normalized = legacy_map.get(normalized, normalized)
        allowed = {item.value for item in OrderStatus}
        if normalized not in allowed:
            raise HTTPException(status_code=400, detail=f"Unsupported order status: {value}")
        return normalized

    @staticmethod
    def _normalize_payment_method(value: str) -> str:
        normalized = (value or "").strip().lower()
        allowed = {item.value for item in PaymentMethod}
        if normalized not in allowed:
            return PaymentMethod.CASH.value
        return normalized

    def validate_transition(self, old_status: str, new_status: str) -> None:
        current = self._normalize_status(old_status)
        target = self._normalize_status(new_status)
        if not self._transition_allowed(current, target):
            raise HTTPException(status_code=400, detail=f"Invalid status transition: {current} -> {target}")

    async def update_status(
        self,
        order_id: int,
        new_status: str,
        changed_by: str,
        *,
        notes: str = "",
    ) -> Order:
        order = await self.order_repo.get(order_id, with_relations=True)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        current = self._normalize_status(order.status or OrderStatus.PENDING.value)
        target = self._normalize_status(new_status)
        if current == target:
            return order
        self.validate_transition(current, target)

        now = datetime.now(UTC)
        order.status = target
        if target == OrderStatus.CONFIRMED.value and order.paid_at is None:
            order.paid_at = now
        if target == OrderStatus.DELIVERED.value and order.delivered_at is None:
            order.delivered_at = now
        await self.history_repo.create(
            {
                "order_id": order.id,
                "old_status": current,
                "new_status": target,
                "changed_by": changed_by,
                "notes": notes,
            }
        )
        await self.order_repo.session.flush()
        if order.user and order.user.telegram_user_id:
            await self.notification.notify_status_change(order, order.user.telegram_user_id)
        return order

    async def cancel_order(self, order_id: int, user_id: int) -> Order:
        order = await self.order_repo.get_for_user(order_id, user_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if self._normalize_status(order.status) != OrderStatus.PENDING.value:
            raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")
        return await self.update_status(
            order_id=order.id,
            new_status=OrderStatus.CANCELLED.value,
            changed_by=f"user:{user_id}",
            notes="Cancelled by user",
        )

    async def get_user_orders(self, user_id: int, page: int = 1, limit: int = 20) -> list[Order]:
        return await self.order_repo.get_by_user(user_id=user_id, page=page, limit=limit)

    async def get_admin_orders(self, limit: int = 50) -> list[Order]:
        return await self.order_repo.list_recent(limit=limit)

    async def reorder_from_order(self, *, order_id: int, user_id: int, language: str) -> dict:
        order = await self.order_repo.get(order_id, with_relations=True)
        if not order or order.user_id != user_id:
            raise HTTPException(status_code=404, detail="Order not found")

        if not order.items:
            return {"order_id": order_id, "items": [], "skipped_count": 0, "skipped_products": []}

        quantities: dict[int, int] = {}
        for item in order.items:
            product_id = int(item.product_id)
            quantities[product_id] = quantities.get(product_id, 0) + int(item.quantity)
        rows = await self.product_repo.get_many_active(list(quantities.keys()))
        rows_by_id = {row.id: row for row in rows}
        cart_items, skipped_names = CartService.from_order(order.items, set(rows_by_id.keys()))
        lang = language if language in {"uz", "ru", "en"} else "en"
        items: list[dict] = []
        for row in cart_items:
            product_id = int(row["product_id"])
            quantity = int(row["quantity"])
            product = rows_by_id.get(product_id)
            if not product:
                continue
            items.append(
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "name": getattr(product, f"name_{lang}"),
                }
            )

        return {
            "order_id": order_id,
            "items": items,
            "skipped_count": len(skipped_names),
            "skipped_products": skipped_names,
        }
