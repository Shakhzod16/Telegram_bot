from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Order)

    async def get_by_idempotency_key(self, key: str) -> Order | None:
        stmt = select(Order).where(Order.idempotency_key == key)
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_for_user(self, order_id: int, user_id: int) -> Order | None:
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id, Order.user_id == user_id)
        )
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_for_user(self, user_id: int, page: int, size: int) -> tuple[list[Order], int]:
        base = select(Order).where(Order.user_id == user_id)
        total = int(
            (await self._session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        )
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        res = await self._session.execute(stmt)
        return list(res.scalars().all()), total

    async def list_admin(self, status: str | None, page: int, size: int) -> tuple[list[Order], int]:
        q = select(Order)
        if status:
            q = q.where(Order.status == status)
        total = int((await self._session.execute(select(func.count()).select_from(q.subquery()))).scalar_one())
        stmt = (
            q.options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        res = await self._session.execute(stmt)
        return list(res.scalars().all()), total

    async def get_with_items(self, order_id: int) -> Order | None:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.user),
                selectinload(Order.address),
            )
            .where(Order.id == order_id)
        )
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()
