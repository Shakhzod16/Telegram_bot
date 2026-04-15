from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    BranchClosedError,
    EmptyCartError,
    MinOrderAmountError,
    NotFoundError,
    OutOfDeliveryZoneError,
    ValidationAppError,
)
from app.models.address import Address
from app.models.branch import Branch
from app.models.order import Order, OrderItem
from app.repositories.address import AddressRepository
from app.repositories.branch import BranchRepository
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.repositories.promo import PromoRepository
from app.repositories.user import UserRepository
from app.services.cart import CartService
from app.services.notification import NotificationService
from app.schemas.order import CheckoutPreviewRequest, CheckoutPreviewResponse


@dataclass
class VerifiedLine:
    product_id: int
    variant_id: int | None
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    snapshot_json: dict[str, Any]


class CheckoutService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self._session = session
        self._redis = redis
        self._addresses = AddressRepository(session)
        self._branches = BranchRepository(session)
        self._orders = OrderRepository(session)
        self._products = ProductRepository(session)
        self._promos = PromoRepository(session)
        self._users = UserRepository(session)
        self._cart = CartService(session, redis)
        self._notify = NotificationService()

    async def _verify_lines(self, user_id: int) -> list[VerifiedLine]:
        cart = await self._cart.get_cart(user_id)
        out: list[VerifiedLine] = []
        for line in cart.items:
            p = await self._products.get_by_id_with_relations(line.product_id)
            if not p or not p.is_active:
                raise ValidationAppError(f"Product unavailable: {line.product_id}")
            variant_id = line.variant_id
            unit = p.base_price
            variant_name: str | None = None
            if p.variants:
                if variant_id is None:
                    dv = next((v for v in p.variants if v.is_default), p.variants[0])
                    variant_id = dv.id
                    unit = dv.price
                    variant_name = dv.name_uz
                else:
                    v = next((x for x in p.variants if x.id == variant_id), None)
                    if not v:
                        raise ValidationAppError("Invalid variant")
                    unit = v.price
                    variant_name = v.name_uz
            mods = await self._products.get_modifiers_for_product(p.id)
            mod_by_id = {m.id: m for m in mods}
            mid_from_line = line.snapshot.get("modifier_ids") if line.snapshot else []
            extra = Decimal("0")
            snap_mods: list[dict[str, Any]] = []
            for mid in mid_from_line:
                m = mod_by_id.get(mid)
                if not m:
                    raise ValidationAppError("Invalid modifier")
                extra += m.price_delta
                snap_mods.append(
                    {"id": m.id, "name_uz": m.name_uz, "price_delta": str(m.price_delta)},
                )
            unit = unit + extra
            total = unit * line.quantity
            snap = {
                "product_name": p.name_uz,
                "variant_name": variant_name,
                "variant_id": variant_id,
                "image_url": p.image_url,
                "modifier_ids": list(mid_from_line),
                "modifiers": snap_mods,
            }
            out.append(
                VerifiedLine(
                    product_id=p.id,
                    variant_id=variant_id,
                    quantity=line.quantity,
                    unit_price=unit,
                    total_price=total,
                    snapshot_json=snap,
                )
            )
        return out

    def _pick_branch(self, address: Address, branches: list[Branch]) -> Branch:
        active_branches = [b for b in branches if b.is_active]
        open_branches = [b for b in active_branches if b.is_open_now()]
        candidates = open_branches
        if not candidates:
            # Dev muhitda checkout oqimini vaqtga bog'lab qo'ymaslik uchun
            # aktiv filialni fallback sifatida ishlatamiz.
            if settings.DEV_MODE and active_branches:
                candidates = active_branches
            else:
                raise BranchClosedError()
        if address.lat is not None and address.lng is not None:
            sorted_bs = sorted(
                candidates,
                key=lambda x: x.distance_km(address.lat, address.lng),
            )
            for b in sorted_bs:
                if b.distance_km(address.lat, address.lng) <= b.radius_km:
                    return b
            raise OutOfDeliveryZoneError()
        return candidates[0]

    async def preview(self, user_id: int, body: CheckoutPreviewRequest) -> CheckoutPreviewResponse:
        addr = await self._addresses.get_for_user(body.address_id, user_id)
        if not addr:
            raise NotFoundError("Address not found")
        lines = await self._verify_lines(user_id)
        if not lines:
            raise EmptyCartError()
        subtotal = sum((x.total_price for x in lines), Decimal("0"))
        branches = await self._branches.list_active()
        branch = self._pick_branch(addr, branches)
        delivery_fee = Decimal(str(branch.delivery_fee))
        discount = Decimal("0")
        if body.promo_code:
            promo = await self._promos.get_by_code(body.promo_code)
            if promo and self._promos.is_promo_valid_now(promo) and subtotal >= promo.min_order_amount:
                if promo.discount_type == "percent":
                    discount = (subtotal * promo.discount_value / Decimal("100")).quantize(Decimal("1.00"))
                else:
                    discount = promo.discount_value
        total = subtotal + delivery_fee - discount
        if total < Decimal("0"):
            total = Decimal("0")
        return CheckoutPreviewResponse(
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            discount=discount,
            total=total,
            branch_name=branch.name,
        )

    async def create_order(
        self,
        user_id: int,
        *,
        address_id: int,
        comment: str | None,
        promo_code: str | None,
        idempotency_key: str,
    ) -> Order:
        existing = await self._orders.get_by_idempotency_key(idempotency_key)
        if existing:
            return existing

        lines = await self._verify_lines(user_id)
        if not lines:
            raise EmptyCartError()

        addr = await self._addresses.get_for_user(address_id, user_id)
        if not addr:
            raise NotFoundError("Address not found")

        branches = await self._branches.list_active()
        branch = self._pick_branch(addr, branches)

        subtotal = sum((x.total_price for x in lines), Decimal("0"))
        if subtotal < settings.MIN_ORDER_AMOUNT:
            raise MinOrderAmountError(str(settings.MIN_ORDER_AMOUNT))

        delivery_fee = Decimal(str(branch.delivery_fee))
        discount = Decimal("0")
        promo_row = None
        if promo_code:
            promo_row = await self._promos.get_by_code(promo_code)
            if promo_row and self._promos.is_promo_valid_now(promo_row) and subtotal >= promo_row.min_order_amount:
                if promo_row.discount_type == "percent":
                    discount = (subtotal * promo_row.discount_value / Decimal("100")).quantize(Decimal("1.00"))
                else:
                    discount = promo_row.discount_value

        total_amount = subtotal + delivery_fee - discount
        if total_amount < Decimal("0"):
            total_amount = Decimal("0")

        order = Order(
            user_id=user_id,
            address_id=addr.id,
            branch_id=branch.id,
            status="pending",
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            discount=discount,
            total_amount=total_amount,
            payment_method="cash",
            payment_status="pending",
            comment=comment,
            promo_code=(promo_code.upper().strip() if promo_code else None),
            idempotency_key=idempotency_key,
        )
        self._session.add(order)
        await self._session.flush()

        for vl in lines:
            self._session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=vl.product_id,
                    variant_id=vl.variant_id,
                    quantity=vl.quantity,
                    unit_price=vl.unit_price,
                    total_price=vl.total_price,
                    snapshot_json=vl.snapshot_json,
                )
            )

        if promo_row and discount > 0:
            promo_row.used_count += 1

        await self._cart.clear(user_id)
        await self._session.commit()

        full = await self._orders.get_with_items(order.id)
        assert full is not None
        u = full.user or await self._users.get_by_id(user_id)
        if u:
            await self._notify.send_order_confirmation(u.telegram_id, full)
        await self._notify.notify_courier_group(full)
        return full
