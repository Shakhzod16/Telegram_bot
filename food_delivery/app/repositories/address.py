from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.repositories.base import BaseRepository


class AddressRepository(BaseRepository[Address]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Address)

    async def list_by_user(self, user_id: int) -> list[Address]:
        stmt = select(Address).where(Address.user_id == user_id).order_by(Address.is_default.desc(), Address.id.desc())
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def get_for_user(self, address_id: int, user_id: int) -> Address | None:
        stmt = select(Address).where(Address.id == address_id, Address.user_id == user_id)
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def clear_default_for_user(self, user_id: int) -> None:
        await self._session.execute(update(Address).where(Address.user_id == user_id).values(is_default=False))
