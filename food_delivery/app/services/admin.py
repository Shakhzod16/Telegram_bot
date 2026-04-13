from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.branch import Branch
from app.models.category import Category
from app.models.product import Product
from app.models.promo import Promo
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.repositories.user import UserRepository
from app.schemas.admin import (
    BranchCreateAdmin,
    BranchUpdateAdmin,
    CategoryCreateAdmin,
    CategoryUpdateAdmin,
    ProductCreateAdmin,
    ProductUpdateAdmin,
    PromoCreateAdmin,
    PromoUpdateAdmin,
)
from app.services.notification import NotificationService


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._products = ProductRepository(session)
        self._orders = OrderRepository(session)
        self._users = UserRepository(session)
        self._notify = NotificationService()

    async def create_product(self, body: ProductCreateAdmin) -> Product:
        p = Product(
            category_id=body.category_id,
            name_uz=body.name_uz,
            name_ru=body.name_ru,
            description_uz=body.description_uz,
            description_ru=body.description_ru,
            base_price=body.base_price,
            weight_grams=body.weight_grams,
            image_url=body.image_url,
            is_active=body.is_active,
        )
        self._session.add(p)
        await self._session.commit()
        await self._session.refresh(p)
        return p

    async def update_product(self, product_id: int, body: ProductUpdateAdmin) -> Product:
        p = await self._products.get_by_id(product_id)
        if not p:
            raise NotFoundError("Product not found")
        for k, v in body.model_dump(exclude_unset=True).items():
            setattr(p, k, v)
        await self._session.commit()
        await self._session.refresh(p)
        return p

    async def delete_product(self, product_id: int) -> None:
        p = await self._products.get_by_id(product_id)
        if not p:
            raise NotFoundError("Product not found")
        self._session.delete(p)
        await self._session.commit()

    async def create_category(self, body: CategoryCreateAdmin) -> Category:
        c = Category(
            name_uz=body.name_uz,
            name_ru=body.name_ru,
            image_url=body.image_url,
            sort_order=body.sort_order,
            is_active=body.is_active,
        )
        self._session.add(c)
        await self._session.commit()
        await self._session.refresh(c)
        return c

    async def update_category(self, category_id: int, body: CategoryUpdateAdmin) -> Category:
        c = await self._session.get(Category, category_id)
        if not c:
            raise NotFoundError("Category not found")
        for k, v in body.model_dump(exclude_unset=True).items():
            setattr(c, k, v)
        await self._session.commit()
        await self._session.refresh(c)
        return c

    async def delete_category(self, category_id: int) -> None:
        c = await self._session.get(Category, category_id)
        if not c:
            raise NotFoundError("Category not found")
        self._session.delete(c)
        await self._session.commit()

    async def create_branch(self, body: BranchCreateAdmin) -> Branch:
        b = Branch(
            name=body.name,
            lat=body.lat,
            lng=body.lng,
            radius_km=body.radius_km,
            address=body.address,
            phone=body.phone,
            is_active=body.is_active,
            open_time=body.open_time,
            close_time=body.close_time,
            delivery_fee=body.delivery_fee,
        )
        self._session.add(b)
        await self._session.commit()
        await self._session.refresh(b)
        return b

    async def update_branch(self, branch_id: int, body: BranchUpdateAdmin) -> Branch:
        b = await self._session.get(Branch, branch_id)
        if not b:
            raise NotFoundError("Branch not found")
        for k, v in body.model_dump(exclude_unset=True).items():
            setattr(b, k, v)
        await self._session.commit()
        await self._session.refresh(b)
        return b

    async def delete_branch(self, branch_id: int) -> None:
        b = await self._session.get(Branch, branch_id)
        if not b:
            raise NotFoundError("Branch not found")
        self._session.delete(b)
        await self._session.commit()

    async def create_promo(self, body: PromoCreateAdmin) -> Promo:
        pr = Promo(
            code=body.code.upper().strip(),
            discount_type=body.discount_type,
            discount_value=body.discount_value,
            min_order_amount=body.min_order_amount,
            max_uses=body.max_uses,
            starts_at=body.starts_at,
            ends_at=body.ends_at,
            is_active=body.is_active,
        )
        self._session.add(pr)
        await self._session.commit()
        await self._session.refresh(pr)
        return pr

    async def update_promo(self, promo_id: int, body: PromoUpdateAdmin) -> Promo:
        pr = await self._session.get(Promo, promo_id)
        if not pr:
            raise NotFoundError("Promo not found")
        for k, v in body.model_dump(exclude_unset=True).items():
            setattr(pr, k, v)
        await self._session.commit()
        await self._session.refresh(pr)
        return pr

    async def delete_promo(self, promo_id: int) -> None:
        pr = await self._session.get(Promo, promo_id)
        if not pr:
            raise NotFoundError("Promo not found")
        self._session.delete(pr)
        await self._session.commit()

    async def list_admin_orders(self, status: str | None, page: int, size: int):
        return await self._orders.list_admin(status, page, size)

    async def patch_order_status(self, order_id: int, status: str) -> None:
        o = await self._orders.get_with_items(order_id)
        if not o:
            raise NotFoundError("Order not found")
        old = o.status
        o.status = status
        now = datetime.now(timezone.utc)
        if status == "confirmed":
            o.confirmed_at = now
        if status == "delivered":
            o.delivered_at = now
        await self._session.commit()
        u = await self._users.get_by_id(o.user_id)
        if u and old != status:
            await self._notify.send_status_update(u.telegram_id, status)

    async def list_users(self, page: int, size: int) -> tuple[list, int]:
        total = await self._users.count_all()
        offset = (page - 1) * size
        rows = await self._users.list_all(offset, size)
        return rows, total
