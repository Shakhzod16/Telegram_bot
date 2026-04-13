from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.order import OrderRepository
from app.repositories.user import UserRepository
from app.schemas.cart import CartAddItem
from app.schemas.order import OrderListResponse, OrderOut
from app.services.cart import CartService
from app.services.notification import NotificationService


class OrderService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self._session = session
        self._redis = redis
        self._orders = OrderRepository(session)
        self._users = UserRepository(session)
        self._cart = CartService(session, redis)
        self._notify = NotificationService()

    async def list_orders(self, user_id: int, page: int, size: int) -> OrderListResponse:
        rows, total = await self._orders.list_for_user(user_id, page, size)
        return OrderListResponse(
            items=[OrderOut.model_validate(r) for r in rows],
            total=total,
            page=page,
            size=size,
        )

    async def get_order(self, user_id: int, order_id: int) -> OrderOut:
        o = await self._orders.get_for_user(order_id, user_id)
        if not o:
            raise NotFoundError("Order not found")
        return OrderOut.model_validate(o)

    async def cancel_order(self, user_id: int, order_id: int) -> OrderOut:
        o = await self._orders.get_for_user(order_id, user_id)
        if not o:
            raise NotFoundError("Order not found")
        if o.status in ("delivered", "cancelled"):
            raise ValidationAppError("Cannot cancel this order")
        o.status = "cancelled"
        await self._session.commit()
        await self._session.refresh(o)
        u = await self._users.get_by_id(user_id)
        if u:
            await self._notify.send_status_update(u.telegram_id, "cancelled")
        return OrderOut.model_validate(o)

    async def repeat_order(self, user_id: int, order_id: int) -> None:
        o = await self._orders.get_for_user(order_id, user_id)
        if not o:
            raise NotFoundError("Order not found")
        for it in o.items:
            snap = it.snapshot_json or {}
            mids = list(snap.get("modifier_ids", []))
            body = CartAddItem(
                product_id=it.product_id,
                variant_id=it.variant_id,
                quantity=it.quantity,
                modifier_ids=mids,
            )
            await self._cart.add_item(user_id, body)
