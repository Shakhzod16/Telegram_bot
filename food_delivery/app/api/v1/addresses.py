from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.address import AddressCreate, AddressOut, AddressUpdate
from app.services.address import AddressService

router = APIRouter()


@router.get("", response_model=list[AddressOut])
async def list_addresses(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AddressOut]:
    return await AddressService(db).list_addresses(user.id)


@router.post("", response_model=AddressOut)
async def create_address(
    body: AddressCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AddressOut:
    return await AddressService(db).create(user.id, body)


@router.patch("/{address_id}", response_model=AddressOut)
async def update_address(
    address_id: int,
    body: AddressUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AddressOut:
    return await AddressService(db).update(user.id, address_id, body)


@router.delete("/{address_id}")
async def delete_address(
    address_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    await AddressService(db).delete(user.id, address_id)
    return {"success": True}
