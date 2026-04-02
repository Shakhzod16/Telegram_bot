# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        self.session = session
        self.model = model

    async def get(self, obj_id: Any) -> ModelType | None:
        return await self.session.get(self.model, obj_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[ModelType]:
        stmt = select(self.model).limit(max(1, min(limit, 500))).offset(max(0, offset))
        return (await self.session.scalars(stmt)).all()

    async def create(self, data: dict[str, Any]) -> ModelType:
        entity = self.model(**data)
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(self, entity: ModelType, data: dict[str, Any]) -> ModelType:
        for key, value in data.items():
            setattr(entity, key, value)
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: ModelType) -> None:
        await self.session.delete(entity)
        await self.session.flush()
