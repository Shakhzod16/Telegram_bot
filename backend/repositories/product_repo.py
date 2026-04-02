# -*- coding: utf-8 -*-
from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Product
from backend.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Product)

    async def get(self, product_id: int) -> Product | None:
        return await super().get(product_id)

    async def count_all(self) -> int:
        stmt = select(func.count(Product.id))
        return int((await self.session.execute(stmt)).scalar_one())

    async def get_all(self, *, active_only: bool = True) -> list[Product]:
        stmt: Select[tuple[Product]] = select(Product).order_by(Product.category, Product.id)
        if active_only:
            stmt = stmt.where(Product.is_active.is_(True))
        return (await self.session.scalars(stmt)).all()

    async def get_many_active(self, product_ids: list[int]) -> list[Product]:
        if not product_ids:
            return []
        stmt = select(Product).where(Product.id.in_(product_ids), Product.is_active.is_(True))
        return (await self.session.scalars(stmt)).all()

    async def get_by_category(self, category: str, *, active_only: bool = True) -> list[Product]:
        stmt: Select[tuple[Product]] = select(Product).where(Product.category == category).order_by(Product.id)
        if active_only:
            stmt = stmt.where(Product.is_active.is_(True))
        return (await self.session.scalars(stmt)).all()
