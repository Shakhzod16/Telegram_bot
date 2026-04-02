# -*- coding: utf-8 -*-
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import Payment
from backend.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Payment)

    async def get_last_by_order(self, order_id: int) -> Payment | None:
        stmt = select(Payment).where(Payment.order_id == order_id).order_by(Payment.id.desc())
        return await self.session.scalar(stmt)

    async def get_last_by_order_and_provider(self, order_id: int, provider: str) -> Payment | None:
        stmt = (
            select(Payment)
            .where(Payment.order_id == order_id, Payment.provider == provider)
            .order_by(Payment.id.desc())
        )
        return await self.session.scalar(stmt)

    async def get_by_external_id(self, provider: str, external_id: str) -> Payment | None:
        if not external_id:
            return None
        stmt = (
            select(Payment)
            .where(Payment.provider == provider, Payment.external_id == external_id)
            .order_by(Payment.id.desc())
        )
        return await self.session.scalar(stmt)

    async def get_with_order(self, payment_id: int) -> Payment | None:
        stmt = (
            select(Payment)
            .where(Payment.id == payment_id)
            .options(selectinload(Payment.order))
        )
        return await self.session.scalar(stmt)

    async def create(self, data: dict) -> Payment:
        return await super().create(data)
