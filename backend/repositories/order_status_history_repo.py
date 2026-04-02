# -*- coding: utf-8 -*-
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import OrderStatusHistory
from backend.repositories.base import BaseRepository


class OrderStatusHistoryRepository(BaseRepository[OrderStatusHistory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, OrderStatusHistory)

    async def create(self, data: dict) -> OrderStatusHistory:
        return await super().create(data)
