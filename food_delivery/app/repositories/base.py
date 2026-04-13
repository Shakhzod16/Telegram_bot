from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    model: type[T]

    def __init__(self, session: AsyncSession, model: type[T] | None = None) -> None:
        self.session = session
        if model is not None:
            self.model = model
        if not hasattr(self, "model"):
            raise ValueError("Repository model is not configured")

        # Backward-compatible aliases used by current codebase.
        self._session = self.session
        self._model = self.model

    async def get_by_id(self, id: int) -> T | None:
        return await self.session.get(self.model, id)

    async def get_all(self, **filters: Any) -> list[T]:
        stmt = select(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> T:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: int, **kwargs: Any) -> T | None:
        obj = await self.get_by_id(id)
        if obj is None:
            return None
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: int | T) -> bool:
        obj: T | None
        if isinstance(id, self.model):
            obj = id
        else:
            obj = await self.get_by_id(id)
        if obj is None:
            return False
        self.session.delete(obj)
        await self.session.flush()
        return True

    # Backward-compatible helper for existing services.
    async def add(self, obj: T) -> T:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    # Backward-compatible helper for existing services.
    async def execute_scalar(self, stmt: Any) -> Any:
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
