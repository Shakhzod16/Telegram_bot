import base64
import json
from decimal import Decimal
from typing import Any

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.cart import CartItem
from app.repositories.cart import CartRepository
from app.repositories.product import ProductRepository
from app.schemas.cart import CartAddItem, CartItemModifier, CartLineOut, CartOut, CartPatchItem



def encode_item_id(line_key: str) -> str:
    return base64.urlsafe_b64encode(line_key.encode()).decode().rstrip("=")


def decode_item_id(item_id: str) -> str:
    pad = "=" * (-len(item_id) % 4)
    return base64.urlsafe_b64decode(item_id + pad).decode()


def build_line_key(product_id: int, variant_id: int | None, modifier_ids: list[int]) -> str:
    mid = ",".join(str(x) for x in sorted(modifier_ids)) if modifier_ids else ""
    v = str(variant_id) if variant_id is not None else ""
    return f"{product_id}|{v}|{mid}"


class CartService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self._session = session
        self._redis = redis
        self._carts = CartRepository(session)
        self._products = ProductRepository(session)

    def _cart_key(self, user_id: int) -> str:
        return f"cart:{user_id}"

    def _count_key(self, user_id: int) -> str:
        return f"cart_count:{user_id}"

    def _touch_key(self, user_id: int) -> str:
        return f"cart_touch:{user_id}"

    async def _refresh_ttl(self, user_id: int) -> None:
        ttl = settings.CART_TTL_SECONDS
        for k in (self._cart_key(user_id), self._count_key(user_id), self._touch_key(user_id)):
            await self._redis.expire(k, ttl)
        import time

        await self._redis.set(self._touch_key(user_id), str(int(time.time())))

    async def _recompute_count(self, user_id: int) -> int:
        key = self._cart_key(user_id)
        data = await self._redis.hgetall(key)
        total = 0
        for _, raw in data.items():
            row = json.loads(raw)
            total += int(row.get("quantity", 0))
        await self._redis.set(self._count_key(user_id), str(total))
        await self._refresh_ttl(user_id)
        return total

    async def get_cart_count(self, user_id: int) -> int:
        raw = await self._redis.get(self._count_key(user_id))
        if raw:
            return int(raw)
        await self._hydrate_from_db_if_needed(user_id)
        return await self._recompute_count(user_id)

    async def _hydrate_from_db_if_needed(self, user_id: int) -> None:
        key = self._cart_key(user_id)
        if await self._redis.hlen(key) > 0:
            return
        cart = await self._carts.get_by_user_id(user_id)
        if not cart:
            return
        full = await self._carts.get_with_items(cart.id)
        if not full or not full.items:
            return
        for it in full.items:
            lk = build_line_key(it.product_id, it.variant_id, list((it.snapshot_json or {}).get("modifier_ids", [])))
            payload = {
                "quantity": it.quantity,
                "unit_price": str(it.unit_price),
                "product_name": (it.snapshot_json or {}).get("product_name", ""),
                "variant_name": (it.snapshot_json or {}).get("variant_name"),
                "image_url": (it.snapshot_json or {}).get("image_url"),
                "modifier_ids": (it.snapshot_json or {}).get("modifier_ids", []),
                "modifiers": (it.snapshot_json or {}).get("modifiers", []),
            }
            await self._redis.hset(key, lk, json.dumps(payload))
        await self._recompute_count(user_id)

    async def get_cart(self, user_id: int) -> CartOut:
        await self._hydrate_from_db_if_needed(user_id)
        key = self._cart_key(user_id)
        raw_map = await self._redis.hgetall(key)
        lines: list[CartLineOut] = []
        subtotal = Decimal("0")
        for lk_b, raw in raw_map.items():
            lk = lk_b.decode() if isinstance(lk_b, bytes) else lk_b
            row = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
            qty = int(row["quantity"])
            unit = Decimal(row["unit_price"])
            total = unit * qty
            mods_raw = row.get("modifiers") or []
            modifiers = [CartItemModifier.model_validate(x) for x in mods_raw if isinstance(x, dict)]
            pid, _, _ = self._parse_line_key(lk)
            unavailable = False
            p = await self._products.get_by_id_with_relations(pid)
            if not p or not p.is_active:
                unavailable = True
            lines.append(
                CartLineOut(
                    id=encode_item_id(lk),
                    line_key=lk,
                    product_id=pid,
                    product_name=row.get("product_name", ""),
                    variant_id=int(row["variant_id"]) if row.get("variant_id") not in (None, "") else None,
                    variant_name=row.get("variant_name"),
                    quantity=qty,
                    unit_price=unit,
                    total_price=total,
                    modifiers=modifiers,
                    snapshot=row,
                    unavailable=unavailable,
                )
            )
            subtotal += total
        return CartOut(items=lines, subtotal=subtotal)

    def _parse_line_key(self, lk: str) -> tuple[int, int | None, list[int]]:
        parts = lk.split("|")
        pid = int(parts[0])
        v_raw = parts[1] if len(parts) > 1 else ""
        m_raw = parts[2] if len(parts) > 2 else ""
        variant_id = int(v_raw) if v_raw else None
        modifier_ids = [int(x) for x in m_raw.split(",") if x.strip()]
        return pid, variant_id, modifier_ids

    async def add_item(self, user_id: int, body: CartAddItem) -> CartOut:
        p = await self._products.get_by_id_with_relations(body.product_id)
        if not p or not p.is_active:
            raise NotFoundError("Product not found")
        variant_id = body.variant_id
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
        extra = Decimal("0")
        mod_snap: list[dict[str, Any]] = []
        for mid in body.modifier_ids:
            m = mod_by_id.get(mid)
            if not m:
                raise ValidationAppError("Invalid modifier")
            extra += m.price_delta
            mod_snap.append(
                {"id": m.id, "name_uz": m.name_uz, "price_delta": str(m.price_delta)},
            )
        req_ids = {m.id for m in mods if m.is_required}
        if req_ids - set(body.modifier_ids):
            raise ValidationAppError("Missing required modifiers")
        unit = unit + extra
        lk = build_line_key(p.id, variant_id, body.modifier_ids)
        key = self._cart_key(user_id)
        existing = await self._redis.hget(key, lk)
        qty = body.quantity
        if existing:
            prev = json.loads(existing.decode() if isinstance(existing, bytes) else existing)
            qty += int(prev["quantity"])
        payload = {
            "quantity": qty,
            "unit_price": str(unit),
            "product_name": p.name_uz,
            "variant_name": variant_name,
            "variant_id": variant_id,
            "image_url": p.image_url,
            "modifier_ids": body.modifier_ids,
            "modifiers": mod_snap,
        }
        await self._redis.hset(key, lk, json.dumps(payload))
        await self._recompute_count(user_id)
        return await self.get_cart(user_id)

    async def patch_item(self, user_id: int, item_id: str, body: CartPatchItem) -> CartOut:
        lk = decode_item_id(item_id)
        key = self._cart_key(user_id)
        raw = await self._redis.hget(key, lk)
        if not raw:
            raise NotFoundError("Cart item not found")
        if body.quantity <= 0:
            await self._redis.hdel(key, lk)
        else:
            row = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
            row["quantity"] = body.quantity
            await self._redis.hset(key, lk, json.dumps(row))
        await self._recompute_count(user_id)
        return await self.get_cart(user_id)

    async def delete_item(self, user_id: int, item_id: str) -> None:
        lk = decode_item_id(item_id)
        await self._redis.hdel(self._cart_key(user_id), lk)
        await self._recompute_count(user_id)

    async def clear(self, user_id: int) -> None:
        uid = user_id
        await self._redis.delete(self._cart_key(uid), self._count_key(uid), self._touch_key(uid))

    async def sync_redis_to_db(self, user_id: int) -> None:
        key = self._cart_key(user_id)
        raw_map = await self._redis.hgetall(key)
        if not raw_map:
            return
        cart = await self._carts.get_or_create(user_id)
        await self._carts.delete_items(cart.id)
        for lk_b, raw in raw_map.items():
            lk = lk_b.decode() if isinstance(lk_b, bytes) else lk_b
            row = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
            pid, variant_id, _ = self._parse_line_key(lk)
            qty = int(row["quantity"])
            unit = Decimal(row["unit_price"])
            total = unit * qty
            snap: dict[str, Any] = {
                "product_name": row.get("product_name"),
                "variant_name": row.get("variant_name"),
                "image_url": row.get("image_url"),
                "modifier_ids": row.get("modifier_ids", []),
                "modifiers": row.get("modifiers", []),
            }
            self._session.add(
                CartItem(
                    cart_id=cart.id,
                    product_id=pid,
                    variant_id=variant_id,
                    quantity=qty,
                    unit_price=unit,
                    total_price=total,
                    snapshot_json=snap,
                )
            )
        await self._session.commit()

    async def maybe_background_sync(self, user_id: int) -> None:
        import time

        raw = await self._redis.get(self._touch_key(user_id))
        if not raw:
            return
        last = int(raw.decode() if isinstance(raw, bytes) else raw)
        if int(time.time()) - last > settings.CART_SYNC_IDLE_SECONDS:
            await self.sync_redis_to_db(user_id)
