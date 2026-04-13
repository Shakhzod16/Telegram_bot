from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.db.session import get_db
from app.models.user import User
from app.schemas.cart import CartAddItem, CartOut, CartPatchItem
from app.services.cart import CartService

router = APIRouter()


@router.get("", response_model=CartOut)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    user: User = Depends(get_current_user),
) -> CartOut:
    return await CartService(db, redis).get_cart(user.id)


@router.post("/items", response_model=CartOut)
async def add_item(
    body: CartAddItem,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    user: User = Depends(get_current_user),
) -> CartOut:
    return await CartService(db, redis).add_item(user.id, body)


@router.patch("/items/{item_id}", response_model=CartOut)
async def patch_item(
    item_id: str,
    body: CartPatchItem,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    user: User = Depends(get_current_user),
) -> CartOut:
    return await CartService(db, redis).patch_item(user.id, item_id, body)


@router.delete("/items/{item_id}")
async def delete_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    user: User = Depends(get_current_user),
) -> dict:
    await CartService(db, redis).delete_item(user.id, item_id)
    return {"success": True}


@router.delete("/clear")
async def clear_cart(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    user: User = Depends(get_current_user),
) -> dict:
    await CartService(db, redis).clear(user.id)
    return {"success": True}
