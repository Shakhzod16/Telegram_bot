from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.branch import Branch
from app.repositories.base import BaseRepository


class BranchRepository(BaseRepository[Branch]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Branch)

    async def list_active(self) -> list[Branch]:
        stmt = select(Branch).where(Branch.is_active.is_(True)).order_by(Branch.id)
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def list_all(self) -> list[Branch]:
        stmt = select(Branch).order_by(Branch.id)
        res = await self._session.execute(stmt)
        return list(res.scalars().all())
