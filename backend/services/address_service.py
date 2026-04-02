# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import HTTPException

from backend.repositories.address_repo import AddressRepository
from backend.schemas.address import SavedAddressCreate


class AddressService:
    MAX_SAVED_ADDRESSES = 5

    def __init__(self, address_repo: AddressRepository) -> None:
        self.address_repo = address_repo

    async def list_addresses(self, user_id: int):
        return await self.address_repo.list_by_user(user_id)

    async def create_address(self, *, user_id: int, payload: SavedAddressCreate):
        count = await self.address_repo.count_by_user(user_id)
        if count >= self.MAX_SAVED_ADDRESSES:
            raise HTTPException(
                status_code=400,
                detail=f"You can save at most {self.MAX_SAVED_ADDRESSES} addresses.",
            )

        should_be_default = payload.is_default or count == 0
        if should_be_default:
            await self.address_repo.unset_default_for_user(user_id)

        entity = await self.address_repo.create(
            {
                "user_id": user_id,
                "label": payload.label.strip(),
                "address_text": payload.address_text.strip(),
                "latitude": payload.latitude,
                "longitude": payload.longitude,
                "is_default": should_be_default,
            }
        )
        await self.address_repo.session.flush()
        return entity

    async def delete_address(self, *, user_id: int, address_id: int) -> int:
        entity = await self.address_repo.get_for_user(address_id, user_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Address not found")

        was_default = bool(entity.is_default)
        deleted_id = entity.id
        await self.address_repo.delete(entity)
        await self.address_repo.session.flush()

        if was_default:
            rows = await self.address_repo.list_by_user(user_id)
            if rows:
                rows[0].is_default = True
                await self.address_repo.session.flush()
        return deleted_id

    async def set_default(self, *, user_id: int, address_id: int):
        entity = await self.address_repo.get_for_user(address_id, user_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Address not found")
        await self.address_repo.unset_default_for_user(user_id, exclude_id=entity.id)
        entity.is_default = True
        await self.address_repo.session.flush()
        return entity
