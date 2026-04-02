# -*- coding: utf-8 -*-
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User
from backend.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_telegram_id(self, tg_id: int) -> User | None:
        stmt = select(User).where(User.telegram_user_id == tg_id)
        return await self.session.scalar(stmt)

    async def create(self, data: dict) -> User:
        return await super().create(data)

    async def update(self, user_id: int, data: dict) -> User | None:
        user = await self.get(user_id)
        if not user:
            return None
        return await super().update(user, data)
