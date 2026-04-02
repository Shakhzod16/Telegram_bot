# -*- coding: utf-8 -*-
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Order, OrderItem, Product


class CartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_or_create_cart(self, user_id: int) -> Order:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id, Order.status == "cart")
            .order_by(Order.id.desc())
        )
        cart = await self.session.scalar(stmt)
        if cart:
            return cart
        cart = Order(user_id=user_id, status="cart", total_amount=0)
        self.session.add(cart)
        await self.session.flush()
        return cart

    async def get_by_user(self, user_id: int) -> list[OrderItem]:
        stmt = (
            select(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.user_id == user_id, Order.status == "cart")
            .order_by(OrderItem.id.desc())
        )
        return (await self.session.scalars(stmt)).all()

    async def add_item(self, user_id: int, product_id: int, qty: int) -> OrderItem:
        cart = await self._get_or_create_cart(user_id)
        stmt = select(OrderItem).where(OrderItem.order_id == cart.id, OrderItem.product_id == product_id)
        item = await self.session.scalar(stmt)
        product = await self.session.get(Product, product_id)
        if not product or not product.is_active:
            raise ValueError("Product unavailable")
        if item:
            item.quantity += qty
            item.total_price = item.quantity * item.unit_price
            self.session.add(item)
            await self.session.flush()
            return item

        new_item = OrderItem(
            order_id=cart.id,
            product_id=product.id,
            quantity=qty,
            unit_price=product.price,
            total_price=product.price * qty,
            product_name=product.name_en,
        )
        self.session.add(new_item)
        await self.session.flush()
        return new_item

    async def remove_item(self, item_id: int) -> bool:
        item = await self.session.get(OrderItem, item_id)
        if not item:
            return False
        await self.session.delete(item)
        await self.session.flush()
        return True

    async def clear(self, user_id: int) -> int:
        items = await self.get_by_user(user_id)
        removed = 0
        for item in items:
            await self.session.delete(item)
            removed += 1
        await self.session.flush()
        return removed
