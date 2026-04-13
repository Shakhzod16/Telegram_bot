from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.repositories.base import BaseRepository


class CartRepository(BaseRepository[Cart]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Cart)

    async def get_by_user_id(self, user_id: int) -> Cart | None:
        stmt = select(Cart).where(Cart.user_id == user_id, Cart.status == "active")
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_or_create(self, user_id: int) -> Cart:
        cart = await self.get_by_user_id(user_id)
        if cart:
            return cart
        cart = Cart(user_id=user_id, status="active")
        return await self.add(cart)

    async def get_with_items(self, cart_id: int) -> Cart | None:
        stmt = select(Cart).options(selectinload(Cart.items)).where(Cart.id == cart_id)
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete_items(self, cart_id: int) -> None:
        await self._session.execute(delete(CartItem).where(CartItem.cart_id == cart_id))
