from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.address import Address
from app.repositories.address import AddressRepository
from app.schemas.address import AddressCreate, AddressOut, AddressUpdate


class AddressService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AddressRepository(session)

    async def list_addresses(self, user_id: int) -> list[AddressOut]:
        rows = await self._repo.list_by_user(user_id)
        return [AddressOut.model_validate(r) for r in rows]

    async def create(self, user_id: int, body: AddressCreate) -> AddressOut:
        if body.is_default:
            await self._repo.clear_default_for_user(user_id)
        addr = Address(
            user_id=user_id,
            title=body.title,
            address_line=body.address_line,
            lat=body.lat,
            lng=body.lng,
            apartment=body.apartment,
            floor=body.floor,
            entrance=body.entrance,
            door_code=body.door_code,
            landmark=body.landmark,
            comment=body.comment,
            is_default=body.is_default,
        )
        addr = await self._repo.add(addr)
        await self._session.commit()
        return AddressOut.model_validate(addr)

    async def update(self, user_id: int, address_id: int, body: AddressUpdate) -> AddressOut:
        addr = await self._repo.get_for_user(address_id, user_id)
        if not addr:
            raise NotFoundError("Address not found")
        data = body.model_dump(exclude_unset=True)
        if data.get("is_default") is True:
            await self._repo.clear_default_for_user(user_id)
        for k, v in data.items():
            setattr(addr, k, v)
        await self._session.commit()
        await self._session.refresh(addr)
        return AddressOut.model_validate(addr)

    async def delete(self, user_id: int, address_id: int) -> None:
        addr = await self._repo.get_for_user(address_id, user_id)
        if not addr:
            raise NotFoundError("Address not found")
        await self._repo.delete(addr)
        await self._session.commit()
