# -*- coding: utf-8 -*-
from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Address
from backend.repositories.base import BaseRepository


class AddressRepository(BaseRepository[Address]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Address)

    async def count_by_user(self, user_id: int) -> int:
        stmt = select(func.count(Address.id)).where(Address.user_id == user_id)
        return int((await self.session.execute(stmt)).scalar_one())

    async def list_by_user(self, user_id: int) -> list[Address]:
        stmt = (
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.is_default.desc(), Address.id.asc())
        )
        return (await self.session.scalars(stmt)).all()

    async def get_for_user(self, address_id: int, user_id: int) -> Address | None:
        stmt = select(Address).where(Address.id == address_id, Address.user_id == user_id)
        return await self.session.scalar(stmt)

    async def unset_default_for_user(self, user_id: int, *, exclude_id: int | None = None) -> None:
        stmt = update(Address).where(Address.user_id == user_id)
        if exclude_id is not None:
            stmt = stmt.where(Address.id != exclude_id)
        await self.session.execute(stmt.values(is_default=False))
        await self.session.flush()
