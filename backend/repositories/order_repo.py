# -*- coding: utf-8 -*-
from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import Order, OrderItem
from backend.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Order)

    async def get(self, order_id: int, *, with_relations: bool = False) -> Order | None:
        if not with_relations:
            return await super().get(order_id)
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.user), selectinload(Order.items), selectinload(Order.payments))
        )
        return await self.session.scalar(stmt)

    async def get_for_user(self, order_id: int, user_id: int) -> Order | None:
        stmt = select(Order).where(Order.id == order_id, Order.user_id == user_id)
        return await self.session.scalar(stmt)

    async def get_by_user(self, user_id: int, *, page: int = 1, limit: int = 20) -> list[Order]:
        safe_limit = max(1, min(limit, 200))
        offset = max(0, (max(page, 1) - 1) * safe_limit)
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.id.desc())
            .options(selectinload(Order.items))
            .limit(safe_limit)
            .offset(offset)
        )
        return (await self.session.scalars(stmt)).all()

    async def list_recent(self, *, limit: int = 50) -> list[Order]:
        stmt = (
            select(Order)
            .options(selectinload(Order.user), selectinload(Order.items), selectinload(Order.payments))
            .order_by(Order.id.desc())
            .limit(max(1, min(limit, 200)))
        )
        return (await self.session.scalars(stmt)).all()

    async def create(self, data: dict) -> Order:
        return await super().create(data)

    async def create_item(self, data: dict) -> OrderItem:
        item = OrderItem(**data)
        self.session.add(item)
        await self.session.flush()
        return item

    async def update_status(self, order_id: int, status: str) -> Order | None:
        order = await self.get(order_id)
        if not order:
            return None
        order.status = status
        self.session.add(order)
        await self.session.flush()
        return order
